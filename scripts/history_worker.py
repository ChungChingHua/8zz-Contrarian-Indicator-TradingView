"""One authorized original-author batch with durable GitHub CAS checkpoints. MPL-2.0."""
import base64,copy,hashlib,json,os,re,subprocess,urllib.error,urllib.parse,urllib.request
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import original_author as policy
import social_pipeline as s
import safe_media
from review_rules import media_plan
from authorized_chatanywhere_smoke import StopRedirect,counters_headers,summary,SAFE_CODES
from history_plan import BATCH_ID,PLAN
ROOT=policy.ROOT
BRANCH='codex/social-pipeline-20261106'
LEDGER_PATH='data/history_progress/'+BATCH_ID+'.json'
LOCAL=ROOT/LEDGER_PATH
BASE='https://api.chatanywhere.tech/v1'

def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()

def safe_response(value,secrets):
    body=json.dumps(value,ensure_ascii=False)
    if any(k and k in body for k in secrets):raise ValueError('response_reflects_credential')
    if re.search(r'\bsk-[A-Za-z0-9_-]{24,}',body):raise ValueError('response_contains_key_pattern')
    def clean(x):
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k!='encrypted_content'}
        if isinstance(x,list):return [clean(v) for v in x]
        return x
    return {'json':clean(value),'complete_json_sha256':digest(value),'redaction_note':'Opaque encrypted_content omitted; all classification, usage and ordinary metadata retained. No claim of original HTTP bytes.'}

class GitHubStore:
    def __init__(self,token):
        self.token=token;self.sha=None
        self.url='https://api.github.com/repos/ChungChingHua/8zz-Contrarian-Indicator-TradingView/contents/'+LEDGER_PATH
    def _request(self,method,url,payload=None):
        req=urllib.request.Request(url,method=method,headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json'},data=None if payload is None else json.dumps(payload).encode())
        try:
            with urllib.request.build_opener(StopRedirect()).open(req,timeout=30) as res:return json.loads(res.read(2_000_000))
        except urllib.error.HTTPError as exc:
            if method=='GET' and exc.code==404:return None
            raise RuntimeError('GitHub checkpoint HTTP '+str(exc.code)) from None
        except Exception:raise RuntimeError('GitHub checkpoint transport failure; no retry') from None
    def load(self):
        d=self._request('GET',self.url+'?ref='+urllib.parse.quote(BRANCH,safe=''))
        if d is None:return None
        self.sha=d['sha'];return json.loads(base64.b64decode(d['content']))
    def save(self,state):
        raw=json.dumps(s.public_safe(state),ensure_ascii=False,indent=2)+'\n'
        if self.token in raw:raise ValueError('checkpoint_contains_credential')
        if len(raw.encode())>900000:raise ValueError('checkpoint_size_limit')
        body={'message':'data: durable history checkpoint [skip ci]','branch':BRANCH,'content':base64.b64encode(raw.encode()).decode()}
        if self.sha:body['sha']=self.sha
        result=self._request('PUT',self.url,body)
        self.sha=result['content']['sha']  # ACK required before any generation.

class Provider:
    def __init__(self,key):self.key=key
    def __call__(self,payload):
        req=urllib.request.Request(BASE+'/responses',headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},data=json.dumps(payload).encode())
        try:
            with urllib.request.build_opener(StopRedirect()).open(req,timeout=90) as res:
                raw=res.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError('response_too_large')
                try:body=json.loads(raw)
                except ValueError:body={'invalid_json_response_sha256':hashlib.sha256(raw).hexdigest()}
                return res.status,counters_headers(res.headers),body
        except urllib.error.HTTPError as exc:
            raw=exc.read(65536)
            try:body=json.loads(raw)
            except ValueError:body={}
            return exc.code,counters_headers(exc.headers),body


def original_posts(plan):
    old=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],capture_output=True,check=True).stdout)
    current=s.read(ROOT/'data/social_posts.json',{})
    out=[]
    for row in plan['posts']:
        p=copy.deepcopy(old[row['key']])
        for k in ('text','post_id','published_at','source'):
            if p[k]!=row[k] or current[row['key']][k]!=row[k]:raise ValueError('post_identity_changed')
        out.append(p)
    return out


