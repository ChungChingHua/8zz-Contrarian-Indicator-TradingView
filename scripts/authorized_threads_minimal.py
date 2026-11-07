"""One new Threads request, reuse Facebook evidence offline. MPL-2.0."""
import copy
import json
import os
import re
from contextlib import ExitStack
from datetime import datetime,timezone
from unittest.mock import patch
import authorized_chatanywhere_smoke as old
from ai_provider import config
s=old.s
SCOPE='2026-11-07-threads-minimal-once-v1'
REPORT=s.ROOT/'data/social_chatanywhere_minimal_20261107.json'


def reused_facebook():
    saved=s.read(s.ROOT/'data/social_chatanywhere_403_diagnostic_20261107.json',{})['samples'][0]
    row=copy.deepcopy(saved)
    a=row['service_candidate']
    reconstructed={'status':'completed','model':row['service_response']['model_claim'],
        'reasoning':row['service_response']['reasoning_claim'],'text':{'format':row['service_response']['format_claim']},
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(a,ensure_ascii=False)}]}]}
    # Structural revalidation only: these are reconstructed saved fields, not the raw response.
    with patch.object(s,'credentials',return_value=({'provider':'chatanywhere','base':'https://api.chatanywhere.tech/v1','effort':'minimal'}, {'Authorization':'Bearer offline-placeholder'})),patch.object(s,'request_json',return_value=reconstructed),patch.object(s,'MODEL','gpt-5-mini'),patch.object(s,'image_parts',return_value=[{'type':'input_image','image_url':'data:image/jpeg;base64,offline'}]):
        result=s.classify({'text':row['text'],'quoted_content':{},'quote_flag':False,'attachments':[{}]})
    row.update(status='review',reused=True,new_requests=0,offline_fields_revalidated=True,
        requested_settings_original={'model':'gpt-5-mini','reasoning_effort':'low'},
        accepted_service_report_for_technical_evaluation='minimal',
        limitation='Full raw response unavailable. Revalidated saved classification fields only; no fresh image inspection or independent model/reasoning verification. Original audit remains unchanged.')
    if result['direction']!=0 or result['clear']:raise ValueError('cached_facebook_requires_review')
    return row


class ThreadsAudit(old.Audit):
    def call(self,url,headers=None,payload=None,retries=1):
        if url!='https://api.chatanywhere.tech/v1/responses' or payload is None:raise ValueError('only_threads_generation_authorized')
        return super().call(url,headers,payload,retries)


def run(audit,post,headers):
    provider=config()
    if post['key']!=old.KEYS[1] or provider['base']!='https://api.chatanywhere.tech/v1' or provider['effort']!='minimal':raise ValueError('scope_mismatch')
    row={k:post[k] for k in ('key','source','url','display_time','text')}
    row.update(status='retry',api_status=None,download_success=False,request_includes_image=False,schema_valid=False)
    audit.report['samples'].append(row);audit.current=row;audit.save()
    with ExitStack() as stack:
        stack.enter_context(patch.object(s,'credentials',return_value=(provider,headers)))
        stack.enter_context(patch.object(s,'request_json',side_effect=audit.call))
        stack.enter_context(patch.object(s,'MODEL','gpt-5-mini'))
        stack.enter_context(patch.object(s,'INSTRUCTION',s.INSTRUCTION+' 請在 reason 中分別指出文字與實際附圖可見的投資證據；若圖片只有生活物品或玩笑，請明說。不能僅因「下週穩了」推測交易立場或標的。'))
        stack.enter_context(patch.object(old.safe_media,'assert_online_enabled',return_value=None))
        original=old.safe_media.PinnedTLS.request
        def download(conn,*args,**kwargs):
            if audit.report['http_counts']['image_downloads']>=1:raise ValueError('image_budget_exhausted')
            audit.report['http_counts']['image_downloads']+=1;audit.save()
            return original(conn,*args,**kwargs)
        stack.enter_context(patch.object(old.safe_media.PinnedTLS,'request',download))
        try:
            result=s.classify(post)
            row.update(status=result['status'],analysis=result,download_success=bool(result['image_evidence']),necessary_settings_validated=True)
            audit.report['passed']=True
        finally:
            if '_image_evidence' in post:
                row['image_evidence']=post.pop('_image_evidence');row['download_success']=bool(row['image_evidence'])
            audit.save()


def main():
    if os.getenv('AUTHORIZED_SMOKE_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Authorization missing or rerun refused')
    if REPORT.exists() and s.read(REPORT,{}).get('consumed'):raise SystemExit('Authorization consumed')
    cached=reused_facebook()  # No key or network needed for this check.
    c=config()
    if c['provider']!='chatanywhere' or c['model']!='gpt-5-mini' or c['effort']!='minimal':raise SystemExit('Configuration mismatch')
    key=os.getenv('CHATANYWHERE_API_KEY')
    if not key:raise SystemExit('Missing dedicated secret; no requests')
    audit=ThreadsAudit(key,REPORT,expected_effort='minimal',max_generations=1)
    audit.report.update(scope=SCOPE,reasoning_requested='minimal',requested_settings={'base':c['base'],'model':'gpt-5-mini','reasoning_effort':'minimal','strict_schema':True,'images_required':True},samples=[cached],model_listing='Reuse saved successful .tech model listing; no new query. All model/reasoning metadata are service claims.')
    audit.save()
    try:
        post=old.selected_posts()[1]
        run(audit,post,{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    except Exception as exc:
        audit.report.update(stopped=True,error_type=type(exc).__name__,http_status=getattr(exc,'status',None),stop_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]+',str(exc)) else 'Stopped; raw exception omitted')
    finally:
        audit.report['finished_at']=datetime.now(timezone.utc).isoformat();audit.save()
    print(json.dumps({'passed':audit.report['passed'],'http_counts':audit.report['http_counts']}))
    if not audit.report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
