"""Single authorized technical evaluation; never enables the general pipeline. MPL-2.0."""
import base64
import copy
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import social_pipeline as s
import safe_media
from ai_provider import config

SCOPE='2026-11-07-chatanywhere-two-public-posts-v1'
KEYS=('facebook:1703774981107090','threads:4024468641932717746')
MEDIA_REF='51e27179cc4fa3447ce9e011c2e7d194ad5a9520'
REPORT=s.ROOT/'data/social_chatanywhere_authorized_smoke_20261107.json'
SAFE_CODES={'insufficient_quota','rate_limit_exceeded','invalid_api_key','model_not_found','invalid_json_schema','billing_hard_limit_reached','unsupported_value','invalid_value','permission_denied'}


def safe_label(value):
    return value if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',value) and not value.startswith('sk-') else None


def counters_headers(headers):
    names=('x-ratelimit-remaining-requests','x-ratelimit-remaining-tokens','x-ratelimit-reset-requests','x-ratelimit-remaining-points','x-free-points-remaining','x-free-requests-remaining')
    return {k:headers[k] for k in names if headers.get(k) and re.fullmatch(r'[0-9TZ:.+ -]{1,80}',headers[k])}


def summary(result):
    usage={k:v for k,v in (result.get('usage') or {}).items() if k in ('input_tokens','output_tokens','total_tokens') and type(v) is int and 0<=v<=10000000}
    details=(result.get('usage') or {}).get('output_tokens_details') or {}
    if type(details.get('reasoning_tokens')) is int:usage['reasoning_tokens']=details['reasoning_tokens']
    fmt=(result.get('text') or {}).get('format') or {}
    return {'model_claim':safe_label(result.get('model')),'reasoning_claim':{'effort':safe_label((result.get('reasoning') or {}).get('effort'))},
            'format_claim':{'type':safe_label(fmt.get('type')),'strict':fmt.get('strict') is True},'usage':usage or None}


