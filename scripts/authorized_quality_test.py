"""Authorized 10-post blind quality test, at most one generation/post. MPL-2.0."""
import copy
import hashlib
import json
import os
import re
import subprocess
from contextlib import ExitStack
from datetime import datetime,timezone
from unittest.mock import patch
import social_pipeline as s
import safe_media
from authorized_chatanywhere_smoke import Audit as OldTransport,summary,SAFE_CODES
import quality_protocol as q
SCOPE='2026-11-07-independent-quality-ten-v1'
REPORT=s.ROOT/'data/quality_test_results.json'
PLAN=s.ROOT/'data/quality_test_plan.json'
MEDIA_REF='51e27179cc4fa3447ce9e011c2e7d194ad5a9520'


def plan_hash(plan):return hashlib.sha256(json.dumps(plan,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def selected_posts(plan):
    current=s.read(s.ROOT/'data/social_posts.json',{})
    old=json.loads(subprocess.run(['git','show',MEDIA_REF+':data/social_posts.json'],capture_output=True,check=True).stdout)
    out=[]
    for p in plan['samples']:
        row=copy.deepcopy(current[p['key']]);historical=old[p['key']]
        for field in ('text','post_id','source','published_at'):
            if row[field]!=p[field] or historical[field]!=p[field]:raise ValueError('sample_identity_mismatch')
        if len(historical['attachments'])!=p['image_count']:raise ValueError('sample_image_identity_mismatch')
        row['attachments']=historical['attachments'];out.append(row)
    return out


class Audit:
    def __init__(self,key,plan,path=REPORT,transport=None):
        self.key=key;self.path=path;self.transport=transport or (lambda *args:OldTransport.http(self,*args));self.current=None
        self.report={'scope':SCOPE,'consumed':True,'started_at':datetime.now(timezone.utc).isoformat(),
            'protocol_version':q.VERSION,'protocol_sha256':q.digest(),'plan_sha256':plan_hash(plan),
            'requested_settings':{'base':q.BASE,'model':q.MODEL,'reasoning_effort':q.EFFORT,'strict_schema':True,'store':False,'tools':False},
            'http_counts':{'generation':0,'model_queries':0,'other_provider_queries':0,'image_downloads':0},
            'quota_before':None,'quota_after':None,'actual_points_deducted':None,
            'quota_note':'Only returned numeric quota headers. Points are not tokens. No confirmed balance endpoint used; absent/delayed values unknown, not zero.',
            'reuse_decision':'No eligible saved response: old prompt coupled target uncertainty to emotion and lacks this protocol/schema and image evidence transcripts. No replay or silent conversion to new answers.',
            'context_policy':'same_post_only','external_context_used':[],
            'candidate_answers_in_prompt':False,'formal_archive_or_pine_modified':False,
            'samples':[{**p,'status':'not_attempted','api_status':None,'schema_valid':False,'download_success':False,'request_includes_image':False,'generation_attempts':0,'context_used':[]} for p in plan['samples']],
            'stopped':False,'completed':False}
        self.save()
    def save(self):s.write(self.path,self.report)
    def generate(self,payload):
        row=self.current
        if row is None or row['generation_attempts'] or self.report['http_counts']['generation']>=10:raise ValueError('generation_budget_exhausted')
        parts=payload['input'][0]['content'];content=json.loads(parts[0]['text'])
        if content['text']!=row['text'] or content['context'] or payload['instructions']!=q.INSTRUCTION or payload['text']['format']['schema']!=q.SCHEMA:raise ValueError('payload_scope_mismatch')
        if payload['model']!=q.MODEL or payload['reasoning']!={'effort':q.EFFORT} or payload.get('tools') or payload['store'] is not False:raise ValueError('required_settings_mismatch')
        images=[x for x in parts if x['type']=='input_image']
        if len(images)!=row['image_count'] or any(not x['image_url'].startswith('data:image/') for x in images):raise ValueError('required_images_missing')
        row.update(generation_attempts=1,request_includes_image=bool(images),images_attached=len(images),status='retry')
        self.report['http_counts']['generation']+=1;self.save()  # Reserve before the sole attempt.
        status,remaining,result=self.transport(q.BASE+'/responses',{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},payload)
        row['api_status']=status
        if not isinstance(result,dict):raise ValueError('invalid_service_response')
        if self.key in json.dumps(result,ensure_ascii=False):raise ValueError('provider_response_contains_credential')
        row.update(service_response=summary(result),remaining_headers=remaining)
        self.report['quota_after']=remaining or None
        if not 200<=status<300:
            error=result.get('error') or {};code=error.get('code') if isinstance(error,dict) else None
            row['error_code']=code if code in SAFE_CODES else None
            self.save();raise s.APIError(status,row['error_code'])
        self.save()
        return result


def run(audit,posts):
    if [p['key'] for p in posts]!=[p['key'] for p in audit.report['samples']]:raise ValueError('sample_scope_mismatch')
    with ExitStack() as stack:
        stack.enter_context(patch.object(safe_media,'assert_online_enabled',return_value=None))
        original=safe_media.PinnedTLS.request
        def download(conn,*args,**kwargs):
            row=audit.current
            if row is None or row.get('image_http_attempts',0)>=row['image_count']:raise ValueError('image_budget_exhausted')
            row['image_http_attempts']=row.get('image_http_attempts',0)+1
            audit.report['http_counts']['image_downloads']+=1;audit.save()
            return original(conn,*args,**kwargs)
        stack.enter_context(patch.object(safe_media.PinnedTLS,'request',download))
        for p,row in zip(posts,audit.report['samples']):
            if row['status'] in ('evaluated_test_only','input_review'):continue
            audit.current=row;row['status']='input_review';audit.save()
            try:
                images=s.image_parts(p)
                row.update(download_success=bool(images) and len(images)==row['image_count'],image_requirement_satisfied=len(images)==row['image_count'],image_evidence=p.pop('_image_evidence',[]))
                result=audit.generate(q.make_payload(p,images))
                answer=q.parse_response(result)
                row.update(schema_valid=True,response_status_service_claim='completed',model_answer=answer,
                    independent_checks=q.inspect(p,answer,row['image_evidence']),status='evaluated_test_only')
            except Exception as exc:
                if '_image_evidence' in p:row['image_evidence']=p.pop('_image_evidence')
                row.update(status='retry' if row['generation_attempts'] else 'input_review',error_type=type(exc).__name__,
                    error_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]{1,100}',str(exc)) else 'Transport/service/media failure; raw error omitted',
                    http_status=getattr(exc,'status',row.get('api_status')))
                audit.report.update(stopped=True,stop_sample=row['number'])
                audit.save();break  # No automatic retry, fallback, paid service or next request on anomaly.
            audit.save()
    audit.report['completed']=all(r['status']=='evaluated_test_only' for r in audit.report['samples'])
    audit.report['finished_at']=datetime.now(timezone.utc).isoformat();audit.save()


def main():
    if os.getenv('AUTHORIZED_QUALITY_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Authorization missing or rerun refused')
    if REPORT.exists() and s.read(REPORT,{}).get('consumed'):raise SystemExit('Quality authorization consumed')
    plan=s.read(PLAN,{})
    if plan.get('protocol_sha256')!=q.digest() or os.getenv('AUTHORIZED_PROTOCOL_SHA256')!=q.digest() or os.getenv('AUTHORIZED_PLAN_SHA256')!=plan_hash(plan):raise SystemExit('Frozen protocol/input mismatch')
    if len(plan['samples'])!=10 or len({p['key'] for p in plan['samples']})!=10:raise SystemExit('Wrong samples')
    key=os.getenv('CHATANYWHERE_API_KEY')
    if not key:raise SystemExit('Missing dedicated Secret; no provider requests')
    audit=Audit(key,plan)
    try:run(audit,selected_posts(plan))
    except Exception as exc:
        audit.report.update(stopped=True,stop_reason='Preflight failed; no retry',error_type=type(exc).__name__);audit.save()
    print(json.dumps({'completed':audit.report['completed'],'http_counts':audit.report['http_counts'],'stopped':audit.report['stopped']}))
    if not audit.report['completed']:raise SystemExit(1)

if __name__=='__main__':main()
