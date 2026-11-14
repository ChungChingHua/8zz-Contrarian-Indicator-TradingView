"""Offline evidence rules; no API, credentials, media downloads or future context. MPL-2.0."""
import re

VERSION='review-rules-v3'
# An action, loss amount, price drop, emoji or resignation is not itself panic.
PANIC_WORDS=re.compile(r'恐慌|恐怖|崩潰|痛苦|虧爛|爆倉|鮮血|害怕')
STRONG_PANIC=re.compile(r'(?:很|狠|非常|極度).{0,2}(?:恐慌|恐怖|害怕)|崩潰|好痛苦|痛不欲生|虧爛|爆倉')
NEGATED=re.compile(r'(?:沒有|並無|並非|不是|不算|不感到|不用|不必)[^，。；;\n]{0,60}')
EUPHORIA=re.compile(r'亢奮|歡呼|爽啦|台股簡單|天下無敵|賺爆|賺爛|台股.{0,5}萬點')
NON_PERSONAL=re.compile(r'獎金|抽獎|贈獎|新聞|報導|轉貼|轉述')
VIDEO_KINDS={'Video','video'}
IMAGE_KINDS={'Photo','photo','image'}


def panic_evidence(text):
    affirmative=NEGATED.sub('',text)
    return {'explicit':bool(PANIC_WORDS.search(affirmative)),
            'strong':bool(STRONG_PANIC.search(affirmative)),
            'cues':[m.group() for m in PANIC_WORDS.finditer(affirmative)]}


def text_independent(text):
    clean=re.sub(r'https?://\S+','',text).strip()
    if len(re.sub(r'\s+','',clean))<16:return False
    if re.search(r'答案(?:都)?在影片|詳情(?:都)?在影片|只看影片|文字無法說明|如影片所示',clean):return False
    return True  # Conservative preflight, not a proof of semantic sufficiency.


def media_plan(post):
    images=[];indices=[];unanalysed=[]
    for i,m in enumerate(post.get('attachments',[])):
        kind=m.get('type') or m.get('__typename')
        if kind in VIDEO_KINDS:unanalysed.append({'attachment_index':i,'kind':'video','status':'影片未分析'})
        else:images.append(m);indices.append(i)  # Unknown media still fails the existing downloader; no silent skip.
    return {'image_attachments':images,'image_attachment_indices':indices,'unanalysed_media':unanalysed,
            'analysis_scope':'text_only_video_unanalysed' if unanalysed and not images else 'text_and_images_video_unanalysed' if unanalysed else 'text_and_images',
            'text_sufficient_for_preflight':not unanalysed or bool(images) or text_independent(post.get('text',''))}


def medical_text_decision(text):
    if (text_independent(text) and re.search(r'醫美|鳳凰電波|眼周音波',text)
        and re.search(r'#業配|感謝.*美學',text) and not panic_evidence(text)['explicit'] and not EUPHORIA.search(text)):
        return {'relevance':'unrelated','emotion':'not_applicable','direction':0,'strength':1,
                'reason':'完整原文主題為醫美業配與投資自己；股票名是引子，沒有明確本人投資恐慌或亢奮。僅文字規則判讀，影片未分析。'}
    return None


def paragraph(text,quote,name):
    # Preserve paragraph boundaries so fear elsewhere cannot turn a prize/company into a holding.
    if quote and quote in text:
        position=text.index(quote)
        start=text.rfind('\n\n',0,position)+2
        if start==1:start=0
        end=text.find('\n\n',position+len(quote))
        return text[start:end if end!=-1 else len(text)]
    return next((p for p in text.split('\n\n') if name and name in p),'')


def asset_bucket(text,target,evidence):
    text_proofs=[p for p in evidence if p['source']=='author_text']
    image_proofs=[p for p in evidence if p['source']=='image']
    if not text_proofs and image_proofs:return 'image_quotes','圖片可見候選僅表示報價／畫面提及，不證明本人交易或持倉'
    contexts=[paragraph(text,p['quote'],target.get('name','')) for p in text_proofs]
    if any(NON_PERSONAL.search(c) for c in contexts):return 'mentioned_targets','名稱位於新聞／轉述／獎金段落，不能直接歸為本人持倉'
    activity=re.compile(r'我的.{0,20}(?:單|股票|持股|持倉|庫存)|(?:我|本人).{0,15}(?:買|賣|持有|持股|持倉|加碼|減碼|還有)|今日我的庫存')
    if text_proofs and (any(activity.search(c) for c in contexts) or len(text)<180 and activity.search(text)):
        return 'personal_assets','本人文字含可追溯的交易／持倉敘述；泛稱不等於具體股票已辨識'
    return 'mentioned_targets','只確認名稱被提及，沒有足夠本人交易／持倉證據'
