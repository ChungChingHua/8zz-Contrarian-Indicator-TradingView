"""Offline safety/accounting integration: no Apify, AI or Telegram traffic. MPL-2.0."""
import copy
import io
import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import Mock,patch
import history_worker as h
import live_pipeline as l
import telegram_notify as t
import trading_calendar as c
from build_audited_dashboard import simulate,events
from test_original_history import answer,prepare,plan_and_posts,Store
NOW=datetime(2026,11,10,1,tzinfo=timezone.utc)

class Docs:
    token='mock-github-token'
    def __init__(self,data=None):self.data=copy.deepcopy(data or {});self.saves=[]
    def load(self,path,default=None):return copy.deepcopy(self.data.get(path,default))
    def save(self,path,value):self.data[path]=copy.deepcopy(value);self.saves.append((path,copy.deepcopy(value)))
    def document(self,path):
        owner=self
        class Doc:
            def load(self):return owner.load(path)
            def save(self,value):owner.save(path,value)
        return Doc()

def event():
    return {'event_key':'fixture','id':1,'direction':1,'strength':2,'is_flip':True,'time':NOW.isoformat(),
        'completed_at':NOW.isoformat(),'platform':'Facebook','target':'0050','summary':'【模擬】摘要','urls':[],
        'historical':False,'baseline':False,'unix_ms':int(NOW.timestamp()*1000)}

def calendar():
    d=json.loads(c.PATH.read_text());d['fetched_at']=(NOW-timedelta(hours=1)).isoformat();d['expires_at']=(NOW+timedelta(hours=23)).isoformat();return d

class CalendarTests(unittest.TestCase):
    def test_exact_twenty_slots_and_endpoints(self):
        d=calendar();d.update(fetched_at='2026-11-09T16:00:00+00:00',expires_at='2026-11-10T16:00:00+00:00');slots=[]
        for n in range(24*60):
            now=datetime(2026,11,10,tzinfo=c.TAIPEI)+timedelta(minutes=n)
            slot=c.due_slot(now,d)
            if slot:slots.append(slot)
        self.assertEqual(len(set(slots)),20)
        self.assertEqual(c.due_slot(datetime(2026,11,10,8,45,tzinfo=c.TAIPEI),d),'2026-11-10/00')
        self.assertEqual(c.due_slot(datetime(2026,11,10,13,30,tzinfo=c.TAIPEI),d),'2026-11-10/19')
        self.assertIsNone(c.due_slot(datetime(2026,11,10,13,31,tzinfo=c.TAIPEI),d))
    def test_official_weekday_holiday_and_stale(self):
        d=calendar();now=datetime(2026,10,9,9,tzinfo=c.TAIPEI)
        d.update(fetched_at=(now-timedelta(hours=1)).isoformat(),expires_at=(now+timedelta(hours=23)).isoformat())
        self.assertFalse(c.trading_day(d,now))
        with self.assertRaisesRegex(ValueError,'expired'):c.trading_day(d,now+timedelta(days=1))
        with self.assertRaisesRegex(ValueError,'missing'):c.trading_day({},now)
    def test_explicit_emergency_closure(self):
        d=calendar();d['closure_overrides']['2026-11-10']='TWSE 臨時休市公告'
        self.assertFalse(c.trading_day(d,NOW))

