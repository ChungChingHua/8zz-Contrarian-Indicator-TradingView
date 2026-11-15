"""Bounded image transport: no redirects, public-IP pinning, TLS hostname checks. MPL-2.0."""
import http.client
import ipaddress
import socket
import ssl
import time
import threading
import urllib.parse
import urllib.request
from ai_provider import assert_online_enabled

MAX_BYTES=8_000_000


def validate_url(url):
    p=urllib.parse.urlsplit(url)
    host=p.hostname or ''
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443) or p.fragment:
        raise ValueError('unsafe_media_url')
    if not any(host.endswith('.'+d) for d in ('fbcdn.net','cdninstagram.com')):
        raise ValueError('unsupported_image_host')
    return host,p.path or '/',p.query


def public_addresses(host):
    ips=list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError('non_public_media_address')
    return ips


class PinnedTLS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,443,timeout=10,context=ssl.create_default_context())
        self.checked_ip=ip
    def connect(self):
        # The actual connection uses the checked address; no second hostname lookup.
        sock=socket.create_connection((self.checked_ip,443),timeout=self.timeout)
        try:self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except BaseException:
            sock.close();raise


def valid_magic(mime,data):
    return ((mime=='image/jpeg' and data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9')) or
            (mime=='image/png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or
            (mime=='image/webp' and data.startswith(b'RIFF') and data[8:12]==b'WEBP'))


def download_image(url):
    host,path,query=validate_url(url)
    assert_online_enabled()
    # Do not bypass a configured proxy. A reviewed proxy-aware transport is required there.
    if any(urllib.request.getproxies().get(k) for k in ('http','https')):
        raise ValueError('media_proxy_transport_requires_review')
    ips=public_addresses(host)
    start=time.monotonic()
    conn=PinnedTLS(host,ips[0])
    def abort():
        sock=getattr(conn,'sock',None)
        if sock is not None:
            try:sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        conn.close()
    deadline=threading.Timer(30,abort)
    deadline.daemon=True
    deadline.start()
    try:
        conn.request('GET',path+('?' +query if query else ''),headers={'Accept':'image/jpeg,image/png,image/webp','Connection':'close'})
        res=conn.getresponse()
        if res.status!=200:raise ValueError('media_http_status_rejected')
        mime=res.getheader('Content-Type','').split(';')[0].strip().lower()
        if mime not in ('image/jpeg','image/png','image/webp'):raise ValueError('unsupported_image_format')
        length=res.getheader('Content-Length')
        if length is not None and (not length.isdigit() or int(length)>MAX_BYTES):raise ValueError('image_too_large')
        chunks=[];size=0
        while True:
            if time.monotonic()-start>30:raise ValueError('image_total_timeout')
            chunk=res.read1(min(65536,MAX_BYTES+1-size))
            if not chunk:break
            size+=len(chunk)
            if size>MAX_BYTES:raise ValueError('image_too_large')
            chunks.append(chunk)
        data=b''.join(chunks)
        if length is not None and size!=int(length):raise ValueError('image_length_mismatch')
        if not valid_magic(mime,data):raise ValueError('invalid_image_magic')
        return mime,data
    finally:
        deadline.cancel()
        conn.close()
