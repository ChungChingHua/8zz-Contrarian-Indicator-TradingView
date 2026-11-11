import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import history_cached_completion as c

JPEG=b'\xff\xd8\xffcache-test\xff\xd9'
class Tests(unittest.TestCase):
    def post(self,n=1):return {'key':'facebook:'+str(n),'source':'facebook','post_id':str(n),'published_at':'2026-09-23T00:00:00+00:00','text':'public text','unix_ms':n,'url':'https://www.facebook.com/DieWithoutBang/posts/'+str(n),'attachments':[{'type':'photo','url':'https://test.fbcdn.net/'+str(n)+'.jpg'}]}
    def image(self,root):
        sha=hashlib.sha256(JPEG).hexdigest();filename=sha+'.bin';(root/filename).write_bytes(JPEG)
        return {'sha256':sha,'filename':filename,'bytes':len(JPEG),'mime':'image/jpeg'}
    def test_recovery_accounting_preserves_transition_and_counts_new_failures(self):
        current={'input_failure':4,'completed_signal':185};baseline={'input_failure':4,'completed_signal':138}
        counts,transitions=c.hc.session_status_delta(current,baseline,3)
        self.assertEqual(counts['input_failure'],3);self.assertEqual(transitions['input_failure'],0)
        self.assertEqual(counts['completed_signal'],47);self.assertEqual(current['input_failure'],4)
        with self.assertRaises(ValueError):c.hc.session_status_delta(current,baseline,5)
    def test_album_failure_shared_across_buckets_maps_index_once(self):
        import history_batch_02 as batch
        p=self.post();p['attachments']=[{'mediaset_token':'pcb.'+p['post_id'],'url':'https://www.facebook.com/album'}]+[{'type':'photo','url':'https://test.fbcdn.net/'+str(i)+'.jpg'} for i in range(4)]
        original=copy.deepcopy(p)
        failure={'attachment_index':3,'kind':'image'}
        scope={'unanalysed_media':[failure],'media_failures':[failure],'image_evidence':[{'attachment_index':0}]}
        with patch.object(batch.h,'prepare_media',return_value=([],scope)):
            _,out=batch.prepare(p)
        self.assertEqual(out['media_failures'][0]['attachment_index'],4)
        self.assertEqual(out['unanalysed_media'][0]['attachment_index'],4)
        self.assertEqual(out['image_evidence'][0]['attachment_index'],1)
        self.assertEqual(p,original)
    def test_cache_tampering_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);i=self.image(root)
            self.assertEqual(c.checked_cache(i,root),('image/jpeg',JPEG))
            (root/i['filename']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'cache_hash_mismatch'):c.checked_cache(i,root)
            with self.assertRaisesRegex(ValueError,'invalid_cache_filename'):c.checked_cache({**i,'filename':'../outside.bin'},root)
    def test_cached_image_uses_verified_bytes_without_network(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);info=self.image(root);p=self.post();m=object.__new__(c.Media)
            m.manifest={'posts':{p['key']:copy.deepcopy(p)},'images':{p['key']:{'/1.jpg':info}}}
            def prepare(post):
                self.assertEqual(c.h.s.download_image(post['attachments'][0]['url']),('image/jpeg',JPEG))
                return ['offline-test-part'],{'images_supplied':1}
            real_check=c.checked_cache
            with patch.object(c,'checked_cache',side_effect=lambda i:real_check(i,root)),patch.object(c,'original_prepare',side_effect=prepare),patch.object(c.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')):
                parts,scope=m.prepare(p)
            self.assertTrue(scope['cache_verified']);self.assertEqual(len(parts),1)
    def test_cached_post_identity_must_match(self):
        p=self.post();m=object.__new__(c.Media);q=copy.deepcopy(p);q['text']='changed'
        m.manifest={'posts':{p['key']:q},'images':{}}
        with self.assertRaisesRegex(ValueError,'cache_post_identity_mismatch'):m.prepare(p)
    def test_monthly_guard_prevents_any_provider_request(self):
        p=self.post();m=object.__new__(c.Media);m.state={'batches':[]};m.attempted=set();m.data={p['key']:p};m.manifest={'posts':{}};m.budget={'apify_runs':70};m.save=lambda:None
        class Client:
            def request(self,*args):raise AssertionError('no request allowed')
        m.client=Client()
        with patch.object(c.hc,'exclusions',return_value=(set(),{})):
            with self.assertRaises(c.MediaStop):m.refresh(p)
        self.assertEqual(m.state['blocked'],'monthly_70_run_guard')
    def test_actor_failure_is_not_retried_and_batch_is_bounded(self):
        m=object.__new__(c.Media);m.state={'batches':[],'actor_starts_reserved':0};m.attempted=set();m.data={p['key']:p for p in [self.post(n) for n in range(1,20)]};m.manifest={'posts':{}};m.budget={'apify_runs':50};m.save=lambda:None;m.budget_save=lambda:None
        class Client:
            posts=0;payload=None
            def request(self,path,payload=None):
                if payload is None:return {'data':{'pricingInfos':[{'startedAt':'2000-01-01T00:00:00Z','pricingModel':'PAY_PER_EVENT'}]}}
                self.posts+=1;self.payload=payload
                raise c.t.Failure('rejected',401)
        client=Client();m.client=client
        with patch.object(c.hc,'exclusions',return_value=(set(),{})):
            with self.assertRaises(c.MediaStop):m.refresh(m.data['facebook:1'])
            with self.assertRaises(c.MediaStop):m.refresh(m.data['facebook:1'])
        self.assertEqual(client.posts,1);self.assertEqual(len(client.payload['startUrls']),12)
        self.assertEqual(m.budget['apify_runs'],51)

if __name__=='__main__':unittest.main()
