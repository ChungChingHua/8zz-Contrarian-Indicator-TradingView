"""One authorized continuation with unchanged author policy and no automatic resends. MPL-2.0."""
import copy,json,os,subprocess
from unittest.mock import patch
import history_completion as hc
import history_worker as h
import history_cached_completion as m
import history_latest_acquire_20261114 as latest
import apify_cost_test as t
from review_rules import media_plan

SESSION='20261114-media-repair-04'
OLD_EMPTY_RUN='aN1ESUqN4kVceCqBH'
OLD_EMPTY_DATASET='yv2pVJKq2araXljnc'

class Client(t.Client):
    def request(self,path,payload=None):return super().request(latest.canonical(path),payload)

def empty_proof(run,rows):
    if run.get('id')!=OLD_EMPTY_RUN or run.get('status')!='ABORTED' or run.get('defaultDatasetId')!=OLD_EMPTY_DATASET or rows!=[]:
        raise ValueError('predecessor_not_verified_terminal_empty_no_resend')
    return {'run_id':OLD_EMPTY_RUN,'dataset_id':OLD_EMPTY_DATASET,'terminal_status':'ABORTED','dataset_items':0,'verified_at':h.now()}

class Media(m.Media):
    def budget_save(self):
        proof=self.state.get('verified_empty_predecessor')
        if proof:
            allowed=set(self.state['recovery_candidate_keys'])
            for batch in self.state['batches']:
                if set(batch['keys'])<=allowed:batch['empty_predecessor']=copy.deepcopy(proof)
        super().budget_save()

def allow_proven_missing_only(media,held):
    candidates={k for k in held if media.prior_by_key.get(k,{}).get('batch',{}).get('id')==OLD_EMPTY_RUN}
    if not candidates:return set(held)
    try:
        run=media.client.request('/actor-runs/'+OLD_EMPTY_RUN)['data']
        # Never read a running/unknown/wrong predecessor and never submit its URLs again.
        if run.get('status')!='ABORTED':raise ValueError('predecessor_not_aborted')
        rows=media.client.request('/datasets/'+OLD_EMPTY_DATASET+'/items?format=json&limit=1')
        proof=empty_proof(run,rows)
    except Exception as exc:
        media.state['old_missing_recovery']={'status':'held_no_resend','error_type':type(exc).__name__,'http_status':getattr(exc,'status',None)}
        media.save();return set(held)
    media.state.update(verified_empty_predecessor=proof,recovery_candidate_keys=sorted(candidates),recovery_note='User authorized unfetched missing data; predecessor terminal ABORTED and dataset verified empty. One new session attempt, never retry unknown/nonempty run.')
    media.save() # Evidence ACK before a newly authorized paid attempt is possible.
    for key in candidates:media.prior_by_key.pop(key);media.attempted.discard(key)
    return set(held)-candidates

