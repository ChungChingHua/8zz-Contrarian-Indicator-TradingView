"""One explicit repair of proven zero-result media; no denied old-run retry. MPL-2.0."""
import hashlib,json,os,subprocess
from unittest.mock import patch
import history_continue_20261115 as continuation
import history_latest_classify_20261114 as classify
import history_completion as hc
import history_worker as h

RESUME='20261115-media-repair-02'
EVIDENCE_COMMIT='c137481646469c46b42fde0ac2151c04181c9a14'
EVIDENCE_PATH='data/history_media_repairs/budget-audit-20261114.json'
EVIDENCE_SHA='be681da028b6c31e39ecb6db9247ceb396e94de109312dadac0be591aa30e4d5'
EXPECTED={'facebook:'+x for x in ('1702487071235881','1702731291211459','1702897424528179','1703163464501575','1703429887808266','1703740244443897','1703792734438648','1704945814323340','1705156784302243','1705237887627466')}

def validate_empty_evidence(audit,prior):
    matches=[r for r in audit.get('runs',[]) if r.get('id')==classify.OLD_EMPTY_RUN]
    if len(matches)!=1:raise ValueError('missing_unique_pinned_run_evidence')
    run=matches[0]
    if (prior.get('id')!=classify.OLD_EMPTY_RUN or prior.get('status')!='ABORTED' or prior.get('posts') or
        prior.get('defaultDatasetId')!=classify.OLD_EMPTY_DATASET or run.get('status')!='ABORTED' or
        run.get('defaultDatasetId')!=classify.OLD_EMPTY_DATASET or not run.get('finishedAt')):raise ValueError('predecessor_not_proven_aborted')
    for n in (run.get('dataset_counts',{}).get('itemCount'),run.get('dataset_counts',{}).get('cleanItemCount'),run.get('chargedEventCounts',{}).get('post')):
        if type(n) is not int or n!=0:raise ValueError('predecessor_not_proven_zero_result')
    proof=classify.empty_proof(run,[])
    proof.update(verification_method='offline_pinned_previous_official_API_snapshot',source_git_commit=EVIDENCE_COMMIT,
        source_path=EVIDENCE_PATH,source_sha256=EVIDENCE_SHA,provider_observed_at=run.get('cost_observed_at'),
        current_old_run_access='not_queried; previous scoped token denied. This evidence describes the recorded terminal run, not a new API observation.')
    return proof

def authorize_only_unfetched(media,held):
    if set(held)!=EXPECTED:raise ValueError('exact_missing_media_scope_changed')
    excluded,_=hc.exclusions(media.data)
    if EXPECTED & excluded:raise ValueError('dispatched_or_reviewed_post_must_not_be_retried')
    prior=[media.prior_by_key.get(k,{}).get('batch',{}) for k in EXPECTED]
    if any(p.get('id')!=classify.OLD_EMPTY_RUN for p in prior):raise ValueError('unknown_or_different_predecessor_no_resend')
    blob=subprocess.run(['git','show',EVIDENCE_COMMIT+':'+EVIDENCE_PATH],check=True,capture_output=True).stdout
    if hashlib.sha256(blob).hexdigest()!=EVIDENCE_SHA:raise ValueError('pinned_snapshot_hash_mismatch')
    proof=validate_empty_evidence(json.loads(blob),prior[0])
    media.state.update(verified_empty_predecessor=proof,recovery_candidate_keys=sorted(EXPECTED),
        recovery_note='User authorized unfetched missing public posts. Recorded official terminal ABORTED/zero-post/empty-dataset evidence is pinned and hash verified. One new session attempt; no unknown or completed request is replayed.')
    media.save() # Durable evidence ACK before newly authorized targeted Actor submission.
    for k in EXPECTED:media.prior_by_key.pop(k);media.attempted.discard(k)
    return set()

def main():
    if (os.getenv('AUTHORIZED_LATEST_HISTORY')!=continuation.SESSION or os.getenv('AUTHORIZED_RESUME_ID')!=RESUME or
        os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH or os.getenv('GITHUB_RUN_ATTEMPT')!='1' or h.policy.fingerprint()!=hc.RULE):raise SystemExit('authorization mismatch')
    continuation.configure();classify.SESSION=RESUME
    remote=hc.Remote(os.environ.get('GH_TOKEN',''));control=remote.load(hc.CONTROL,{})
    if (control.get('current_session',{}).get('id')!=continuation.RESUME or not control.get('closed') or
        control.get('stop_reason')!='prior_missing_media_not_verified_for_resend'):raise SystemExit('previous session not safely complete; no repair started')
    excluded,_=hc.exclusions(hc.archive());groups,_=hc.select(hc.archive(),excluded,100)
    if {p['key'] for g in groups for p in g}!=EXPECTED:raise SystemExit('only exact ten never-dispatched missing posts authorized')
    with patch.object(classify,'allow_proven_missing_only',authorize_only_unfetched):classify.main()

if __name__=='__main__':main()