class TelegramTests(unittest.TestCase):
    def test_multiple_private_candidates_no_guess_or_message_leak(self):
        client=Mock();client.call.side_effect=[{'url':''},[
            {'message':{'chat':{'type':'private','id':2},'text':'do not print'}},
            {'message':{'chat':{'type':'private','id':1}}},
            {'message':{'chat':{'type':'group','id':-3}}}]]
        r=t.discover(client);self.assertEqual(r['candidate_chat_ids'],[1,2]);self.assertNotIn('do not print',json.dumps(r))
        self.assertFalse(client.send.called)
    def test_no_messages_and_webhook_never_deleted(self):
        client=Mock();client.call.side_effect=[{'url':''},[]]
        self.assertIn('重新傳送文字',t.discover(client)['status'])
        client=Mock();client.call.return_value={'url':'https://private.example/webhook'}
        with self.assertRaisesRegex(t.TelegramError,'webhook'):t.discover(client)
        self.assertEqual(client.call.call_count,1)
    def test_raw_transport_exception_and_conflict_redacted(self):
        client=t.Telegram('123:TEST_SECRET')
        for error in (OSError('https://api.telegram.org/bot123:TEST_SECRET/getUpdates'),urllib.error.HTTPError('secret-url',409,'secret-token',{},None)):
            with patch('urllib.request.OpenerDirector.open',side_effect=error):
                with self.assertRaises(t.TelegramError) as cm:client.call('getUpdates')
            self.assertNotIn('TEST_SECRET',str(cm.exception));self.assertNotIn('secret-url',str(cm.exception))
    def test_private_target_only(self):
        client=t.Telegram('mock');client.call=Mock(return_value={'type':'group','id':1})
        with self.assertRaises(t.TelegramError):client.private('1')
        with self.assertRaises(t.TelegramError):client.private('-1')
    def test_success_persist_before_post_and_duplicate_suppressed(self):
        docs=Docs();store=docs.document('outbox');client=Mock()
        def send(*args):
            self.assertEqual(docs.data['outbox']['records']['fixture']['status'],'unknown');return 9
        client.send.side_effect=send
        t.deliver([event()],store,client,'123');t.deliver([event()],store,client,'123')
        self.assertEqual(client.send.call_count,1)
        self.assertEqual(docs.data['outbox']['records']['fixture']['status'],'sent')
        self.assertNotIn('chat_id',docs.data['outbox']['records']['fixture'])
    def test_missing_secrets_preserves_events(self):
        docs=Docs();e=event();before=copy.deepcopy(e)
        state=t.deliver([e],docs.document('outbox'),None,'')
        self.assertIn('未設定',state['configuration']);self.assertEqual(e,before)
    def test_failed_and_unknown_never_auto_resend(self):
        for uncertain,status in ((False,'failed'),(True,'unknown')):
            docs=Docs();client=Mock();client.send.side_effect=t.TelegramError('模擬失敗',uncertain)
            t.deliver([event()],docs.document('outbox'),client,'123')
            t.deliver([event()],docs.document('outbox'),client,'123')
            self.assertEqual(client.send.call_count,1);self.assertEqual(docs.data['outbox']['records']['fixture']['status'],status)
    def test_crash_after_send_remote_ack_failure_retains_unknown(self):
        class FailingDocs(Docs):
            def save(self,path,value):
                if value.get('records',{}).get('fixture',{}).get('status')=='sent':raise RuntimeError('checkpoint unavailable')
                super().save(path,value)
        docs=FailingDocs();client=Mock();client.send.return_value=9
        with self.assertRaises(RuntimeError):t.deliver([event()],docs.document('outbox'),client,'123')
        t.deliver([event()],docs.document('outbox'),client,'123')
        self.assertEqual(client.send.call_count,1)
    def test_notification_retry_isolated_from_ai_unknown_preserved(self):
        state=l.initial_state();docs=Docs({l.CONTROL:state,l.OUTBOX:{'records':{'a':{'status':'failed'},'b':{'status':'unknown'},'c':{'status':'sent'}}}})
        with patch.object(h.Provider,'__call__',side_effect=AssertionError('AI forbidden')):
            l.run('retry-notifications',docs,now=NOW)
        self.assertEqual([r['status'] for r in docs.data[l.OUTBOX]['records'].values()],['pending','unknown','sent'])

