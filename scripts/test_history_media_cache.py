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
    def test_restored_cache_keeps_unstarted_shared_bytes_and_prunes_only_working_copy(self):
        import json
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);info=self.image(root)
            unused=b'\xff\xd8\xffunused\xff\xd9';sha=hashlib.sha256(unused).hexdigest()
            (root/(sha+'.bin')).write_bytes(unused)
            manifest={'posts':{'done':{},'pending':{}},'images':{'done':{'/done.jpg':info},'pending':{'/pending.jpg':info}}}
            (root/'manifest.json').write_text(json.dumps(manifest))
            with patch.object(c.hc,'archive',return_value={}),patch.object(c.hc,'exclusions',return_value=({'done'},{})),patch.object(c.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')):
                stats=c.prepare_restored_cache(root)
            self.assertEqual(stats['retained_posts'],1);self.assertEqual(stats['verified_image_files'],1)
            self.assertTrue((root/info['filename']).exists());self.assertFalse((root/(sha+'.bin')).exists())
            self.assertEqual(set(json.loads((root/'manifest.json').read_text())['posts']),{'pending'})
            self.assertEqual(c.checked_cache(info,root),('image/jpeg',JPEG))
    def test_metadata_auth_failure_preserves_status_without_start_or_retry(self):
        p=self.post();m=object.__new__(c.Media);m.state={'batches':[],'actor_starts_reserved':0};m.attempted=set();m.data={p['key']:p};m.manifest={'posts':{}};m.budget={'apify_runs':57};m.save=lambda:None
        class Client:
            calls=0
            def request(self,*args):
                self.calls+=1
                raise c.t.Failure('apify_http_error',401)
        m.client=Client()
        with patch.object(c.hc,'exclusions',return_value=(set(),{})):
            with self.assertRaises(c.MediaStop):m.refresh(p)
            with self.assertRaises(c.MediaStop):m.refresh(p)
        self.assertEqual(m.client.calls,1)
        self.assertEqual(m.state['last_error']['http_status'],401)
        self.assertEqual(m.state['last_error']['safe_code'],'apify_http_error')
        self.assertEqual(m.state['actor_starts_reserved'],0);self.assertEqual(m.budget['apify_runs'],57)
    def test_cache_tampering_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);i=self.image(root)
            self.assertEqual(c.checked_cache(i,root),('image/jpeg',JPEG))
            (root/i['filename']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'cache_hash_mismatch'):c.checked_cache(i,root)
            with self.assertRaisesRegex(ValueError,'invalid_cache_filename'):c.checked_cache({**i,'filename':'../outside.bin'},root)
    def test_prior_reservation_index_covers_legacy_and_unknown_without_new_start(self):
        from unittest.mock import Mock
        docs=Mock();docs.load.return_value={'actors':{'facebook':{'requested_keys':['facebook:1'],'status':'submission_unknown'}}}
        budget={'media_repair_reservations':{'old':{'ledger':'data/history_media_repairs/old.json'}}}
        prior=c.previous_media_batches(docs,budget)
        self.assertIn('facebook:1',prior);self.assertIsNone(prior['facebook:1']['batch'].get('id'))
        docs.load.return_value=None
        with self.assertRaisesRegex(ValueError,'missing_reserved_media_ledger'):c.previous_media_batches(docs,budget)
    def test_existing_dataset_is_read_once_and_prefetches_missing_bytes_without_actor_start(self):
        from unittest.mock import Mock
        p=self.post();q=self.post(2);m=object.__new__(c.Media)
        m.state={};m.data={p['key']:p,q['key']:q};m.manifest={'posts':{}};m.save=Mock()
        batch={'id':'paid-run','status':'SUCCEEDED','defaultDatasetId':'saved-data','keys':[p['key'],q['key']]}
        m.prior_by_key={p['key']:{'ledger':'data/history_media_repairs/old.json','batch':batch}}
        m.client=Mock();m.client.request.return_value=[p,q]
        m.cache_post=Mock()
        with patch.object(c.hc,'exclusions',return_value=(set(),{})),patch.object(c.h.s,'normalize',side_effect=lambda row,src:(row,None)):
            m.reuse_prior_dataset(p)
            with self.assertRaisesRegex(ValueError,'already_attempted'):m.reuse_prior_dataset(p)
        m.client.request.assert_called_once_with('/datasets/saved-data/items?format=json&limit=100')
        self.assertEqual(m.cache_post.call_count,2);self.assertEqual(m.state['prior_dataset_reuses'][0]['status'],'existing_dataset_read_complete')
    def test_unknown_prior_submission_never_reads_dataset_or_starts_actor(self):
        from unittest.mock import Mock
        p=self.post();m=object.__new__(c.Media);m.client=Mock()
        m.prior_by_key={p['key']:{'batch':{'status':'submission_unknown'},'ledger':'data/history_media_repairs/old.json'}}
        with self.assertRaisesRegex(ValueError,'unresolved_no_duplicate_start'):m.reuse_prior_dataset(p)
        m.client.request.assert_not_called()
    def test_new_batch_does_not_include_previously_reserved_urls(self):
        from unittest.mock import Mock
        p=self.post();q=self.post(2);m=object.__new__(c.Media)
        m.state={'batches':[],'actor_starts_reserved':0};m.attempted={q['key']};m.data={p['key']:p,q['key']:q};m.manifest={'posts':{}};m.budget={'apify_runs':60};m.save=Mock();m.budget_save=Mock()
        def request(path,payload=None):
            if payload is None:return {'data':{'pricingInfos':[{'startedAt':'2000-01-01T00:00:00Z','pricingModel':'PAY_PER_EVENT'}]}}
            self.assertEqual([u['url'] for u in payload['startUrls']],[p['url']])
            raise c.t.Failure('blocked',403)
        m.client=Mock();m.client.request.side_effect=request
        with patch.object(c.hc,'exclusions',return_value=(set(),{})):
            with self.assertRaises(c.MediaStop):m.refresh(p)
        self.assertEqual(m.client.request.call_count,2);self.assertEqual(m.state['batches'][0]['keys'],[p['key']])
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
