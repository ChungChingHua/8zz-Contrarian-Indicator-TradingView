"""Reprocess the same ten samples offline. Raw responses and formal data are immutable. MPL-2.0."""
import copy
import hashlib
import json
from pathlib import Path
from collections import Counter
import quality_protocol as frozen
from semantic_gate import _contains
from review_rules import VERSION,panic_evidence,medical_text_decision,asset_bucket
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/quality_test_results.json'


def citation(row,c):
    if c['source']=='author_text':
        if c['image_index']==-1 and c['quote'] and c['quote'] in row['text']:
            return {**c,'status':'literal_text_match','human_verified':False}
    else:
        images=row.get('image_evidence',[]);i=c['image_index']
        if c['quote'] and 0<=i<len(images):
            return {**c,'sha256':images[i]['sha256'],'status':'pending_image_confirmation','human_verified':False}
    return None


def assets(row,answer):
    buckets={'personal_assets':[],'mentioned_targets':[],'image_quotes':[]};corrections=[]
    for target in answer.get('targets',[]):
        if not target['name'] and not target['ticker']:continue
        proofs=[p for c in target['evidence'] if (p:=citation(row,c))]
        name=target['name'] if any(_contains(target['name'],p['quote']) for p in proofs) else ''
        ticker=target['ticker'] if any(_contains(target['ticker'],p['quote']) for p in proofs) else ''
        if name!=target['name']:corrections.append({'field':'name','original':target['name'],'processed':'','reason':'缺乏對應逐字證據'})
        if ticker!=target['ticker']:corrections.append({'field':'ticker','original':target['ticker'],'processed':'','reason':'代碼與引用證據不一致；不自動猜改成另一代碼'})
        bucket,why=asset_bucket(row['text'],target,proofs)
        if bucket!='personal_assets' and target['relationship'] in ('author_stance','holding_only'):
            corrections.append({'field':'relationship','name':name,'original':target['relationship'],'processed':bucket,'reason':why})
        buckets[bucket].append({'name':name,'ticker':ticker,'identity':'asset_class_only' if name in ('個股','主動ETF','ETF','股票') else 'candidate',
            'evidence':proofs,'attribution_reason':why,'status':'pending_image_confirmation' if bucket=='image_quotes' else 'text_evidence_only',
            'human_image_verified':False})
    return buckets,corrections


