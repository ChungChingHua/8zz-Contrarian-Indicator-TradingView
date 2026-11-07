"""Build a proposed 10-post review set offline from existing archive only. MPL-2.0.

No price data, API client, credentials, media fetch or future outcome labels.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
ROOT=Path(__file__).resolve().parents[1]
# Proposed annotations, not model answers or approved gold labels.
SELECTION=[
 ('facebook:1696581131826475','明確恐慌','panic',1,2,'BTC','',
  '本人說 BTC 單沒了、這波很恐怖，並提醒停損；恐慌情緒的反向方向為 +1，不因之後漲跌改標。BTC 逐字在原文。尚須核對圖片是否引入矛盾。', ['signal','insufficient_information']),
 ('threads:3981333267379483868','明確亢奮','euphoria',-1,2,'台股','',
  '本人「爽啦」「加碼再賺」「台股簡單啦」是明確投資歡呼，反向方向 -1；台股在原文，不能把喬喬猜成特定股票代號。', ['signal']),
 ('threads:3952464799527950315','中性持倉邊界','neutral',0,1,'','',
  '原文報告個股及主動 ETF 未停損，未描述明確恐慌或亢奮；持有／未停損本身不是情緒訊號。「隨便他了」也可能是無奈，故中性只是候選，確認前亦接受資訊不足；不猜 ETF 代號。', ['neutral','insufficient_information']),
 ('threads:4024468641932717746','生活玩笑／既有 smoke','unrelated',0,1,'','',
  '新 GShock 與「下週穩了」未提供投資情境或標的。舊服務描述圖片是手錶，但本輪未人工看圖；圖片若確為生活物品，確定無關，否則保留資訊不足，不能硬判看多。', ['unrelated','insufficient_information']),
 ('facebook:1640562917428297','生活業配、股票名稱干擾','unrelated',0,1,'','',
  '主題為醫美業配與投資自己；欣興、康霈只是引子，沒有本人明確交易情緒或立場。不能因出現股票名就輸出這兩檔訊號。附圖待核。', ['unrelated','insufficient_information']),
 ('facebook:1629435205207735','投資亢奮＋行情圖片候選','euphoria',-1,2,'台股','',
  '本人「今天穩了」「一天100點、台股5萬點」是台股亢奮。平台 OCR 顯示 ADR 報價表，屬待人工核對的交易資訊圖片候選；即使表中有多檔，也不能把每檔變成評論標的，不能用後來漲跌作答案。', ['signal','insufficient_information']),
 ('facebook:1610126397138616','恐慌＋庫存圖片資訊缺口','panic',1,3,'','',
  '文字「今日我的庫存」「好痛苦」「貸款買的部分都是大虧」支持強烈投資痛苦，但未提供單一標的。平台未提供可讀圖片描述，本輪未人工核圖，不能宣稱圖內確有庫存或從中猜標的；即使圖內有多檔持股也不等於對每檔表態。相關性、情緒與標的分開：投資痛苦明確，候選反向方向+1、強度3；標的空白或待核圖不會使情緒歸零。', ['insufficient_information']),
 ('facebook:1703774981107090','單篇上下文不足／既有 smoke','insufficient_information',0,1,'','',
  '「不用停損、因為停不掉」可能為自嘲或流動性等問題，不能單憑字眼斷定恐慌強度。亞翔／6139 不在原文，舊模型答案沒有可追溯圖片文字證據，須留空。「市場跟我說」是修辭，不當作第三方文章。', ['insufficient_information']),
 ('threads:4023888423198910089','情緒強烈但投資情境不足','insufficient_information',0,1,'','',
  '只有「恐慌的睡不著」，無圖片、無標的或投資情境。不能讀鄰近／之後貼文把恐慌原因補成股票；也不能肯定無關，應為資訊不足。', ['insufficient_information']),
 ('threads:3946164126477408639','矛盾情緒＋業配及獎金股價','insufficient_information',0,1,'','',
  '本人明說漲不爽、跌痛苦的矛盾情緒；群創股價在果乾團購獎金段落，不足以指定為本人交易立場標的。先區分本人情緒與業配，方向0，不以群創之後表現決定。', ['insufficient_information'])]


def build(archive):
    samples=[]
    for number,(key,category,sentiment,direction,strength,target,ticker,basis,acceptable) in enumerate(SELECTION,1):
        p=archive[key];images=[]
        for i,m in enumerate(p['attachments']):
            image=m.get('photo_image') or {}
            # Link to public photo permalink if present; never republish signed CDN URLs.
            url=m.get('url','');parts=urlsplit(url)
            photo_url=p['url']
            if parts.hostname=='www.facebook.com' and parts.path=='/photo/' and parse_qs(parts.query).get('fbid'):
                photo_url='https://www.facebook.com/photo/?fbid='+parse_qs(parts.query)['fbid'][0]
            images.append({'index':i,'media_id':str(m.get('id','')),'type':m.get('type') or m.get('__typename'),
                'viewer_url':photo_url,'width':image.get('width') or m.get('width'),'height':image.get('height') or m.get('height'),
                'platform_ocr_unverified':m.get('ocrText') or '',
                'downloaded_this_round':False,'human_verified':False})
        samples.append({'number':number,'key':key,'post_id':p['post_id'],'source':p['source'],'url':p['url'],
            'published_at':p['published_at'],'display_time':p['display_time'],'text':p['text'],
            'text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),'images':images,
            'category':category,'proposed':{'sentiment':sentiment,'direction':direction,'strength':strength,'target':target,'ticker':ticker,
                'acceptable_decisions':acceptable,'basis':basis,'requires_image_review':bool(images)},
            'approval':'pending_user_confirmation'})
    return {'version':'quality-samples-v1','approved':False,'api_requests':0,'selection_approved':True,'labels_are_gold':False,
        'label_policy':'Only the text and attached media of each post at publication time; no subsequent posts, comments, prices or outcomes. OCR is unverified. Proposed labels await user confirmation.',
        'samples':samples}


def main():
    archive=json.loads((ROOT/'data/social_posts.json').read_text());data=build(archive)
    (ROOT/'data/quality_samples.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    lines=['# 判讀品質候選樣本：10 篇（尚待確認）','',
      '本輪只讀既有 archive，沒有模型、圖片下載或其他供應商 API 請求。原文逐字保存；圖片以下方原貼文／公開照片連結與索引列出。現有資料只有部分平台 OCR，本輪未人工看圖，**OCR 不代表圖片已核實**。涉及圖片的預期答案都需先核圖，這份不是已確認的黃金答案。','',
      '只採各篇發文當下的文字與附圖；不看之後貼文、網友留言、價格快取或績效，日期只用於識別原貼文。方向 +1 是恐慌的反向訊號，-1 是亢奮的反向訊號；0 不產生訊號。確定中性／無關、資訊不足及技術失敗分開。','',
      '中性持倉樣本刻意保留「隨便他了」的邊界：不能為湊滿類別而假稱已確認中性。使用者已同意這10篇做最多10次生成的品質測試；候選答案不是標準答案，不放入模型提示。','',
      '| # | 類別 | 來源 | 預期方向 | 候選標的 | 圖片數 |','| --- | --- | --- | ---: | --- | ---: |']
    for x in data['samples']:
        lines.append(f"| {x['number']} | {x['category']} | {x['source']} | {x['proposed']['direction']} | {x['proposed']['target'] or '空白'} | {len(x['images'])} |")
    for x in data['samples']:
        a=x['proposed'];lines += ['',f"## {x['number']}. {x['category']}",'',f"[原貼文]({x['url']}) · `{x['key']}` · {x['display_time']}（Asia/Taipei）",'', '原文：','']
        lines += ['> '+line if line else '>' for line in x['text'].splitlines()]
        lines += ['',f"預期：方向 **{a['direction']}**、參考強度 {a['strength']}；標的 **{a['target'] or '空白'}**，ticker **{a['ticker'] or '空白'}**。候選決策：`{' / '.join(a['acceptable_decisions'])}`。",'',a['basis'],'']
        if not x['images']:lines += ['圖片：無附件。']
        for image in x['images']:
            lines += [f"- [圖片 {image['index']+1}／原貼文檢視]({image['viewer_url']})；類型 {image['type']}；media ID `{image['media_id'] or '未提供'}`。本輪未下載、未人工核圖。"]
            if image['platform_ocr_unverified']:lines += ['  平台 OCR／alt（未驗證）：'+image['platform_ocr_unverified']]
    lines += ['','本輪品質測試結果只存測試紀錄，無 API 答案不標記完成。不得把供應商技術成功當成語意標籤正確，亦不批次／排程／Pages／合併。','']
    (ROOT/'docs/QUALITY_SAMPLES.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
