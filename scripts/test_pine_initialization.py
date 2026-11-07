"""Compiler-size regression and exact data preservation, no provider requests."""
import unittest
from pathlib import Path
from pine_initialization import split_initialization,check_initialization,initialization_span
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
    def test_latest_complete_pine_uses_bounded_initialization(self):
        pine=(Path(__file__).resolve().parents[1]/'candidates/8zz-history-latest.pine').read_text()
        check=check_initialization(pine)
        self.assertEqual(check['first_bar_calls'],(len(EVENT_PATTERN.findall(pine))+19)//20)
        _,start,end=initialization_span(pine)
        self.assertNotIn('array.push(',pine[start:end])
if __name__=='__main__':unittest.main()