def prepare_media(post):
    scope=media_plan(post)  # No text-length or emotion gate.
    parts=[];evidence=[];unanalysed=copy.deepcopy(scope['unanalysed_media']);failures=[]
    with patch.object(safe_media,'assert_online_enabled',return_value=None):
        for index,attachment in zip(scope['image_attachment_indices'],scope['image_attachments']):
            media={**post,'attachments':[attachment]}
            try:
                supplied=s.image_parts(media)
            except OSError as exc:
                if exc.errno!=101:raise  # Only established network-unreachable case, not TLS/SSRF/format failures.
                failure={'attachment_index':index,'kind':'image','status':'圖片未分析','error_type':type(exc).__name__,'errno':101,'reason':'network_unreachable'}
                unanalysed.append(failure);failures.append(failure);continue
            parts.extend(supplied)
            evidence.extend({**e,'attachment_index':index} for e in media.get('_image_evidence',[]))
    if failures:analysis_scope='text_and_available_images' if parts else 'text_only_images_unavailable'
    elif not parts and not unanalysed:analysis_scope='text_only_no_attachments'
    else:analysis_scope=scope['analysis_scope']
    info={'analysis_scope':analysis_scope,'unanalysed_media':unanalysed,'media_failures':failures,
          'images_supplied':len(parts),'image_evidence':evidence,'human_image_verified':False,
          'source_note':'Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule.'}
    return parts,info

