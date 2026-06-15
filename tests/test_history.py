import unittest
import os
import tempfile
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import patch

# Clear any caching in core.history first before we test
import core.history

class TestHistoryDatabase(unittest.TestCase):

    def setUp(self):
        # 1. Create a isolated temp directory for our test database
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_history.db"

        # 2. Patch the get_db_path function to redirect to our temporary database
        self.db_path_patcher = patch("core.history.get_db_path", return_value=self.db_path)
        self.db_path_patcher.start()

        # 3. Clear any existing thread-local connections to start fresh
        if hasattr(core.history._local, "conn"):
            try:
                if core.history._local.conn:
                    core.history._local.conn.close()
            except Exception:
                pass
            core.history._local.conn = None

        # 4. Swap the global _db_writer with a new instance connected to the mocked DB path
        self.old_db_writer = core.history._db_writer
        core.history._db_writer = core.history.DatabaseWriter()

        # 5. Initialize schema in the temporary database
        core.history.init_db()

    def tearDown(self):
        # 1. Shutdown the test writer to release the connection to the temp DB
        try:
            core.history._db_writer.shutdown()
        except Exception:
            pass
        core.history._db_writer = self.old_db_writer

        # 2. Clear active connections
        if hasattr(core.history._local, "conn"):
            try:
                if core.history._local.conn:
                    core.history._local.conn.close()
            except Exception:
                pass
            core.history._local.conn = None

        # 3. Stop patcher
        self.db_path_patcher.stop()

        # 4. Physically delete the temporary test database folder
        shutil.rmtree(self.tmp_dir)

    def test_init_db_creates_tables(self):
        self.assertTrue(self.db_path.exists())
        
        # Verify schema is version 3 and tables exist
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        self.assertEqual(version, 3)

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("downloads", tables)
        self.assertIn("channel_rules", tables)
        conn.close()

    def test_database_writer_submits_and_flushes(self):
        # Submit a record to write asynchronously
        core.history.add_download_record(
            item_id="task_123",
            title="Rick Roll",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            format_desc="Video (1080p)",
            file_path="RickRoll.mp4",
            status="Completed",
            file_size=5000000,
            duration=212,
            thumbnail_path="thumb.jpg"
        )
        
        # Manually join/wait for the background queue to complete
        core.history._db_writer._queue.join()

        downloads = core.history.get_all_downloads()
        self.assertEqual(len(downloads), 1)
        record = downloads[0]
        self.assertEqual(record["id"], "task_123")
        self.assertEqual(record["title"], "Rick Roll")
        self.assertEqual(record["file_size_bytes"], 5000000)

    def test_update_download_status(self):
        core.history.add_download_record(
            item_id="task_update",
            title="Title",
            url="https://youtube.com/watch?v=123",
            format_desc="Video",
            file_path="path.mp4",
            status="Bekliyor"
        )
        core.history._db_writer._queue.join()

        # Update status
        core.history.update_download_status("task_update", "Completed", file_path="new_path.mp4", file_size=1234)
        core.history._db_writer._queue.join()

        downloads = core.history.get_all_downloads()
        self.assertEqual(len(downloads), 1)
        self.assertEqual(downloads[0]["status"], "Completed")
        self.assertEqual(downloads[0]["file_path"], "new_path.mp4")
        self.assertEqual(downloads[0]["file_size_bytes"], 1234)

    def test_channel_rule_save_delete(self):
        settings = {"mode": "Audio", "audio_format": "mp3"}
        core.history.save_channel_rule("UC123", "Cool Creator", settings)
        core.history._db_writer._queue.join()

        # Read rules
        rules = core.history.get_all_channel_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["channel_id"], "UC123")
        self.assertEqual(rules[0]["channel_name"], "Cool Creator")
        self.assertEqual(rules[0]["settings_dict"], settings)

        # Retrieve specific rule
        rule = core.history.get_channel_rule("UC123")
        self.assertIsNotNone(rule)
        self.assertEqual(rule["channel_name"], "Cool Creator")

        # Delete rule
        core.history.delete_channel_rule("UC123")
        core.history._db_writer._queue.join()

        self.assertEqual(len(core.history.get_all_channel_rules()), 0)

    def test_shutdown_flushes_pending_writes(self):
        # Create a separate, isolated DatabaseWriter to test shutdown draining
        from core.history import DatabaseWriter, _do_add_download_record
        
        writer = DatabaseWriter()
        
        # Enqueue 10 separate async writes
        for i in range(10):
            writer.submit(
                _do_add_download_record,
                item_id=f"id_{i}",
                title=f"Title {i}",
                url=f"https://youtube.com/watch?v={i}",
                format_desc="Video",
                file_path=f"file_{i}.mp4",
                status="Completed",
                file_size=1000,
                duration=100
            )

        # Call shutdown immediately, which should block and join the queue before terminating
        writer.shutdown()

        # Since shutdown blocks until all writes are completed and committed,
        # they must be present in the temporary database now
        downloads = core.history.get_all_downloads()
        self.assertEqual(len(downloads), 10)

if __name__ == "__main__":
    unittest.main()
