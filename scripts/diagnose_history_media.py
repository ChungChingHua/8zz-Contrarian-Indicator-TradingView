"""Bounded no-key diagnostic of first planned image; no provider calls. MPL-2.0."""
import json,re
from urllib.parse import urlsplit
from unittest.mock import patch
import history_worker as h
import safe_media as m

def main():
    import os
    if os.getenv("AUTHORIZED_MEDIA_DIAGNOSTIC")!=h.BATCH_ID:raise SystemExit("Archived diagnostic; explicit scope required, no requests")
    p=h.original_posts(h.s.read(h.PLAN,{}))[0]
    media=p['attachments'][0];url=media.get('photo_image',{}).get('uri') or media.get('url')
    report={'provider_requests':0,'host':urlsplit(url).hostname,'post_id':p['post_id']}
    try:
        host,_,_=m.validate_url(url)
        report['verified_public_addresses']=m.public_addresses(host)
        with patch.object(m,'assert_online_enabled',return_value=None):mime,data=m.download_image(url)
        report.update(download_success=True,bytes=len(data),mime=mime)
    except Exception as exc:
        report.update(download_success=False,error_type=type(exc).__name__,errno=getattr(exc,'errno',None))
        if isinstance(exc,ValueError) and re.fullmatch(r'[a-z_]+',str(exc)):report['safe_error']=str(exc)
    print(json.dumps(report))

if __name__=="__main__":main()
