import ast
import copy
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import apify_day_replay as d
import apify_cost_test as t

class Docs:
    def __init__(self,count=8): self.data={'data/usage.json':{'2026-11':{'apify_runs':count,'ai_attempts':10}}}
    def load(self,path): return copy.deepcopy(self.data.get(path))
    def save(self,path,value): self.data[path]=copy.deepcopy(t.plain(value))
    def formal_shas(self): return {'formal.pine':'unchanged','data/live_control.json':'unchanged'}

class Client:
    def __init__(self,rows=None,unknown=False,fee='0.008'):
        self.counts={'GET':0,'POST':0};self.calls=[];self.runs={};self.rows=rows;self.unknown=unknown;self.fee=fee
    def request(self,path,payload=None):
        self.counts['GET' if payload is None else 'POST']+=1;self.calls.append((path,payload))
        if '/abort' in path: return {}
        if payload is not None:
            if self.unknown: raise t.Failure('transport_unknown')
            id=str(len(self.runs)+1)
            self.runs[id]={'id':id,'defaultDatasetId':id,'status':'SUCCEEDED','buildNumber':'1.2.3',
                'finishedAt':'2026-11-10T00:00:00Z','options':{'maxTotalChargeUsd':Decimal('.10'),
                'isMaxTotalChargeUsdSetByUser':True,'restartOnError':False},'usageTotalUsd':Decimal(self.fee),
                'externalChargedTotalUsd':Decimal('.001'),'usageUsd':{'event':Decimal(self.fee)},'stats':{'runTimeSecs':Decimal('9.123')}}
            return {'data':copy.deepcopy(self.runs[id])}
        if path.startswith('/acts/'):
            return {'data':{'pricingInfos':[{'startedAt':'2026-01-01T00:00:00Z','pricingModel':'PAY_PER_EVENT'}]}}
        if path.startswith('/actor-runs/'): return {'data':copy.deepcopy(self.runs[path.rsplit('/',1)[-1]])}
        if path.startswith('/datasets/'):
            source='facebook' if int(path.split('/')[2])%2 else 'threads'
            return self.rows if self.rows is not None else ([{'error':'no_items','errorDescription':'No posts'}] if source=='facebook' else [])
        raise AssertionError(path)

class TestReplay(unittest.TestCase):
    def go(self,docs=None,client=None):
        docs=docs or Docs();client=client or Client()
        with patch.object(d,'now',return_value=datetime(2026,11,10,8,tzinfo=timezone.utc)):
            r=d.execute(docs,client,pause=lambda n:None)
        return docs,client,r
    def test_full_day_windows_budget_no_retry_isolation_and_cost(self):
        docs,c,r=self.go()
        self.assertEqual(r['status'],'completed');self.assertEqual(c.counts['POST'],40)
        self.assertEqual(r['runs'][0]['query_start_taipei'],'2026-11-09T11:30:00+08:00')
        self.assertEqual(r['runs'][0]['query_end_taipei'],'2026-11-10T08:45:00+08:00')
        self.assertEqual(r['runs'][2]['query_start_taipei'],'2026-11-10T06:45:00+08:00')
        self.assertEqual(r['runs'][-1]['query_end_taipei'],'2026-11-10T13:30:00+08:00')
        self.assertEqual(r['test_cursors']['facebook'],'2026-11-10T05:30:00+00:00')
        self.assertEqual(r['costs']['observed_total_usd'],'0.320') # no double counting other fields
        self.assertEqual(r['costs']['monthly_estimates_usd']['20'],'6.400')
        self.assertEqual(r['reserved_starts'],40);self.assertEqual(r['monthly_runs_after'],48)
        self.assertEqual(set(docs.data),{'data/usage.json',d.LEDGER,d.POSTS})
        self.assertTrue(r['formal_state_unchanged']);self.assertEqual(r['unattempted'],[])
        self.assertEqual(r['runs'][0]['diagnostic_rows'],1);self.assertEqual(r['runs'][0]['valid_posts'],0)
        self.assertEqual(r['incomplete_windows'],[])
        before=dict(c.counts);d.execute(docs,c);self.assertEqual(c.counts,before)
    def test_monthly_guard(self):
        _,c,r=self.go(Docs(31));self.assertEqual(c.counts['POST'],0)
        self.assertIn('monthly_70',r['error_code'])
    def test_unknown_submission_is_not_resent(self):
        docs,c,r=self.go(client=Client(unknown=True));self.assertEqual(c.counts['POST'],1)
        self.assertEqual(r['runs'][0]['status'],'submission_unknown');self.assertEqual(r['monthly_runs_after'],9)
        d.execute(docs,c);self.assertEqual(c.counts['POST'],1)
    def test_saturated_window_does_not_advance(self):
        _,c,r=self.go(client=Client(rows=[{'error':'no_items'}]*50))
        self.assertEqual(c.counts['POST'],40)
        self.assertEqual(r['runs'][2]['base_start_utc'],d.stamp(d.INITIAL))
        self.assertEqual(r['test_cursors']['facebook'],d.stamp(d.INITIAL))
        self.assertEqual(len(r['incomplete_windows']),40)
    def test_cost_limit_does_not_advance(self):
        _,_,r=self.go(client=Client(fee='.10'))
        self.assertEqual(r['test_cursors']['threads'],d.stamp(d.INITIAL))
        self.assertEqual(r['costs']['observed_total_usd'],'4.00')
    def test_diagnostic_quota_stops_no_next_actor(self):
        _,c,r=self.go(client=Client(rows=[{'error':'quota_exhausted'}]))
        self.assertEqual(c.counts['POST'],1);self.assertEqual(r['status'],'stopped')
        self.assertIn('quota_auth',r['error_code'])
    def test_persistent_schema_errors_stop(self):
        _,c,r=self.go(client=Client(rows=[{'error':'unexpected_schema'}]))
        self.assertEqual(c.counts['POST'],3);self.assertEqual(r['error_code'],'persistent_unrecognized_dataset_stop')
    def test_independent_dedup(self):
        posts={};entry={'round':1};p={'key':'facebook:x','published_at':'2026-11-10T00:59:00+00:00','text':'public','post_id':'x'}
        with patch.object(t.h.s,'normalize',return_value=(p,None)):
            for n in range(2):
                entry={'round':n+1};d.inspect_rows([{}],'facebook',d.FIRST,d.SLOTS[1],posts,entry)
        self.assertEqual(len(posts),1);self.assertEqual(entry['duplicates'],1);self.assertEqual(entry['first_new'],0)
    def test_final_cost_can_revoke_cursor(self):
        r={'test_cursors':{},'runs':[{'round':1,'source':'facebook','status':'SUCCEEDED','result_count':1,
            'query_start_utc':d.stamp(d.INITIAL-timedelta(hours=2)),'query_end_utc':d.stamp(d.FIRST),'usageTotalUsd':'.10'}]}
        d.reconcile_coverage(r);self.assertEqual(r['test_cursors']['facebook'],d.stamp(d.INITIAL))
    def test_formal_actor_input_parity(self):
        tree=ast.parse(Path(__file__).with_name('live_pipeline.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='acquire')
        branch=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and ast.unparse(n.test)=="source == 'facebook'")
        for source in t.ACTORS:
            env={'source':source,'start':d.stamp(d.INITIAL),'end':d.stamp(d.FIRST)}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[branch],type_ignores=[])),'formal','exec'),env)
            self.assertEqual(env['body'],t.inputs(source,env['start'],env['end']));self.assertEqual(env['actor'],t.ACTORS[source])

from datetime import timedelta
if __name__=='__main__':unittest.main()
