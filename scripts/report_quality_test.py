"""Offline post-generation comparison. Never imported by the model request runner. MPL-2.0."""
import json
from pathlib import Path
from social_pipeline import ROOT,read,write


def compare(report,original,revised):
    before={x['key']:x for x in original['samples']};after={x['key']:x for x in revised['samples']}
    rows=[]
    for row in report['samples']:
        a=row.get('model_answer');old=before[row['key']]['proposed'];new=after[row['key']]['proposed']
        diffs=[]
        if a:
            if a['direction']!=old['direction']:diffs.append(f"與原候選方向不同：{old['direction']} → {a['direction']}")
            if a['direction']!=new['direction']:diffs.append(f"與本輪修正候選方向不同：{new['direction']} → {a['direction']}")
            if a['strength']!=new['strength']:diffs.append(f"與參考強度不同：{new['strength']} → {a['strength']}")
            if old['sentiment'] in ('panic','euphoria','neutral') and a['emotion']!=old['sentiment']:diffs.append('情緒類別與原候選不同：'+old['sentiment']+' → '+a['emotion'])
            if old['sentiment']=='unrelated' and a['relevance']!='unrelated':diffs.append('相關性與原無關候選不同：'+a['relevance'])
            names=[t['name'] for t in a['targets'] if t['name']]
            if set(names)!=({new['target']} if new['target'] else set()):diffs.append('標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）')
        rows.append({'number':row['number'],'key':row['key'],'original_candidate':old,'revised_candidate':new,
                     'differences':diffs,'model_answer_available':a is not None,'gold_label':False})
    return {'comparison_timing':'after_generation_only','candidates_sent_to_model':False,'gold_labels':False,'rows':rows}


def main():
    report=read(ROOT/'data/quality_test_results.json',{})
    comparison=compare(report,read(ROOT/'data/quality_original_proposals.json',{}),read(ROOT/'data/quality_samples.json',{}))
    write(ROOT/'data/quality_test_comparison.json',comparison)
    totals={k:sum(r.get('service_response',{}).get('usage',{}).get(k,0) for r in report['samples']) for k in ('input_tokens','output_tokens','total_tokens','reasoning_tokens')}
    lines=['# 10篇盲測結果（測試紀錄，不是正式Pine訊號）','',
      '每筆只使用原貼文快照及實際附圖，**外部上下文一律無**。候選答案未進prompt；規則與輸入於執行前凍結，生成後才比對。候選不是標準答案，差異不等於模型錯誤；本輪不計算「準確率」。圖片觀察與轉錄均為服務輸出，**沒有人工核圖**。','',
      '[固定規則與限制](QUALITY_PROTOCOL.md)；完整原文與圖片連結見 [樣本](QUALITY_SAMPLES.md)。', '',
      '## 請求與用量','',
      '實際HTTP：'+json.dumps(report['http_counts'],ensure_ascii=False)+'。無自動重試。', '',
      'API回報token加總：'+json.dumps(totals,ensure_ascii=False)+'。僅加總取得的usage；模型與推理資訊為服務回報／宣稱，未獨立驗證底層模型或推理。', '',
      '前後免費點數、剩餘請求額度與實際扣點若無回傳則未知；點數不是tokens，不宣稱零扣點，不估算點數。實際quota欄位：'+json.dumps({k:report.get(k) for k in ('quota_before','quota_after','actual_points_deducted')},ensure_ascii=False), '',
      '請求設定：'+json.dumps(report['requested_settings'],ensure_ascii=False), '',
      '整輪已取得10篇答案：'+str(report.get('completed'))+'；異常停止：'+str(report.get('stopped'))+'。未取得答案的樣本不標記完成。','',
      '| # | 原文摘要 | 相關性 | 情緒／方向／強度 | 圖片 | 狀態 |','| --- | --- | --- | --- | --- | --- |']
    for row in report['samples']:
        a=row.get('model_answer',{});preview=row['text'].replace('\n',' ')[:48].replace('|','\\|')
        lines.append(f"| {row['number']} | {preview} | {a.get('relevance','未取得')} | {a.get('emotion','未取得')} / {a.get('direction','—')} / {a.get('strength','—')} | {row.get('images_attached',0)}/{row['image_count']}附圖 | {row['status']} |")
    for row,diff in zip(report['samples'],comparison['rows']):
        lines+=['',f"## {row['number']}. {row['source']}：{row['key']}",'',f"[來源]({row['url']}) · {row['display_time']}（Asia/Taipei）",'',
          '原文摘要：'+row['text'].replace('\n',' ')[:180], '',
          '使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。', '',
          f"HTTP：{row.get('api_status')}；schema通過：{row.get('schema_valid')}；生成嘗試：{row['generation_attempts']}。狀態：{row['status']}。",'',
          f"圖片：原附件{row['image_count']}張，實際附於生成請求{row.get('images_attached',0)}張；下載成功={row['download_success']}（無附件時為不適用），未人工核圖。"]
        for image in row.get('image_evidence',[]):lines+=['- 下載證據：'+json.dumps(image,ensure_ascii=False)]
        a=row.get('model_answer')
        if a:
            lines+=['',f"相關性：**{a['relevance']}**。理由：{a['relevance_reason']}",'',
                    f"情緒：**{a['emotion']}**；反向方向 **{a['direction']}**；強度 **{a['strength']}**。理由：{a['emotion_reason']}"]
            for image in a['images']:lines+=['','圖片觀察（服務聲稱）：'+json.dumps(image,ensure_ascii=False)]
            for target in row['independent_checks']['target_candidates']:lines+=['','標的候選及證據：'+json.dumps(target,ensure_ascii=False)]
            if not a['targets']:lines+=['','標的：空白／未辨識；不因而抹除已明確的情緒方向。']
            lines+=['','本人評論：'+a['author_commentary'],'','第三方引用摘要：'+(a['quoted_summary'] or '無'),'','模型限制：'+a['limitations'], '',
                   '離線一致性／證據提示：'+json.dumps(row['independent_checks']['issues'],ensure_ascii=False)]
        else:lines+=['','相關性、方向、強度、標的與判讀理由：未取得。錯誤：'+str(row.get('error_code') or row.get('error_reason') or '前筆異常後未嘗試')]
        lines+=['','與候選比較：'+('；'.join(diff['differences']) if a and diff['differences'] else '方向／強度／候選標的與提案未見上述差異；非正確性證明' if a else '無答案可比較'), '',
                '原候選：'+json.dumps({k:diff['original_candidate'][k] for k in ('sentiment','direction','strength','target')},ensure_ascii=False), '',
                '本輪修正候選：'+json.dumps({k:diff['revised_candidate'][k] for k in ('sentiment','direction','strength','target')},ensure_ascii=False), '',
                '服務回報：'+json.dumps(row.get('service_response'),ensure_ascii=False)]
    lines+=['','## 保留限制','',
      '第5篇來源附件是Video，不是靜態照片；生成前被擋，沒有影片／音訊分析，也沒有把縮圖當作看完整影片。先前樣本文件把它列於圖片清單不精確；這是來源型態的更正，不更動候選答案。其餘尚未嘗試樣本的續行不重送任何已生成資料，也不改凍結prompt/schema。',
      '這是10篇選定樣本的技術及語意評估，不代表659篇整體品質，也不能證明服務實際模型或視覺推理。舊回應不符合本輪同規則與資料完整要求，未重用為新答案。不得用這輪答案修改候選後再宣稱事前命中。正式archive與Pine未寫入；一般暫停、排程、Pages與PR未合併維持。', '']
    (ROOT/'docs/QUALITY_TEST_RESULTS.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