def candidate(result):
    try:
        parts=[c for item in result.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text']
        if len(parts)!=1:return None
        a=json.loads(parts[0]['text'])
        if set(a)!=set(s.SCHEMA['required']):return None
        if any(type(a[k]) is not bool for k in ('clear','investment_related','images_reviewed')):return None
        if type(a['direction']) is not int or a['direction'] not in (-1,0,1):return None
        if type(a['strength']) is not int or a['strength'] not in (1,2,3):return None
        if any(not isinstance(a[k],str) or len(a[k])>4000 for k in ('target','ticker','reason','author_commentary','quoted_summary')):return None
        return a
    except (TypeError,ValueError,KeyError):return None


class StopRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise urllib.error.HTTPError(req.full_url,code,'Redirect refused',headers,fp)


class Audit:
    def __init__(self,key,path=REPORT,transport=None,expected_effort="low",max_generations=2):
        self.key=key;self.path=path;self.transport=transport or self.http
        self.current=None;self.expected_effort=expected_effort;self.max_generations=max_generations
        self.report={'scope':SCOPE,'consumed':True,'provider':'chatanywhere','requested_model':'gpt-5-mini','reasoning_requested':'low',
          'started_at':datetime.now(timezone.utc).isoformat(),'http_counts':{'model_queries':0,'generation':0,'other_provider_queries':0,'image_downloads':0},
          'events':[],'samples':[],'passed':False,'quota_before':None,'quota_after':None,
          'quota_note':'Only service-returned headers are recorded. No confirmed point-balance API; missing or delayed values remain unknown. Points are not tokens; no zero-deduction claim.',
          'unchanged':'General pause, archive, Pine, schedule and Pages remain unchanged; no batch or merge.'}
        self.save()
    def save(self):s.write(self.path,self.report)
    def http(self,url,headers,payload):
        req=urllib.request.Request(url,headers=headers,data=None if payload is None else json.dumps(payload).encode())
        opener=urllib.request.build_opener(StopRedirect())
        try:
            with opener.open(req,timeout=90) as res:
                raw=res.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError('response_too_large')
                return res.status,counters_headers(res.headers),json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw=exc.read(65536)
            try:body=json.loads(raw)
            except ValueError:body={}
            return exc.code,counters_headers(exc.headers),body
    def call(self,url,headers=None,payload=None,retries=1):
        kind='model_queries' if url in ('https://api.chatanywhere.org/v1/models','https://api.chatanywhere.tech/v1/models') and payload is None else 'generation'
        if retries!=1 or url not in ('https://api.chatanywhere.org/v1/models','https://api.chatanywhere.org/v1/responses','https://api.chatanywhere.tech/v1/models','https://api.chatanywhere.tech/v1/responses'):raise ValueError('unauthorized_route_or_retry')
        if headers!={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'}:raise ValueError('credential_scope_mismatch')
        cap=1 if kind=='model_queries' else self.max_generations
        if self.report['http_counts'][kind]>=cap:raise ValueError('request_budget_exhausted')
        if kind=='generation':
            if self.current is None or payload.get('model')!='gpt-5-mini' or payload.get('reasoning')!={'effort':self.expected_effort}:raise ValueError('generation_scope_mismatch')
            fmt=payload.get('text',{}).get('format',{})
            content=payload['input'][0]['content']
            if not fmt.get('strict') or fmt.get('schema')!=s.SCHEMA or payload.get('tools'):raise ValueError('required_format_or_no_tools_violated')
            if json.loads(content[0]['text'])['text']!=self.current['text']:raise ValueError('unexpected_post_content')
            images=[p for p in content if p.get('type')=='input_image']
            if len(images)!=1 or not images[0]['image_url'].startswith('data:image/'):raise ValueError('required_image_missing')
            self.current.update(images_attached=len(images),request_includes_image=True)
        self.report['http_counts'][kind]+=1
        event={'kind':kind,'http_status':None,'remaining_headers':{}}
        self.report['events'].append(event);self.save()  # Reserve before network; never auto retry.
        status,remaining,result=self.transport(url,headers,payload)
        if not isinstance(result,dict):raise ValueError('invalid_response')
        if self.key in json.dumps(result,ensure_ascii=False):raise ValueError('provider_response_contains_credential')
        event.update(http_status=status,remaining_headers=remaining)
        if kind=='model_queries':self.report['quota_before']=remaining or None
        else:
            self.report['quota_after']=remaining or None
            self.current.update(api_status=status,service_response=summary(result),schema_valid=candidate(result) is not None)
            parsed=candidate(result)
            if parsed:self.current['service_candidate']=parsed
        self.save()
        if not 200<=status<300:
            error=result.get('error') or {}
            code=error.get('code') if isinstance(error,dict) and error.get('code') in SAFE_CODES else None
            event['error_code']=code
            event['error_reason']='Service rejected required request; raw error omitted to protect credentials/content'
            self.save();raise s.APIError(status,code)
        return result


def selected_posts():
    current=s.read(s.ROOT/'data/social_posts.json',{})
    # Existing historical public archive, read locally only. Never republish signed URLs.
    proc=subprocess.run(['git','show',MEDIA_REF+':data/social_posts.json'],capture_output=True,check=True)
    historical=json.loads(proc.stdout)
    selected=[]
    for key in KEYS:
        p=copy.deepcopy(current[key]);old=historical[key]
        if p['text']!=old['text'] or p['post_id']!=old['post_id'] or len(old['attachments'])!=1:raise ValueError('sample_identity_mismatch')
        p['attachments']=old['attachments'];selected.append(p)
    return selected


def run(audit,posts,headers):
    # Scoped in-memory authorization for these fixed samples only; pause file remains true.
    provider=config()
    if tuple(p['key'] for p in posts)!=KEYS:raise ValueError('unauthorized_samples')
    with ExitStack() as stack:
        stack.enter_context(patch.object(s,'credentials',return_value=(provider,headers)))
        stack.enter_context(patch.object(s,'request_json',side_effect=audit.call))
        stack.enter_context(patch.object(s,'MODEL','gpt-5-mini'))
        original=safe_media.PinnedTLS.request
        def image_request(conn,method,path,*args,**kwargs):
            if audit.current is None or audit.report['http_counts']['image_downloads']>=2:raise ValueError('image_scope_budget_exhausted')
            audit.report['http_counts']['image_downloads']+=1;audit.save()
            return original(conn,method,path,*args,**kwargs)
        stack.enter_context(patch.object(safe_media.PinnedTLS,'request',image_request))
        stack.enter_context(patch.object(safe_media,'assert_online_enabled',return_value=None))
        audit.report['samples']=[{**{k:p[k] for k in ('key','source','url','display_time','text')},
            'status':'not_sent','api_status':None,'download_success':False,'request_includes_image':False,'schema_valid':False} for p in posts]
        audit.save()
        model_result=audit.call(provider['base']+'/models',headers,retries=1)
        models=sorted(x['id'] for x in model_result.get('data',[]) if isinstance(x.get('id'),str) and re.fullmatch(r'gpt-5[A-Za-z0-9._-]{0,80}',x['id']))
        audit.report['available_gpt5_models_claim']=models;audit.save()
        if 'gpt-5-mini' not in models:raise ValueError('requested_model_not_listed_no_fallback')
        for p,row in zip(posts,audit.report['samples']):
            row['status']='retry';audit.current=row;audit.save()
            try:
                analysis=s.classify(p)
                row.update(status=analysis['status'],analysis=analysis,download_success=bool(analysis.get('image_evidence')),necessary_settings_validated=True)
            except Exception as exc:
                row.update(status='retry',error_type=type(exc).__name__,http_status=getattr(exc,'status',None),error_code=getattr(exc,'code',None),
                           image_evidence=p.pop('_image_evidence',[]),
                           reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]+',str(exc)) else 'Request or image failed; no raw error stored')
                row['download_success']=bool(row['image_evidence'])
                audit.save();raise  # Stop on any unsupported requirement/failure; no retry or second call.
            audit.save()
        audit.report['passed']=len(audit.report['samples'])==2 and all(x.get('necessary_settings_validated') for x in audit.report['samples'])
        audit.save()


def main():
    if os.getenv('AUTHORIZED_SMOKE_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('One-shot authorization missing or rerun refused')
    if REPORT.exists() and s.read(REPORT,{}).get('consumed'):raise SystemExit('Authorization already consumed; no further requests')
    key=os.getenv('CHATANYWHERE_API_KEY')
    if not key:raise SystemExit('Missing CHATANYWHERE_API_KEY; no requests made')
    c=config()
    if c['provider']!='chatanywhere' or c['model']!='gpt-5-mini' or c['effort']!='low':raise SystemExit('Provider/model/effort mismatch')
    audit=Audit(key)
    try:
        posts=selected_posts()
        run(audit,posts,{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    except Exception as exc:
        audit.report.update(stopped=True,error_type=type(exc).__name__,http_status=getattr(exc,'status',None),error_code=getattr(exc,'code',None),
                            stop_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]+',str(exc)) else 'Stopped without retries; inspect sanitized evidence')
        audit.save()
    finally:
        audit.report['finished_at']=datetime.now(timezone.utc).isoformat();audit.save()
    print(json.dumps({'passed':audit.report['passed'],'http_counts':audit.report['http_counts'],'stopped':audit.report.get('stopped',False)}))
    if not audit.report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
