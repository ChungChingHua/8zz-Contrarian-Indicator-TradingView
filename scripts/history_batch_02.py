"""One frozen, bounded continuation; same original policy. MPL-2.0."""
import copy,json,os,subprocess
import history_worker as h
import original_author as policy
from original_candidate import build

BATCH='original-author-20261107-02'
PLAN=policy.ROOT/'data/history_batch_02_plan.json'
LEDGER='data/history_progress/'+BATCH+'.json'
OUT=policy.ROOT/'candidates/8zz-original-author-batch-02.pine'

def prepare(post):
    # Apify multi-photo album rows include a non-media container, and Photo.image.uri.
    # Preserve raw archive; only normalize recognized Photo metadata for the SAME downloader.
    p=copy.deepcopy(post);normalized=[];containers=[]
    for i,m in enumerate(p['attachments']):
        if (not (m.get('type') or m.get('__typename'))
            and m.get('mediaset_token')=='pcb.'+p['post_id']
            and set(m)<= {'mediaset_token','url','comet_product_tag_feed_overlay_renderer'}):
            containers.append(i);continue
        if m.get('__typename')=='Photo' and m.get('image',{}).get('uri') and not m.get('photo_image'):
            m['photo_image']=copy.deepcopy(m['image'])
        normalized.append((i,m))
    p['attachments']=[m for i,m in normalized]
    parts,scope=h.prepare_media(p)
    mapping=[i for i,m in normalized]
    translated=set()
    for bucket in ('unanalysed_media','media_failures','image_evidence'):
        for item in scope.get(bucket,[]):
            # The same failure object can occur in two buckets; translate once.
            if id(item) in translated:continue
            item['attachment_index']=mapping[item['attachment_index']]
            translated.add(id(item))
    scope['non_media_album_container_indices']=containers
    return parts,scope

def candidate():
    rows=[];seen=set()
    for path in sorted((policy.ROOT/'data/history_progress').glob('*.json')):
        if path.name.endswith('.uncommitted.json'):continue
        ledger=json.loads(path.read_text())
        for r in ledger.get('records',[]):
            if r['key'] in seen:raise ValueError('duplicate_checkpoint_key')
            seen.add(r['key']);rows.append(r)
    rows.sort(key=lambda r:(r['unix_ms'],r['key']))
    text,stats=build({'records':rows})
    OUT.parent.mkdir(exist_ok=True);OUT.write_text(text)
    OUT.with_suffix('.checks.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats))

def main():
    import sys
    if sys.argv[1:]==['candidate']:candidate();return
    plan=json.loads(PLAN.read_text())
    if (os.getenv('GITHUB_REF')!='refs/heads/'+h.BRANCH
        or os.getenv('AUTHORIZED_HISTORY_BATCH')!=BATCH or plan['batch_id']!=BATCH
        or plan['max_generations']!=20 or len(plan['posts'])>20
        or plan['rule_sha256']!=policy.fingerprint()
        or os.getenv('AUTHORIZED_RULE_SHA256')!=policy.fingerprint()
        or os.getenv('AUTHORIZED_PLAN_SHA256')!=h.digest(plan)):
        raise SystemExit('Authorization, frozen plan or policy mismatch; no generation')
    for path,expected in plan['predecessor_git_blob_sha'].items():
        actual=subprocess.run(['git','rev-parse','HEAD:'+path],capture_output=True,text=True,check=True).stdout.strip()
        if actual!=expected:
            raise SystemExit('Predecessor ledger changed; no generation')
    h.BATCH_ID=BATCH;h.LEDGER_PATH=LEDGER
    key=os.environ.pop('CHATANYWHERE_API_KEY','');gh=os.environ.pop('GH_TOKEN','')
    if not key or not gh:raise SystemExit('Missing dedicated Secrets; no generation')
    worker=h.Worker(h.GitHubStore(gh),h.Provider(key),plan,prepare=prepare,secrets=(key,gh),local=policy.ROOT/LEDGER,generation_limit=20)
    worker.run(h.original_posts(plan))
    print(json.dumps({'finished':worker.state['finished'],'stopped':worker.state['stopped'],'stop_reason':worker.state.get('stop_reason'),'reserved_attempts':worker.state['reserved_generation_attempts'],'statuses':[r['status'] for r in worker.state['records']]}))

if __name__=='__main__':main()
