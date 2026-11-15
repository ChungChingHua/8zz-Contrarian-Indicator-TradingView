"""Extend the saved one-time history cutoff without replaying completed windows. MPL-2.0."""
import copy,json,os,sys
from datetime import datetime,timedelta
from unittest.mock import patch
import history_completion as hc
import history_incremental as acq
import history_worker as h

SESSION='latest-history-20261114'
PATH='data/history_latest_acquisition_20261114.json'
BACKUP='data/history_completion_before_latest_20261114.json'
IDS={'apify~facebook-posts-scraper':'KoJrdxJCTtpon81KY','automation-lab~threads-scraper':'yacNYZpu9F3C8EATQ'}

def canonical(path):
    for slug,actor in IDS.items():
        prefix='/acts/'+slug
        if path==prefix or path.startswith(prefix+'/') or path.startswith(prefix+'?'):
            return '/acts/'+actor+path[len(prefix):]
    return path

class Client(acq.Client):
    def request(self,path,payload=None):return super().request(canonical(path),payload)

def fresh_control(prior,cutoff):
    if prior.get('acquisition_completed') is not True:raise ValueError('previous_acquisition_unresolved_no_new_window')
    if any(r.get('submission_unknown') or not r.get('processed') for r in prior.get('runs',[])):raise ValueError('prior_run_unresolved_no_new_window')
    sources={}
    for source in ('facebook','threads'):
        end=prior['sources'][source].get('completed_until')
        if not end or datetime.fromisoformat(cutoff)<=datetime.fromisoformat(end):raise ValueError('invalid_successful_source_cutoff')
        sources[source]={'previous_completed_until':end,'start_utc':(datetime.fromisoformat(end)-timedelta(hours=2)).isoformat(),'end_utc':cutoff,'complete':False,'prior_acquisition':{}}
    return {'scope':hc.SCOPE,'extension_id':SESSION,'cutoff_utc':cutoff,'created_at':cutoff,'rule_sha256':hc.RULE,'closed':False,'stop_reason':None,'acquisition_completed':False,'sources':sources,'runs':[],'apify_http_counts':{'GET':0,'POST':0},'prior_control_snapshot':BACKUP}

def main():
    if os.getenv('AUTHORIZED_LATEST_HISTORY')!=SESSION or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or os.getenv('GITHUB_RUN_ATTEMPT')!='1' or h.policy.fingerprint()!=hc.RULE:raise SystemExit('authorization mismatch')
    gh=os.environ.pop('GH_TOKEN','');apify=os.environ.pop('APIFY_TOKEN','')
    if not gh or not apify:raise SystemExit('missing dedicated secrets')
    remote=hc.Remote(gh)
    try:
        existing=remote.load(PATH)
        if existing is not None:raise ValueError('existing_extension_no_automatic_replay')
        prior=remote.load(hc.CONTROL,{})
        if remote.load(BACKUP) is not None:raise ValueError('existing_snapshot_no_replay')
        control=fresh_control(prior,h.now())
        remote.save(BACKUP,prior);remote.save(PATH,control)
        client=Client(apify)
        with patch.object(acq,'CONTROL',PATH):acq.execute(remote,client)
        result=remote.load(PATH,{})
        if not result.get('acquisition_completed') or result.get('stop_reason'):
            print(json.dumps({'status':'blocked','checkpoint':PATH,'http_status':result.get('http_status'),'stop_reason':result.get('stop_reason'),'apify_requests':client.counts}),flush=True)
            raise SystemExit(1)
        # Publish the new successful cutoff only after both source windows finish.
        combined=copy.deepcopy(prior)
        combined.setdefault('acquisition_history',[]).append({k:prior.get(k) for k in ('cutoff_utc','sources','runs','apify_http_counts')})
        for key in ('sources','runs','cutoff_utc','acquisition_completed','apify_http_counts'):combined[key]=result[key]
        combined['latest_extension_id']=SESSION
        remote.save(hc.CONTROL,combined)
        hc.report(remote)
        print(json.dumps({'status':'acquired','cutoff_utc':result['cutoff_utc'],'apify_requests':client.counts,'runs':len(result['runs'])}),flush=True)
    except SystemExit:raise
    except BaseException as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'http_status':getattr(exc,'status',None),'note':'Durable reservations retained; no retry or raw error logged'}),flush=True)
        raise SystemExit(1)

if __name__=='__main__':main()
