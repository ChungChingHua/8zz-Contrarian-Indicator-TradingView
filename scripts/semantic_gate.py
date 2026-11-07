"""Conservative offline consistency/evidence checks; no model, OCR or network. MPL-2.0."""
import copy
import re

VERSION='semantic-v2-independent-axes'
TERMINAL={'done','no_signal','review'}
INVESTMENT=re.compile(r'股票|股市|台股|美股|股價|持股|持倉|個股|損益|停損|漲停|跌停|ETF|BTC|\$[A-Z]{1,5}\b',re.I)
PANIC=re.compile(r'恐慌|恐怖|崩潰|痛苦|虧爛|爆炸|鮮血|停損|睡不著|害怕')
EUPHORIA=re.compile(r'亢奮|狂喜|歡呼|賺爛|賺爆|爽啦|台股簡單|天下無敵|一起.*念|穩了|追漲')
# These rules flag common explicit contradictions. They are not a general NLU proof.
NO_INVESTMENT=re.compile(r'無關投資|非投資|不涉及投資|沒有(?:任何)?(?:股票、交易介面或)?投資(?:相關)?(?:資料|證據)|投資(?:關聯|證據)不足|僅(?:為|是)生活|只有生活')
UNCERTAIN=re.compile(r'不確定|資訊不足|上下文不足|模糊|混合|矛盾|無法(?:確認|確定|判斷)|無(?:明確|足夠).*?(?:情緒|投資|標的)|沒有明確.*?(?:情緒|標的)|標的不明')
NEUTRAL=re.compile(r'中性|持倉紀錄|持倉記錄|客觀(?:記錄|紀錄)|沒有明顯情緒|無明顯情緒')
NEGATED_CLAUSE=re.compile(r'(?:沒有|並無|未有|並非|非(?=投資|恐慌|亢奮)|不屬於|不是|不算|不感到|不用|不必)[^，。；;\n]{0,60}')


def _contains(value,text):
    if not isinstance(value,str) or not value:return False
    # Tickers must be full tokens: 0050 != 00500, MU != MUSEUM.
    if re.fullmatch(r'[A-Za-z0-9.^=\-]+',value):
        return re.search(r'(?<![A-Za-z0-9])'+re.escape(value)+r'(?![A-Za-z0-9])',text,re.I) is not None
    return value in text


def evidence(post,analysis,value,verified_images):
    if not value:return None
    text=post.get('text','')
    if _contains(value,text):
        return {'source':'author_text','quote':value,'start':text.casefold().find(value.casefold())}
    # Human-transcribed image evidence only. Platform OCR/model claims are not verification.
    supplied={x.get('sha256') for x in analysis.get('image_evidence',[]) if re.fullmatch(r'[0-9a-f]{64}',x.get('sha256',''))}
    for item in verified_images.get(post.get('key'),[]):
        if (item.get('reviewed') is True and item.get('reviewer') and item.get('verified_at')
            and item.get('sha256') in supplied and _contains(value,item.get('observed_text',''))):
            return {'source':'human_verified_image','sha256':item['sha256'],'quote':value,
                    'reviewer':item['reviewer'],'verified_at':item['verified_at']}
    return None


