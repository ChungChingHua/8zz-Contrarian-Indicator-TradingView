"""Operational failure isolation only; no new real-post quality samples."""
import tempfile,unittest
from pathlib import Path
from test_original_history import Store,answer,plan_and_posts,prepare
from history_worker import Worker

class CompletionOperations(unittest.TestCase):
    def test_contradiction_is_review_then_next_post_and_no_resend(self):
        plan,posts=plan_and_posts();store=Store();calls=[]
        responses=iter([answer(direction=1,disposition='pending_confirmation'),answer()])
        with tempfile.TemporaryDirectory() as d:
            def provider(body):calls.append(body);return 200,{},next(responses)
            kwargs=dict(prepare=prepare,local=Path(d)/'ledger.json',generation_limit=25,continue_isolated_failures=True)
            Worker(store,provider,plan,**kwargs).run(posts)
            self.assertEqual([r['status'] for r in store.data['records']],['pending_confirmation','completed_signal'])
            self.assertIn('raw_response',store.data['records'][0]);self.assertNotIn('processed',store.data['records'][0])
            Worker(store,provider,plan,**kwargs).run(posts);self.assertEqual(len(calls),2)
    def test_isolated_media_then_continuation_and_persistent_failure_breaker(self):
        for fail_count in (1,3):
            with self.subTest(fail_count=fail_count),tempfile.TemporaryDirectory() as d:
                plan,posts=plan_and_posts(4);store=Store();calls=[]
                def media(p):
                    if int(p['post_id'])<fail_count:raise ValueError('unsupported_image_host')
                    return prepare(p)
                def provider(body):calls.append(body);return 200,{},answer()
                w=Worker(store,provider,plan,prepare=media,local=Path(d)/'ledger.json',generation_limit=25,continue_isolated_failures=True);w.run(posts)
                self.assertEqual(len(calls),3 if fail_count==1 else 0)
                self.assertEqual(store.data['stopped'],fail_count==3)
                if fail_count==3:self.assertEqual(store.data['records'][3]['status'],'not_started')
    def test_denied_or_quota_stops_first_request_without_retry(self):
        for status in (401,402,403,429,503):
            with self.subTest(status=status),tempfile.TemporaryDirectory() as d:
                plan,posts=plan_and_posts();store=Store();calls=[]
                def provider(body):calls.append(body);return status,{}, {'error':{'code':'insufficient_quota'}}
                kw=dict(prepare=prepare,local=Path(d)/'ledger.json',generation_limit=25,continue_isolated_failures=True)
                Worker(store,provider,plan,**kw).run(posts);Worker(store,provider,plan,**kw).run(posts)
                self.assertEqual(len(calls),1);self.assertTrue(store.data['stopped']);self.assertEqual(store.data['records'][1]['status'],'not_started')
if __name__=='__main__':unittest.main()