def process(row,media_types):
    result={'number':row['number'],'key':row['key'],'url':row['url'],'display_time':row['display_time'],
       'scope':'quality_record_only','decision_origin':'cached_model_plus_offline_rules','raw_record_ref':{'file':'data/quality_test_results.json','number':row['number']},
       'context_used':[],'formal_signal_written':False,'auto_retry':False,'new_generation_requests':0,'model_answer_available':'model_answer' in row,
       'video_unanalysed':any(t in ('Video','video') for t in media_types),
       'image_observations_verified':False,'review_reasons':[],'model_requery':{'required_now':False,'reason':''}}
    answer=row.get('model_answer')
    if answer is None:
        decision=medical_text_decision(row['text']) if result['video_unanalysed'] else None
        if decision:
            mentions=[]
            import re
            for m in re.finditer(r'(?:^|\n)買([\u4e00-\u9fff]{2,4})[，,]',row['text']):
                mentions.append({'name':m[1],'ticker':'','evidence':[{'source':'author_text','quote':m.group().strip(),'status':'literal_text_match'}],
                    'attribution_reason':'醫美文引子；沒有本人具體持倉證據','human_image_verified':False})
            result.update(status='acceptable',decision_origin='offline_text_rule_no_model_response',analysis_scope='text_only_video_unanalysed',
                relevance=decision['relevance'],emotion=decision['emotion'],direction=0,strength=1,reason=decision['reason'],
                asset_groups={'personal_assets':[],'mentioned_targets':mentions,'image_quotes':[]},corrections=[],model_answer_available=False)
            result['model_requery']['reason']='目前無需模型；若未來要求與AI結果同規格比較，須另授權一次文字限定判讀，明列影片未分析，不能把本筆規則結果冒充模型答案。'
        else:
            technical=row.get('status')=='retry'
            result.update(status='technical_failure' if technical else 'pending_confirmation',analysis_scope='text_only_video_unanalysed' if result['video_unanalysed'] else 'unavailable',
                relevance=None,emotion='undetermined',direction=None,strength=None,reason='無可重用答案；文字不足時不得憑影片縮圖推測',
                asset_groups={'personal_assets':[],'mentioned_targets':[],'image_quotes':[]},corrections=[],model_answer_available=False)
            result['model_requery']['reason']='先補齊可用輸入或排查技術問題，再另行授權；本輪不重送。'
        return result
    try:frozen.validate(answer)
    except ValueError:
        result.update(status='technical_failure',reason='保存輸出不符合原schema；未重送',direction=None,strength=None)
        return result
    buckets,changes=assets(row,answer)
    result.update(status='acceptable',analysis_scope='same_post_text_and_saved_image_observations',
        relevance=answer['relevance'],emotion=answer['emotion'],direction=answer['direction'],strength=answer['strength'],
        reason=answer['emotion_reason'],asset_groups=buckets,corrections=changes,model_answer_available=True)
    if answer['relevance']=='insufficient_information' or answer['emotion']=='insufficient_information':
        result['status']='pending_confirmation';result['review_reasons'].append('投資相關性或情緒資訊不足；不改成確定中性／無關')
    if answer['emotion']=='panic' and not panic_evidence(row['text'])['explicit']:
        result.update(status='pending_confirmation',emotion='undetermined',direction=None,strength=None)
        result['review_reasons'].append('完整原文缺少明確恐慌／痛苦證據；未停損、停不掉、無奈或顏文字本身不足，不改成中性')
    if result['status']=='pending_confirmation':
        result['model_requery']['reason']='先人工確認情緒閾值／發文當時可用脈絡；相同文字再問模型未必補足證據，本輪不重送。'
    else:result['model_requery']['reason']='現有回應足以離線修正；圖片／代碼疑點先核證據，不需為清空或調整歸屬重新生成。'
    if any(c['source']=='image' and c['quote'].startswith(('畫面顯示','圖片含','截圖顯示')) for c in answer['emotion_evidence']):
        result['review_reasons'].append('原圖名字不可讀不影響明確文字情緒；描述性的圖片quote不當作逐字OCR或標的證據')
    return result


def reprocess(raw,metadata):
    by_key={x['key']:x for x in metadata['samples']}
    records=[process(row,[m.get('type') for m in by_key[row['key']]['images']]) for row in raw['samples']]
    counts=Counter(r['status'] for r in records)
    return {'rules_version':VERSION,'new_generation_requests':0,'raw_response_count':sum('model_answer' in r for r in raw['samples']),
        'formal_signal_written':False,'count_scope':'10 original samples; acceptable means relevance/emotion at stated scope, not image verification or formal signal approval',
        'counts':{k:counts[k] for k in ('acceptable','pending_confirmation','technical_failure')},
        'model_response_only_counts':{k:sum(r['status']==k and r['model_answer_available'] for r in records) for k in ('acceptable','pending_confirmation','technical_failure')},
        'records':records}


def main():
    raw_bytes=RAW.read_bytes();raw=json.loads(raw_bytes);metadata=json.loads((ROOT/'data/quality_samples.json').read_text())
    plan=json.loads((ROOT/'data/quality_test_plan.json').read_text())
    if [r['key'] for r in raw['samples']]!=[r['key'] for r in plan['samples']]:raise SystemExit('Only original quality sample set allowed')
    result=reprocess(raw,metadata);result['raw_file_sha256']=hashlib.sha256(raw_bytes).hexdigest()
    (ROOT/'data/quality_rule_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert RAW.read_bytes()==raw_bytes
    print(json.dumps({'counts':result['counts'],'model_response_only_counts':result['model_response_only_counts'],'new_generation_requests':0}))

if __name__=='__main__':main()