def assess(post,analysis,verified_images=None):
    """Return a copy; never convert technical failure to semantic completion, or vice versa.

    Raw candidate stays separate. Named instruments and ticker are checked independently;
    a screenshot holding alone never establishes the author's stance on that instrument.
    """
    a=copy.deepcopy(analysis)
    if a.get('status') in ('pending','retry'):
        a['decision_type']='technical_failure' if a.get('status')=='retry' else 'unprocessed'
        a['auto_retry_eligible']=a.get('status')=='retry'
        a['direction']=0
        return a
    fields=('investment_related','clear','direction','strength','target','ticker','reason','author_commentary','quoted_summary','images_reviewed')
    raw=copy.deepcopy(a.get('model_candidate') or {k:a.get(k) for k in fields})
    a['model_candidate']=raw
    issues=[];target_issues=[];proof={}
    # Revalidation is idempotent and always starts from the saved candidate, not a corrected answer.
    a.update({k:v for k,v in raw.items() if k in fields})
    reason=a.get('reason') if isinstance(a.get('reason'),str) else ''
    complete=(all(type(a.get(k)) is bool for k in ('investment_related','clear','images_reviewed'))
              and type(a.get('direction')) is int and a['direction'] in (-1,0,1)
              and type(a.get('strength')) is int and a['strength'] in (1,2,3)
              and all(isinstance(a.get(k),str) for k in ('target','ticker','reason','author_commentary','quoted_summary')))
    if not complete:issues.append('legacy_or_incomplete_classification')
    for field in ('target','ticker'):
        value=a.get(field) or ''
        found=evidence(post,a,value,verified_images or {})
        if value and not found:
            target_issues.append(field+'_without_traceable_evidence');a[field]=''
        elif found:proof[field]=found
    if not a.get('target'):a['ticker']='';proof.pop('ticker',None)
    reason=re.sub(r'(?:標的|代碼|ticker)[^，。；;\n]{0,80}', '', reason,flags=re.I)
    direction=a.get('direction',0)
    related=a.get('investment_related') is True
    text=post.get('text','').replace('投資自己','')
    investment_context=bool(INVESTMENT.search(text) or any(x['source']=='human_verified_image' for x in proof.values()))
    if related and not investment_context:issues.append('investment_context_not_grounded')
    if not related and direction:issues.append('unrelated_with_direction')
    if related and NO_INVESTMENT.search(reason):issues.append('relevance_reason_conflict')
    if direction and not a.get('clear'):issues.append('unclear_with_direction')
    if direction and UNCERTAIN.search(reason):issues.append('uncertain_reason_with_direction')
    if a.get('clear') and UNCERTAIN.search(reason):issues.append('clarity_reason_conflict')
    # Examine unnegated reason clauses; "沒有恐慌" must not justify a panic signal.
    positive_reason=NEGATED_CLAUSE.sub('',reason)
    positive_text=NEGATED_CLAUSE.sub('',text)
    panic=bool(PANIC.search(positive_reason));euphoria=bool(EUPHORIA.search(positive_reason))
    if related and NEUTRAL.search(reason) and re.search(r'恐慌|崩潰|痛苦|虧爛|鮮血|爽啦|天下無敵|台股簡單',positive_text):issues.append('neutral_despite_explicit_distress')
    if direction and (panic and euphoria):issues.append('mixed_sentiment_reason')
    if direction and PANIC.search(positive_text) and EUPHORIA.search(positive_text):issues.append('mixed_source_sentiment')
    if direction==1 and (not panic or not PANIC.search(positive_text)):
        issues.append('panic_direction_not_supported')
    if direction==-1 and (not euphoria or not EUPHORIA.search(positive_text)):
        issues.append('euphoria_direction_not_supported')
    # Explicit third-party structures, not a rhetorical "市場跟我說", establish quotations.
    if a.get('quoted_summary') and not post.get('quoted_content') and post.get('quote_flag') is not True:
        issues.append('quotation_without_source_boundary')
    if post.get('attachments') and not (a.get('images_reviewed') is True and a.get('image_evidence')):
        issues.append('image_evidence_missing')
    if not related and investment_context and (PANIC.search(positive_text) or EUPHORIA.search(positive_text)):
        issues.append('unrelated_despite_investment_emotion')
    if issues:
        decision='semantic_conflict';status='review'
    elif not related:
        if UNCERTAIN.search(reason) or not NO_INVESTMENT.search(reason):
            decision='insufficient_information';status='review'
        else:decision='unrelated';status='no_signal'
    elif direction==0 and NEUTRAL.search(reason) and not UNCERTAIN.search(reason):
        decision='neutral';status='no_signal'
    elif not a.get('clear') or direction==0:
        decision='insufficient_information';status='review'
    else:decision='signal';status='done'
    a.update(status=status,decision_type=decision,auto_retry_eligible=False,
             semantic_check={'version':VERSION,'issues':sorted(set(issues)),'target_issues':sorted(set(target_issues)),'evidence':proof})
    if not related:
        a.update(target='',ticker='');a['semantic_check']['evidence']={}
    if status!='done':a.update(direction=0,clear=False)
    # Target uncertainty does not invalidate a determined emotion or its direction.
    a['relevance_assessment']={'investment_related':related}
    a['emotion_assessment']={'direction':a['direction'],'strength':a.get('strength'),'clear':a.get('clear')}
    a['target_assessment']={'status':'text_or_verified_image_supported' if proof else 'unknown',
        'issues':sorted(set(target_issues)),'evidence':proof}
    if target_issues:
        a['target_assessment']['status']='pending_confirmation'
        a['status']='review'
        a['decision_type']='target_confirmation' if not issues and decision=='signal' else decision
    return a


def retry_candidate(analysis):
    return analysis.get('status') in ('pending','retry')


# Stable input/policy problems require human correction, not another paid attempt.
INPUT_REVIEW_ERRORS={
    'too_many_images_requires_review','video_or_unknown_media_requires_review',
    'unsupported_image_host','unsafe_media_url','non_public_media_address',
    'unsupported_image_or_size','missing_image_url','text_too_long_requires_review',
    'context_too_large','media_proxy_transport_requires_review','unsupported_image_format',
    'image_too_large','invalid_image_magic'}


def failure_state(exc):
    if isinstance(exc,ValueError) and str(exc) in INPUT_REVIEW_ERRORS:
        return {'status':'review','decision_type':'insufficient_information','auto_retry_eligible':False,
                'direction':0,'clear':False,'target':'','ticker':'',
                'reason':'輸入或附件需要人工補正；不自動重送，不產生訊號'}
    return {'status':'retry','decision_type':'technical_failure','auto_retry_eligible':True,
            'direction':0,'clear':False,'target':'','ticker':'',
            'reason':'判讀或附件讀取技術失敗；保留待重試，不產生訊號'}
