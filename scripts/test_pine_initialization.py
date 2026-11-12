"""Compiler-size regression and exact data preservation, no provider requests."""
import unittest
from pathlib import Path
from pine_initialization import split_initialization,check_initialization,initialization_span,pack_event,unpack_rows,decoded_event,PAYLOAD,literal,BEGIN,END,DECODER
from update_pine_script import EVENT_PATTERN,build_push_block

class PineInitializationTests(unittest.TestCase):
    def script(self,count):
        return ('//@version=6\nvar int[] evt_time = array.new_int(0)\nif barstate.isfirst\n'+''.join(build_push_block({'unix_ms':1760000000000+i,'direction':(-1,0,1)[i%3],'strength':i%3+1,'tooltip':'引號 " 與反斜線 \\ 及\n換行','ticker':'2330.TW'}) for i in range(count))+'\n// unrelated runtime\nplot(close)\n')
    def test_growth_keeps_all_fields_order_and_runtime_identical(self):
        for count in (1,20,21,187,800):
            with self.subTest(count=count):
                before=self.script(count);after=split_initialization(before)
                self.assertEqual(EVENT_PATTERN.findall(before),EVENT_PATTERN.findall(after))
                s,_,e=initialization_span(before)
                self.assertTrue(after.startswith(before[:s]));self.assertTrue(after.endswith(before[e:]))
                check=check_initialization(after)
                self.assertLessEqual(check['max_events_per_function'],20)
                self.assertEqual(check['first_bar_calls'],(count+19)//20)
                self.assertEqual(split_initialization(after),after)
    def test_other_first_bar_logic_cannot_be_dropped_silently(self):
        text=self.script(1).replace('if barstate.isfirst\n','if barstate.isfirst\n    unexpected := 1\n')
        with self.assertRaisesRegex(ValueError,'non_event_logic'):split_initialization(text)
    def test_packed_fields_preserve_delimiters_percent_quotes_unicode_and_integer_timestamps(self):
        tip='痛苦 | ~ %0A %25 %7C " \\ \n\r\t 台積電😀'
        event=EVENT_PATTERN.findall(build_push_block({'unix_ms':1764721680000,'direction':-1,'strength':3,'tooltip':tip,'ticker':'X|Y~%25'}))[0]
        runtime=unpack_rows(pack_event(event))[0]
        self.assertEqual(runtime,decoded_event(event));self.assertEqual(runtime[3],tip.replace('\r','\n'))
        from pine_initialization import pack_field,unpack_field
        with self.assertRaisesRegex(ValueError,'carriage_return_must_be_normalized'):pack_field(tip)
        self.assertEqual(unpack_field(pack_field(tip.replace('\r','\n'))),tip.replace('\r','\n'))
        self.assertEqual(int(float(runtime[0])),1764721680000)
    def test_runtime_payload_or_decoder_tampering_is_rejected(self):
        script=split_initialization(self.script(2));payload=PAYLOAD.search(script)
        changed=script[:payload.start(1)]+payload.group(1).replace('1760000000000','1760000000001',1)+script[payload.end(1):]
        with self.assertRaisesRegex(ValueError,'runtime_event_mismatch'):check_initialization(changed)
        with self.assertRaisesRegex(ValueError,'modified_packed_decoder'):check_initialization(script.replace('str.tonumber(array.get(fields, 0))','str.tonumber(array.get(fields, 1))'))
    def test_large_unicode_payloads_split_below_string_limit(self):
        text=self.script(21).replace('2330.TW','台'*1800)
        result=split_initialization(text);checks=check_initialization(result)
        self.assertGreater(checks['first_bar_calls'],2)
        self.assertLessEqual(checks['max_payload_bytes'],30000)
        self.assertEqual(EVENT_PATTERN.findall(result),EVENT_PATTERN.findall(text))
    def test_executable_event_push_count_is_constant_as_history_grows(self):
        for count in (1,362,800):
            result=split_initialization(self.script(count))
            region=result[result.index(BEGIN):result.index(END)]
            executable='\n'.join(l for l in region.splitlines() if not l.lstrip().startswith('//'))
            self.assertEqual(executable.count('array.push('),5)
            self.assertEqual(check_initialization(result)['executable_array_push_statements'],5)
    def test_legacy_chunk_functions_upgrade_without_changing_events(self):
        text=self.script(2);start,body,end=initialization_span(text)
        old=text[:start]+BEGIN+'\ninitEvtChunk001() =>\n'+text[body:end]+'    0\n\nif barstate.isfirst\n    initEvtChunk001()\n'+END+'\n'+text[end:]
        before=EVENT_PATTERN.findall(old);result=split_initialization(old)
        self.assertEqual(EVENT_PATTERN.findall(result),before)
        self.assertEqual(check_initialization(result)['event_encoding'],'packed-v1')
    def test_latest_complete_pine_uses_bounded_initialization(self):
        pine=(Path(__file__).resolve().parents[1]/'candidates/8zz-history-latest.pine').read_text()
        check=check_initialization(pine)
        self.assertEqual(check['event_encoding'],'packed-v1')
        self.assertTrue(check['packed_event_round_trip'])
        self.assertEqual(check['first_bar_calls'],(len(EVENT_PATTERN.findall(pine))+19)//20)
        _,start,end=initialization_span(pine)
        self.assertNotIn('array.push(',pine[start:end])
if __name__=='__main__':unittest.main()
