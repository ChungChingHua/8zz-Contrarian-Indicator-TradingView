import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import social_pipeline as s
import build_site_data as b


def row(source='threads',text='我投資股票非常恐慌，今天又停損損失了好多錢',id='1'):
    r={'postId':id,'username':'banini31','isReply':False,'isRepost':False,'text':text,
       'url':'https://www.threads.com/@banini31/post/'+id,'date':'2026-08-01T00:00:00Z',
       'time':'2026-08-01T00:00:00Z','user':{'id':'100044238139017'},'media':[]}
    return r


def post(source='threads',text=None,id='1'):
    r=row(source,id=id)
    if text is not None:r['text']=text
    p,_=s.normalize(r,source)
    p['analysis']={'status':'done','direction':1,'clear':True,'investment_related':True,'strength':2,'reason':'恐慌'}
    return p


class SocialTests(unittest.TestCase):
    def test_strict_reply_flags(self):
        for field in ('isReply','isRepost'):
            for v in (None,True,0,'false'):
                r=row();r[field]=v
                self.assertIsNone(s.normalize(r,'threads')[0])
            r=row();r.pop(field)
            self.assertIsNone(s.normalize(r,'threads')[0])

    def test_author_and_timezone_and_no_comments(self):
        r=row();r['topComments']=[{'text':'買進'}]
        p,_=s.normalize(r,'facebook')
        self.assertEqual(p['display_time'],'2026-08-01T08:00:00+08:00')
        self.assertNotIn('topComments',p)
        r['user']['id']='wrong'
        self.assertIsNone(s.normalize(r,'facebook')[0])

    def test_same_post_reimport_and_edit(self):
        a={};s.ingest([row()],'threads',a)
        a['threads:1']['analysis']={'status':'done','direction':1}
        s.ingest([row()],'threads',a)
        self.assertEqual(len(a),1)
        self.assertEqual(a['threads:1']['analysis']['status'],'done')
        r=row();r['text']='edited';s.ingest([r],'threads',a)
        self.assertEqual(a['threads:1']['analysis']['status'],'pending')

    def test_exact_merge_earliest_both_links_opposite_never_merge(self):
        p=post('facebook');q=post('threads')
        q['unix_ms']+=60000
        gs=s.groups({p['key']:p,q['key']:q})
        self.assertEqual(len(gs),1);self.assertEqual(gs[0][0]['source'],'facebook')
        q['analysis']['direction']=-1
        self.assertEqual(len(s.groups({p['key']:p,q['key']:q})),2)

    def test_prefix_and_unknown_do_not_merge(self):
        p=post('facebook');q=post('threads',text=p['text']+'但是現在我改成看多')
        self.assertEqual(len(s.groups({p['key']:p,q['key']:q})),2)
        q=post('threads');q['analysis']['status']='pending'
        self.assertEqual(len(s.groups({p['key']:p,q['key']:q})),2)

    def test_quotes_kept_separate(self):
        r=row();r['quotedPost']={'text':'看多'}
        p,_=s.normalize(r,'threads')
        self.assertEqual(p['quoted_content']['quotedPost']['text'],'看多')
        self.assertEqual(p['text'],r['text'])

    def test_media_fail_closed(self):
        p=post();p['attachments']=[{'type':'video','url':'https://example.com'}]
        with self.assertRaises(ValueError):s.image_parts(p)

    def test_model_ambiguity_and_images(self):
        p=post()
        answer={'investment_related':True,'clear':False,'direction':-1,'strength':2,'reason':'模糊',
                'target':'台股','ticker':'','author_commentary':'','quoted_summary':'','images_reviewed':False}
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(answer)}]}]}
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test'}),patch.object(s,'request_json',return_value=response):
            self.assertEqual(s.classify(p)['direction'],0)
            p['attachments']=[{'type':'image'}]
            with patch.object(s,'image_parts',return_value=[{'type':'input_image','image_url':'data:image/png;base64,AA=='}]):
                with self.assertRaises(ValueError):s.classify(p)

    def test_both_sides_losses_modes_a_b(self):
        def event(day,d):return {'is_flip':True,'direction':d,'ticker':'X','time_utc':f'2026-08-0{day}T00:00:00+00:00'}
        for direction,prices in ((1,[100,90,80]),(-1,[100,110,120])):
            events=[event(1,direction),event(2,-direction)]
            market={'X':{f'2026-08-0{i+1}':v for i,v in enumerate(prices)}}
            b.compute_outcomes_mode_b(events,market);b.compute_outcomes_mode_a(events,market,1)
            self.assertEqual(events[0]['outcome'],'loss')
            self.assertEqual(events[0]['outcome_a'],'loss')

    def test_win_rate_excludes_open(self):
        stats=b._build_mode_stats([{'outcome':x,'pnl_pct':v,'direction':1,'strength':2} for x,v in [('win',10),('loss',-10),('open',3)]],'outcome','pnl_pct')
        self.assertEqual(stats['win_rate'],50)

    def test_fixture_counts_and_history_preserved(self):
        archive=s.read(s.ROOT/'data/social_posts.json',{})
        from collections import Counter
        counts=Counter(p['source'] for p in archive.values())
        self.assertGreaterEqual(counts['facebook'],284)
        self.assertGreaterEqual(counts['threads'],375)
        original=(s.ROOT/'data/historical-indicator.pine').read_text()
        generated=(s.ROOT/'8zz-indicator.pine').read_text()
        import re
        blocks=lambda t:re.findall(r'array.push\(evt_time,.*?array.push\(evt_ticker,[^\n]+',t,re.S)
        for block in blocks(original):self.assertIn(block,generated)

if __name__=='__main__':unittest.main()
