"""Continue author-policy history with fresh exact-post media and verified byte cache. MPL-2.0."""
import copy,hashlib,json,os,re,subprocess,time,urllib.parse
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import apify_cost_test as t
import history_completion as hc
import history_worker as h
from history_batch_02 import prepare as original_prepare
from history_plan import media_identity
from review_rules import media_plan
import safe_media

SESSION=os.getenv('AUTHORIZED_RESUME_ID') or '20261111-media-repair-01'
LEDGER='data/history_media_repairs/'+SESSION+'.json'
CACHE=Path('/tmp/8zz-history-media-cache')
MAX_CACHE=128*1024*1024
MAX_BATCH=12
RECOVER_KEYS=('facebook:1660785808739341','threads:3992201729433763729','threads:3992213198011063292')

class MediaStop(BaseException):pass


def acknowledged_cap(options):
    """A verified lower provider cap remains within the user's USD0.10 ceiling."""
    if not isinstance(options,dict):return False
    value=options.get('maxTotalChargeUsd')
    if isinstance(value,bool) or options.get('isMaxTotalChargeUsdSetByUser') is not True:return False
    try:amount=Decimal(str(value))
    except (InvalidOperation,ValueError):return False
    return amount.is_finite() and Decimal('0')<amount<=t.CAP


def previous_media_batches(docs,budget):
    """A reserved URL must never cause a second Actor start, even after interruption."""
    result={}
    for reservation in budget.get('media_repair_reservations',{}).values():
        path=reservation.get('ledger','')
        if path==LEDGER:continue
        if not re.fullmatch(r'data/history_media_repairs/[A-Za-z0-9_-]+\.json',path):raise ValueError('invalid_prior_media_ledger')
        saved=docs.load(path)
        if saved is None:raise ValueError('missing_reserved_media_ledger_no_new_start')
        batches=list(saved.get('batches',[]))+list(saved.get('actors',{}).values())
        for batch in batches:
            for key in batch.get('keys',batch.get('requested_keys',[])):
                if key in result and result[key]['batch'].get('id')!=batch.get('id'):raise ValueError('duplicate_prior_media_reservations')
                result[key]={'ledger':path,'batch':batch}
    return result


def checked_cache(info,root=CACHE):
    if not re.fullmatch(r'[a-f0-9]{64}\.bin',info['filename']):raise ValueError('invalid_cache_filename')
    path=root/info['filename']
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('unsafe_cache_path')
    data=path.read_bytes()
    if len(data)!=info['bytes'] or hashlib.sha256(data).hexdigest()!=info['sha256']:raise ValueError('cache_hash_mismatch')
    if len(data)>8_000_000 or not safe_media.valid_magic(info['mime'],data):raise ValueError('invalid_cached_image')
    return info['mime'],data


def prepare_restored_cache(root=CACHE):
    """Verify needed cache; old completed bytes remain in the source artifact."""
    manifest=json.loads((root/'manifest.json').read_text())
    excluded,_=hc.exclusions(hc.archive())
    before=len(manifest['posts'])
    keep={k:p for k,p in manifest['posts'].items() if k not in excluded}
    files=set()
    for key in keep:
        for image in manifest['images'].get(key,{}).values():
            checked_cache(image,root)
            files.add(image['filename'])
    for path in root.glob('*.bin'):
        if path.is_symlink():raise ValueError('unsafe_cache_symlink')
        if path.name not in files and re.fullmatch(r'[a-f0-9]{64}\.bin',path.name):path.unlink()
    manifest['posts']=keep
    manifest['images']={k:manifest['images'][k] for k in keep}
    if 'provenance' in manifest:manifest['provenance']={k:v for k,v in manifest['provenance'].items() if k in keep}
    manifest['verified_unstarted_at']=h.now()
    (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False));os.chmod(root/'manifest.json',0o600)
    return {'retained_posts':len(keep),'previously_processed_posts_removed_from_working_copy':before-len(keep),
            'verified_image_files':len(files),'retained_bytes':sum((root/name).stat().st_size for name in files),
            'source_artifact_unchanged':True}

