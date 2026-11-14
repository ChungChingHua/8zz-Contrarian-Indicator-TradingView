"""Only the two remaining never-reserved Threads posts; no Facebook replay. MPL-2.0."""
import copy,json,os,subprocess
import history_cached_completion as m
import history_completion as hc
import history_worker as h
import apify_cost_test as t

EXPECTED={'threads:4024090220249602678','threads:4025043302263849308'}
def main():
    session=os.environ.get('AUTHORIZED_RESUME_ID')
    if session!='20261114-media-repair-03' or os.getenv('AUTHORIZED_HISTORY_SCOPE')!=hc.SCOPE or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH:raise SystemExit('authorization mismatch')
    gh=os.environ.pop('GH_TOKEN','');key=os.environ.pop('CHATANYWHERE_API_KEY','');apify=os.environ.pop('APIFY_TOKEN','')
    if not gh or not key or not apify:raise SystemExit('missing dedicated credentials')
    remote=hc.Remote(gh);control=remote.load(hc.CONTROL,{})
    if control.get('closed') or control.get('stop_reason') or control.get('current_session',{}).get('id')!=session:return
    docs=t.Docs(gh);media=m.Media(docs,t.Client(apify))
    try:
        data=hc.archive();excluded,_=hc.exclusions(data);groups,_=hc.select(data,excluded,len(data))
        chosen=[g for g in groups if g[0]['source']=='threads']
        if {g[0]['key'] for g in chosen}!=EXPECTED or any(k in media.attempted for k in EXPECTED):raise ValueError('target_or_prior_reservation_mismatch_no_start')
        original=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],check=True,capture_output=True).stdout)
        posts=[copy.deepcopy(original.get(g[0]['key']) or g[0]) for g in chosen]
        if any(any(p[k]!=g[0][k] for k in ('text','source','post_id','published_at')) for p,g in zip(posts,chosen)):raise ValueError('post_identity_changed')
        plan=hc.frozen_plan(chosen,33);path='data/history_progress/'+plan['batch_id']+'.json'
        if (h.ROOT/path).exists():raise ValueError('existing_batch_no_resend')
        h.BATCH_ID=plan['batch_id'];h.LEDGER_PATH=path
        remote.save('data/history_plans/'+plan['batch_id']+'.json',plan)
        worker=h.Worker(h.GitHubStore(gh,path),h.Provider(key),plan,prepare=media.prepare,secrets=(gh,key),local=h.ROOT/path,generation_limit=2,continue_isolated_failures=True)
        worker.run(posts)
        control=remote.load(hc.CONTROL,{})
        control.update(last_chunk=plan['batch_id'],updated_at=h.now())
        if worker.state['stopped']:control.update(stop_reason=worker.state.get('stop_reason'),stopped_at=next((r['display_time'] for r in reversed(worker.state['records']) if r['status']!='not_started'),None))
        remote.save(hc.CONTROL,control)
    except BaseException as exc:
        control=remote.load(hc.CONTROL,{})
        control.update(stop_reason='last_threads_continuation_block',error_type=type(exc).__name__)
        remote.save(hc.CONTROL,control)
    finally:
        media.finalize()
        control=remote.load(hc.CONTROL,{})
        control['current_session'].update(closed=True,actor_runs_started=media.state['actor_starts_reserved'],saved_dataset_get_requests=len(media.state.get('prior_dataset_reuses',[])),media_repair_ledger=m.LEDGER,media_repair_http_counts=media.client.counts)
        try:
            limits=media.client.request('/users/me/limits')['data']
            maximum=limits.get('limits',{}).get('maxMonthlyUsageUsd');used=limits.get('current',{}).get('monthlyUsageUsd')
            from decimal import Decimal
            state={'maximum_usd':maximum,'used_usd':used,'remaining_headroom_usd_derived':None if maximum is None or used is None else max(Decimal('0'),Decimal(str(maximum))-Decimal(str(used))),'observed_at':h.now(),'note':'Usage limit headroom, not cash balance or settled bill.'}
            docs.save('data/history_media_repairs/final-budget-20261114.json',state)
        except Exception as exc:media.state['budget_read_error_type']=type(exc).__name__
        media.save()
        control['current_session']['media_repair_http_counts']=media.client.counts
        remote.save(hc.CONTROL,control)
        summary=hc.report()
        control=remote.load(hc.CONTROL,{})
        if not control.get('stop_reason'):control.update(stop_reason='remaining_missing_facebook_media' if summary['remaining_not_started_groups'] else None)
        control.update(closed=True,all_unstarted_visited=not summary['remaining_not_started_groups'],closure_reason='missing_images_and_low_apify_headroom' if summary['remaining_not_started_groups'] else 'all_unstarted_visited')
        control['held_missing_media_keys']=[r['key'] for r in h.s.read(h.ROOT/'data/history_completion_inventory.json',[]) if r['status']=='not_started']
        remote.save(hc.CONTROL,control);hc.report(remote)
        print(json.dumps({'target_posts':2,'actor_starts':media.state['actor_starts_reserved'],'Apify_http':media.client.counts,'stop_reason':control.get('stop_reason')}))
if __name__=='__main__':main()
