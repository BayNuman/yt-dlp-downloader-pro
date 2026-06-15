import unittest
from core.profiles import (
    EXPORT_PROFILES,
    StandardProfile,
    SizeBoundedProfile,
    MemeGifProfile,
    AudiobookProfile,
    CenterCropProfile
)

class TestExportProfiles(unittest.TestCase):

    def test_standard_profile_mp4(self):
        profile = EXPORT_PROFILES["Default (No Profile)"]
        self.assertEqual(profile.name, "Default")
        self.assertEqual(profile.ext, "mp4")
        self.assertIsNone(profile.max_duration)
        
        args = profile.get_ffmpeg_args(60.0)
        self.assertEqual(args, ["-c:v", "copy", "-c:a", "copy"])

    def test_standard_profile_mp3(self):
        profile = StandardProfile("MP3 Audio", "mp3")
        args = profile.get_ffmpeg_args(60.0)
        self.assertIn("libmp3lame", args)
        self.assertIn("192k", args)

    def test_meme_gif_profile(self):
        profile = EXPORT_PROFILES["Meme / GIF Creator (No Audio, 15fps)"]
        self.assertEqual(profile.ext, "gif")
        args = profile.get_ffmpeg_args(5.0)
        self.assertIn("-an", args)
        self.assertIn("paletteuse", "".join(args))

    def test_audiobook_profile(self):
        profile = EXPORT_PROFILES["Voice Note / Audiobook (Mono, Light M4A)"]
        self.assertEqual(profile.ext, "m4a")
        args = profile.get_ffmpeg_args(300.0)
        self.assertIn("-ac", args)
        self.assertIn("1", args)
        self.assertIn("48k", args)

    def test_center_crop_profile(self):
        profile = EXPORT_PROFILES["YouTube Shorts (Max 60s, 9:16 Crop)"]
        self.assertEqual(profile.ext, "mp4")
        self.assertEqual(profile.max_duration, 60)
        args = profile.get_ffmpeg_args(15.0)
        self.assertIn("crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0", args)

    def test_size_bounded_profile_normal(self):
        # target_mb = 25 (Discord)
        profile = EXPORT_PROFILES["Discord Share (Max 25MB)"]
        self.assertEqual(profile.ext, "mp4")
        
        # 100 seconds video duration
        args = profile.get_ffmpeg_args(100.0)
        
        # Check that video and audio bitrate values are configured
        v_idx = args.index("-b:v")
        v_rate = args[v_idx + 1]
        self.assertTrue(v_rate.endswith("k"))
        v_val = int(v_rate[:-1])
        
        # Expected total size limit is 25MB (25 * 0.95 * 8192 = 194560 kb)
        # For 100s, total bitrate limit is 1945.6 kbps.
        # Audio is 96 kbps, Video should be around 1849 kbps
        self.assertAlmostEqual(v_val, 1849, delta=5)

    def test_size_bounded_profile_very_short_duration(self):
        # 1 second video duration
        profile = SizeBoundedProfile("Discord Share Test", target_mb=25)
        args = profile.get_ffmpeg_args(1.0)
        
        v_idx = args.index("-b:v")
        v_rate = args[v_idx + 1]
        v_val = int(v_rate[:-1])
        
        # For 1 second, total bitrate would be very high: (25 * 0.95 * 8192) / 1.0 = 194560 kbps.
        # Video bitrate: 194560 - 96 = 194464 kbps.
        self.assertAlmostEqual(v_val, 194464, delta=10)

    def test_size_bounded_profile_very_long_duration(self):
        # 10 hours video duration (36000 seconds)
        profile = SizeBoundedProfile("Discord Share Test", target_mb=25)
        args = profile.get_ffmpeg_args(36000.0)
        
        v_idx = args.index("-b:v")
        v_rate = args[v_idx + 1]
        v_val = int(v_rate[:-1])
        
        # For 36000 seconds, total bitrate would be extremely small: 194560 / 36000 = 5.4 kbps.
        # But we clamp video bitrate to a minimum of 100.0 kbps!
        self.assertEqual(v_val, 100)

if __name__ == "__main__":
    unittest.main()
