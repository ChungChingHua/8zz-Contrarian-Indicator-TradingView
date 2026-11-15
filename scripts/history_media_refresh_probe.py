"""Bounded repair of three proven-unsent image failures. No AI calls. MPL-2.0."""
from apify_run_policy import run_options,provider_charge_limited
import copy,hashlib,json,os,re,subprocess,time,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import apify_cost_test as t
import history_worker as h
import safe_media
from history_completion import archive
from history_batch_02 import prepare
from history_plan import media_identity

ID='media-repair-20261111-01'
LEDGER='data/history_media_repairs/'+ID+'.json'
KEYS=('facebook:1660785808739341','threads:3992201729433763729','threads:3992213198011063292')
CACHE=Path('/tmp/8zz-history-media-cache')


def save_private(path,value):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.write_text(json.dumps(value,ensure_ascii=False));os.chmod(path,0o600)


def run(docs,client):
    prior=docs.load(LEDGER)
    if prior is not None:return prior # Unknown/failed starts are never automatically re-submitted.
    state={'id':ID,'status':'preflight','actors':{},'posts':{},'max_starts':2,'cap_usd_per_start':None,
        'ai_requests':0,'actor_starts_reserved':0,'artifact_name':ID+'-cache','workflow_run_id':os.getenv('GITHUB_RUN_ID')}
    def save():state['http_requests']=dict(client.counts);docs.save(LEDGER,state)
    data=archive();raw=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],capture_output=True,check=True).stdout)
    usage=docs.load('data/usage.json') or {};month=datetime.now(timezone.utc).strftime('%Y-%m')
    budget=usage.setdefault(month,{'apify_runs':0,'ai_attempts':0})
    state['monthly_runs_before']=budget['apify_runs'];save()
    try:
        for source,actor in t.ACTORS.items():
            meta=client.request('/acts/'+actor)['data'];pricing=t.pricing(meta,datetime.now(timezone.utc))
            state['actors'][source]={'actor':actor,'pricing':t.plain(pricing)}
        for source,entry in state['actors'].items():
            keys=[k for k in KEYS if k.startswith(source+':')]
            urls=[data[k]['url'] for k in keys]
            body={'startUrls':[{'url':u} for u in urls],'resultsLimit':1} if source=='facebook' else {'mode':'urls','postUrls':urls,'maxPosts':2,'includeProfile':False}
            budget['apify_runs']+=1
            budget.setdefault('media_repair_reservations',{}).setdefault(ID,{'ledger':LEDGER,'reserved_starts':0})['reserved_starts']+=1
            docs.save('data/usage.json',usage)
            state['actor_starts_reserved']+=1;entry.update(status='submission_unknown',requested_keys=keys,input=body);save()
            query=urllib.parse.urlencode(run_options())
            run=client.request('/acts/'+entry['actor']+'/runs?'+query,body)['data'];t.record_run(entry,run);save()
            for attempt in range(50):
                run=client.request('/actor-runs/'+entry['id'])['data']
                if run['status'] not in ('READY','RUNNING','TIMING-OUT','ABORTING'):break
                time.sleep(4)
            t.record_run(entry,run);save()
            if run['status']!='SUCCEEDED':raise ValueError('actor_not_successful')
            if provider_charge_limited(run):raise ValueError('provider_charge_limit_may_have_truncated_media')
            rows=client.request('/datasets/'+run['defaultDatasetId']+'/items?format=json&limit=100')
            if not isinstance(rows,list):raise ValueError('invalid_dataset')
            entry['rows']=len(rows);found={}
            for row in rows:
                p,reason=h.s.normalize(t.plain(row),source)
                if p and p['key'] in keys:found[p['key']]=p
                elif reason:entry.setdefault('exclusions',{}).setdefault(reason,0);entry['exclusions'][reason]+=1
            # Keep signed URLs only in this runner; the persistent manifest is query-redacted.
            save_private(Path('/tmp/8zz-media-refreshed-'+source+'.json'),found)
            entry['matched_keys']=list(found);save()
        CACHE.mkdir(mode=0o700,exist_ok=True)
        manifest={'schema':1,'posts':{},'images':{},'created_at':datetime.now(timezone.utc).isoformat()}
        for key in KEYS:
            source=key.split(':',1)[0];found=json.loads(Path('/tmp/8zz-media-refreshed-'+source+'.json').read_text())
            result=state['posts'][key]={'status':'checking','images_sent_to_ai':0};save()
            if key not in found:result['status']='post_not_returned';save();continue
            post=found[key];old=raw[key]
            if any(post[k]!=old[k] for k in ('text','source','post_id','published_at')):
                result['status']='post_identity_or_text_changed';save();continue
            if media_identity(post)!=media_identity(old):
                result['status']='attachment_identity_changed';save();continue
            image_map={}
            original=h.s.download_image
            original_response=safe_media.PinnedTLS.getresponse
            def response(conn):
                res=original_response(conn);result.setdefault('image_http_statuses',[]).append(res.status);return res
            def download(url):
                host,path,query=safe_media.validate_url(url)
                hint={'host':host,'fresh_url_sha256':hashlib.sha256(url.encode()).hexdigest()}
                oe=urllib.parse.parse_qs(query).get('oe',[])
                if oe and re.fullmatch('[0-9a-fA-F]{8}',oe[0]):hint['oe_hint_utc']=datetime.fromtimestamp(int(oe[0],16),timezone.utc).isoformat()
                result.setdefault('download_hints',[]).append(hint)
                mime,blob=original(url)
                digest=hashlib.sha256(blob).hexdigest();filename=digest+'.bin'
                target=CACHE/filename;target.write_bytes(blob);os.chmod(target,0o600)
                image_map[urllib.parse.urlsplit(url).path]={'sha256':digest,'filename':filename,'mime':mime,'bytes':len(blob),'fresh_url_sha256':hashlib.sha256(url.encode()).hexdigest()}
                return mime,blob
            try:
                with patch.object(h.s,'download_image',download),patch.object(safe_media.PinnedTLS,'getresponse',response):parts,scope=prepare(post)
                if not parts or scope.get('media_failures'):raise ValueError('required_images_unavailable')
                manifest['posts'][key]=h.s.public_safe(post);manifest['images'][key]=image_map
                result.update(status='cached',images_downloaded=len(parts),scope=scope)
            except Exception as exc:
                result.update(status='download_failed',error_type=type(exc).__name__,safe_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[a-z_]+',str(exc)) else None)
            save()
        save_private(CACHE/'manifest.json',manifest)
        state['cache_manifest_posts']=len(manifest['posts'])
        state['status']='ready' if all(p['status']=='cached' for p in state['posts'].values()) else 'blocked'
    except Exception as exc:
        state.update(status='blocked',error_type=type(exc).__name__,http_status=getattr(exc,'status',None),safe_reason=str(exc) if isinstance(exc,ValueError) and re.fullmatch('[a-z_]+',str(exc)) else None)
    for entry in state['actors'].values():
        if not entry.get('id'):continue
        try:t.record_run(entry,client.request('/actor-runs/'+entry['id'])['data'])
        except Exception as exc:entry['cost_refresh_error_type']=type(exc).__name__;break
    state['monthly_runs_after']=budget['apify_runs']
    reservation=budget.get('media_repair_reservations',{}).get(ID)
    if reservation is not None:
        reservation['runs']=[{'source':s,'id':r.get('id'),'status':r.get('status'),'usageTotalUsd':r.get('usageTotalUsd')} for s,r in state['actors'].items()]
        docs.save('data/usage.json',usage)
    save();return state


if __name__=='__main__':
    if os.getenv('AUTHORIZED_MEDIA_REPAIR')!=ID:raise SystemExit('wrong repair authorization')
    key=os.environ.pop('APIFY_TOKEN','');token=os.environ.pop('GH_TOKEN','')
    if not key or not token:raise SystemExit('missing dedicated credentials')
    result=run(t.Docs(token),t.Client(key))
    print(json.dumps({'id':ID,'status':result['status'],'posts':result['posts'],'actor_starts_reserved':result['actor_starts_reserved']},ensure_ascii=False))
