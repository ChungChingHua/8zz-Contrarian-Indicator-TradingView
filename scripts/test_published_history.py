"""Regression against the actual 65-event Pine supplied by the user; offline only."""
import hashlib,json,unittest
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from update_pine_script import EVENT_PATTERN
from pine_history import reconcile_history,ROOT

def fields(text):return EVENT_PATTERN.findall(text)
def stamp(value):return int(datetime.fromisoformat(value).timestamp()*1000)

def replay_hourly(text):
    """Replay the Pine timestamp/flip/add branches, with filters disabled, Apr 8-10.
    This checks event dispatch/state; it is not a Pine compiler or a market backtest.
    """
    events=[(int(r[0]),int(r[1]),int(r[2])) for r in fields(text)]
    previous=stamp('2026-04-07T13:30:00+08:00');direction=0;position=0
    for ts,d,s in events:
        if ts>=previous:break
        if not d:continue
        position=min(position+1,5) if d==direction else 1;direction=d
    trace=[]
    for day in (8,9,10):
        for hour,minute in ((10,0),(11,0),(12,0),(13,0),(13,30)):
            closing=stamp(f'2026-04-{day:02d}T{hour:02d}:{minute:02d}:00+08:00')
            labels=[];background=direction
            for ts,d,s in events:
                if previous<=ts<closing and d:
                    flip=d!=direction
                    position=1 if flip else min(position+1,5);direction=d
                    labels.append((ts,d,s,'flip' if flip else 'add'))
            trace.append((closing,background,direction,position,labels));previous=closing
    return trace

class PublishedHistoryTests(unittest.TestCase):
    def setUp(self):
        self.base=(ROOT/'data/historical-indicator.pine').read_text()
        self.reference=(ROOT/'data/author-published-20260410.pine').read_text()
        self.result,self.audit=reconcile_history(self.base)
    def test_all_published_literals_and_later_fork_events_preserved(self):
        result=fields(self.result);reference=fields(self.reference)
        self.assertEqual(len(reference),65);self.assertEqual(len(result),151)
        self.assertEqual([r for r in result if int(r[0])<=int(reference[-1][0])],reference)
        for r in fields(self.base):
            if int(r[0])>int(reference[-1][0]):self.assertIn(r,result)
        self.assertEqual(self.audit['updated_events'],5);self.assertEqual(self.audit['retimed_events'],1)
        self.assertEqual(self.audit['inserted_events'],1);self.assertEqual(self.audit['unchanged_fork_events'],144)
    def test_real_april_nine_hourly_signals_match_published_source(self):
        candidate=(ROOT/'candidates/8zz-history-latest.pine').read_text()
        expected=replay_hourly(self.reference)
        self.assertEqual(replay_hourly(candidate),expected)
        self.assertNotEqual(replay_hourly(self.base),expected)
        bar=next(r for r in expected if r[0]==stamp('2026-04-09T10:00:00+08:00'))
        self.assertEqual([x[1] for x in bar[4]],[1,1]);self.assertEqual(bar[2],1)
        observed=next(r for r in expected if r[0]==stamp('2026-04-09T13:00:00+08:00'))
        self.assertEqual([x[1] for x in observed[4]],[1]);self.assertEqual(observed[2],1)
    def test_source_changes_require_explicit_reconciliation(self):
        manifest=json.loads((ROOT/'data/author_history_reconciliation.json').read_text())
        self.assertEqual(hashlib.sha256(self.base.encode()).hexdigest(),manifest['fork_base_sha256'])
        with self.assertRaisesRegex(ValueError,'fork_history_source_changed'):reconcile_history(self.base+'\n// unexpected edit\n')
        self.assertEqual(reconcile_history(self.base)[0],self.result)
if __name__=='__main__':unittest.main()
