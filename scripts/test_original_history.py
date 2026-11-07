import copy,json,tempfile,unittest
from pathlib import Path
import original_author as p
import history_worker as h
from original_candidate import build
from history_plan import select
from test_social_pipeline import post

class Crash(BaseException):pass
class Store:
    def __init__(self):self.data=None;self.saves=0;self.fail_on=None
    def load(self):return copy.deepcopy(self.data)
    def save(self,state):
        self.saves+=1
        if self.saves==self.fail_on:raise RuntimeError('simulated checkpoint outage')
        self.data=copy.deepcopy(state)

def answer(direction=1,strength=2,ticker='',disposition=None):
    a={'direction':direction,'strength':strength,'action':'情緒','ticker':ticker,'reasoning':'依完整本人情緒判斷','disposition':disposition or ('signal' if direction else 'no_signal'),'images':[],'target_notes':'標的可留空'}
    return {'status':'completed','model':'gpt-5-mini','reasoning':{'effort':'minimal'},'text':{'format':{'type':'json_schema','strict':True}},'usage':{'input_tokens':11,'output_tokens':7,'total_tokens':18},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(a)}]}]}

def plan_and_posts(n=2):
    rows=[];posts=[]
    for i in range(n):
        x=post(text='一般文字，沒有指定關鍵字',id=str(i));posts.append(x)
        rows.append({k:x[k] for k in ('key','content_hash','post_id','source','url','published_at','display_time','unix_ms','text')})
        rows[-1].update(number=i+1,members=[{'key':x['key'],'url':x['url']}])
    return {'posts':rows},posts

def prepare(post):return [],{'images_supplied':0,'image_evidence':[],'analysis_scope':'text_only'}

class OriginalPolicyTests(unittest.TestCase):
    def test_original_exclusions_examples_strength_retained(self):
        self.assertEqual(len(p.C['_EXAMPLES']),20)
        for term in ('情緒 > 動作','還沒停損','粉絲/追蹤者','完全沒想法','委託成功','ticker'):
            self.assertIn(term,p.C['_SYSTEM'])
        self.assertEqual(p.POLICY['source_commit'],'7b626f2007128eea9cb8111ed4c18185bbfc650a')
    def test_no_added_keyword_target_or_human_review_gate(self):
        x=post(text='買進了，但我真的好難受');a=p.parse(answer(),0);r=p.process(x,a)
        self.assertEqual(r['direction'],1);self.assertEqual(r['ticker'],'');self.assertTrue(p.event_eligible(r))
        x['text']='買入成功 委託成功';r=p.process(x,a)
        self.assertEqual(r['strength'],3)
        a=p.parse(answer(direction=-1),0);self.assertEqual(p.process(x,a)['strength'],3)
        a=p.parse(answer(direction=0),0);self.assertEqual(p.process(x,a)['strength'],2)
    def test_pending_no_signal_no_arrow_and_all_history_preserved(self):
        plan,posts=plan_and_posts(2);state={'records':[]}
        for row,d in zip(plan['posts'],(1,0)):
            row.update(status='completed_signal' if d else 'pending_confirmation',processed=p.process(posts[0],p.parse(answer(direction=d,disposition='pending_confirmation' if d==0 else 'signal'),0)))
            state['records'].append(row)
        pine,stats=build(state)
        self.assertEqual(stats['added_events'],1);self.assertGreaterEqual(stats['historical_events'],150)
        self.assertIn('Mozilla Public License',pine);self.assertIn('© hansai-art',pine)
        self.assertFalse(stats['tradingview_compiled'])
    def test_format_and_tools_still_fail_technically(self):
        r=answer();r['output'].append({'type':'function_call','name':'read_secret'})
        with self.assertRaises(ValueError):p.parse(r,0)
        with self.assertRaises(ValueError):p.parse(answer(direction=1,disposition='pending_confirmation'),0)
    def test_selection_exact_dedup_and_stance_context_not_fuzzy(self):
        a=post('facebook',text='同一個完整投資貼文');b=post('threads',text=a['text'])
        a['analysis']={'status':'pending'};b['analysis']={'status':'pending'}
        groups,stats=select({a['key']:a,b['key']:b},set());self.assertEqual(len(groups),1)
        b['text']+='但是轉空';groups,_=select({a['key']:a,b['key']:b},set());self.assertEqual(len(groups),2)

