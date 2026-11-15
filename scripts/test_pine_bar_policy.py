"""Execute only generated selection expressions; not a Pine compiler/broker emulator."""
import re,textwrap,unittest
from pathlib import Path
from types import SimpleNamespace
from pine_bar_policy import MARKER,apply_latest_post_policy
ROOT=Path(__file__).resolve().parents[1]

def execute_subset(block,scope):
    lines=[]
    for raw in textwrap.dedent(block).splitlines():
        if not raw.strip() or raw.lstrip().startswith('//'):continue
        line=re.sub(r'^(\s*)(?:int|bool|string|float) ',r'\1',raw).replace(':=','=')
        line=line.replace('time_close[1]','previous_close').replace('emaBasis[1]','previous_ema')
        line=re.sub(r'= na$', '= None',line)
        if line.lstrip().startswith('for i = '):
            indent=line[:len(line)-len(line.lstrip())]
            line=indent+'for i in range(0, array.size(evt_time)):'
        elif line.lstrip().startswith(('if ','while ')):line+=':'
        elif '?' in line:
            left,expr=line.split('=',1);condition,rest=expr.split('?',1);yes,no=rest.split(':',1)
            line=left+'= ('+yes+') if ('+condition+') else ('+no+')'
        lines.append(line)
    scope.update(array=SimpleNamespace(get=lambda a,i:a[i],size=len),na=lambda v:v is None)
    exec('\n'.join(lines),{'__builtins__':{'range':range}},scope)
    return scope

class SameBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indicator=(ROOT/'candidates/8zz-history-latest.pine').read_text()
        cls.strategy=(ROOT/'candidates/8zz-strategy-latest.pine').read_text()
    def select(self,events,previous=0,close=1800,cursor=0):
        times=[t for t,d in events];dirs=[d for t,d in events]
        shared=dict(evt_time=times,evt_dir=dirs,previous_close=previous,time_close=close)
        indicator=self.indicator.split(MARKER,1)[1].split('if not na(latestEventIndex)',1)[0]
        a=execute_subset(indicator,dict(shared))['latestEventIndex']
        start=self.strategy.index('        int selectedEventIndex = na')
        end=self.strategy.index('        // Select by publication time',start)
        b=execute_subset(self.strategy[start:end],dict(shared,startAt=0,decisionClose=close,eventCursor=cursor))
        return a,b
    def test_last_post_wins_long_short_and_round_trip_within_one_bar(self):
        for events,expected in [([(100,1),(200,-1)],-1), ([(100,-1),(200,1)],1), ([(100,1),(200,-1),(300,1)],1), ([(100,-1),(200,1),(300,-1)],-1)]:
            a,b=self.select(events)
            self.assertEqual(events[a][1],expected);self.assertEqual(events[b['selectedEventIndex']][1],expected)
            self.assertEqual(a,len(events)-1);self.assertEqual(b['eventCursor'],len(events))
    def test_boundaries_and_cursor_next_bar_never_replay_older_posts(self):
        events=[(-1,-1),(0,1),(1799,-1),(1800,1),(1801,-1)]
        a,b=self.select(events);self.assertEqual((a,b['selectedEventIndex']),(2,2))
        a,b=self.select(events,previous=1800,close=3600,cursor=b['eventCursor'])
        self.assertEqual((a,b['selectedEventIndex']),(4,4))
        a,b=self.select(events,previous=3600,close=5400,cursor=b['eventCursor'])
        self.assertIsNone(a);self.assertIsNone(b['selectedEventIndex'])
    def test_neutral_non_signal_does_not_replace_latest_directional_signal(self):
        a,b=self.select([(100,1),(200,0)])
        self.assertEqual((a,b['selectedEventIndex']),(0,0))
    def test_indicator_uses_publication_timestamp_not_array_position(self):
        # Production arrays are validated sorted; this also guards the selection comparison.
        a,_=self.select([(100,1),(300,-1),(200,1)])
        self.assertEqual(a,1)
    def test_latest_filtered_event_does_not_fall_back_to_older_passing_event(self):
        events=[(100,1),(200,-1)];_,selected=self.select(events)
        start=self.strategy.index('        if not na(selectedEventIndex)')
        end=self.strategy.index('\n\n        // Terminal liquidation',start)
        scope=dict(selected,evt_str=[3,1],signalQuality=lambda *args:58,minQualityScore=0,qualityEntryOk=False,lastSignalScore=None,evt_tips=['older-long','latest-short'],signalDir=0,beforeDir=0,eligibleEvents=0,lastTip='',close=100,emaBasis=90,previous_ema=90,rsiValue=60,htfClose=100,htfEma=90,useTrendFilter=False,useRsiFilter=True,useVolFilter=False,useHtfConfirm=False,atrPct=2,minAtrPct=1)
        out=execute_subset(self.strategy[start:end],scope)
        self.assertFalse(out['passFilters']);self.assertEqual(out['signalDir'],0);self.assertFalse(out['flipNow']);self.assertEqual(out['lastTip'],'')
    def test_indicator_only_applies_one_event_and_refreshes_background_after_it(self):
        source=self.indicator
        self.assertEqual(source.count('int i = latestEventIndex'),1)
        self.assertGreater(source.index('int barsSinceSignal = '),source.index('lastSignalBar := bar_index'))
        self.assertGreater(source.index('effectiveDir = '),source.index('currentDir := d'))
        self.assertEqual(apply_latest_post_policy(source),source)