class Worker:
    def __init__(self,store,provider,plan,prepare=prepare_media,secrets=(),local=LOCAL,after_response=None):
        self.store=store;self.provider=provider;self.plan=plan;self.prepare=prepare;self.secrets=secrets;self.local=local;self.after_response=after_response
        self.state=store.load()
        if self.state:
            if self.state['batch_id']!=BATCH_ID or self.state['plan_sha256']!=digest(plan) or self.state['rule_sha256']!=policy.fingerprint():raise ValueError('ledger_manifest_mismatch')
        else:
            self.state={'batch_id':BATCH_ID,'plan_sha256':digest(plan),'rule_version':policy.VERSION,'rule_sha256':policy.fingerprint(),
               'created_at':now(),'max_generations':5,'reserved_generation_attempts':0,'stopped':False,'finished':False,
               'provider_settings':{'base':BASE,'model':'gpt-5-mini','reasoning_effort':'minimal','strict_schema':True,'store':False,'tools':False},
               'quota_before':None,'quota_after':None,'actual_points_deducted':None,
               'quota_note':'Returned numeric headers only. Missing/delayed quota and actual deductions unknown; points are not tokens.',
               'response_storage_note':'Provider JSON retained except opaque encrypted_content; complete JSON hash recorded. No headers/credentials or signed media URLs.',
               'records':[{**r,'status':'not_started','attempts':0,'context_used':[]} for r in plan['posts']]}
            self.save()
    def save(self):
        self.state['updated_at']=now()
        serialized=json.dumps(self.state,ensure_ascii=False)
        if any(k and k in serialized for k in self.secrets):raise ValueError('checkpoint_contains_credential')
        pending=self.local.with_suffix('.uncommitted.json')
        s.write(pending,self.state)
        self.store.save(self.state)
        s.write(self.local,self.state)
        pending.unlink(missing_ok=True)
    def resume_unsent_media_failure(self):
        if (self.state['reserved_generation_attempts']!=0 or not self.state['stopped']
            or self.state.get('stop_reason')!='media_preflight_failure' or self.state.get('unsent_media_recovery_used')
            or any(r['attempts'] or 'http_status' in r or r['status'] not in ('input_failure','not_started') for r in self.state['records'])):
            raise ValueError('only_proven_zero_generation_media_failure_can_resume')
        for r in self.state['records']:
            if r['status']=='input_failure':
                r.setdefault('input_failure_history',[]).append({'status':'input_failure','error_type':r.get('error_type'),'reason':r.get('reason'),'attempts':0})
                r.update(status='not_started');r.pop('error_type',None);r.pop('reason',None)
        self.state.update(stopped=False,stop_reason=None,unsent_media_recovery_used=True,
            recovery_note='Operator continued the same authorized batch after proven 0-generation IPv6 network failure; explicit unavailable-image scope, no TLS/host bypass or generation retry.')
        self.save()

    def run(self,posts):
        if self.state['finished'] or self.state['stopped']:return
        if any(r['status']=='unknown' for r in self.state['records']):
            self.state.update(stopped=True,stop_reason='unknown_request_requires_manual_reconciliation');self.save();return
        for p,r in zip(posts,self.state['records']):
            if p['key']!=r['key']:raise ValueError('post_order_mismatch')
            if r['status']!='not_started':continue
            if self.state['reserved_generation_attempts']>=5:break
            try:parts,scope=self.prepare(p)
            except Exception as exc:
                r.update(status='input_failure',error_type=type(exc).__name__,reason='Media preflight failed; no generation, no URL/raw error logged')
                self.state.update(stopped=True,stop_reason='media_preflight_failure');self.save();return
            body=policy.payload(p,parts,scope)
            r.update(media_scope=scope,request_sha256=digest(body),status='unknown',attempts=1,dispatch_reserved_at=now())
            self.state['reserved_generation_attempts']+=1
            self.save()  # Remote CAS commit ACK before request; crash from here is never replayed.
            try:
                status,quota,response=self.provider(body)
                if self.after_response:self.after_response()  # Simulation crash point (no production callback).
            except Exception as exc:
                r.update(status='unknown',error_type=type(exc).__name__,reason='Request may have been sent; never automatically resend')
                self.state.update(stopped=True,stop_reason='uncertain_provider_transport');self.save();return
            r.update(http_status=status,remaining_headers=quota)
            self.state['quota_after']=quota or None
            try:
                r['raw_response']=safe_response(response,self.secrets)
                r['service_response']=summary(response) if isinstance(response,dict) else {}
                if not 200<=status<300:
                    error=response.get('error') or {};code=error.get('code') if isinstance(error,dict) else None
                    r['api_error_code']=code if code in SAFE_CODES else None
                    raise ValueError('provider_http_error')
                a=policy.parse(response,len(parts));r['processed']=policy.process(p,a)
                r['status']='completed_signal' if r['processed']['status']=='done' else 'pending_confirmation' if r['processed']['status']=='review' else 'completed_no_signal'
            except Exception as exc:
                r.update(status='technical_failure',error_type=type(exc).__name__,reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]+',str(exc)) else 'Invalid required provider response; raw error omitted')
                self.state.update(stopped=True,stop_reason='api_or_required_format_failure')
            self.save()  # Result must be durably stored before considering next post.
            if self.state['stopped']:return
            remaining=[v for k,v in quota.items() if k in ('x-ratelimit-remaining-requests','x-ratelimit-remaining-points','x-free-points-remaining','x-free-requests-remaining')]
            if any(re.fullmatch(r'0+(?:\.0+)?',v.strip()) for v in remaining):
                self.state.update(stopped=True,stop_reason='returned_allowance_exhausted');self.save();return
        self.state['finished']=True;self.save()


def main():
    if os.getenv('AUTHORIZED_HISTORY_BATCH')!=BATCH_ID or os.getenv('GITHUB_REF')!='refs/heads/'+BRANCH:raise SystemExit('Wrong authorization or branch')
    plan=s.read(PLAN,{})
    if plan.get('rule_sha256')!=policy.fingerprint() or os.getenv('AUTHORIZED_RULE_SHA256')!=policy.fingerprint() or os.getenv('AUTHORIZED_PLAN_SHA256')!=digest(plan) or len(plan['posts'])>5:raise SystemExit('Frozen plan/policy mismatch')
    key=os.environ.pop('CHATANYWHERE_API_KEY','');gh=os.environ.pop('GH_TOKEN','')
    if not key or not gh:raise SystemExit('Missing dedicated Secrets; no provider requests')
    store=GitHubStore(gh)
    worker=Worker(store,Provider(key),plan,secrets=(key,gh))
    if os.getenv('RESUME_UNSENT_MEDIA_FAILURE')=='1':worker.resume_unsent_media_failure()
    worker.run(original_posts(plan))
    print(json.dumps({'finished':worker.state['finished'],'stopped':worker.state['stopped'],'reserved_attempts':worker.state['reserved_generation_attempts'],'statuses':[r['status'] for r in worker.state['records']]}))

if __name__=='__main__':main()
