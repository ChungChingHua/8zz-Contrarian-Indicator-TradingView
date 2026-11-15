"""Deterministic public projection and explicit Pages artifact allowlist. MPL-2.0."""
import hashlib
import json
import shutil
from pathlib import Path
from public_safety import public_url, POST_HOSTS
from urllib.parse import urlsplit

ASSETS=('chart-date-adapter.min.js','chart.umd.min.js','index.html','dashboard.css','dashboard.js','dashboard-data.js','dashboard-data.json','data-version.json')

def finalize(result, docs):
    # No raw ledgers, provider responses, credentials, configuration or internal paths.
    for e in result['events']:
        e['urls']=[u for raw in e['urls'] if (u:=public_url(raw)) and urlsplit(u).hostname in POST_HOSTS]
        e['media_note']='歷史媒體判讀範圍請以原始來源核對' if e['historical'] else '已保存判讀；未重新分析媒體'
    for r in result['inventory']:
        r['url']=public_url(r['url'] or '')
    content={k:v for k,v in result.items() if k not in ('built_at','version')}
    version=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    previous=docs/'dashboard-data.json'
    if previous.exists():
        old=json.loads(previous.read_text())
        if old.get('version')==version:result['built_at']=old['built_at']
    result['version']=version
    return result

def package(docs, destination):
    docs=Path(docs);destination=Path(destination)
    if destination.exists():shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in ASSETS:shutil.copyfile(docs/name,destination/name)
    manifest=json.loads((docs/'data-version.json').read_text())
    version=manifest['version']
    if len(version)!=64 or any(c not in '0123456789abcdef' for c in version):raise ValueError('invalid_version')
    expected='snapshots/'+version+'.json'
    if manifest['url']!=expected:raise ValueError('invalid_snapshot_path')
    (destination/'snapshots').mkdir()
    snapshot=(docs/expected).read_bytes()
    data=json.loads(snapshot)
    from publication_scope import assert_boundary
    assert_boundary(data)
    if data.get('version')!=version or snapshot!=(docs/'dashboard-data.json').read_bytes():raise ValueError('inconsistent_public_snapshot')
    shutil.copyfile(docs/expected,destination/expected)
    (destination/'.nojekyll').touch()
    digest=hashlib.sha256()
    for p in sorted(destination.rglob('*')):
        if p.is_file():digest.update(str(p.relative_to(destination)).encode());digest.update(p.read_bytes())
    return digest.hexdigest()

if __name__=='__main__':
    import sys
    print(package(sys.argv[1],sys.argv[2]))