class Media:
    def __init__(self,docs,client):
        self.docs=docs;self.client=client
        self.state=docs.load(LEDGER) or {'session':SESSION,'batches':[],'actor_starts_reserved':0,'ai_requests':0}
        self.manifest=json.loads((CACHE/'manifest.json').read_text())
        self.data=hc.archive()
        self.usage=docs.load('data/usage.json') or {}
        self.month=datetime.now(timezone.utc).strftime('%Y-%m')
        self.budget=self.usage.setdefault(self.month,{'apify_runs':0,'ai_attempts':0})
        self.state.setdefault('monthly_runs_before',self.budget['apify_runs'])
        self.attempted={k for b in self.state['batches'] for k in b['keys']}
        self.prior_by_key=previous_media_batches(docs,self.budget)
        self.attempted.update(self.prior_by_key)
        self.save()
    def save(self):
        self.state['http_requests']=dict(self.client.counts);self.state['updated_at']=h.now()
        self.docs.save(LEDGER,self.state)
    def budget_save(self):
        reservation=self.budget.setdefault('media_repair_reservations',{}).setdefault(SESSION,{})
        reservation.update(ledger=LEDGER,reserved_starts=self.state['actor_starts_reserved'],
            runs=[{'id':b.get('id'),'source':b['source'],'status':b['status'],'usageTotalUsd':b.get('usageTotalUsd')} for b in self.state['batches']])
        self.docs.save('data/usage.json',self.usage)
    def stop(self,reason):
        self.state['blocked']=reason;self.save();raise MediaStop(reason)
    def cache_post(self,p,old):
        if any(p[k]!=old[k] for k in ('text','source','post_id','published_at')):raise ValueError('refreshed_post_changed')
        if media_identity(p)!=media_identity(old):raise ValueError('refreshed_attachment_identity_changed')
        images={};download=h.s.download_image
        def cached_download(url):
            mime,blob=download(url)
            digest=hashlib.sha256(blob).hexdigest();filename=digest+'.bin';target=CACHE/filename
            size=sum(x.stat().st_size for x in CACHE.glob('*.bin'))
            if not target.exists() and size+len(blob)>MAX_CACHE: self.stop('cache_byte_limit')
            target.write_bytes(blob);os.chmod(target,0o600)
            images[urllib.parse.urlsplit(url).path]={'sha256':digest,'filename':filename,'mime':mime,'bytes':len(blob),'fresh_url_sha256':hashlib.sha256(url.encode()).hexdigest()}
            return mime,blob
        with patch.object(h.s,'download_image',cached_download):parts,scope=original_prepare(p)
        if not parts or scope.get('media_failures'):raise ValueError('required_refreshed_images_unavailable')
        self.manifest['posts'][p['key']]=h.s.public_safe(p);self.manifest['images'][p['key']]=images
        self.manifest.setdefault('provenance',{})[p['key']]={'cached_at':h.now(),'images':len(parts)}
        (CACHE/'manifest.json').write_text(json.dumps(self.manifest,ensure_ascii=False));os.chmod(CACHE/'manifest.json',0o600)
    def refresh(self,post):
        if self.state.get('blocked'):raise MediaStop(self.state['blocked'])
        if post['key'] in self.attempted:raise ValueError('media_refresh_already_attempted_no_retry')
        excluded,_=hc.exclusions(self.data)
        candidates=[post]
        for p in sorted(self.data.values(),key=lambda x:(x['unix_ms'],x['key'])):
            if len(candidates)>=MAX_BATCH:break
            if p['source']!=post['source'] or p['unix_ms']<post['unix_ms'] or p['key']==post['key'] or p['key'] in excluded or p['key'] in self.attempted or p['key'] in self.manifest['posts']:continue
            if media_plan(p)['image_attachments']:candidates.append(p)
        keys=[p['key'] for p in candidates];source=post['source'];actor=t.ACTORS[source]
        if self.budget['apify_runs']>=70:self.stop('monthly_70_run_guard')
        try:
            meta=self.client.request('/acts/'+actor)['data'];t.pricing(meta,datetime.now(timezone.utc))
        except Exception as exc:
            known_codes={'apify_http_error','apify_transport_failure','pricing_not_verifiable_no_start','actor_minimum_exceeds_authorized_cap_no_start','unknown_pricing_model_no_start'}
            self.state['last_error']={'phase':'actor_metadata_or_pricing','error_type':type(exc).__name__,
                'http_status':getattr(exc,'status',None),'safe_code':getattr(exc,'code',None) if getattr(exc,'code',None) in known_codes else None}
            self.stop('actor_pricing_or_access_'+type(exc).__name__)
        self.budget['apify_runs']+=1;self.state['actor_starts_reserved']+=1
        entry={'source':source,'actor':actor,'keys':keys,'status':'reserved_not_submitted','posts':{}}
        self.state['batches'].append(entry);self.attempted.update(keys)
        self.budget_save();self.save() # Both remote ACKs before sending a potentially chargeable request.
        entry['status']='submission_unknown';self.save()
        urls=[p['url'] for p in candidates]
        body={'startUrls':[{'url':u} for u in urls],'resultsLimit':1} if source=='facebook' else {'mode':'urls','postUrls':urls,'maxPosts':MAX_BATCH,'includeProfile':False}
        entry['input']=body
        options={'timeout':180,'memory':512,'maxItems':50,'maxTotalChargeUsd':'0.10','restartOnError':'false'}
        try:
            run=self.client.request('/acts/'+actor+'/runs?'+urllib.parse.urlencode(options),body)['data'];t.record_run(entry,run);self.save()
            if not acknowledged_cap(run.get('options',{})):
                self.client.request('/actor-runs/'+run['id']+'/abort',{});self.stop('cap_not_acknowledged_aborted')
            for attempt in range(50):
                run=self.client.request('/actor-runs/'+entry['id'])['data']
                if run['status'] not in ('READY','RUNNING','TIMING-OUT','ABORTING'):break
                time.sleep(4)
            t.record_run(entry,run);self.save()
            if run['status']!='SUCCEEDED':self.stop('actor_service_failure')
            rows=self.client.request('/datasets/'+run['defaultDatasetId']+'/items?format=json&limit=100')
            if not isinstance(rows,list):self.stop('invalid_dataset_shape')
        except Exception as exc:
            entry['error_type']=type(exc).__name__;entry['http_status']=getattr(exc,'status',None);self.stop('actor_access_or_transport_failure')
        found={}
        for row in rows:
            p,reason=h.s.normalize(t.plain(row),source)
            if p and p['key'] in keys:found[p['key']]=p
        for old in candidates:
            key=old['key'];record=entry['posts'][key]={}
            if key not in found:record['status']='post_not_returned';continue
            try:
                self.cache_post(found[key],old);record['status']='cached'
            except Exception as exc:
                record.update(status='input_failure',error_type=type(exc).__name__,safe_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[a-z_]+',str(exc)) else None)
            self.save()
        self.save();self.budget_save()
    def prepare(self,post):
        if not media_plan(post)['image_attachments']:return original_prepare(post)
        key=post['key']
        if key not in self.manifest['posts']:
            if key in getattr(self,'prior_by_key',{}):self.reuse_prior_dataset(post)
            else:self.refresh(post)
        if key not in self.manifest['posts']:raise ValueError('refreshed_media_unavailable')
        fresh=self.manifest['posts'][key]
        if any(fresh[k]!=post[k] for k in ('text','source','post_id','published_at')) or media_identity(fresh)!=media_identity(post):raise ValueError('cache_post_identity_mismatch')
        p=copy.deepcopy(post);p['attachments']=copy.deepcopy(fresh['attachments'])
        def download(url):
            path=urllib.parse.urlsplit(url).path
            info=self.manifest['images'][key].get(path)
            if info is None:raise ValueError('cached_attachment_missing')
            return checked_cache(info)
        with patch.object(h.s,'download_image',download):parts,scope=original_prepare(p)
        scope['cache_verified']=True;scope['media_refresh_session']=SESSION
        return parts,scope

    def reuse_prior_dataset(self,post):
        """Read one paid run's existing dataset; never start or retry an Actor."""
        prior=self.prior_by_key[post['key']];batch=prior['batch']
        if batch.get('status')!='SUCCEEDED' or not batch.get('defaultDatasetId'):
            raise ValueError('prior_media_run_unresolved_no_duplicate_start')
        run_id=batch.get('id')
        reuses=self.state.setdefault('prior_dataset_reuses',[])
        if any(r['run_id']==run_id for r in reuses):raise ValueError('prior_dataset_reuse_already_attempted_no_actor_retry')
        excluded,_=hc.exclusions(self.data)
        keys=[k for k in batch.get('keys',batch.get('requested_keys',[])) if k in self.data and k not in excluded and k not in self.manifest['posts']]
        record={'run_id':run_id,'source_ledger':prior['ledger'],'keys':keys,'status':'reading_existing_dataset','posts':{}}
        reuses.append(record);self.save()
        try:
            rows=self.client.request('/datasets/'+batch['defaultDatasetId']+'/items?format=json&limit=100')
            if not isinstance(rows,list):self.stop('invalid_existing_dataset_shape')
        except Exception as exc:
            record.update(error_type=type(exc).__name__,http_status=getattr(exc,'status',None))
            self.stop('existing_dataset_access_failure_no_actor_retry')
        found={}
        for row in rows:
            p,reason=h.s.normalize(t.plain(row),post['source'])
            if p and p['key'] in keys:found[p['key']]=p
        for key in keys:
            item=record['posts'][key]={}
            if key not in found:item['status']='post_not_returned'
            else:
                try:self.cache_post(found[key],self.data[key]);item['status']='cached'
                except Exception as exc:item.update(status='input_failure',error_type=type(exc).__name__,safe_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[a-z_]+',str(exc)) else None)
            self.save()
        record['status']='existing_dataset_read_complete';self.save()
    def finalize(self):
        for entry in self.state['batches']:
            if not entry.get('id'):continue
            try:t.record_run(entry,self.client.request('/actor-runs/'+entry['id'])['data'])
            except Exception as exc:entry['cost_refresh_error_type']=type(exc).__name__;break
        self.state['monthly_runs_after']=self.budget['apify_runs'];self.save();self.budget_save()


def restore_unsent_worker(media,token,key):
    path='data/history_progress/history-completion-20261107-020.json'
    plan=h.s.read(h.ROOT/'data/history_plans/history-completion-20261107-020.json',{})
    h.BATCH_ID=plan['batch_id'];h.LEDGER_PATH=path
    worker=h.Worker(h.GitHubStore(token,path),h.Provider(key),plan,prepare=media.prepare,secrets=(token,key),local=h.ROOT/path,generation_limit=25,continue_isolated_failures=True)
    records={r['key']:r for r in worker.state['records']}
    if worker.state.get('media_cache_recovery_used'):
        if any(r['status']=='unknown' for r in worker.state['records']):raise MediaStop('unknown_request_requires_manual_reconciliation')
        return True
    for k in RECOVER_KEYS:
        r=records[k]
        if r['status']!='input_failure' or r['attempts']!=0 or 'http_status' in r or r.get('raw_response'):raise ValueError('recovery_not_proven_zero_generation')
        media.prepare(media.data[k]) # Verified cache only; no provider request.
    if worker.state.get('media_cache_recovery_used'):raise ValueError('recovery_already_used')
    for k in RECOVER_KEYS:
        r=records[k];r.setdefault('input_failure_history',[]).append({q:r.get(q) for q in ('status','reason','error_type','attempts')})
        r.update(status='not_started',recovery_authorization=SESSION);r.pop('error_type',None);r.pop('reason',None)
    worker.state.update(stopped=False,finished=False,consecutive_isolated_failures=0,media_cache_recovery_used=True)
    worker.state.pop('stop_reason',None);worker.save()
    raw=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],check=True,capture_output=True).stdout)
    posts=[copy.deepcopy(raw.get(r['key']) or media.data[r['key']]) for r in plan['posts']]
    worker.run(posts)
    remote=hc.Remote(token);control=remote.load(hc.CONTROL,{})
    control.update(last_chunk=plan['batch_id'],updated_at=h.now(),consecutive_isolated_failures=worker.state.get('consecutive_isolated_failures',0))
    if worker.state['stopped']:control.update(stop_reason=worker.state.get('stop_reason'),stopped_at=next((r['display_time'] for r in reversed(worker.state['records']) if r['status']!='not_started'),None))
    remote.save(hc.CONTROL,control);hc.report(remote)
    return not worker.state['stopped']


