import base64,copy,json,unittest
import verify_manual_dispatch as v

class DedicatedManualDispatchTests(unittest.TestCase):
    def ledger(self):return {'batch_id':v.BATCH_ID,'finished':True,'reserved_generation_attempts':5,'records':[{'attempts':1,'status':'completed_no_signal'} for _ in range(5)]}
    def test_only_dedicated_id_and_explicit_pr_ref_after_consumed_check(self):
        calls=[]
        def request(method,url,body=None):
            calls.append((method,url,body))
            if '/contents/' in url:return {'content':base64.b64encode(json.dumps(self.ledger()).encode()).decode()}
            if method=='GET':return {'path':'.github/workflows/history-batch-manual.yml','state':'active'}
            return 204
        result=v.run_check(request)
        self.assertEqual(result['dispatch_http_status'],204)
        self.assertEqual(calls[-1][2],{'ref':'codex/social-pipeline-20261106'})
        self.assertIn('/410173704/dispatches',calls[-1][1]);self.assertNotIn('fetch-fb-events',str(calls))
        self.assertEqual(result['provider_requests_in_verifier'],0)
    def test_not_consumed_or_wrong_identity_never_dispatch(self):
        for which in ('ledger','workflow'):
            calls=[]
            def request(method,url,body=None):
                calls.append(method)
                if '/contents/' in url:
                    ledger=self.ledger()
                    if which=='ledger':ledger['reserved_generation_attempts']=4
                    return {'content':base64.b64encode(json.dumps(ledger).encode()).decode()}
                return {'path':'.github/workflows/not-the-history-worker.yml','state':'active'}
            with self.assertRaises(ValueError):v.run_check(request)
            self.assertNotIn('POST',calls)
