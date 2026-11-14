"""Restore media URLs from existing datasets only; never start an Actor. MPL-2.0."""
import json,os,re
import history_worker as h
from history_incremental import Client
from history_completion import Remote,CONTROL,RAW,SCOPE,RULE,archive

def main():
    if os.getenv('AUTHORIZED_HISTORY_SCOPE')!=SCOPE or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or h.policy.fingerprint()!=RULE:
        raise SystemExit('Wrong scope/branch/policy')
    key=os.environ.pop('APIFY_TOKEN','');gh=os.environ.pop('GH_TOKEN','')
    if not key or not gh:raise SystemExit('Missing existing-dataset read credentials; no Actor started')
    remote=Remote(gh);control=remote.load(CONTROL,{})
    if control.get('closed') or control.get('stop_reason'):return
    session=control.get('current_session',{})
    if session.get('id')!=os.getenv('AUTHORIZED_RESUME_ID'):raise SystemExit('Resume authorization mismatch')
    data=archive();raw={};client=Client(key)
    for saved in control.get('runs',[]):
        dataset=saved.get('dataset_id','')
        if not re.fullmatch(r'[A-Za-z0-9]{1,40}',dataset):raise SystemExit('Invalid saved dataset ID')
        offset=0
        while True:
            rows=client.request('/datasets/'+dataset+'/items?format=json&offset='+str(offset)+'&limit=100')
            if not isinstance(rows,list):raise SystemExit('Invalid saved dataset shape')
            for row in rows:
                p,reason=h.s.normalize(row,saved['source'])
                if p is None or p['key'] not in data:continue
                if any(p[k]!=data[p['key']][k] for k in ('text','source','post_id','published_at')):
                    raise SystemExit('Saved dataset identity mismatch')
                raw[p['key']]=p
            if len(rows)<100:break
            offset+=len(rows)
    assert client.counts['POST']==0
    RAW.touch(mode=0o600,exist_ok=True);os.chmod(RAW,0o600);RAW.write_text(json.dumps(raw,ensure_ascii=False))
    session.update(saved_dataset_get_requests=client.counts['GET'],actor_runs_started=0)
    control.setdefault('apify_http_counts',{}).setdefault('GET',0)
    control['apify_http_counts']['GET']+=client.counts['GET']
    remote.save(CONTROL,control)
    print(json.dumps({'session':session['id'],'saved_dataset_get_requests':client.counts['GET'],'actor_runs_started':0,'private_media_posts_restored':len(raw)}))

if __name__=='__main__':main()