def main():
    if (os.getenv('AUTHORIZED_LATEST_HISTORY')!=latest.SESSION or os.getenv('AUTHORIZED_RESUME_ID')!=SESSION or m.SESSION!=SESSION or
        os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or os.getenv('GITHUB_RUN_ATTEMPT')!='1' or h.policy.fingerprint()!=hc.RULE):raise SystemExit('authorization mismatch')
    gh=os.environ.pop('GH_TOKEN','');key=os.environ.pop('CHATANYWHERE_API_KEY','');apify=os.environ.pop('APIFY_TOKEN','')
    if not gh or not key or not apify:raise SystemExit('missing dedicated secrets')
    remote=hc.Remote(gh);control=remote.load(hc.CONTROL,{})
    if not control.get('acquisition_completed') or control.get('latest_extension_id')!=latest.SESSION:raise SystemExit('latest acquisition not complete')
    if control.get('current_session',{}).get('id')==SESSION:raise SystemExit('existing session no automatic replay')
    baseline=hc.report()
    old=control.get('current_session')
    if old and not any(s.get('id')==old.get('id') for s in control.get('session_history',[])):control.setdefault('session_history',[]).append(old)
    control.update(closed=False,stop_reason=None,consecutive_isolated_failures=0,current_session={
        'id':SESSION,'baseline_generation_attempts':baseline['new_generation_attempts'],'baseline_validated_responses':baseline['new_validated_responses'],
        'baseline_usage':baseline['service_reported_usage'],'baseline_total_events':baseline['pine']['total_events'],'baseline_status_counts':baseline['new_status_counts'],
        'recovered_zero_generation_inputs':0,'actor_runs_started':0,'saved_dataset_get_requests':0,'closed':False,
        'run_url':'https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/'+os.environ['GITHUB_RUN_ID']})
    remote.save(hc.CONTROL,control)
    media=None
    try:
        media=Media(t.Docs(gh),Client(apify))
        held=allow_proven_missing_only(media,control.get('held_missing_media_keys',[]))
        data=hc.archive();snapshot=h.s.read(hc.ROOT/latest.BACKUP,{})
        previous_end=min(datetime.fromisoformat(x['completed_until']) for x in snapshot['sources'].values())
        new_keys={k for k,p in data.items() if datetime.fromisoformat(p['published_at'])>=previous_end}
        media.attempted.update(new_keys) # Fresh incrementally fetched media is never re-scraped by a second Actor.
        original=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],check=True,capture_output=True).stdout)
        def prepare(post):
            if post['key'] in new_keys and media_plan(post)['image_attachments'] and post['key'] not in media.manifest['posts']:
                raise ValueError('new_capture_image_unavailable_no_actor_refetch')
            return media.prepare(post)
        number=1
        while True:
            excluded,_=hc.exclusions(data);groups,_=hc.select(data,excluded|held,25)
            if not groups:break
            while (hc.ROOT/('data/history_progress/'+hc.SCOPE+'-'+str(number).zfill(3)+'.json')).exists():number+=1
            plan=hc.frozen_plan(groups,number);path='data/history_progress/'+plan['batch_id']+'.json'
            h.BATCH_ID=plan['batch_id'];h.LEDGER_PATH=path
            remote.save('data/history_plans/'+plan['batch_id']+'.json',plan)
            posts=[]
            for row in plan['posts']:
                p=copy.deepcopy(original.get(row['key']) or data[row['key']])
                if any(p[k]!=row[k] for k in ('text','source','post_id','published_at')):raise ValueError('post_identity_changed')
                posts.append(p)
            worker=h.Worker(h.GitHubStore(gh,path),h.Provider(key),plan,prepare=prepare,secrets=(gh,key,apify),local=hc.ROOT/path,generation_limit=25,continue_isolated_failures=True)
            worker.state['consecutive_isolated_failures']=control.get('consecutive_isolated_failures',0)
            worker.run(posts)
            control=remote.load(hc.CONTROL,{})
            control.update(last_chunk=plan['batch_id'],updated_at=h.now(),consecutive_isolated_failures=worker.state.get('consecutive_isolated_failures',0))
            if worker.state['stopped']:control.update(stop_reason=worker.state.get('stop_reason'),stopped_at=next((r['display_time'] for r in reversed(worker.state['records']) if r['status']!='not_started'),None))
            remote.save(hc.CONTROL,control);hc.report(remote)
            if worker.state['stopped']:break
            number+=1
        control=remote.load(hc.CONTROL,{})
        control['held_missing_media_keys']=sorted(held)
        if held and not control.get('stop_reason'):control['stop_reason']='prior_missing_media_not_verified_for_resend'
        remote.save(hc.CONTROL,control)
    except BaseException as exc:
        control=remote.load(hc.CONTROL,{})
        control.update(stop_reason=str(exc) if isinstance(exc,m.MediaStop) else 'latest_history_execution_block',error_type=type(exc).__name__)
        remote.save(hc.CONTROL,control)
    finally:
        if media:
            media.finalize()
            control=remote.load(hc.CONTROL,{})
            control['current_session'].update(closed=True,actor_runs_started=media.state['actor_starts_reserved'],saved_dataset_get_requests=len(media.state.get('prior_dataset_reuses',[])),media_repair_ledger=m.LEDGER,media_repair_http_counts=media.client.counts)
            remote.save(hc.CONTROL,control)
        control=remote.load(hc.CONTROL,{})
        control.update(closed=True)
        remote.save(hc.CONTROL,control)
        summary=hc.report(remote)
        print(json.dumps({'session':SESSION,'stop_reason':control.get('stop_reason'),'results':summary.get('current_session'),'remaining':summary['remaining_not_started_platform_posts']}),flush=True)

from datetime import datetime
if __name__=='__main__':main()
