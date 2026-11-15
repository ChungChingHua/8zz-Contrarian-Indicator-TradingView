"""Public artifacts may contain provenance, never signed attachment queries. MPL-2.0."""
import urllib.parse

TEXT_FIELDS={'text','reason','tooltip','author_commentary','quoted_summary'}
POST_HOSTS={'facebook.com','www.facebook.com','threads.com','www.threads.com','threads.net','www.threads.net'}


def public_url(value):
    p=urllib.parse.urlsplit(value)
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443):return ''
    # Strip all authorization-bearing queries/fragments. Retain IDs separately in archive.
    query=urllib.parse.urlencode([(k,v) for k,v in urllib.parse.parse_qsl(p.query) if p.hostname in POST_HOSTS and k in ('id','fbid','story_fbid')])
    return urllib.parse.urlunsplit(('https',p.netloc,p.path,query,''))


def public_safe(value,key=''):
    if isinstance(value,dict):return {k:public_safe(v,k) for k,v in value.items()}
    if isinstance(value,list):return [public_safe(v,key) for v in value]
    if isinstance(value,str) and key not in TEXT_FIELDS and value.startswith(('https://','http://')):
        return public_url(value)
    return value
