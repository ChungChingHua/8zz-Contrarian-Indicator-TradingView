"""Finish media-ready pending posts without starting or querying Apify. MPL-2.0."""
import copy,json,os,re,subprocess
from unittest.mock import patch
import history_cached_completion as m
import history_completion as hc
import history_worker as h
import apify_cost_test as t
from review_rules import media_plan

class NoApify:
    counts={'GET':0,'POST':0}
    def request(self,*args,**kwargs):raise AssertionError('Apify forbidden in existing-media continuation')

def main():
    session=os.environ.get('AUTHORIZED_RESUME_ID','')
    if session!='20261114-media-repair-02' or os.getenv('AUTHORIZED_HISTORY_SCOPE')!=hc.SCOPE or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH:raise SystemExit('authorization mismatch')
    token=os.environ.pop('GH_TOKEN','');key=os.environ.pop('CHATANYWHERE_API_KEY','')
    if not token or not key:raise SystemExit('missing dedicated credentials')
    remote=hc.Remote(token);control=remote.load(hc.CONTROL,{})
    if control.get('closed') or control.get('stop_reason') or control.get('current_session',{}).get('id')!=session:return
    media=m.Media(t.Docs(token),NoApify())
    try:
        data=hc.archive();excluded,_=hc.exclusions(data);groups,_=hc.select(data,excluded,len(data))
        original=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],check=True,capture_output=True).stdout)
        ready=[];raw_by_key={};audit=[]
        for group in groups:
            p=copy.deepcopy(original.get(group[0]['key']) or group[0]);old=group[0]
            if any(p[k]!=old[k] for k in ('text','source','post_id','published_at')):raise ValueError('post_identity_changed')
            row={'key':p['key'],'display_time':p['display_time'],'status':'preflight','already_cached':p['key'] in media.manifest['posts']}
            audit.append(row)
            try:
                if media_plan(p)['image_attachments'] and not row['already_cached']:
                    media.cache_post(p,old) # Only existing public image URLs; no Actor or dataset requests.
                parts,scope=media.prepare(p)
                row.update(status='ready',images_supplied_if_sent=scope.get('images_supplied',0),media_scope=scope)
                ready.append(group);raw_by_key[p['key']]=p
            except Exception as exc:
                row.update(status='held_media_unavailable',error_type=type(exc).__name__,reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[a-z_]+',str(exc)) else 'media_preflight_failure')
            media.state['existing_media_preflight']=audit;media.save()
        def cached_only(post):
            if media_plan(post)['image_attachments'] and post['key'] not in media.manifest['posts']:raise ValueError('media_not_ready_no_actor')
            return media.prepare(post)
        for offset in range(0,len(ready),25):
            number=32+offset//25;plan=hc.frozen_plan(ready[offset:offset+25],number);path='data/history_progress/'+plan['batch_id']+'.json'
            if (h.ROOT/path).exists():raise ValueError('existing_batch_no_resend')
            h.BATCH_ID=plan['batch_id'];h.LEDGER_PATH=path
            remote.save('data/history_plans/'+plan['batch_id']+'.json',plan)
            worker=h.Worker(h.GitHubStore(token,path),h.Provider(key),plan,prepare=cached_only,secrets=(token,key),local=h.ROOT/path,generation_limit=25,continue_isolated_failures=True)
            worker.run([raw_by_key[p['key']] for p in plan['posts']])
            control=remote.load(hc.CONTROL,{})
            control.update(last_chunk=plan['batch_id'],updated_at=h.now(),consecutive_isolated_failures=worker.state.get('consecutive_isolated_failures',0))
            if worker.state['stopped']:
                control.update(stop_reason=worker.state.get('stop_reason'),stopped_at=next((r['display_time'] for r in reversed(worker.state['records']) if r['status']!='not_started'),None))
            remote.save(hc.CONTROL,control);hc.report(remote)
            if worker.state['stopped']:break
        control=remote.load(hc.CONTROL,{})
        held=[r['key'] for r in audit if r['status']!='ready']
        if not control.get('stop_reason'):
            control.update(stop_reason='missing_public_media_no_new_actor' if held else None,closure_reason='existing_media_exhausted' if held else 'all_unstarted_visited',all_unstarted_visited=not held)
        control.update(closed=True,held_missing_media_keys=held,existing_media_preflight_ledger=m.LEDGER)
        remote.save(hc.CONTROL,control)
    except BaseException as exc:
        control=remote.load(hc.CONTROL,{})
        control.update(closed=True,stop_reason='existing_media_continuation_block',error_type=type(exc).__name__)
        remote.save(hc.CONTROL,control)
    finally:
        media.finalize()
        control=remote.load(hc.CONTROL,{})
        control['current_session'].update(closed=True,actor_runs_started=0,saved_dataset_get_requests=0,media_repair_ledger=m.LEDGER,media_repair_http_counts=media.client.counts,existing_public_media_only=True)
        remote.save(hc.CONTROL,control);hc.report(remote)
        print(json.dumps({'session':session,'Apify_requests':media.client.counts,'new_actor_starts':0,'stop_reason':control.get('stop_reason')}))
if __name__=='__main__':main()
