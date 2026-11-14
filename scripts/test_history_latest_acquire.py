import copy,unittest
from datetime import datetime,timedelta
import history_latest_acquire_20261114 as latest

class LatestAcquisitionTests(unittest.TestCase):
    def prior(self):
        return {'acquisition_completed':True,'sources':{s:{'completed_until':'2026-11-07T12:15:59+00:00'} for s in ('facebook','threads')},'runs':[{'processed':True,'submission_unknown':False}]}
    def test_successful_cutoffs_with_overlap_and_original_unchanged(self):
        prior=self.prior();before=copy.deepcopy(prior)
        c=latest.fresh_control(prior,'2026-11-14T10:30:00+00:00')
        self.assertEqual(prior,before);self.assertEqual(c['runs'],[])
        for s in c['sources'].values():
            self.assertEqual(s['start_utc'],'2026-11-07T10:15:59+00:00')
            self.assertEqual(s['end_utc'],c['cutoff_utc']);self.assertFalse(s['complete'])
        self.assertFalse(c['acquisition_completed'])
    def test_unresolved_old_run_or_window_prevents_new_acquisition(self):
        for change in ({'processed':False},{'submission_unknown':True}):
            p=self.prior();p['runs'][0].update(change)
            with self.assertRaisesRegex(ValueError,'prior_run_unresolved'):latest.fresh_control(p,'2026-11-14T10:30:00+00:00')
        p=self.prior();p['acquisition_completed']=False
        with self.assertRaisesRegex(ValueError,'previous_acquisition_unresolved'):latest.fresh_control(p,'2026-11-14T10:30:00+00:00')
    def test_source_cutoffs_are_independent(self):
        p=self.prior();p['sources']['threads']['completed_until']='2026-11-08T12:00:00+00:00'
        c=latest.fresh_control(p,'2026-11-14T10:30:00+00:00')
        self.assertEqual(c['sources']['threads']['start_utc'],'2026-11-08T10:00:00+00:00')
        self.assertEqual(c['sources']['facebook']['start_utc'],'2026-11-07T10:15:59+00:00')
    def test_no_fallback_to_latest_post_for_missing_cutoff(self):
        p=self.prior();p['sources']['threads'].pop('completed_until')
        with self.assertRaisesRegex(ValueError,'invalid_successful_source_cutoff'):latest.fresh_control(p,'2026-11-14T10:30:00+00:00')
    def test_exact_actor_alias_rewrite_never_rewrites_other_paths(self):
        self.assertEqual(latest.canonical('/acts/apify~facebook-posts-scraper/runs?maxItems=50'),'/acts/KoJrdxJCTtpon81KY/runs?maxItems=50')
        self.assertEqual(latest.canonical('/acts/automation-lab~threads-scraper'),'/acts/yacNYZpu9F3C8EATQ')
        for path in ('/actor-runs/existing','/datasets/existing/items','/acts/apify~facebook-posts-scraper-other'):
            self.assertEqual(latest.canonical(path),path)

if __name__=='__main__':unittest.main()
