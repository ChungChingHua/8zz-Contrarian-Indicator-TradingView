"""Evaluate generated scoring and order decisions offline, not Pine compilation."""
import re,textwrap,unittest
from types import SimpleNamespace
from pathlib import Path
from pine_quality import scoring_source
from test_pine_bar_policy import execute_subset
ROOT=Path(__file__).resolve().parents[1]

class EntryQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=(ROOT/'candidates/8zz-strategy-latest.pine').read_text()
        cls.indicator=(ROOT/'candidates/8zz-history-latest.pine').read_text()
    def score(self,strength,profile='台股個股',enabled=False,passed=True):
        env={k:float(v) for k,v in re.findall(r'(?m)^([A-Z]+_FILTER_(?:BONUS|PENALTY)) = (-?[\d.]+)$',self.text)}
        profile_body=self.text.split('profileBias(profile) =>',1)[1].split('qualityLabel(',1)[0]
        profiles={k:float(v) for k,v in re.findall(r'"([^"]+)" => (-?[\d.]+)',profile_body)}
        fallback=float(re.findall(r'(?m)^        => (-?[\d.]+)',profile_body)[0])
        env.update(s=strength,assetProfile=profile,profileBias=lambda p:profiles.get(p,fallback),clampFloat=lambda v,lo,hi:max(lo,min(hi,v)))
        env.update({k:enabled for k in ('useTrendFilter','useRsiFilter','useVolFilter','useHtfConfirm')})
        env.update({k:passed for k in ('trendOk','rsiOk','volatilityOk','htfOk')})
        body=self.text.split('signalQuality(s, trendOk, rsiOk, volatilityOk, htfOk) =>\n',1)[1].split('\nstring tz',1)[0]
        for name in ('baseScore','filterScore','score'):
            expr=re.search(r'(?m)^    '+name+r' = (.+)$',body)[1]
            expr=re.sub(r'\((\w+) \? \((\w+) \? (\w+) : (\w+)\) : 0\.0\)',r'((\3 if \2 else \4) if \1 else 0.0)',expr)
            env[name]=eval(expr,{'__builtins__':{}},env)
        return env['score']
    def quality_ok(self,score,threshold):
        expr=re.search(r'qualityEntryOk := (.+)',self.text)[1]
        return eval(expr,{'__builtins__':{}},dict(score=score,minQualityScore=threshold,na=lambda v:v is None))
    def orders(self,mode_a,direction,position,quality,margin=True,allow_short=True,fixed_exit=False):
        begin=self.text.index('            if flipNow and orderQty')
        end=self.text.index('// Stops are submitted',begin)
        block=textwrap.dedent(self.text[begin:end]);lines=[]
        for raw in block.splitlines():
            if not raw.strip() or raw.lstrip().startswith('//'):continue
            indent=raw[:len(raw)-len(raw.lstrip())];s=raw.strip().replace(':=','=')
            if s.startswith('else if '):s='elif '+s[8:]+':'
            elif s.startswith('if '):s+=':'
            elif s=='else':s='else:'
            s=re.sub(r'\btrue\b','True',s);s=re.sub(r'\bfalse\b','False',s)
            lines.append(indent+s)
        calls=[]
        strategy=SimpleNamespace(position_size=position,long=1,short=-1,
            entry=lambda id,direction,**kw:calls.append(('entry',id,direction)),
            close=lambda id,**kw:calls.append(('close',id,kw['comment'])))
        env=dict(strategy=strategy,modeA=mode_a,signalDir=direction,qualityEntryOk=quality,entryMarginReady=margin,
            allowShort=allow_short,fixedExitNow=fixed_exit,flipNow=True,orderQty=1,useAtrStop=True,useTrailingStop=True,
            riskAtr=10,na=lambda v:v is None,dayBarCount=1)
        exec('\n'.join(lines),{'__builtins__':{}},env)
        return calls
    def test_shared_formula_is_exactly_generated_from_indicator(self):
        self.assertIn(scoring_source(self.indicator),self.text)
        self.assertNotIn('__QUALITY_SCORING__',self.text)
        self.assertIn('minQualityScore = input.float(0.0',self.text)
        for strength,expected in ((1,58),(2,73),(3,88)):
            self.assertEqual(self.score(strength),expected)
        self.assertEqual(self.score(3,'商品'),76)
        self.assertEqual(self.score(3,'ETF'),72)
        self.assertEqual(self.score(3,enabled=True,passed=True),100)
        self.assertEqual(self.score(1,enabled=True,passed=False),0)
    def test_inclusive_boundary_disabled_and_missing_score(self):
        for score,threshold,expected in ((79.999,80,False),(80,80,True),(80.001,80,True),(100,100,True),(None,0,True),(None,1,False),(0,0,True)):
            self.assertEqual(self.quality_ok(score,threshold),expected)
    def test_both_modes_and_directions_require_quality_for_new_entries(self):
        for mode_a in (True,False):
            for direction,id in ((1,'L'),(-1,'S')):
                self.assertEqual(self.orders(mode_a,direction,0,False),[])
                self.assertEqual(self.orders(mode_a,direction,0,True),[('entry',id,direction)])
                self.assertEqual(self.orders(mode_a,direction,0,True,margin=False),[])
    def test_low_quality_reverse_still_closes_both_existing_sides(self):
        for direction,position,id in ((1,-1,'S'),(-1,1,'L')):
            for margin in (True,False):
                calls=self.orders(False,direction,position,False,margin)
                self.assertEqual(len(calls),1);self.assertEqual(calls[0][:2],('close',id));self.assertIn('品質不足',calls[0][2])
            self.assertEqual(self.orders(False,direction,position,True),[('entry','L' if direction==1 else 'S',direction)])
        self.assertEqual(self.orders(False,-1,1,False,allow_short=False)[0][:2],('close','L'))
    def test_quality_does_not_enable_a_overlap_or_same_close_reentry(self):
        self.assertEqual(self.orders(True,-1,1,True),[])
        self.assertEqual(self.orders(True,1,0,True,fixed_exit=True),[])
        risk=self.text.split('// Stops are submitted',1)[1].split('plot(showRiskStop',1)[0]
        self.assertNotIn('qualityEntryOk',risk)
        self.assertLess(self.text.index('if decisionClose == finishAt'),self.text.index('if flipNow and orderQty'))
    def test_latest_low_score_never_restores_earlier_high_score(self):
        start=self.text.index('        if not na(selectedEventIndex)');end=self.text.index('\n\n        // Terminal liquidation',start)
        env=dict(selectedEventIndex=1,evt_dir=[1,-1],evt_str=[3,1],evt_tips=['earlier-high','latest-low'],
            close=100,emaBasis=90,previous_ema=90,rsiValue=60,htfClose=100,htfEma=90,atrPct=2,minAtrPct=1,
            useTrendFilter=False,useRsiFilter=False,useVolFilter=False,useHtfConfirm=False,
            signalQuality=lambda s,*args:self.score(s),minQualityScore=80,qualityEntryOk=False,
            signalDir=0,beforeDir=0,eligibleEvents=0,lastSignalScore=None,lastTip='')
        out=execute_subset(self.text[start:end],env)
        self.assertEqual(out['lastSignalScore'],58);self.assertEqual(out['signalDir'],-1)
        self.assertFalse(out['qualityEntryOk']);self.assertTrue(out['flipNow']);self.assertEqual(out['lastTip'],'latest-low')
    def test_same_direction_after_skipped_entry_is_not_late_filled(self):
        expr=re.search(r'flipNow := (.+)',self.text)[1]
        self.assertFalse(eval(expr,{'__builtins__':{}},dict(signalDir=1,beforeDir=1)))

if __name__=='__main__':unittest.main()
