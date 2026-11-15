import copy,unittest
import history_missing_media_20261115 as r
import history_latest_classify_20261114 as c

class PinnedEmptyRecoveryTests(unittest.TestCase):
    def fixture(self):
        run={'id':c.OLD_EMPTY_RUN,'defaultDatasetId':c.OLD_EMPTY_DATASET,'status':'ABORTED','finishedAt':'2026-11-14T07:00:39Z','dataset_counts':{'itemCount':0,'cleanItemCount':0},'chargedEventCounts':{'post':0},'cost_observed_at':'2026-11-14T07:06:12Z'}
        prior={'id':c.OLD_EMPTY_RUN,'defaultDatasetId':c.OLD_EMPTY_DATASET,'status':'ABORTED','posts':{}}
        return {'runs':[run]},prior
    def test_valid_archived_evidence_is_honestly_labelled_not_current_api_read(self):
        audit,prior=self.fixture();proof=r.validate_empty_evidence(audit,prior)
        self.assertEqual(proof['dataset_items'],0)
        self.assertEqual(proof['verification_method'],'offline_pinned_previous_official_API_snapshot')
        self.assertEqual(proof['provider_observed_at'],'2026-11-14T07:06:12Z')
        self.assertEqual(proof['source_git_commit'],r.EVIDENCE_COMMIT)
    def test_nonzero_unknown_or_boolean_counts_never_authorize_resend(self):
        for key in ('itemCount','cleanItemCount'):
            for value in (1,None,False):
                audit,prior=self.fixture();audit['runs'][0]['dataset_counts'][key]=value
                with self.assertRaises(ValueError):r.validate_empty_evidence(audit,prior)
        audit,prior=self.fixture();audit['runs'][0]['chargedEventCounts']['post']=1
        with self.assertRaises(ValueError):r.validate_empty_evidence(audit,prior)
    def test_running_nonempty_or_different_prior_run_is_never_replayed(self):
        for change in ({'status':'RUNNING'},{'status':'SUCCEEDED'},{'id':'unknown'},{'posts':{'p':{'status':'cached'}}}):
            audit,prior=self.fixture();prior.update(change)
            with self.assertRaises(ValueError):r.validate_empty_evidence(audit,prior)

if __name__=='__main__':unittest.main()
