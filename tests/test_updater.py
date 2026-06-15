import unittest
import os
import tempfile
import shutil
import hashlib
from unittest.mock import patch, MagicMock
from core.updater import (
    UpdatePayload,
    verify_hash_against_pypi,
    calculate_sha256,
    execute_update
)

class TestUpdaterIntegrity(unittest.TestCase):

    def setUp(self):
        self.scratch_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.scratch_dir)

    @patch("urllib.request.urlopen")
    def test_verify_hash_against_pypi_success(self, mock_urlopen):
        # Mock PyPI JSON response
        mock_response = MagicMock()
        mock_response.read.return_value = b"""
        {
            "urls": [
                {
                    "digests": {
                        "sha256": "abc123expectedhash"
                    }
                }
            ]
        }
        """
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Check positive match
        self.assertTrue(verify_hash_against_pypi("2026.06.09", "abc123expectedhash"))

        # Check case-insensitivity
        self.assertTrue(verify_hash_against_pypi("2026.06.09", "ABC123EXPECTEDHASH"))

        # Check mismatch
        self.assertFalse(verify_hash_against_pypi("2026.06.09", "wronghash"))

    @patch("urllib.request.urlopen")
    def test_verify_hash_against_pypi_error(self, mock_urlopen):
        # Mock network failure
        mock_urlopen.side_effect = Exception("Connection Refused")
        self.assertFalse(verify_hash_against_pypi("2026.06.09", "anyhash"))

    def test_calculate_sha256(self):
        temp_file = os.path.join(self.scratch_dir, "test_file.txt")
        content = b"hello updater"
        with open(temp_file, "wb") as f:
            f.write(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        self.assertEqual(calculate_sha256(temp_file), expected_hash)

    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    @patch("core.updater.verify_hash_against_pypi")
    def test_execute_update_sha256_mismatch_aborts(self, mock_pypi_verify, mock_urlopen, mock_subproc):
        # 1. Setup mock content
        mock_response = MagicMock()
        mock_response.read.return_value = b"malicious binary data"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # 2. Payload with an expected hash that differs from "malicious binary data"'s hash
        payload = UpdatePayload(
            current_version="2026.01.01",
            latest_version="2026.06.09",
            download_url="https://api.baynuman.com/downloads/yt-dlp.tar.gz",
            sha256="expected_good_hash_but_different",
            action="upgrade",
            is_fallback=False
        )

        success, msg = execute_update(payload, self.scratch_dir)
        
        # Should abort before calling pip install
        self.assertFalse(success)
        self.assertIn("Bütünlük Doğrulaması Başarısız", msg)
        mock_subproc.assert_not_called()

    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    @patch("core.updater.verify_hash_against_pypi")
    def test_execute_update_sha256_untrusted_source_aborts(self, mock_pypi_verify, mock_urlopen, mock_subproc):
        # 1. Setup mock content
        dummy_content = b"good update binary"
        computed_hash = hashlib.sha256(dummy_content).hexdigest()

        mock_response = MagicMock()
        mock_response.read.return_value = dummy_content
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # 2. PyPI verification returns False (untrusted source)
        mock_pypi_verify.return_value = False

        payload = UpdatePayload(
            current_version="2026.01.01",
            latest_version="2026.99.99", # Version not in KNOWN_VERSIONS
            download_url="https://api.baynuman.com/downloads/yt-dlp.tar.gz",
            sha256=computed_hash,
            action="upgrade",
            is_fallback=False
        )

        success, msg = execute_update(payload, self.scratch_dir)
        
        self.assertFalse(success)
        self.assertIn("güvenilmeyen bir kaynaktan", msg)
        mock_subproc.assert_not_called()

    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    @patch("core.updater.verify_hash_against_pypi")
    def test_execute_update_success_via_pypi(self, mock_pypi_verify, mock_urlopen, mock_subproc):
        # 1. Setup mock content
        dummy_content = b"good update binary"
        computed_hash = hashlib.sha256(dummy_content).hexdigest()

        mock_response = MagicMock()
        mock_response.read.return_value = dummy_content
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # 2. PyPI verification returns True
        mock_pypi_verify.return_value = True

        # Mock pip execution return code
        mock_subproc.return_value.returncode = 0

        payload = UpdatePayload(
            current_version="2026.01.01",
            latest_version="2026.07.01",
            download_url="https://api.baynuman.com/downloads/yt-dlp.tar.gz",
            sha256=computed_hash,
            action="upgrade",
            is_fallback=False
        )

        success, msg = execute_update(payload, self.scratch_dir)
        
        self.assertTrue(success)
        mock_subproc.assert_called_once()

if __name__ == "__main__":
    unittest.main()
