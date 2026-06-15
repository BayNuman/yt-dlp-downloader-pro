import unittest
from core.command_builder import (
    safe_get,
    sanitize_extra_args,
    build_command,
    effective_video_height
)

class DummyConfig:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestCommandBuilder(unittest.TestCase):

    def test_safe_get_dictionary(self):
        d = {"key": "value", "none_key": None}
        self.assertEqual(safe_get(d, "key", "default"), "value")
        self.assertEqual(safe_get(d, "none_key", "default"), "default")
        self.assertEqual(safe_get(d, "missing", "default"), "default")

    def test_safe_get_object(self):
        obj = DummyConfig(key="value", none_key=None)
        self.assertEqual(safe_get(obj, "key", "default"), "value")
        self.assertEqual(safe_get(obj, "none_key", "default"), "default")
        self.assertEqual(safe_get(obj, "missing", "default"), "default")

    def test_sanitize_extra_args_allowed(self):
        allowed = "--quiet --socket-timeout 30 --retries 5"
        sanitized = sanitize_extra_args(allowed)
        self.assertEqual(sanitized, ["--quiet", "--socket-timeout", "30", "--retries", "5"])

    def test_sanitize_extra_args_blocked_exec(self):
        blocked = "--exec 'rm -rf /'"
        sanitized = sanitize_extra_args(blocked)
        self.assertNotIn("--exec", sanitized)

    def test_sanitize_extra_args_blocked_postprocessor(self):
        # --post-processor-args is not in whitelisted SAFE_ARG_PREFIXES (only --postprocessor-args is)
        blocked = "--post-processor-args 'ffmpeg:-v quiet'"
        sanitized = sanitize_extra_args(blocked)
        self.assertNotIn("--post-processor-args", sanitized)

    def test_sanitize_extra_args_blocked_download_archive(self):
        blocked = "--download-archive /path/to/archive.txt"
        sanitized = sanitize_extra_args(blocked)
        self.assertNotIn("--download-archive", sanitized)

    def test_sanitize_extra_args_blocked_config_location(self):
        blocked = "--config-location /path/to/config.conf"
        sanitized = sanitize_extra_args(blocked)
        self.assertNotIn("--config-location", sanitized)

    def test_effective_video_height(self):
        item_best = {"video_profile": "Maksimum (Best)"}
        self.assertIsNone(effective_video_height(item_best))

        item_preset = {"video_profile": "Full HD (1080p)"}
        self.assertEqual(effective_video_height(item_preset), 1080)

        item_custom = {"video_profile": "Ozel (Custom)", "video_limit": "720"}
        self.assertEqual(effective_video_height(item_custom), 720)

        item_invalid = {"video_profile": "Ozel (Custom)", "video_limit": "invalid"}
        self.assertEqual(effective_video_height(item_invalid), 1080) # Fallback

    def test_build_command_video_default(self):
        item = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "Video",
            "video_profile": "Full HD (1080p)",
            "video_container": "mp4",
            "video_audio_codec": "AAC",
            "playlist": False,
            "metadata": True,
            "thumbnail_flag": False,
            "subs": False,
            "auto_subs": False,
            "restrict_names": False,
            "sponsorblock": False,
            "archive": False
        }
        cmd = build_command(item, "~/Downloads")
        self.assertIn("yt_dlp", cmd[2])
        self.assertIn("-P", cmd)
        self.assertIn("bv*[height<=?1080]+ba[acodec^=mp4a]/bv*[height<=?1080]+ba[ext=m4a]/bv*[height<=?1080]+ba/b[height<=?1080]", cmd)
        self.assertIn("--no-playlist", cmd)
        self.assertIn("--add-metadata", cmd)
        self.assertEqual(cmd[-1], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_build_command_audio(self):
        item = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "Audio",
            "audio_format": "mp3",
            "audio_quality": "Yuksek (320K)",
            "playlist": False,
            "metadata": False,
            "thumbnail_flag": True,
            "subs": False,
            "auto_subs": False,
            "restrict_names": False,
            "sponsorblock": False,
            "archive": False
        }
        cmd = build_command(item, "~/Downloads")
        self.assertIn("-x", cmd)
        self.assertIn("--audio-format", cmd)
        self.assertIn("mp3", cmd)
        self.assertIn("--audio-quality", cmd)
        self.assertIn("320K", cmd)
        self.assertIn("--write-thumbnail", cmd)
        self.assertIn("--embed-thumbnail", cmd)

if __name__ == "__main__":
    unittest.main()
