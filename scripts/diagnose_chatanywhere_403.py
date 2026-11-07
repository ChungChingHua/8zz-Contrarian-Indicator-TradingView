"""Authorized, bounded 403 diagnosis. No retries, no unconfirmed destinations. MPL-2.0."""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from unittest.mock import patch
import authorized_chatanywhere_smoke as a

SCOPE='2026-11-07-chatanywhere-403-diagnosis-v1'
REPORT=a.s.ROOT/'data/social_chatanywhere_403_diagnostic_20261107.json'
HOSTS=('https://api.chatanywhere.org','https://api.chatanywhere.tech')


def redact(value,key):
    text=str(value).replace(key,'[redacted]') if key else str(value)
    text=re.sub(r'sk-[A-Za-z0-9*_.-]+','[redacted-key]',text)
    text=re.sub(r'data:[^\s\"\']+','[redacted-data]',text)
    text=re.sub(r'Bearer\s+\S+','Bearer [redacted]',text,flags=re.I)
    text=re.sub(r'https?://\S+','[url]',text)
    text=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','[redacted-jwt]',text)
    return re.sub(r'[\x00-\x1f\x7f]',' ',text)[:500]


def evidence(status,headers,raw,key):
    ct=headers.get('Content-Type','').split(';')[0].strip().lower()
    safe={'content_type':ct if re.fullmatch(r'[a-z0-9.+-]+/[a-z0-9.+-]+',ct) else None}
    for name in ('server','via','cf-ray','x-request-id','x-envoy-upstream-service-time','retry-after','x-mitmproxy-blocked-reason','cf-mitigated','x-squid-error','x-denied-reason','x-proxy-error'):
        value=headers.get(name)
        if value:safe[name]=redact(value,key)[:100]
    safe.update(a.counters_headers(headers))
    try:body=json.loads(raw)
    except (ValueError,UnicodeDecodeError):body={}
    error=body.get('error',{}) if isinstance(body,dict) else {}
    if not isinstance(error,dict):error={'message':error}
    message=error.get('message') or (body.get('message') if isinstance(body,dict) else '')
    text=raw.decode('utf-8',errors='replace')
    lower=text.lower()
    policy=bool(headers.get('x-mitmproxy-blocked-reason')) or headers.get('cf-mitigated')=='challenge' or ('cloudflare' in lower and any(x in lower for x in ('captcha','cf_chl_opt')))  or any(x in lower for x in ('request forbidden by organizational policy','blocked by network policy','domain is not allowed','network access denied'))
    markers=[x for x in ('cloudflare','access denied','forbidden','captcha','chatanywhere_error','insufficient_quota','invalid_api_key') if x in lower]
    clean=redact(message or ('HTML/text response omitted' if '<' in text else text),key)
    return body,{'http_status':status,'headers':safe,'error_type':redact(error.get('type',''),key)[:100] or None,
        'error_code':redact(error.get('code',''),key)[:100] or None,'error_message_redacted':clean,
        'body_markers':markers,'explicit_network_policy_block':policy,'redacted_body_sha256':hashlib.sha256(clean.encode()).hexdigest(),
        'attribution_note':'Headers/body are evidence, not independent proof of the responder identity.'}


