import io
import json
import socket
import unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import ai_provider as provider
import safe_media as media
import social_pipeline as s
from public_safety import public_safe


class SecurityTests(unittest.TestCase):
    def test_pause_blocks_keys_models_and_transmission(self):
        import check_chatanywhere,run_social_update
        with patch.object(provider.os,'getenv',side_effect=AssertionError('must not read credentials')),patch.object(s.urllib.request,'urlopen',side_effect=AssertionError('network disabled')):
            for fn in (provider.credentials,check_chatanywhere.main,run_social_update.main):
                with self.assertRaisesRegex(RuntimeError,'paused'):fn()
            with self.assertRaisesRegex(RuntimeError,'paused'):s.request_json('https://api.chatanywhere.org/v1/models')

    def test_url_restrictions(self):
        for url in ('http://x.fbcdn.net/a','https://x.fbcdn.net.evil.test/a','https://evilfbcdn.net/a','https://user:pass@x.fbcdn.net/a','https://x.fbcdn.net:8443/a','https://127.0.0.1/a','https://x.fbcdn.net/a#fragment'):
            with self.subTest(url=url),self.assertRaises(ValueError):media.validate_url(url)
        self.assertEqual(media.validate_url('https://x.fbcdn.net/a?signature=test')[0],'x.fbcdn.net')

    def test_dns_private_and_mixed_records_rejected(self):
        for addresses in (['127.0.0.1'],['169.254.169.254'],['10.1.2.3'],['::1'],['fd00::1'],['8.8.8.8','10.1.2.3']):
            records=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in addresses]
            with patch.object(media.socket,'getaddrinfo',return_value=records),self.assertRaises(ValueError):media.public_addresses('x.fbcdn.net')

    def test_connect_pins_checked_ip_and_tls_host(self):
        conn=media.PinnedTLS('x.fbcdn.net','8.8.8.8')
        context=MagicMock();conn._context=context
        with patch.object(media.socket,'create_connection') as create:
            conn.connect()
            create.assert_called_once_with(('8.8.8.8',443),timeout=10)
            self.assertEqual(context.wrap_socket.call_args.kwargs['server_hostname'],'x.fbcdn.net')

    def test_no_redirect_or_html_or_oversize_images(self):
        for status,content_type,length in ((302,'image/jpeg','5'),(200,'text/html','5'),(200,'image/jpeg','8000001')):
            res=MagicMock(status=status);res.getheader.side_effect=lambda k,default='',ct=content_type,n=length:ct if k=='Content-Type' else n
            with patch.object(media,'assert_online_enabled'),patch.object(media.urllib.request,'getproxies',return_value={}),patch.object(media,'public_addresses',return_value=['8.8.8.8']),patch.object(media,'PinnedTLS') as cls:
                cls.return_value.getresponse.return_value=res
                with self.assertRaises(ValueError):media.download_image('https://x.fbcdn.net/a')
                cls.return_value.close.assert_called()

    def test_magic_matches_mime(self):
        self.assertFalse(media.valid_magic('image/png',b'<html>'))
        self.assertFalse(media.valid_magic('image/jpeg',b'\x89PNG\r\n\x1a\n'))
        self.assertTrue(media.valid_magic('image/jpeg',b'\xff\xd8\xffdata\xff\xd9'))

    def test_signed_urls_removed_without_rewriting_original_text(self):
        value={'text':'原文不能改 https://example.test/?id=1','attachments':[{'url':'https://x.fbcdn.net/a?oh=secret&oe=123#secret'}]}
        result=public_safe(value)
        self.assertEqual(result['text'],value['text'])
        self.assertEqual(result['attachments'][0]['url'],'https://x.fbcdn.net/a')

    def test_tool_call_is_rejected_not_executed(self):
        from test_social_pipeline import post
        with patch.object(provider,'assert_online_enabled'),patch.dict('os.environ',{'AI_PROVIDER':'openai','OPENAI_API_KEY':'test'}),patch.object(s,'request_json',return_value={'status':'completed','output':[{'type':'function_call','name':'read_secret'}]}):
            with self.assertRaisesRegex(ValueError,'tool_output_rejected'):s.classify(post())

    def test_workflow_no_secret_injection_or_write(self):
        text=(s.ROOT/'.github/workflows/fetch-fb-events.yml').read_text()
        self.assertNotIn('secrets.',text);self.assertNotIn('contents: write',text)
        self.assertNotIn('schedule:',text);self.assertNotIn('run_social_update.py',text)

if __name__=='__main__':unittest.main()
