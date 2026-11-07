"""Bounded incremental Apify acquisition for the one-time completion. MPL-2.0."""
import json,os,time,urllib.request,urllib.error,urllib.parse
from datetime import datetime,timedelta,timezone
from pathlib import Path
import history_worker as h
from history_completion import Remote,ROOT,SCOPE,CONTROL,DELTA,RAW,archive,RULE,report
BASE='https://api.apify.com/v2'

class AcquisitionError(Exception):
    def __init__(self,status,code=None):self.status=status;self.code=code

class Client:
    def __init__(self,key):self.key=key;self.counts={'GET':0,'POST':0}
    def request(self,path,payload=None):
        method='GET' if payload is None else 'POST';self.counts[method]+=1
        req=urllib.request.Request(BASE+path,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},data=None if payload is None else json.dumps(payload).encode())
        try:
            with urllib.request.build_opener(h.StopRedirect()).open(req,timeout=90) as res:
                raw=res.read(4_000_001)
                if len(raw)>4_000_000:raise ValueError('bounded_apify_response_exceeded')
                if self.key.encode() in raw:raise ValueError('apify_response_reflects_credential')
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            # Never retain raw URL, headers, body or reflected credentials.
            raise AcquisitionError(exc.code) from None


def execute(remote,client):
    control=remote.load(CONTROL,{})
    if control.get('closed') or control.get('stop_reason'):return
    data=archive()
    if not control:
        cutoff=h.now();control={'scope':SCOPE,'cutoff_utc':cutoff,'created_at':cutoff,'rule_sha256':RULE,'closed':False,'acquisition_completed':False,'sources':{},'runs':[],'apify_http_counts':{'GET':0,'POST':0}}
        for source in ('facebook','threads'):
            latest=max(datetime.fromisoformat(p['published_at']) for p in data.values() if p['source']==source)
            control['sources'][source]={'previous_latest_post_utc':latest.isoformat(),'start_utc':(latest-timedelta(hours=2)).isoformat(),'end_utc':cutoff,'complete':False,'prior_acquisition':h.s.read(ROOT/'data/acquisition.json',{}).get(source,{})}
        remote.save(CONTROL,control)
    def save():
        control['apify_http_counts']={k:control.get('prior_http_counts',{}).get(k,0)+v for k,v in client.counts.items()};remote.save(CONTROL,control)
    control['prior_http_counts']=dict(control.get('apify_http_counts',{}))
    raw_posts={};delta=h.s.read(ROOT/DELTA,{})
    try:
        for source,state in control['sources'].items():
            prior=state.get('prior_acquisition',{}).get('last_run_id')
            if prior and 'previous_fetch_metadata' not in state:
                old=client.request('/actor-runs/'+prior)['data']
                state['previous_fetch_metadata']={k:old.get(k) for k in ('id','startedAt','finishedAt','status')};save()
            # Re-read saved datasets on resume, never start their Actor again.
            def ingest_run(run_info):
                dataset=run_info['dataset_id'];rows=[];offset=0
                while True:
                    page=client.request('/datasets/'+dataset+'/items?format=json&offset='+str(offset)+'&limit=100')
                    if not isinstance(page,list):raise ValueError('invalid_dataset_shape')
                    rows.extend(page)
                    if len(page)<100:break
                    offset+=len(page)
                if rows and not any(isinstance(r,dict) and r.get('postId') and (r.get('time') or r.get('date')) for r in rows):raise ValueError('dataset_has_no_post_identity')
                counts={'fetched':len(rows),'accepted':0,'new':0,'overlap':0,'excluded':{}};dates=[]
                lo=datetime.fromisoformat(state['start_utc']);hi=datetime.fromisoformat(control['cutoff_utc'])
                for row in rows:
                    p,reason=h.s.normalize(row,source)
                    if p is None:counts['excluded'][reason]=counts['excluded'].get(reason,0)+1;continue
                    dt=datetime.fromisoformat(p['published_at'])
                    if not lo<=dt<hi:counts['excluded']['outside_incremental_window']=counts['excluded'].get('outside_incremental_window',0)+1;continue
                    dates.append(dt);counts['accepted']+=1
                    existing=data.get(p['key'])
                    if existing:
                        counts['overlap']+=1
                        if any(existing[k]!=p[k] for k in ('text','source','post_id','published_at','quoted_content')):
                            state.setdefault('changed_existing_keys',[]).append(p['key']);continue
                    else:
                        counts['new']+=1;data[p['key']]=p;delta[p['key']]=p
                    raw_posts[p['key']]=p
                run_info['counts']=counts
                remote.save(DELTA,delta);save()
                return rows,dates
            for saved in control['runs']:
                if saved['source']==source and saved.get('dataset_id'):ingest_run(saved)
            while not state['complete']:
                active=next((r for r in control['runs'] if r['source']==source and not r.get('processed')),None)
                if active and active.get('submission_unknown') and not active.get('run_id'):
                    control['stop_reason']='apify_submission_unknown';save();return
                if not active:
                    usage=remote.load('data/usage.json',{});month=datetime.now(timezone.utc).strftime('%Y-%m');budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
                    if budget['apify_runs']>=70:control['stop_reason']='existing_monthly_apify_budget_exhausted';save();return
                    budget['apify_runs']+=1;remote.save('data/usage.json',usage)
                    end=state.get('page_before') or state['end_utc'];start=state['start_utc']
                    active={'source':source,'start_utc':start,'end_utc':end,'submission_unknown':True,'processed':False,'cap_usd':0.10,'max_items':50}
                    control['runs'].append(active);save() # ACK before chargeable POST.
                    if source=='facebook':
                        actor='apify~facebook-posts-scraper';body={'startUrls':[{'url':'https://www.facebook.com/DieWithoutBang'}],'resultsLimit':50,'onlyPostsNewerThan':start.replace('+00:00','Z'),'onlyPostsOlderThan':end.replace('+00:00','Z')}
                    else:
                        actor='automation-lab~threads-scraper';body={'mode':'posts','usernames':['banini31'],'maxPosts':50,'includeProfile':False,'postedAfter':start.replace('+00:00','Z'),'postedBefore':end.replace('+00:00','Z')}
                    try:
                        run=client.request('/acts/'+actor+'/runs?'+urllib.parse.urlencode({'timeout':180,'memory':512,'maxItems':50,'maxTotalChargeUsd':0.10}),body)['data']
                    except AcquisitionError as exc:
                        active['http_status']=exc.status
                        if exc.status in (400,401,402,403,404,422):active['submission_unknown']=False
                        raise
                    active.update(run_id=run['id'],submission_unknown=False);save()
                for _ in range(60):
                    run=client.request('/actor-runs/'+active['run_id'])['data']
                    if run['status'] in ('SUCCEEDED','FAILED','TIMED-OUT','ABORTED'):break
                    time.sleep(4)
                active['status']=run['status'];active['reported_cost']={k:run[k] for k in ('usageTotalUsd','externalChargedTotalUsd') if isinstance(run.get(k),(int,float))}
                active['finished_at']=run.get('finishedAt')
                msg=str(run.get('statusMessage','')).lower()
                active['possible_cost_truncation']=any(isinstance(run.get(k),(int,float)) and run[k]>=0.10 for k in ('usageTotalUsd','externalChargedTotalUsd')) or any(word in msg for word in ('maximum total charge','max total charge','max charge'))
                if run['status']!='SUCCEEDED':control['stop_reason']='apify_run_not_successful';save();return
                active['dataset_id']=run['defaultDatasetId'];save()
                rows,dates=ingest_run(active)
                if active['possible_cost_truncation']:
                    control['stop_reason']='apify_cost_cap_may_have_truncated_window';save();return
                if len(rows)>=50:
                    if not dates:control['stop_reason']='saturated_window_without_valid_dates';save();return
                    boundary=(min(dates)+timedelta(seconds=1)).isoformat()
                    if state.get('page_before') and datetime.fromisoformat(boundary)>=datetime.fromisoformat(state['page_before']):
                        control['stop_reason']='incremental_pagination_no_progress';save();return
                    state['page_before']=boundary
                else:state.update(complete=True,completed_until=control['cutoff_utc'])
                active['processed']=True;save()
        control['acquisition_completed']=all(v['complete'] for v in control['sources'].values());save()
    except Exception as exc:
        control.update(stop_reason='apify_access_or_acquisition_failure',error_type=type(exc).__name__,http_status=getattr(exc,'status',None));save()
    finally:
        # Signed CDN URLs only in a private runner-temp file, never logs/cache/artifact/Git.
        RAW.touch(mode=0o600,exist_ok=True);os.chmod(RAW,0o600);RAW.write_text(json.dumps(raw_posts,ensure_ascii=False))
        print(json.dumps({'acquisition_completed':control.get('acquisition_completed'),'cutoff_utc':control['cutoff_utc'],'stop_reason':control.get('stop_reason'),'http_status':control.get('http_status'),'apify_http_counts':control.get('apify_http_counts'),'new_posts':len(delta)}),flush=True)

if __name__=='__main__':
    if os.getenv('AUTHORIZED_HISTORY_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or h.policy.fingerprint()!=RULE:raise SystemExit('Wrong scope/branch/policy')
    key=os.environ.pop('APIFY_TOKEN','');gh=os.environ.pop('GH_TOKEN','')
    if not key or not gh:raise SystemExit('Missing APIFY_TOKEN/GH_TOKEN; no acquisition started')
    execute(Remote(gh),Client(key))
