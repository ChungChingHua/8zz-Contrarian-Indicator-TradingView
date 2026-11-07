"""Verify only registered dedicated history workflow with a consumed ledger; no provider key. MPL-2.0."""
import base64,json,os,urllib.request,urllib.error
from authorized_chatanywhere_smoke import StopRedirect
from history_worker import BRANCH,BATCH_ID,LEDGER_PATH
WORKFLOW_ID=410173704
ROOT_API='https://api.github.com/repos/ChungChingHua/8zz-Contrarian-Indicator-TradingView'

def run_check(request):
    contents=request('GET',ROOT_API+'/contents/'+LEDGER_PATH+'?ref=codex%2Fsocial-pipeline-20261106')
    ledger=json.loads(base64.b64decode(contents['content']))
    if (ledger.get('batch_id')!=BATCH_ID or ledger.get('finished') is not True
        or ledger.get('reserved_generation_attempts')!=5 or len(ledger.get('records',[]))!=5
        or any(r['attempts']!=1 or r['status'] not in ('completed_signal','completed_no_signal','pending_confirmation') for r in ledger['records'])):
        raise ValueError('only_fully_consumed_finished_batch_can_be_verified')
    workflow=request('GET',ROOT_API+'/actions/workflows/'+str(WORKFLOW_ID))
    if workflow.get('path')!='.github/workflows/history-batch-manual.yml' or workflow.get('state')!='active':raise ValueError('dedicated_workflow_identity_mismatch')
    # Never dispatch any legacy/default-branch scraper or Pages workflow.
    status=request('POST',ROOT_API+'/actions/workflows/'+str(WORKFLOW_ID)+'/dispatches',{'ref':BRANCH})
    return {'dispatch_http_status':status,'ref':BRANCH,'workflow_id':WORKFLOW_ID,'consumed_generation_attempts':5,'provider_requests_in_verifier':0}

def main():
    if os.getenv('AUTHORIZED_DISPATCH_CHECK')!=BATCH_ID or os.getenv('GITHUB_REF')!='refs/heads/'+BRANCH or os.getenv('GITHUB_RUN_ATTEMPT')!='1':raise SystemExit('Wrong scope or rerun')
    token=os.environ['GH_TOKEN']
    def request(method,url,payload=None):
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'},data=None if payload is None else json.dumps(payload).encode(),method=method)
        try:
            with urllib.request.build_opener(StopRedirect()).open(req,timeout=30) as res:
                return res.status if method=='POST' else json.loads(res.read(300000))
        except urllib.error.HTTPError as exc:raise SystemExit('GitHub control-plane HTTP '+str(exc.code)+'; no retry or raw error logged') from None
    print(json.dumps(run_check(request)))

if __name__=='__main__':main()
