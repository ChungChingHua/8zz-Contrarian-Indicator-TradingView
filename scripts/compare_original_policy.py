"""Offline comparison using author's own few-shot answers, not new AI predictions. MPL-2.0."""
import json
import original_author as p
from semantic_gate import assess
from social_pipeline import ROOT

def main():
    comparisons=[]
    for i in range(0,len(p.C['_EXAMPLES']),2):
        text=p.C['_EXAMPLES'][i]['content'];raw=json.loads(p.C['_EXAMPLES'][i+1]['content'])
        a={**raw,'disposition':'signal' if raw['direction'] else 'no_signal','images':[],'target_notes':'作者原範例，非新模型輸出'}
        old={'status':'done','investment_related':bool(raw['direction']),'clear':bool(raw['direction']),
          'direction':raw['direction'],'strength':raw['strength'],'target':'','ticker':raw['ticker'],
          'reason':raw['reasoning'],'author_commentary':text,'quoted_summary':'','images_reviewed':False}
        before=assess({'text':text,'attachments':[],'quoted_content':{},'quote_flag':False},old)
        after=p.process({'text':text},a)
        comparisons.append({'author_example':i//2+1,'source_text':text,'author_answer':raw,
            'previous_extra_gate':{'direction':before['direction'],'status':before['status'],'arrow_eligible':before['status']=='done' and before['direction']!=0},
            'restored_author_path':{'direction':after['direction'],'strength':after['strength'],'status':after['status'],'arrow_eligible':p.event_eligible(after)}})
    out={'method':'Offline replay of author-provided few-shot answers through two postprocessors; not new generation or evidence of AI accuracy.',
        'rule_version':p.VERSION,'rule_sha256':p.fingerprint(),'examples':comparisons}
    (ROOT/'data/original_policy_comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'author_examples':len(comparisons),'changed_arrow_eligibility':sum(x['previous_extra_gate']['arrow_eligible']!=x['restored_author_path']['arrow_eligible'] for x in comparisons),'api_requests':0}))
if __name__=='__main__':main()
