"""Explicit 2026-11-15 continuation; existing author policy, cache and durable ledgers. MPL-2.0."""
import json,os,sys
from unittest.mock import patch
import history_latest_acquire_20261114 as latest
import history_latest_classify_20261114 as classify
import history_cached_completion as media_module
import history_completion as hc
import history_worker as h

SESSION='latest-history-20261115'
RESUME='20261115-media-repair-01'

def configure():
    latest.SESSION=SESSION
    latest.PATH='data/history_latest_acquisition_20261115.json'
    latest.BACKUP='data/history_completion_before_latest_20261115.json'
    classify.SESSION=RESUME

def keep_denied_old_media(media,held):
    media.state['old_missing_recovery']={'status':'held_no_resend','http_status':403,
        'evidence':'data/history_media_repairs/20261114-media-repair-04.json',
        'note':'Previous scoped-key access denied. No credential/scope change reported; no repeated old-run request or unverified Actor restart.'}
    media.save()
    return set(held)

class NoCaptureRefetchMedia(classify.Media):
    def prepare(self,post):
        already_captured=hc.h.s.read(hc.ROOT/hc.DELTA,{})
        if (post['key'] in already_captured and classify.media_plan(post)['image_attachments'] and
            post['key'] not in self.manifest['posts']):
            raise ValueError('saved_capture_image_unavailable_no_actor_refetch')
        return super().prepare(post)

def cache_new_capture():
    root=media_module.CACHE
    manifest=json.loads((root/'manifest.json').read_text())
    media=object.__new__(media_module.Media);media.manifest=manifest
    data=hc.archive();excluded,_=hc.exclusions(data);audit=[]
    for key,p in h.s.read(hc.RAW,{}).items():
        if key in excluded or not classify.media_plan(p)['image_attachments'] or key in manifest['posts']:continue
        row={'key':key,'status':'checking'}
        try:media.cache_post(p,data[key]);row.update(status='cached',images=len(manifest['images'][key]))
        except Exception as exc:row.update(status='unavailable',error_type=type(exc).__name__)
        audit.append(row)
    h.s.write(root/'capture-audit-20261115.json',audit)
    print(json.dumps({'new_image_posts':len(audit),'cached':sum(x['status']=='cached' for x in audit)}),flush=True)

def main():
    if (os.getenv('AUTHORIZED_LATEST_HISTORY')!=SESSION or os.getenv('AUTHORIZED_RESUME_ID')!=RESUME or
        os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or os.getenv('GITHUB_RUN_ATTEMPT')!='1' or h.policy.fingerprint()!=hc.RULE):raise SystemExit('authorization mismatch')
    configure()
    if sys.argv[1:]==['acquire']:latest.main()
    elif sys.argv[1:]==['cache']:cache_new_capture()
    elif sys.argv[1:]==['classify']:
        with patch.object(classify,'Media',NoCaptureRefetchMedia),patch.object(classify,'allow_proven_missing_only',keep_denied_old_media):classify.main()
    else:raise SystemExit('Choose acquire/cache/classify')

if __name__=='__main__':main()
