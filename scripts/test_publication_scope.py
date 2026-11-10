import copy,json,unittest
from datetime import datetime
from pathlib import Path
from publication_scope import scope,assert_boundary
from build_audited_dashboard import ROOT
class ScopeTests(unittest.TestCase):
    def test_actual_release_excludes_later_posts_market_and_curves(self):
        data=json.loads((ROOT/'docs/dashboard-data.json').read_text());assert_boundary(data)
        self.assertEqual(len(data['inventory']),455)
        self.assertEqual(data['history']['post_status_counts']['not_started'],45)
        self.assertEqual(len(data['events']),294)
        self.assertEqual(data['publication']['before'],'2026-10-01T00:00:00+08:00')
    def test_october_and_november_are_removed_before_simulation(self):
        policy=json.loads((ROOT/'data/publication_policy.json').read_text())
        ms=lambda t:int(datetime.fromisoformat(t).timestamp()*1000)
        dates=['2026-09-30T23:59:59+08:00','2026-10-01T00:00:00+08:00','2026-11-10T10:00:00+08:00']
        events=[{'id':i,'unix_ms':ms(t),'time':t,'direction':1} for i,t in enumerate(dates)]
        rows=[{'display_time':t,'status':'not_started'} for t in dates]
        market={'series':{'1d':[{'time':ms(t),'price':100} for t in dates]}}
        e,r,m,s,p=scope(events,rows,market,policy)
        self.assertEqual(len(e),1);self.assertEqual(len(r),1);self.assertEqual(len(m['series']['1d']),1)
        self.assertEqual(s['archive_posts'],1);self.assertEqual(len(events),3)
    def test_packaging_guard_rejects_late_injected_source(self):
        data=json.loads((ROOT/'docs/dashboard-data.json').read_text())
        for target in ('event','post','market','curve'):
            n=copy.deepcopy(data)
            if target=='event':n['events'].append({'unix_ms':1800000000000})
            if target=='post':n['inventory'].append({'display_time':'2026-11-10T00:00:00+08:00'})
            if target=='market':n['market']['series']['1d'].append({'time':1800000000000})
            if target=='curve':n['modes']['B']['curve'].append({'time':1800000000000})
            with self.assertRaises(ValueError):assert_boundary(n)