class AcquisitionTests(unittest.TestCase):
    def row(self,identity='new'):
        return {'postId':identity,'user':{'id':'100044238139017'},'time':'2026-11-10T00:55:00Z','url':'https://www.facebook.com/posts/'+identity,'text':'【模擬】貼文'}
    def setup_docs(self):
        state=l.initial_state();state['sources']['facebook']['completed_until']='2026-11-06T05:30:00+00:00'
        return state,Docs({l.CONTROL:state})
    def client(self,rows,status='SUCCEEDED',cost=.02):
        client=Mock();client.request.side_effect=[{'data':{'id':'run-fixture'}},{'data':{'status':status,'defaultDatasetId':'dataset','usageTotalUsd':cost}},rows]
        return client
    def test_overnight_weekend_incremental_and_dedupe(self):
        state,docs=self.setup_docs();client=self.client([self.row()]);raw={}
        with patch.object(l.hc,'archive',return_value={}):l.acquire('facebook',state,docs,client,NOW,raw)
        body=client.request.call_args_list[0].args[1]
        self.assertEqual(body['onlyPostsNewerThan'],'2026-11-06T03:30:00Z')
        self.assertEqual(state['sources']['facebook']['completed_until'],NOW.isoformat())
        self.assertIn('facebook:new',docs.data[l.POSTS]);self.assertIn('fetched_at',docs.data[l.POSTS]['facebook:new'])
        self.assertEqual(state['sources']['threads']['completed_until'],l.initial_state()['sources']['threads']['completed_until'])
        client=self.client([self.row()])
        with patch.object(l.hc,'archive',return_value={}):l.acquire('facebook',state,docs,client,NOW+timedelta(minutes=15),{})
        self.assertEqual(len(docs.data[l.POSTS]),1)
    def test_failed_truncated_or_invalid_rows_never_advance(self):
        for status,cost,rows in [('FAILED',.02,[]),('SUCCEEDED',.10,[]),('SUCCEEDED',.02,[{'postId':'bad','user':{'id':'100044238139017'}}])]:
            state,docs=self.setup_docs();before=state['sources']['facebook']['completed_until']
            with patch.object(l.hc,'archive',return_value={}):l.acquire('facebook',state,docs,self.client(rows,status,cost),NOW,{})
            self.assertEqual(state['sources']['facebook']['completed_until'],before)
            self.assertTrue(state['sources']['facebook'].get('blocked'))
    def test_saturated_page_retains_cutoff_and_window(self):
        state,docs=self.setup_docs();before=state['sources']['facebook']['completed_until']
        with patch.object(l.hc,'archive',return_value={}):l.acquire('facebook',state,docs,self.client([self.row(str(i)) for i in range(50)]),NOW,{})
        self.assertEqual(state['sources']['facebook']['completed_until'],before)
        self.assertIn('page_before',state['sources']['facebook']['window'])
    def test_unknown_post_submission_not_repeated(self):
        state,docs=self.setup_docs();client=Mock();client.request.side_effect=OSError('mock transport')
        with self.assertRaises(OSError):l.acquire('facebook',state,docs,client,NOW,{})
        client.reset_mock();l.acquire('facebook',state,docs,client,NOW,{})
        client.request.assert_not_called()
        self.assertEqual(state['sources']['facebook']['blocked'],'apify_submission_unknown')
    def test_existing_seventy_run_budget_unchanged(self):
        state,docs=self.setup_docs();docs.data['data/usage.json']={'2026-11':{'apify_runs':70,'ai_attempts':0}}
        client=Mock();l.acquire('facebook',state,docs,client,NOW,{})
        client.request.assert_not_called();self.assertEqual(state['sources']['facebook']['last_error'],'existing_monthly_apify_budget_exhausted')
    def test_duplicate_schedule_round_no_processing(self):
        state=l.initial_state();state['rounds'][c.due_slot(NOW,calendar())]={'status':'reserved'}
        docs=Docs({l.CONTROL:state});client=Mock()
        with patch.object(l,'classify',side_effect=AssertionError('duplicate AI')),patch.object(l,'refresh_outputs'):
            l.run('run',docs,apify=client,now=NOW,calendar=calendar())
        client.request.assert_not_called()
    def test_default_disabled_before_secret_or_network_access(self):
        with patch('sys.argv',['live_pipeline.py','run']),patch.object(l.os,'getenv',side_effect=AssertionError('must not read runtime credentials')),patch.object(l,'refresh',side_effect=AssertionError('must not access network')):
            with self.assertRaisesRegex(SystemExit,'未啟用'):l.main()

    def test_no_pending_live_no_ai_or_media(self):
        docs=Docs({l.POSTS:{}});state=l.initial_state();state['ai_stop']=None
        with patch.object(h.Provider,'__call__',side_effect=AssertionError('no new AI')),patch.object(l,'prepare',side_effect=AssertionError('no media')):
            l.classify(state,docs,'mock-key',{},NOW)
    def test_cas_store_does_not_reload_before_save(self):
        store=Mock();store.load.return_value={'version':1}
        with patch.object(h,'GitHubStore',return_value=store),patch.object(h.s,'write'):
            docs=l.Documents('mock');docs.load('fixture');docs.save('fixture',{'version':2});docs.save('fixture',{'version':3})
        self.assertEqual(store.load.call_count,1)

class AvailabilityTests(unittest.TestCase):
    def test_no_completion_time_no_invented_actual_trades(self):
        e=event();r=simulate([e],[{'time':e['unix_ms']+1000,'price':100}],'B',basis='available')
        self.assertEqual(r['stats']['missing_completion'],1);self.assertEqual(r['trades'],[])
    def test_completion_after_close_cannot_backfill(self):
        e=event();e['available_ms']=e['unix_ms']+2000
        bars=[{'time':e['unix_ms']+1000,'price':100},{'time':e['unix_ms']+3000,'price':101}]
        self.assertEqual(simulate([e],bars,'B',basis='available')['trades'][0]['entry']['time'],bars[1]['time'])
    def test_saved_events_baseline_and_original_policy_unchanged(self):
        ev=events();baseline=[e for e in ev if e['baseline']];self.assertEqual(len(baseline),257)
        self.assertTrue(all(e['completed_at'] is None for e in baseline))
        self.assertEqual(h.policy.fingerprint(),l.RULE)
    def test_worker_saves_true_completion_timestamp_only_for_new_results(self):
        plan,posts=plan_and_posts(1)
        with tempfile.TemporaryDirectory() as d:
            store=Store();w=h.Worker(store,lambda p:(200,{},answer()),plan,prepare=prepare,local=Path(d)/'ledger.json')
            w.run(posts)
            self.assertIn('completed_at',store.data['records'][0])
            self.assertGreaterEqual(store.data['records'][0]['completed_at'],store.data['records'][0]['dispatch_reserved_at'])

if __name__=='__main__':unittest.main()
