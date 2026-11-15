"""Read-only, bounded public-CDN diagnostics; no AI/Apify credentials. MPL-2.0."""
import hashlib
import http.client
import json
import os
import re
import socket
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch
import safe_media
import social_pipeline as s
from history_batch_02 import prepare
from history_completion import Remote

KEYS=['facebook:1660785808739341','threads:3992201729433763729','threads:3992213198011063292']
MAX_REQUESTS=6
TZ=ZoneInfo('Asia/Taipei')
BODY_LIMIT=4096
MARKERS={'url_signature_expired':b'url signature expired','bad_url_signature':b'bad url signature',
         'invalid_signature':b'invalid signature','url_expired':b'url expired',
         'access_denied':b'access denied','request_blocked':b'request blocked',
         'rate_limited':b'rate limit'}


def classify(raw):
    low=raw.lower()
    return [name for name,needle in MARKERS.items() if needle in low]


def info(url):
    host,path,query=safe_media.validate_url(url)
    oe=urllib.parse.parse_qs(query).get('oe',[])
    expiry=int(oe[0],16) if oe and re.fullmatch('[a-fA-F0-9]{8}',oe[0]) else None
    return host,path,query,expiry


class Captured(Exception):pass

def first_image(post):
    result=[]
    def capture(url):
        safe_media.validate_url(url)
        result.append(url)
        raise Captured()
    try:
        with patch.object(s,'download_image',capture): prepare(post)
    except Captured: pass
    except Exception: return None
    return result[0] if result else None


class ProbeConnection(safe_media.PinnedTLS):
    def __init__(self,host,ip,audit):
        super().__init__(host,ip);self.audit=audit
    def connect(self):
        begin=time.monotonic();self.audit['phase']='tcp_connect'
        sock=socket.create_connection((self.checked_ip,443),timeout=self.timeout)
        self.audit['tcp_seconds']=round(time.monotonic()-begin,3)
        try:
            begin=time.monotonic();self.audit['phase']='tls_handshake'
            self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
            self.audit['tls_seconds']=round(time.monotonic()-begin,3)
        except BaseException:
            sock.close();raise
        self.audit['phase']='http_request'


def probe(url,ip,label,key,counter):
    if counter['requests']>=MAX_REQUESTS: raise ValueError('diagnostic_request_bound')
    host,path,query,expiry=info(url)
    # Addresses are validated again before use; never accept user-provided private IPs.
    import ipaddress
    if not ipaddress.ip_address(ip).is_global: raise ValueError('non_public_address')
    counter['requests']+=1
    audit={'key':key,'variant':label,'host':host,'ip_family':'IPv6' if ':' in ip else 'IPv4',
           'url_sha256':hashlib.sha256(url.encode()).hexdigest(),'phase':'starting',
           'started_at':datetime.now(TZ).isoformat(),'image_analysis_performed':False}
    if expiry:
        audit['oe_timestamp_hint_taipei']=datetime.fromtimestamp(expiry,TZ).isoformat()
        audit['oe_hint_before_probe']=expiry<time.time()
    connection=ProbeConnection(host,ip,audit);started=time.monotonic()
    try:
        connection.request('GET',path+('?' +query if query else ''),headers={'Accept':'image/jpeg,image/png,image/webp','Connection':'close'})
        audit['phase']='http_response_headers';response=connection.getresponse()
        audit['http_status']=response.status
        mime=response.getheader('Content-Type','').split(';')[0].strip().lower()
        audit['content_type']=mime if mime in ('text/plain','text/html','image/jpeg','image/png','image/webp','application/json') else 'other'
        audit['phase']='bounded_response_body'
        raw=response.read(BODY_LIMIT)
        audit['body_prefix_bytes']=len(raw)
        audit['body_prefix_sha256']=hashlib.sha256(raw).hexdigest()
        if response.status!=200:
            audit['error_markers']=classify(raw) # Only fixed literals, never raw bodies/URLs/headers.
        else:
            audit['image_magic_prefix']=('jpeg' if raw.startswith(b'\xff\xd8\xff') else
                'png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else
                'webp' if raw.startswith(b'RIFF') and raw[8:12]==b'WEBP' else 'other')
        audit['phase']='completed'
    except Exception as exc:
        audit['error_type']=type(exc).__name__
        if isinstance(exc,OSError) and isinstance(exc.errno,int):audit['errno']=exc.errno
    finally:
        connection.close();audit['elapsed_seconds']=round(time.monotonic()-started,3)
    return audit


