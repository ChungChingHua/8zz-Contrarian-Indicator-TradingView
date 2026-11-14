"""Chronological selection with conservative exact dedup, no paid requests. MPL-2.0."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from original_author import ROOT,VERSION,fingerprint
BATCH_ID='original-author-20261107-01'
PLAN=ROOT/'data/history_batch_01_plan.json'

def normalized(text):return re.sub(r'\s+','',text)
def media_identity(p):
    identities=[]
    for m in p['attachments']:
        kind=m.get('type') or m.get('__typename')
        if (not kind and m.get('mediaset_token')=='pcb.'+p['post_id']
            and set(m)<= {'mediaset_token','url','comet_product_tag_feed_overlay_renderer'}):continue
        url=m.get('photo_image',{}).get('uri') or (m.get('image',{}).get('uri') if kind=='Photo' else None) or m.get('url','')
        identities.append(('image' if kind in ('Photo','photo','image') else kind,urlsplit(url).path))
    return identities

def select(archive,excluded,limit=5):
    groups=[];skips=[]
    for p in sorted(archive.values(),key=lambda x:(x['unix_ms'],x['key'])):
        if p['key'] in excluded or p['analysis'].get('status')!='pending':
            skips.append({'key':p['key'],'reason':'previously_tested_or_processed'});continue
        match=next((g for g in groups if p['source']!=g[0]['source'] and normalized(p['text']) and normalized(p['text'])==normalized(g[0]['text']) and abs(p['unix_ms']-g[0]['unix_ms'])<=172800000 and p['quoted_content']==g[0]['quoted_content'] and media_identity(p)==media_identity(g[0])),None)
        if match is not None:match.append(p)
        else:groups.append([p])
    chosen=groups[:limit]
    return chosen,{'total_posts':len(archive),'excluded_posts':len(skips),'eligible_groups':len(groups),'selected_groups':len(chosen),'deduplicated_posts':sum(len(g)-1 for g in groups),'skips':skips}

def main():
    if (ROOT/'data/history_progress'/ (BATCH_ID+'.json')).exists():
        print('Existing durable batch: keep its frozen plan; use worker recovery, never regenerate authorization');return
    archive=json.loads((ROOT/'data/social_posts.json').read_text());excluded=set()
    for ledger_file in (ROOT/'data/history_progress').glob('*.json'):
        ledger=json.loads(ledger_file.read_text())
        for record in ledger.get('records',[]):
            excluded.add(record['key'])
            excluded.update(m['key'] for m in record.get('members',[]))
    for path in (ROOT/'data').glob('*.json'):
        if not any(s in path.name for s in ('smoke','diagnostic','quality_test_results','quality_samples')):continue
        data=json.loads(path.read_text())
        rows=data if isinstance(data,list) else data.get('samples',[])
        for row in rows:
            if isinstance(row,dict) and 'key' in row:excluded.add(row['key'])
    old=json.loads((ROOT/'data/facebook_posts_2026-05-01_2026-07-20.json').read_text())
    for p in old['posts']:excluded.add('facebook:'+p['post_id'])
    groups,stats=select(archive,excluded)
    snapshot=[]
    for i,g in enumerate(groups,1):
        p=g[0]
        snapshot.append({'number':i,'key':p['key'],'content_hash':p['content_hash'],'post_id':p['post_id'],'source':p['source'],
           'url':p['url'],'published_at':p['published_at'],'display_time':p['display_time'],'unix_ms':p['unix_ms'],'text':p['text'],
           'members':[{k:q[k] for k in ('key','source','url','published_at','post_id')} for q in g]})
    plan={'batch_id':BATCH_ID,'max_generations':5,'rule_version':VERSION,'rule_sha256':fingerprint(),'selection_stats':stats,'excluded_keys':sorted(excluded),'posts':snapshot}
    PLAN.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'selected':[(x['key'],x['display_time']) for x in snapshot],'stats':{k:v for k,v in stats.items() if k!='skips'}},ensure_ascii=False))

if __name__=='__main__':main()
