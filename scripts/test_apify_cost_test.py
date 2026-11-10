import ast
import copy
import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import apify_cost_test as t

NOW = datetime(2026, 11, 10, 4, 0, tzinfo=timezone.utc)

class Docs:
    def __init__(self, count=6): self.data = {'data/usage.json': {'2026-11': {'apify_runs': count, 'ai_attempts': 10}}}
    def load(self, p): return copy.deepcopy(self.data.get(p))
    def save(self, p, v): self.data[p] = copy.deepcopy(t.plain(v))
    def formal_shas(self): return {'cursor': 'unchanged', 'pine': 'unchanged', 'notifications': 'unchanged'}

class Client:
    def __init__(self, error=False, count=0, cap='0.10'):
        self.counts={'GET':0,'POST':0}; self.error=error; self.result_count=count; self.cap=cap; self.calls=[]
    def request(self, path, payload=None):
        method='GET' if payload is None else 'POST'; self.counts[method]+=1; self.calls.append((path,payload))
        if '/abort' in path: return {}
        if payload is not None:
            if self.error: raise t.Failure('transport_unknown')
            return {'data':self.run(str(self.counts['POST']))}
        if path.startswith('/acts/'):
            return {'data': {'pricingInfos': [{'startedAt':'2026-01-01T00:00:00Z','pricingModel':'PAY_PER_EVENT'}]}}
        if path.startswith('/actor-runs/'): return {'data':self.run(path.rsplit('/',1)[-1])}
        if path.startswith('/datasets/'): return [{}]*self.result_count
        raise AssertionError(path)
    def run(self,id):
        return {'id':id,'status':'SUCCEEDED','buildId':'build-id','buildNumber':'1.2.3',
                'defaultDatasetId':'data','options':{'maxTotalChargeUsd':Decimal(self.cap)},
                'usageTotalUsd':Decimal('0.00000123456789'),'stats':{'runTimeSecs':Decimal('1.234')}}

class Test(unittest.TestCase):
    def go(self,d=None,c=None):
        d=d or Docs();c=c or Client()
        return d,c,t.execute(d,c,clock=lambda:NOW,pause=lambda n:None)
    def test_two_starts_and_window_and_state(self):
        d,c,r=self.go()
        self.assertEqual(c.counts['POST'],2)
        self.assertEqual(r['end_taipei'],'2026-11-10T12:00:00+08:00')
        self.assertEqual(r['start_taipei'],'2026-11-10T11:45:00+08:00')
        self.assertTrue(r['formal_state_unchanged'])
        self.assertEqual(set(d.data), {'data/usage.json',t.PATH})
        self.assertEqual(d.data['data/usage.json']['2026-11']['apify_runs'],8)
        self.assertEqual(r['actors']['facebook']['usageTotalUsd'],'0.00000123456789')
        self.assertEqual(r['actors']['facebook']['cost_category'],'no_new_post_check')
        before=dict(c.counts);self.assertEqual(t.execute(d,c),r);self.assertEqual(c.counts,before)
    def test_guard_no_start(self):
        d,c,r=self.go(Docs(69));self.assertEqual(c.counts['POST'],0)
        self.assertEqual(r['error_code'],'existing_monthly_70_run_guard_no_start')
    def test_unknown_never_retry(self):
        d,c,r=self.go(c=Client(error=True));self.assertEqual(c.counts['POST'],1)
        self.assertEqual(r['actors']['facebook']['status'],'submission_unknown')
        t.execute(d,c);self.assertEqual(c.counts['POST'],1)
    def test_missing_cap_aborts_without_second_start(self):
        d,c,r=self.go(c=Client(cap='1'))
        self.assertEqual(r['error_code'],'cap_not_acknowledged_run_aborted')
        self.assertEqual(c.counts['POST'],2) # one start + one abort; never second Actor
        self.assertEqual(sum('/runs?' in p and b is not None for p,b in c.calls),1)
    def test_results_not_called_no_posts(self):
        with patch.object(t.h.s,'normalize',return_value=(None,'other_author')):
            _,_,r=self.go(c=Client(count=1))
        self.assertEqual(r['actors']['facebook']['cost_category'],'results_present')
        self.assertEqual(r['actors']['facebook']['accepted_count'],0)
    def test_actor_minimum_preflight(self):
        with self.assertRaises(t.Failure):
            t.pricing({'pricingInfos':[{'startedAt':'2026-01-01T00:00:00Z','pricingModel':'PAY_PER_EVENT','minimalMaxTotalChargeUsd':1}]}, NOW)
    def test_formal_input_parity(self):
        tree=ast.parse(Path(__file__).with_name('live_pipeline.py').read_text())
        acquire=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='acquire')
        branch=next(x for x in ast.walk(acquire) if isinstance(x,ast.If) and ast.unparse(x.test)=="source == 'facebook'")
        for source in ('facebook','threads'):
            env={'source':source,'start':'2026-11-10T03:45:00+00:00','end':'2026-11-10T04:00:00+00:00'}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[branch],type_ignores=[])),'formal','exec'),env)
            self.assertEqual(env['actor'],t.ACTORS[source]);self.assertEqual(env['body'],t.inputs(source,env['start'],env['end']))
    def test_readonly_observation_cannot_start(self):
        d,c,r=self.go()
        observer=Client();t.observe(d,observer)
        self.assertEqual(observer.counts['POST'],0)
        self.assertEqual(observer.counts['GET'],2)
        self.assertTrue(d.data[t.PATH]['observation_formal_state_unchanged'])
    def test_precision(self):
        parsed=json.loads('{"cost":0.000000000123456789}',parse_float=Decimal)
        self.assertEqual(t.plain(parsed)['cost'],'1.23456789E-10')

if __name__=='__main__':unittest.main()