class DurableTests(unittest.TestCase):
    def test_complete_duplicate_start_no_repeat(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        with tempfile.TemporaryDirectory() as d:
            provider=lambda payload:(calls.append(payload) or (200,{},answer()))
            worker=h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json');worker.run(posts)
            self.assertEqual(len(calls),2);self.assertTrue(store.data['finished'])
            again=h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json');again.run(posts)
            self.assertEqual(len(calls),2)
    def test_quota_and_invalid_schema_stop_and_preserve_raw(self):
        for status,result in [(429,{'error':{'code':'insufficient_quota'}}),(200,{'status':'incomplete'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as d:
                plan,posts=plan_and_posts();store=Store();calls=[]
                worker=h.Worker(store,lambda body:(calls.append(body) or (status,{},result)),plan,prepare,local=Path(d)/'ledger.json');worker.run(posts)
                self.assertEqual(len(calls),1);self.assertEqual(store.data['records'][0]['status'],'technical_failure')
                self.assertIn('raw_response',store.data['records'][0]);self.assertEqual(store.data['records'][1]['status'],'not_started')
                h.Worker(store,worker.provider,plan,prepare,local=Path(d)/'ledger.json').run(posts);self.assertEqual(len(calls),1)
    def test_crash_after_send_unknown_never_resends(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        with tempfile.TemporaryDirectory() as d:
            def crash():raise Crash()
            provider=lambda body:(calls.append(body) or (200,{},answer()))
            worker=h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json',after_response=crash)
            with self.assertRaises(Crash):worker.run(posts)
            self.assertEqual(store.data['records'][0]['status'],'unknown')
            h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json').run(posts)
            self.assertEqual(len(calls),1);self.assertTrue(store.data['stopped'])
    def test_remote_reservation_required_and_result_commit_failure_safe(self):
        for failed_save,expected_calls in ((2,0),(3,1)):
            with self.subTest(failed_save=failed_save),tempfile.TemporaryDirectory() as d:
                plan,posts=plan_and_posts();store=Store();calls=[]
                provider=lambda body:(calls.append(body) or (200,{},answer()))
                worker=h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json');store.fail_on=failed_save
                with self.assertRaises(RuntimeError):worker.run(posts)
                self.assertEqual(len(calls),expected_calls)
                if failed_save==3:
                    self.assertEqual(store.data['records'][0]['status'],'unknown')
                    self.assertEqual(json.loads((Path(d)/'ledger.json').read_text())['records'][0]['status'],'unknown')
                    self.assertTrue((Path(d)/'ledger.uncommitted.json').exists())
    def test_resume_after_saved_result_only_unstarted(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        with tempfile.TemporaryDirectory() as d:
            def stop_second(post):
                if post['post_id']=='1':raise Crash()
                return prepare(post)
            provider=lambda body:(calls.append(body) or (200,{},answer()))
            w=h.Worker(store,provider,plan,stop_second,local=Path(d)/'ledger.json')
            with self.assertRaises(Crash):w.run(posts)
            self.assertEqual(len(calls),1)
            h.Worker(store,provider,plan,prepare,local=Path(d)/'ledger.json').run(posts)
            self.assertEqual(len(calls),2);self.assertTrue(store.data['finished'])
    def test_key_reflection_not_in_checkpoint(self):
        plan,posts=plan_and_posts();store=Store()
        with tempfile.TemporaryDirectory() as d:
            response=answer();response['model']='ghs-fixture-must-never-publish'
            worker=h.Worker(store,lambda body:(200,{},response),plan,prepare,secrets=('ghs-fixture-must-never-publish',),local=Path(d)/'ledger.json');worker.run(posts)
            self.assertNotIn('ghs-fixture-must-never-publish',json.dumps(store.data))
            self.assertEqual(store.data['records'][0]['status'],'technical_failure')
    def test_stale_cas_worker_cannot_dispatch_after_another_worker(self):
        class Remote:
            data=None
            version=0
        class Client:
            def __init__(self):self.version=None
            def load(self):self.version=Remote.version;return copy.deepcopy(Remote.data)
            def save(self,state):
                if self.version!=Remote.version:raise RuntimeError('CAS conflict')
                Remote.data=copy.deepcopy(state);Remote.version+=1;self.version=Remote.version
        plan,posts=plan_and_posts();calls=[]
        with tempfile.TemporaryDirectory() as d:
            provider=lambda body:(calls.append(body) or (200,{},answer()))
            first=h.Worker(Client(),provider,plan,prepare,local=Path(d)/'first.json')
            second=h.Worker(Client(),provider,plan,prepare,local=Path(d)/'second.json')
            first.run(posts)
            with self.assertRaisesRegex(RuntimeError,'CAS conflict'):second.run(posts)
            self.assertEqual(len(calls),2)
            self.assertTrue(Remote.data['finished'])

    def test_returned_zero_quota_stops_after_saved_success(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        with tempfile.TemporaryDirectory() as d:
            w=h.Worker(store,lambda body:(calls.append(body) or (200,{'x-free-points-remaining':'0'},answer())),plan,prepare,local=Path(d)/'ledger.json');w.run(posts)
            self.assertEqual(len(calls),1);self.assertEqual(store.data['records'][0]['status'],'completed_signal');self.assertTrue(store.data['stopped'])

if __name__=='__main__':unittest.main()

class MediaScopeRecoveryTests(unittest.TestCase):
    def test_network_unreachable_is_explicit_not_fake_image_read(self):
        from unittest.mock import patch
        x=post();x['attachments']=[{'type':'image'}]
        with patch.object(h.s,'image_parts',side_effect=OSError(101,'fixture network unavailable')):
            parts,scope=h.prepare_media(x)
        self.assertEqual(parts,[]);self.assertEqual(scope['images_supplied'],0)
        self.assertEqual(scope['unanalysed_media'][0]['status'],'圖片未分析')
        self.assertEqual(scope['analysis_scope'],'text_only_images_unavailable')
    def test_tls_or_unsafe_media_failure_is_not_silently_ignored(self):
        from unittest.mock import patch
        x=post();x['attachments']=[{'type':'image'}]
        for exc in (OSError(1,'TLS fixture'),ValueError('non_public_media_address')):
            with patch.object(h.s,'image_parts',side_effect=exc),self.assertRaises(type(exc)):h.prepare_media(x)
    def test_only_zero_generation_failure_can_be_resumed_once(self):
        plan,posts=plan_and_posts();store=Store()
        with tempfile.TemporaryDirectory() as d:
            def fail(post):raise OSError(101,'fixture')
            worker=h.Worker(store,lambda body:(200,{},answer()),plan,fail,local=Path(d)/'ledger.json');worker.run(posts)
            self.assertEqual(worker.state['reserved_generation_attempts'],0)
            worker.resume_unsent_media_failure()
            self.assertTrue(store.data['unsent_media_recovery_used'])
            self.assertEqual(store.data['records'][0]['input_failure_history'][0]['attempts'],0)
            with self.assertRaises(ValueError):worker.resume_unsent_media_failure()
            worker.prepare=prepare;worker.run(posts)
            self.assertEqual(store.data['reserved_generation_attempts'],2)
    def test_no_resume_after_provider_or_unknown_attempt(self):
        plan,posts=plan_and_posts();store=Store()
        with tempfile.TemporaryDirectory() as d:
            worker=h.Worker(store,lambda body:(429,{}, {'error':{'code':'insufficient_quota'}}),plan,prepare,local=Path(d)/'ledger.json');worker.run(posts)
            with self.assertRaises(ValueError):worker.resume_unsent_media_failure()

class UnavailableNoteValidationTests(unittest.TestCase):
    def response_with_note(self,readable=False,visible=''):
        response=answer(direction=-1)
        a=json.loads(response['output'][0]['content'][0]['text'])
        a['images']=[{'image_index':0,'visible_text':visible,'observation':'圖片未提供／未分析','readable':readable}]
        response['output'][0]['content'][0]['text']=json.dumps(a)
        return response
    def test_honest_unavailable_note_is_not_an_emotion_veto(self):
        response=self.response_with_note();before=copy.deepcopy(response)
        a=p.parse(response,0,[{'attachment_index':0,'kind':'image'}])
        self.assertEqual(a['direction'],-1);self.assertEqual(a['images'],[])
        self.assertEqual(len(a['unanalysed_image_notes']),1);self.assertEqual(response,before)
        for response in (self.response_with_note(True),self.response_with_note(False,'假裝看過字')):
            with self.assertRaises(ValueError):p.parse(response,0,[{'attachment_index':0,'kind':'image'}])
    def test_reconcile_reuses_raw_and_only_continues_unstarted(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        with tempfile.TemporaryDirectory() as d:
            w=h.Worker(store,lambda body:(calls.append(body) or (200,{},self.response_with_note())),plan,prepare,local=Path(d)/'ledger.json')
            w.run(posts);self.assertEqual(len(calls),1)
            raw=copy.deepcopy(store.data['records'][0]['raw_response'])
            # The original request explicitly declared unavailable image 0; no real image was attached.
            w.state['records'][0]['media_scope']['unanalysed_media']=[{'attachment_index':0,'kind':'image'}]
            w.reconcile_saved_unanalysed_image_note()
            self.assertEqual(store.data['records'][0]['raw_response'],raw)
            self.assertEqual(store.data['records'][0]['status'],'completed_signal')
            w.provider=lambda body:(calls.append(body) or (200,{},answer()))
            w.run(posts);self.assertEqual(len(calls),2)
            self.assertEqual(store.data['reserved_generation_attempts'],2)
            with self.assertRaises(ValueError):w.reconcile_saved_unanalysed_image_note()


class StaticTickerReferenceTests(unittest.TestCase):
    def test_static_venue_correction_never_changes_emotion_or_claims_order_proof(self):
        x=post(text='台塑化 so weak')
        a=p.parse(answer(direction=1,strength=3,ticker='6505.TWO'),0)
        r=p.process(x,a)
        self.assertEqual((r['direction'],r['strength']),(1,3))
        self.assertEqual(r['ticker'],'6505.TW');self.assertEqual(a['ticker'],'6505.TWO')
        self.assertEqual(r['original_ai_ticker'],'6505.TWO')
        self.assertFalse(r['order_proof_rule_matched']);self.assertTrue(p.event_eligible(r))
