import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import authorized_quality_test as t
import quality_protocol as q
from semantic_gate import assess


def response(post,**changes):
    a={'relevance':'investment','relevance_reason':'本人談投資虧損','emotion':'panic','direction':1,'strength':2,
      'emotion_reason':'本人投資痛苦，標的不明不影響情緒',
      'emotion_evidence':[{'source':'author_text','image_index':-1,'quote':post['text']}],
      'targets':[],'images':[{'image_index':i,'readable':True,'observation':'離線測試圖','visible_text':'','investment_information':False,'limitation':'fixture'} for i in range(len(post['attachments']))],
      'author_commentary':post['text'],'quoted_summary':'','limitations':'標的空白'}
    a.update(changes)
    return {'status':'completed','model':'gpt-5-mini','reasoning':{'effort':'minimal'},'text':{'format':{'type':'json_schema','strict':True}},'usage':{'input_tokens':20,'output_tokens':30,'total_tokens':50},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(a)}]}]}


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(t.PLAN.read_text())
        archive=t.s.read(t.s.ROOT/'data/social_posts.json',{})
        self.posts=[copy.deepcopy(archive[x['key']]) for x in self.plan['samples']]
    def image_parts(self,post):
        post['_image_evidence']=[{'sha256':'a'*64,'bytes':12,'mime':'image/jpeg'} for _ in post['attachments']]
        return [{'type':'input_image','image_url':'data:image/jpeg;base64,offline'} for _ in post['attachments']]
    def test_blind_inputs_context_and_frozen_digest(self):
        p=copy.deepcopy(self.posts[0]);p.update(proposed='SECRET_EXPECTED_LABEL',category='SECRET_CATEGORY',future_context='FUTURE_PRICE',context=['FUTURE_POST'])
        payload=q.make_payload(p,[]);body=json.dumps(payload)
        for forbidden in ('SECRET_EXPECTED_LABEL','SECRET_CATEGORY','FUTURE_PRICE','FUTURE_POST'):
            self.assertNotIn(forbidden,body)
        self.assertEqual(json.loads(payload['input'][0]['content'][0]['text'])['context'],[])
        self.assertEqual(self.plan['protocol_sha256'],q.digest())
        self.assertNotIn('proposed',json.dumps(self.plan))
    def test_ten_generations_dedicated_key_once_each(self):
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            def transport(url,headers,payload):
                i=len(calls);calls.append(payload)
                self.assertEqual(url,q.BASE+'/responses');self.assertEqual(headers['Authorization'],'Bearer fixture-key')
                return 200,{},response(self.posts[i])
            audit=t.Audit('fixture-key',self.plan,Path(d)/'report.json',transport)
            with patch.object(t.s,'image_parts',side_effect=self.image_parts):t.run(audit,self.posts)
            self.assertTrue(audit.report['completed']);self.assertEqual(len(calls),10)
            self.assertTrue(all(r['generation_attempts']==1 for r in audit.report['samples']))
            self.assertEqual(audit.report['http_counts']['model_queries'],0)
            with self.assertRaises(ValueError):audit.generate(calls[-1])
            with self.assertRaises(RuntimeError):t.s.assert_online_enabled()
    def test_quota_or_format_failure_stops_without_retry(self):
        for status,result in [(429,{'error':{'code':'insufficient_quota'}}),(200,{'status':'incomplete'})]:
            with self.subTest(status=status),tempfile.TemporaryDirectory() as d:
                calls=[]
                def transport(*args):calls.append(args);return status,{},result
                audit=t.Audit('fixture-key',self.plan,Path(d)/'report.json',transport)
                with patch.object(t.s,'image_parts',side_effect=self.image_parts):t.run(audit,self.posts)
                self.assertEqual(len(calls),1);self.assertTrue(audit.report['stopped'])
                self.assertEqual(audit.report['samples'][0]['status'],'retry')
                self.assertTrue(all(r['status']=='not_attempted' for r in audit.report['samples'][1:]))
    def test_image_failure_never_sends_text_only(self):
        with tempfile.TemporaryDirectory() as d:
            audit=t.Audit('fixture-key',self.plan,Path(d)/'report.json',lambda *args:self.fail('no generation without picture'))
            with patch.object(t.s,'image_parts',side_effect=ValueError('missing_image_url')):t.run(audit,self.posts)
            self.assertEqual(audit.report['http_counts']['generation'],0)
            self.assertEqual(audit.report['samples'][0]['status'],'input_review')
    def test_credential_reflection_not_saved(self):
        with tempfile.TemporaryDirectory() as d:
            result=response(self.posts[0],limitations='fixture-secret-key-should-not-leak')
            audit=t.Audit('fixture-secret-key-should-not-leak',self.plan,Path(d)/'report.json',lambda *args:(200,{},result))
            with patch.object(t.s,'image_parts',side_effect=self.image_parts):t.run(audit,self.posts)
            self.assertNotIn(audit.key,audit.path.read_text());self.assertTrue(audit.report['stopped'])
    def test_inventory_pain_without_named_instrument_retains_direction(self):
        p=self.posts[6]
        legacy={'status':'done','investment_related':True,'clear':True,'direction':1,'strength':3,'target':'','ticker':'','reason':'本人投資痛苦；標的不明','author_commentary':p['text'],'quoted_summary':'','images_reviewed':True,'image_evidence':[{'sha256':'a'*64}]}
        a=assess(p,legacy)
        self.assertEqual(a['direction'],1);self.assertEqual(a['strength'],3);self.assertEqual(a['target'],'')
        parsed=q.parse_response(response(p,targets=[]))
        self.assertEqual(parsed['direction'],1);self.assertEqual(q.inspect(p,parsed,[{'sha256':'a'*64}])['issues'],[])
    def test_image_candidate_traceable_but_not_human_verified(self):
        p=self.posts[6]
        a=q.parse_response(response(p,targets=[{'name':'台積電','ticker':'2330','relationship':'holding_only','evidence':[{'source':'image','image_index':0,'quote':'台積電 2330'}]}]))
        checked=q.inspect(p,a,[{'sha256':'a'*64}]);target=checked['target_candidates'][0]
        self.assertEqual(target['status'],'pending_human_confirmation');self.assertFalse(target['human_verified'])
        self.assertEqual(target['evidence'][0]['sha256'],'a'*64)
        self.assertFalse(checked['formal_signal_written'])
    def test_invalid_schema_tools_and_reasoning_not_ignored(self):
        result=response(self.posts[0]);result['reasoning']['effort']='low'
        with self.assertRaisesRegex(ValueError,'reasoning_effort_unconfirmed'):q.parse_response(result)
        result=response(self.posts[0]);result['output'].append({'type':'function_call','name':'read_key'})
        with self.assertRaisesRegex(ValueError,'tool_output_rejected'):q.parse_response(result)
        result=response(self.posts[0]);data=json.loads(result['output'][0]['content'][0]['text']);data['direction']=True
        result['output'][0]['content'][0]['text']=json.dumps(data)
        with self.assertRaises(ValueError):q.parse_response(result)

if __name__=='__main__':unittest.main()
