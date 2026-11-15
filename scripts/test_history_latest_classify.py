import copy,unittest
from unittest.mock import Mock,patch
import history_latest_classify_20261114 as c
import history_cached_completion as m

class MissingMediaRecoveryTests(unittest.TestCase):
    def test_proof_requires_exact_terminal_empty_predecessor(self):
        run={'id':c.OLD_EMPTY_RUN,'defaultDatasetId':c.OLD_EMPTY_DATASET,'status':'ABORTED'}
        self.assertEqual(c.empty_proof(run,[])['dataset_items'],0)
        for change,rows in (({'status':'RUNNING'},[]),({'status':'SUCCEEDED'},[]),({'id':'other'},[]),({},[{'diagnostic':'no_posts'}]),({},[{'postId':'found'}])):
            with self.assertRaises(ValueError):c.empty_proof({**run,**change},rows)
    def media(self):
        key='facebook:missing';old={'id':c.OLD_EMPTY_RUN,'status':'ABORTED','defaultDatasetId':c.OLD_EMPTY_DATASET,'keys':[key],'posts':{}}
        media=Mock();media.state={};media.prior_by_key={key:{'batch':old}};media.attempted={key}
        return key,media,old
    def test_new_attempt_only_after_empty_proof_ack(self):
        key,media,old=self.media();media.client.request.side_effect=[{'data':old},[]]
        self.assertEqual(c.allow_proven_missing_only(media,[key]),set())
        self.assertNotIn(key,media.attempted);self.assertNotIn(key,media.prior_by_key)
        self.assertEqual(media.state['verified_empty_predecessor']['run_id'],c.OLD_EMPTY_RUN)
        self.assertEqual(media.client.request.call_count,2);media.save.assert_called_once()
        self.assertTrue(all(len(call.args)==1 for call in media.client.request.call_args_list))
    def test_denied_or_nonempty_predecessor_never_reopens_url(self):
        for denied in (True,False):
            key,media,old=self.media()
            media.client.request.side_effect=ValueError('denied') if denied else [{'data':old},[{'postId':'already_fetched'}]]
            self.assertEqual(c.allow_proven_missing_only(media,[key]),{key})
            self.assertIn(key,media.attempted);self.assertIn(key,media.prior_by_key)
            self.assertNotIn('verified_empty_predecessor',media.state)
    def test_prior_index_accepts_audited_empty_lineage_but_rejects_other_duplicates(self):
        key,media,old=self.media()
        proof=c.empty_proof(old,[])
        for change,accepted in (({},True),({'dataset_items':1},False),({'dataset_items':False},False),({'terminal_status':'RUNNING'},False),({'run_id':'other'},False)):
            new={'id':'new-once','status':'SUCCEEDED','keys':[key],'empty_predecessor':{**proof,**change}}
            docs=Mock();docs.load.side_effect=[{'batches':[old]},{'batches':[new]}]
            budget={'media_repair_reservations':{'old':{'ledger':'data/history_media_repairs/old.json'},'new':{'ledger':'data/history_media_repairs/new.json'}}}
            if accepted:self.assertEqual(m.previous_media_batches(docs,budget)[key]['batch']['id'],'new-once')
            else:
                with self.assertRaisesRegex(ValueError,'duplicate_prior_media_reservations'):m.previous_media_batches(docs,budget)

if __name__=='__main__':unittest.main()
