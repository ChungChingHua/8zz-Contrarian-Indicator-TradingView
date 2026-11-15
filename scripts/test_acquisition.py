import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
import fetch_social as f
import social_pipeline as s


def row(id):
    return {'postId':id,'user':{'id':'100044238139017'},'text':'今天投資很恐慌',
            'time':f'2026-11-06T0{id}:00:00Z','url':'https://www.facebook.com/DieWithoutBang/posts/'+id}


class AcquisitionTests(unittest.TestCase):
    def test_saturated_window_keeps_cursor_and_saves_posts(self):
        with TemporaryDirectory() as d,patch.object(f,'ROOT',Path(d)),patch.dict('os.environ',{'APIFY_TOKEN':'dummy'}):
            result=[{'data':{'id':'run'}},{'data':{'id':'run','status':'SUCCEEDED','defaultDatasetId':'dataset'}},[row('1'),row('2')]]
            with patch.object(f,'request_json',side_effect=result) as request:
                f.fetch('facebook',2)
            state=s.read(Path(d)/'data/acquisition.json',{})['facebook']
            self.assertNotIn('completed_until',state)
            self.assertTrue(state['saturated']);self.assertIn('page_before',state)
            self.assertEqual(len(s.read(Path(d)/'data/social_posts.json',{})),2)
            self.assertEqual(request.call_args_list[0].kwargs['retries'],1)
            body=request.call_args_list[0].args[2]
            self.assertTrue(body['onlyPostsNewerThan'].endswith('Z'))
            self.assertNotIn('+00:00',body['onlyPostsOlderThan'])

    def test_uncertain_post_is_not_blindly_retried(self):
        with TemporaryDirectory() as d,patch.object(f,'ROOT',Path(d)),patch.dict('os.environ',{'APIFY_TOKEN':'dummy'}):
            with patch.object(f,'request_json',side_effect=RuntimeError('transport')):
                with self.assertRaises(RuntimeError):f.fetch('facebook',2)
            with patch.object(f,'request_json') as request:
                with self.assertRaises(RuntimeError):f.fetch('facebook',2)
                request.assert_not_called()

    def test_saved_run_is_resumed_without_new_paid_post(self):
        with TemporaryDirectory() as d,patch.object(f,'ROOT',Path(d)),patch.dict('os.environ',{'APIFY_TOKEN':'dummy'}):
            s.write(Path(d)/'data/acquisition.json',{'facebook':{'run_id':'existing','window_start':'2026-11-04T00:00:00+00:00','window_end':'2026-11-06T00:00:00+00:00'}})
            with patch.object(f,'request_json',side_effect=[{'data':{'id':'run','status':'SUCCEEDED','defaultDatasetId':'dataset'}},[row('1')]]) as request:
                f.fetch('facebook',2)
            self.assertTrue(all(len(call.args)==2 for call in request.call_args_list))
            state=s.read(Path(d)/'data/acquisition.json',{})['facebook']
            self.assertEqual(state['completed_until'],'2026-11-06T00:00:00+00:00')

    def test_explicit_rejection_can_be_retried_after_fix(self):
        with TemporaryDirectory() as d,patch.object(f,'ROOT',Path(d)),patch.dict('os.environ',{'APIFY_TOKEN':'dummy'}):
            with patch.object(f,'request_json',side_effect=s.APIError(400)):
                with self.assertRaises(s.APIError):f.fetch('facebook',2)
            state=s.read(Path(d)/'data/acquisition.json',{})['facebook']
            self.assertFalse(state['submission_uncertain'])
            self.assertEqual(state['last_rejected_http_status'],400)

    def test_failed_run_retains_id_and_does_not_advance(self):
        with TemporaryDirectory() as d,patch.object(f,'ROOT',Path(d)),patch.dict('os.environ',{'APIFY_TOKEN':'dummy'}):
            with patch.object(f,'request_json',side_effect=[{'data':{'id':'run'}},{'data':{'status':'FAILED'}}]):
                with self.assertRaises(RuntimeError):f.fetch('facebook',2)
            state=s.read(Path(d)/'data/acquisition.json',{})['facebook']
            self.assertEqual(state['run_id'],'run');self.assertNotIn('completed_until',state)

if __name__=='__main__':unittest.main()