class DiagnosticAudit(a.Audit):
    def __init__(self,key,path=REPORT,transport=None):
        super().__init__(key,path,transport)
        self.report.update(scope=SCOPE,diagnostic_budget=3,generation_budget=2,diagnostic_requests=0,diagnostic_events=[],
            injection_check={'secret_present':bool(key),'contains_crlf':any(c in key for c in '\r\n'),'surrounding_whitespace':key!=key.strip(),'already_has_bearer_prefix':key.lower().startswith('bearer ')},
            url_check={'base':'https://api.chatanywhere.org/v1','models':'https://api.chatanywhere.org/v1/models','v1_count':1,'authorization_scheme':'Bearer, once'},
            docs={'models':'https://chatanywhere.apifox.cn/api-92222074','free_models':'https://github.com/chatanywhere/GPT_API_free','free_model_list_denial_confirmed':False},
            proxy_environment_present={k:bool(os.getenv(k)) for k in ('HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy')})
        self.chosen_host=HOSTS[0];self.cached_models=None;self.save()
    def exchange(self,url,headers,payload):
        if urllib.parse.urlsplit(url).scheme!='https' or not any(url==h+p for h in HOSTS for p in ('/v1/models','/v1/responses')):raise ValueError('unconfirmed_endpoint')
        req=urllib.request.Request(url,headers=headers,data=None if payload is None else json.dumps(payload).encode())
        opener=urllib.request.build_opener(a.StopRedirect())
        try:
            with opener.open(req,timeout=90) as res:
                raw=res.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError('response_too_large')
                body,meta=evidence(res.status,res.headers,raw,self.key)
        except urllib.error.HTTPError as exc:
            body,meta=evidence(exc.code,exc.headers,exc.read(65536),self.key)
        return body,meta
    def diagnostic(self,host,authenticated):
        if self.report['diagnostic_requests']>=3:raise ValueError('diagnostic_budget_exhausted')
        self.report['diagnostic_requests']+=1
        self.report['http_counts']['model_queries']+=1
        event={'url':host+'/v1/models','method':'GET','authenticated':authenticated,'http_status':None}
        self.report['diagnostic_events'].append(event);self.save()
        headers={'Accept':'application/json'}
        if authenticated:headers['Authorization']='Bearer '+self.key
        body,meta=self.exchange(event['url'],headers,None)
        event.update(meta);self.save()
        if authenticated and meta['http_status']==200 and isinstance(body,dict) and isinstance(body.get('data'),list):
            self.chosen_host=host;self.cached_models=body
            self.report['quota_before']=a.counters_headers(meta.get('headers',{})) or None
            return True
        return False
    def generation_transport(self,url,headers,payload):
        actual=self.chosen_host+'/v1/responses'
        body,meta=self.exchange(actual,headers,payload)
        self.report['events'][-1]['endpoint']=actual
        self.report['events'][-1]['diagnostic_metadata']=meta
        self.save()
        return meta['http_status'],a.counters_headers(meta.get('headers',{})),body
    def call(self,url,headers=None,payload=None,retries=1):
        if url.endswith('/models'):
            if not self.cached_models:raise ValueError('no_confirmed_model_list_no_blind_generation')
            self.report['model_result_reused_without_new_http']=True;self.save();return self.cached_models
        if url!=self.chosen_host+'/v1/responses':raise ValueError('unexpected_generation_endpoint')
        # Parent enforces the original payload, key and hard two-generation limit.
        self.transport=self.generation_transport
        return super().call(HOSTS[0]+'/v1/responses',headers,payload,retries)


def main():
    if os.getenv('AUTHORIZED_SMOKE_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106' or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Authorization missing or rerun refused')
    if REPORT.exists() and a.s.read(REPORT,{}).get('consumed'):raise SystemExit('Diagnostic authorization consumed')
    c=a.config()
    if c['provider']!='chatanywhere' or c['model']!='gpt-5-mini' or c['effort']!='low':raise SystemExit('Provider/model/effort mismatch')
    key=os.getenv('CHATANYWHERE_API_KEY')
    if not key:raise SystemExit('CHATANYWHERE_API_KEY absent; no network requests')
    audit=DiagnosticAudit(key)
    try:
        flags=audit.report['injection_check']
        if flags['contains_crlf'] or flags['surrounding_whitespace'] or flags['already_has_bearer_prefix']:raise ValueError('secret_format_must_be_corrected_without_exposing_value')
        ok=audit.diagnostic(HOSTS[0],True)
        first=audit.report['diagnostic_events'][-1]
        if not ok and not first['explicit_network_policy_block']:
            # Same endpoint without credentials distinguishes auth handling from a shared block page.
            audit.diagnostic(HOSTS[0],False)
            if not audit.report['diagnostic_events'][-1]['explicit_network_policy_block']:
                ok=audit.diagnostic(HOSTS[1],True)  # Both hosts are explicitly documented by the service.
        if not ok:raise ValueError('403_cause_unresolved_or_access_denied_no_blind_generation')
        provider=a.config();provider['base']=audit.chosen_host+'/v1'
        audit.report['selected_base']=provider['base'];audit.save()
        with patch.object(a,'config',return_value=provider):
            a.run(audit,a.selected_posts(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    except Exception as exc:
        audit.report.update(stopped=True,error_type=type(exc).__name__,http_status=getattr(exc,'status',None),error_code=getattr(exc,'code',None),
            stop_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[a-z0-9_]+',str(exc)) else 'Stopped safely; no automatic retry')
    finally:
        audit.report['finished_at']=datetime.now(timezone.utc).isoformat();audit.save()
    print(json.dumps({'diagnostic_requests':audit.report['diagnostic_requests'],'http_counts':audit.report['http_counts'],'passed':audit.report['passed']}))
    if not audit.report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