def main():
    if not re.fullmatch(r'[0-9]{8}-media-repair-[0-9]{2}',SESSION) or os.getenv('AUTHORIZED_HISTORY_SCOPE')!=hc.SCOPE or os.getenv('AUTHORIZED_RESUME_ID')!=SESSION or os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH:raise SystemExit('authorization mismatch')
    token=os.environ.get('GH_TOKEN','');key=os.environ.get('CHATANYWHERE_API_KEY','');apify=os.environ.pop('APIFY_TOKEN','')
    if not token or not key or not apify:raise SystemExit('missing dedicated credentials')
    remote=hc.Remote(token)
    authorized=remote.load(hc.CONTROL,{})
    if authorized.get('closed') or authorized.get('stop_reason'):return
    if authorized.get('current_session',{}).get('id')!=SESSION:raise SystemExit('remote session authorization mismatch')
    docs=t.Docs(token);media=Media(docs,t.Client(apify))
    try:
        control=remote.load(hc.CONTROL,{})
        if control.get('closed') or control.get('stop_reason'):return
        if restore_unsent_worker(media,token,key):
            with patch.object(hc,'prepare',media.prepare):hc.run()
    except MediaStop as exc:
        control=remote.load(hc.CONTROL,{})
        control.update(stop_reason=str(exc),closed=True,closure_reason='media_repair_service_or_budget_block');remote.save(hc.CONTROL,control)
    except Exception as exc:
        control=remote.load(hc.CONTROL,{})
        control.update(stop_reason='cached_continuation_program_failure',error_type=type(exc).__name__,closed=True);remote.save(hc.CONTROL,control)
    finally:
        media.finalize()
        control=remote.load(hc.CONTROL,{})
        control['current_session'].update(actor_runs_started=control['current_session'].get('initial_actor_starts',0)+media.state['actor_starts_reserved'],saved_dataset_get_requests=len(media.state.get('prior_dataset_reuses',[])),media_repair_ledger=LEDGER,initial_media_repair_ledger='data/history_media_repairs/media-repair-20261111-01.json',media_repair_http_counts=media.client.counts)
        remote.save(hc.CONTROL,control);hc.report(remote)
        print(json.dumps({'session':SESSION,'media_actor_starts':media.state['actor_starts_reserved'],'monthly_apify_runs':media.budget['apify_runs'],'stop_reason':control.get('stop_reason')}))

if __name__=='__main__':main()
