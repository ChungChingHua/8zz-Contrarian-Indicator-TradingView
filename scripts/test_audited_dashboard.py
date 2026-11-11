"""Accounting regression tests plus independent reconciliation of the saved real sample."""
import json, unittest, math
from pathlib import Path
from build_audited_dashboard import simulate,outcome,events,ROOT
from pine_accounting import apply_accounting
class AuditTests(unittest.TestCase):
    def event(self,i,t,d):return {'id':i,'unix_ms':t,'direction':d,'is_flip':True}
    def bars(self,prices):return [{'time':(i+1)*1000,'price':p} for i,p in enumerate(prices)]
    def test_symmetric_loss_and_tie(self):
        self.assertLess(outcome(1,100,90),0);self.assertLess(outcome(-1,100,110),0)
        for d in (-1,1):self.assertEqual(outcome(d,100,100),0)
    def test_future_close_only_and_open_excluded(self):
        r=simulate([self.event(1,1000,1),self.event(2,2200,-1)],self.bars([100,90,80,85]),'B')
        self.assertEqual(r['trades'][0]['entry']['time'],2000)
        self.assertEqual(r['stats']['settled'],1);self.assertEqual(r['stats']['open'],1)
        self.assertEqual(r['stats']['losses'],1);self.assertEqual(r['stats']['win_rate'],0)
    def test_same_close_net_no_fake_round_trip(self):
        r=simulate([self.event(1,100,1),self.event(2,200,-1),self.event(3,300,1)],self.bars([100,110]),'B')
        self.assertEqual(len(r['trades']),1);self.assertEqual(r['trades'][0]['event_id'],3)
        self.assertEqual(r['stats']['settled'],0)
    def test_fixed_17_bars_no_calendar_substitution(self):
        r=simulate([self.event(1,1,1)],self.bars(range(100,119)),'A',17)
        self.assertEqual(r['trades'][0]['exit']['time'],18000)
    def test_fixed_holding_not_overwritten(self):
        r=simulate([self.event(1,1,1),self.event(2,1100,-1),self.event(3,3100,1)],self.bars(range(100,121)),'A',17)
        self.assertEqual(len(r['trades']),1);self.assertFalse(r['rows']['2']['trade'])
    def test_missing_not_open_or_zero(self):
        r=simulate([self.event(1,1,1)],[],'A')
        self.assertEqual(r['stats']['missing'],1);self.assertEqual(r['stats']['open'],0);self.assertIsNone(r['stats']['win_rate']);self.assertEqual(r['curve'],[])
    def test_late_retention_not_fake_entry(self):
        r=simulate([self.event(1,1,1)],[{'time':9*86400000,'price':100}],'A')
        self.assertEqual(r['stats']['missing'],1);self.assertEqual(len(r['trades']),0)
    def test_real_saved_sample_full_reconciliation(self):
        from datetime import datetime
        d=json.loads((ROOT/'docs/dashboard-data.json').read_text())
        limit=int(datetime.fromisoformat(d['publication']['before']).timestamp()*1000)
        expected=[e for e in events() if e['unix_ms']<limit]
        self.assertEqual(len(d['events']),len(expected))
        self.assertEqual(sum(e['direction']==0 for e in d['events']),sum(e['direction']==0 for e in expected))
        for mode,m in d['modes'].items():
            s=m['stats'];ts=m['trades'];closed=[t for t in ts if t['exit']]
            self.assertEqual(s['settled'],s['wins']+s['losses']+s['ties'])
            self.assertEqual(s['settled'],len(closed));self.assertEqual(s['open'],len(ts)-len(closed))
            for t in ts:
                e=d['events'][t['event_id']-1]
                self.assertGreater(t['entry']['time'],e['unix_ms']);self.assertTrue(e['is_flip'])
                self.assertEqual(t,m['rows'][str(t['event_id'])])
                if t['exit']:
                    expected=t['direction']*(t['exit']['price']-t['entry']['price'])/t['entry']['price']*100
                    self.assertAlmostEqual(t['pnl'],expected)
            if ts:
                equity=100
                for t in closed:equity*=1+t['pnl']/100
                for t in ts:
                    if not t['exit']:equity*=1+t['floating']/100
                self.assertAlmostEqual(m['curve'][-1]['equity'],equity)
                for previous,next_t in zip(ts,ts[1:]):self.assertLessEqual(previous['exit']['time'],next_t['entry']['time'])
                self.assertEqual(m['curve'][0]['equity'],100)
                self.assertEqual(m['curve'][0]['benchmark'],100)
    def test_no_judgment_changes_and_idempotent_pine_patch(self):
        from update_pine_script import EVENT_PATTERN
        from pine_history import reconcile_history
        original,_=reconcile_history((ROOT/'data/historical-indicator.pine').read_text())
        candidate=(ROOT/'candidates/8zz-history-latest.pine').read_text()
        for block in EVENT_PATTERN.findall(original):self.assertIn(block,EVENT_PATTERN.findall(candidate))
        self.assertEqual(apply_accounting(candidate),candidate)
        self.assertIn('if passFilters and d != 0',candidate)
if __name__=='__main__':unittest.main()
