import hashlib
import json
import unittest
from pathlib import Path
import build_quality_samples as b

class QualitySampleTests(unittest.TestCase):
    def test_exact_ten_current_snapshots_and_no_future_labels(self):
        archive=json.loads((b.ROOT/'data/social_posts.json').read_text())
        stored=json.loads((b.ROOT/'data/quality_samples.json').read_text())
        self.assertEqual(b.build(archive),stored)
        self.assertFalse(stored['approved']);self.assertEqual(stored['api_requests'],0)
        self.assertEqual(len(stored['samples']),10)
        self.assertEqual(len({p['key'] for p in stored['samples']}),10)
        self.assertEqual({p['source'] for p in stored['samples']},{'facebook','threads'})
        for p in stored['samples']:
            with self.subTest(key=p['key']):
                self.assertEqual(p['text'],archive[p['key']]['text'])
                self.assertEqual(p['text_sha256'],hashlib.sha256(p['text'].encode()).hexdigest())
                self.assertTrue(p['display_time'].endswith('+08:00'))
                self.assertNotIn('outcome',p);self.assertEqual(p['approval'],'pending_user_confirmation')
                for image in p['images']:
                    self.assertFalse(image['human_verified']);self.assertFalse(image['downloaded_this_round'])
                    self.assertNotIn('fbcdn.net',image['viewer_url']);self.assertNotIn('cdninstagram.com',image['viewer_url'])
        sentiments={x['proposed']['sentiment'] for x in stored['samples']}
        self.assertTrue({'panic','euphoria','neutral','unrelated','insufficient_information'}<=sentiments)
        self.assertTrue(any('股價' in m['platform_ocr_unverified'] for p in stored['samples'] for m in p['images']))
class CachedQualityTests(unittest.TestCase):
    def test_only_fixed_cached_posts_and_preserved_source_data(self):
        import copy
        import review_cached_quality as c
        archive=json.loads((b.ROOT/'data/social_posts.json').read_text())
        before=copy.deepcopy(archive)
        audit=json.loads((b.ROOT/c.AUDIT).read_text())
        result=c.review(audit,archive)
        self.assertEqual(archive,before)
        self.assertEqual(len(result['samples']),2)
        self.assertEqual(result['new_generation_requests'],0)
        for row in result['samples']:
            self.assertEqual(row['analysis']['status'],'review')
            self.assertEqual(row['analysis']['direction'],0)
            self.assertEqual(row['analysis']['target'],'')
            self.assertFalse(row['analysis']['auto_retry_eligible'])
        audit['samples'][0]['text']='changed'
        with self.assertRaisesRegex(ValueError,'cached_post_identity_mismatch'):c.review(audit,archive)

if __name__=='__main__':unittest.main()
