"""Offline revalidation of the two authorized saved candidates, no new generation. MPL-2.0."""
import copy
import json
from pathlib import Path
from semantic_gate import assess
from social_pipeline import ROOT,read,write
AUDIT='data/social_chatanywhere_minimal_20261107.json'
KEYS=('facebook:1703774981107090','threads:4024468641932717746')


def review(saved,archive):
    if tuple(row['key'] for row in saved['samples'])!=KEYS:raise ValueError('unexpected_cached_samples')
    rows=[]
    for row in saved['samples']:
        p=archive[row['key']]
        if p['text']!=row['text'] or p['source']!=row['source']:raise ValueError('cached_post_identity_mismatch')
        a=copy.deepcopy(row.get('analysis') or row['service_candidate'])
        a.update(row['service_candidate'])
        a.update(status='review',image_evidence=row.get('image_evidence') or row.get('analysis',{}).get('image_evidence',[]))
        # Preserve the actual generation's prompt/configuration, never claim v3 was sent.
        a.setdefault('provider','chatanywhere');a.setdefault('prompt_version','contrarian-openai-v2')
        a.setdefault('model',row['service_response']['model_claim'])
        a.setdefault('usage',row['service_response']['usage'])
        a['source_audit']=AUDIT
        result=assess(p,a,read(ROOT/'data/verified_image_evidence.json',{}))
        rows.append({'key':p['key'],'source':p['source'],'url':p['url'],'original_response_audit':AUDIT,
            'method':'Offline revalidation of saved classification fields only. No API or image request. Not independent visual inspection.',
            'analysis':result})
    return {'version':'semantic-v1','new_generation_requests':0,'archive_modified':False,'samples':rows}


def main():
    archive=read(ROOT/'data/social_posts.json',{})
    report=review(read(ROOT/AUDIT,{}),archive)
    # Only these two already-generated records; no historical classification or Pine rebuild.
    for row in report['samples']:
        p=archive[row['key']];previous=p['analysis']
        row['analysis']['previous_analysis']=copy.deepcopy(previous.get('previous_analysis',previous))
        p['analysis']=row['analysis']
    report.update(archive_modified=True,updated_existing_cached_records=2)
    write(ROOT/'data/quality_cached_review.json',report)
    write(ROOT/'data/social_posts.json',archive)
    print('Offline cached review saved; exactly two existing analyses updated; no API or Pine changes')

if __name__=='__main__':main()