def main():
    if os.getenv('AUTHORIZED_MEDIA_DIAGNOSTIC')!='20261111-rootcause' or os.getenv('GITHUB_REF')!='refs/heads/codex/social-pipeline-20261106':
        raise SystemExit('Diagnostic authorization mismatch; no network requests')
    if any(urllib.request.getproxies().get(k) for k in ('http','https')):
        raise SystemExit('Configured proxy requires reviewed transport; no direct bypass')
    # The classifier never returns arbitrary response text.
    assert classify(b'URL signature expired sk-secret https://example.invalid/token')==['url_signature_expired']
    data=json.loads(subprocess.run(['git','show','51e27179cc4fa3447ce9e011c2e7d194ad5a9520:data/social_posts.json'],capture_output=True,check=True).stdout)
    urls={};corpus={'recognized_image_posts':0,'oe_hint_before_execution':0,'future_oe_hint':0}
    for key,post in data.items():
        url=first_image(post)
        if not url:continue
        urls[key]=url;corpus['recognized_image_posts']+=1
        expiry=info(url)[3]
        if expiry:corpus['oe_hint_before_execution' if expiry<time.time() else 'future_oe_hint']+=1
    counts={'requests':0};results=[];dns=[];facebook_default=None
    for key in KEYS:
        if key not in urls:
            results.append({'key':key,'error_type':'NoRecognizedImage'});continue
        url=urls[key];host=info(url)[0]
        try: ips=safe_media.public_addresses(host)
        except Exception as exc:
            results.append({'key':key,'error_type':type(exc).__name__,'phase':'dns'});continue
        dns.append({'key':key,'host':host,'public_ipv4_count':sum(':' not in ip for ip in ips),
                    'public_ipv6_count':sum(':' in ip for ip in ips),'production_first_family':'IPv6' if ':' in ips[0] else 'IPv4'})
        audit=probe(url,ips[0],'production_first_address',key,counts);results.append(audit)
        if key.startswith('facebook:'):
            facebook_default=(key,url,ips,audit)
    if facebook_default and facebook_default[3].get('http_status') is None and len(facebook_default[2])>1:
        key,url,ips,_=facebook_default
        alternate=next((ip for ip in ips[1:] if (':' in ip)!=(':' in ips[0])),ips[1])
        results.append(probe(url,alternate,'alternate_validated_dns_address',key,counts))
    controls=[]
    for platform in ('facebook','threads'):
        target=next((urls[k] for k in KEYS if k.startswith(platform+':') and k in urls),None)
        if not target:continue
        host=info(target)[0]
        candidates=[(k,url,info(url)[3]) for k,url in urls.items() if k.startswith(platform+':') and
                    info(url)[0]==host and info(url)[3] and info(url)[3]>time.time()+600 and k not in KEYS]
        if not candidates:
            controls.append({'platform':platform,'same_host_future_hint_control':'not_found'});continue
        key,url,_=max(candidates,key=lambda x:x[2])
        ips=safe_media.public_addresses(host)
        controls.append({'platform':platform,'key':key,'same_host_future_hint_control':'selected'})
        if counts['requests']<MAX_REQUESTS:
            results.append(probe(url,ips[0],'same_host_future_oe_hint_control',key,counts))
    report={'executed_at':datetime.now(TZ).isoformat(),'source_snapshot':'51e27179cc4fa3447ce9e011c2e7d194ad5a9520',
        'max_image_requests':MAX_REQUESTS,'image_http_requests':counts['requests'],'ai_requests':0,'actor_starts':0,
        'dns':dns,'probes':results,'controls':controls,'offline_corpus':corpus,
        'safety':'TLS hostname/certificate verification and existing public-IP/domain restrictions retained. No redirects, cookies, API credentials, URL rewriting or raw body/query/header output. At most 4096 bytes read per response; image prefixes are transport evidence, not completed image download or analysis.',
        'oe_note':'Timestamp hint only; semantics inferred only when corroborated by explicit CDN error marker, not independently documented.'}
    Remote(os.environ.pop('GH_TOKEN')).save('data/history_media_rootcause_20261111.json',report)
    print(json.dumps(report))

if __name__=='__main__':main()
