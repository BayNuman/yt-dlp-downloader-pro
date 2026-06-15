import unittest
from core.clip import (
    parse_time_to_seconds,
    format_seconds_to_mmss,
    validate_clip_range,
    decide_clip_strategy,
    optimize_clip_intervals,
    MicroClip
)

class TestClipOperations(unittest.TestCase):

    def test_parse_time_to_seconds_seconds(self):
        self.assertEqual(parse_time_to_seconds("45"), 45.0)
        self.assertEqual(parse_time_to_seconds("12.34"), 12.34)
        self.assertIsNone(parse_time_to_seconds(""))
        self.assertIsNone(parse_time_to_seconds("   "))

    def test_parse_time_to_seconds_minutes(self):
        self.assertEqual(parse_time_to_seconds("1:30"), 90.0)
        self.assertEqual(parse_time_to_seconds("02:15.5"), 135.5)

    def test_parse_time_to_seconds_hours(self):
        self.assertEqual(parse_time_to_seconds("1:00:00"), 3600.0)
        self.assertEqual(parse_time_to_seconds("02:05:10.25"), 7510.25)

    def test_parse_time_to_seconds_invalid(self):
        self.assertIsNone(parse_time_to_seconds("abc"))
        self.assertIsNone(parse_time_to_seconds("1:2:3:4"))
        self.assertIsNone(parse_time_to_seconds("1:ab:3"))

    def test_format_seconds_to_mmss(self):
        self.assertEqual(format_seconds_to_mmss(90.0), "01:30.00")
        self.assertEqual(format_seconds_to_mmss(7510.25), "02:05:10.25")
        self.assertEqual(format_seconds_to_mmss(0.5), "00:00.50")

    def test_validate_clip_range_valid(self):
        start, end = validate_clip_range("00:10", "00:20", 100.0)
        self.assertEqual(start, 10.0)
        self.assertEqual(end, 20.0)

    def test_validate_clip_range_invalid_format(self):
        self.assertEqual(validate_clip_range("invalid", "00:20", 100.0), "err_clip_format")
        self.assertEqual(validate_clip_range("00:10", "invalid", 100.0), "err_clip_format")

    def test_validate_clip_range_negative(self):
        self.assertEqual(validate_clip_range("-00:10", "00:20", 100.0), "err_clip_negative")

    def test_validate_clip_range_order(self):
        self.assertEqual(validate_clip_range("00:20", "00:10", 100.0), "err_clip_order")
        self.assertEqual(validate_clip_range("00:10", "00:10", 100.0), "err_clip_order")

    def test_validate_clip_range_clamp_end(self):
        start, end = validate_clip_range("00:10", "02:00", 100.0)
        self.assertEqual(start, 10.0)
        self.assertEqual(end, 100.0)  # Clamped to total_duration

    def test_validate_clip_range_minimum(self):
        self.assertEqual(validate_clip_range("00:10", "00:10.4", 100.0), "err_clip_min")
        # 0.5s is valid
        start, end = validate_clip_range("00:10", "00:10.5", 100.0)
        self.assertEqual(start, 10.0)
        self.assertEqual(end, 10.5)

    def test_decide_clip_strategy_live(self):
        info = {"is_live": True}
        self.assertEqual(decide_clip_strategy(info, 10, 20), "full_trim")

    def test_decide_clip_strategy_stream_seek(self):
        info = {
            "is_live": False,
            "duration": 1000,
            "formats": [{"protocol": "https"}]
        }
        # 10% clip -> stream_seek
        self.assertEqual(decide_clip_strategy(info, 100, 200), "stream_seek")

    def test_decide_clip_strategy_hybrid(self):
        info = {
            "is_live": False,
            "duration": 1000,
            "formats": [{"protocol": "https"}]
        }
        # 30% clip -> hybrid
        self.assertEqual(decide_clip_strategy(info, 100, 400), "hybrid")

    def test_decide_clip_strategy_full_trim(self):
        info = {
            "is_live": False,
            "duration": 1000,
            "formats": [{"protocol": "https"}]
        }
        # 60% clip -> full_trim
        self.assertEqual(decide_clip_strategy(info, 100, 700), "full_trim")

    def test_decide_clip_strategy_no_seekable_protocol(self):
        info = {
            "is_live": False,
            "duration": 1000,
            "formats": [{"protocol": "m3u8"}]
        }
        # Even small clip should fall back to full download if protocol is not seekable
        self.assertEqual(decide_clip_strategy(info, 10, 20), "full_trim")

    def test_optimize_clip_intervals_empty(self):
        self.assertEqual(optimize_clip_intervals([]), [])

    def test_optimize_clip_intervals_merging(self):
        clips = [
            MicroClip("1", 10.0, 20.0, "Default", "out1"),
            MicroClip("2", 15.0, 30.0, "Default", "out2"),
            MicroClip("3", 45.0, 60.0, "Default", "out3"),
        ]
        macros = optimize_clip_intervals(clips, threshold_sec=10.0)
        self.assertEqual(len(macros), 2)
        # Macro 1: 10.0 to 30.0
        self.assertEqual(macros[0].start, 10.0)
        self.assertEqual(macros[0].end, 30.0)
        self.assertEqual(len(macros[0].micro_clips), 2)
        # Macro 2: 45.0 to 60.0
        self.assertEqual(macros[1].start, 45.0)
        self.assertEqual(macros[1].end, 60.0)
        self.assertEqual(len(macros[1].micro_clips), 1)

    def test_optimize_clip_intervals_near_threshold(self):
        clips = [
            MicroClip("1", 10.0, 20.0, "Default", "out1"),
            MicroClip("2", 28.0, 40.0, "Default", "out2"), # Gap of 8s <= threshold 10s
        ]
        macros = optimize_clip_intervals(clips, threshold_sec=10.0)
        self.assertEqual(len(macros), 1)
        self.assertEqual(macros[0].start, 10.0)
        self.assertEqual(macros[0].end, 40.0)

        # Gap of 12s > threshold 10s -> split
        clips2 = [
            MicroClip("1", 10.0, 20.0, "Default", "out1"),
            MicroClip("2", 32.0, 40.0, "Default", "out2"),
        ]
        macros2 = optimize_clip_intervals(clips2, threshold_sec=10.0)
        self.assertEqual(len(macros2), 2)

if __name__ == "__main__":
    unittest.main()
