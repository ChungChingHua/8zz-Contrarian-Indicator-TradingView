import os
import unittest
from unittest.mock import patch
import check_chatanywhere
import ai_provider as p
import social_pipeline as s
from test_openai import answer
from test_social_pipeline import post


class ProviderTests(unittest.TestCase):
    def setUp(self):
        for target in ('ai_provider.assert_online_enabled','social_pipeline.assert_online_enabled','run_social_update.assert_online_enabled','check_chatanywhere.assert_online_enabled'):
            guard=patch(target)
            guard.start()
            self.addCleanup(guard.stop)

    def test_official_key_never_substituted(self):
        with patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','OPENAI_API_KEY':'official'},clear=True):
            with self.assertRaises(RuntimeError):p.credentials()

    def test_provider_hosts_and_keys_are_separate(self):
        with patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','CHATANYWHERE_API_KEY':'third','OPENAI_API_KEY':'official'},clear=True):
            c,h=p.credentials()
            self.assertEqual(h['Authorization'],'Bearer third')
            self.assertEqual(c['base'],'https://api.chatanywhere.tech/v1')
            self.assertEqual(c['model'],'gpt-5-mini')

    def test_paid_candidate_and_unknown_provider_blocked(self):
        for env in ({'AI_PROVIDER':'chatanywhere','CHATANYWHERE_MODEL':'gpt-5-pro'},{'AI_PROVIDER':'unknown'}):
            with patch.dict(os.environ,env,clear=True):
                with self.assertRaises(ValueError):p.config()

    def test_full_responses_contract_and_reasoning_required(self):
        response=answer();response.update(model='gpt-5-mini',reasoning={'effort':'low'},text={'format':{'type':'json_schema','strict':True}})
        env={'AI_PROVIDER':'chatanywhere','CHATANYWHERE_API_KEY':'third','OPENAI_API_KEY':'official'}
        with patch.dict(os.environ,env,clear=True),patch.object(s,'MODEL','gpt-5-mini'),patch.object(s,'request_json',return_value=response) as api:
            a=s.classify(post())
            self.assertEqual(a['provider'],'chatanywhere')
            self.assertEqual(api.call_args.args[0],'https://api.chatanywhere.tech/v1/responses')
            self.assertEqual(api.call_args.args[2]['reasoning'],{'effort':'low'})
            del response['reasoning']
            with self.assertRaisesRegex(ValueError,'reasoning_effort_unconfirmed'):s.classify(post())

    def test_strict_schema_cannot_be_silently_removed(self):
        response=answer();response.update(model='gpt-5-mini',reasoning={'effort':'low'})
        with patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','CHATANYWHERE_API_KEY':'third'},clear=True),patch.object(s,'request_json',return_value=response):
            with self.assertRaisesRegex(ValueError,'strict_schema_unconfirmed'):s.classify(post())

    def test_model_preflight_lists_without_switching(self):
        import tempfile
        import check_chatanywhere as check
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'AI_PROVIDER':'chatanywhere','CHATANYWHERE_API_KEY':'third'},clear=True),patch.object(check,'ROOT',Path(d)),patch.object(check,'request_json',return_value={'data':[{'id':'gpt-5-nano'},{'id':'gpt-5-pro'}]}):
            with self.assertRaises(SystemExit):check.main()
            report=s.read(Path(d)/'data/social_chatanywhere_preflight.json',{})
            self.assertFalse(report['model_listed'])
            self.assertFalse(report['preflight_passed'])
            self.assertEqual(report['available_gpt5_models'],['gpt-5-nano','gpt-5-pro'])
            self.assertEqual(report['generation_requests'],0)

    def test_quota_exhaustion_stops_before_second_sample(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d,patch.object(s,'ROOT',Path(d)),patch.object(s,'generate',return_value=0),patch.object(s,'classify',side_effect=s.APIError(429)) as api,patch('sys.argv',['pipeline','--classify-limit','2']):
            a=post(id='a');b=post(id='b')
            a['analysis']={'status':'pending'};b['analysis']={'status':'pending'}
            s.write(Path(d)/'data/social_posts.json',{a['key']:a,b['key']:b});s.main()
            self.assertEqual(api.call_count,1)
            archive=s.read(Path(d)/'data/social_posts.json',{})
            self.assertEqual(archive[b['key']]['analysis']['status'],'pending')

    def test_authenticated_redirect_is_refused(self):
        with self.assertRaises(RuntimeError):s.NoAuthRedirect().redirect_request(None,None,302,'',{},'https://other.invalid')

if __name__=='__main__':unittest.main()
