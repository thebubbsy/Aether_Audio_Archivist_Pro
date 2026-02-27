import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

# --- 1. PRE-IMPORT MOCKING ---
# We must mock dependencies BEFORE importing the main module to:
# a) Bypass 'bootstrap_dependencies' which installs packages/runs browsers.
# b) Ensure 'Archivist' inherits from controllable fake classes, not MagicMocks (which break method resolution).

# Define Fake classes for Textual inheritance
class FakeScreen:
    """Fake Textual Screen to allow inheritance."""
    def __init__(self, *args, **kwargs):
        pass

    def query_one(self, *args, **kwargs):
        return MagicMock()

class FakeMessage:
    """Fake Textual Message to allow inheritance."""
    def __init__(self, *args, **kwargs):
        pass

class FakeApp:
    """Fake Textual App."""
    def __init__(self, *args, **kwargs):
        self.default_url = ""
        self.default_library = ""
        self.default_threads = 1

# Mock 'textual.screen'
mock_screen_module = MagicMock()
mock_screen_module.Screen = FakeScreen
sys.modules["textual.screen"] = mock_screen_module

# Mock 'textual.message'
mock_message_module = MagicMock()
mock_message_module.Message = FakeMessage
sys.modules["textual.message"] = mock_message_module

# Mock 'textual.app'
mock_app_module = MagicMock()
mock_app_module.App = FakeApp
sys.modules["textual.app"] = mock_app_module

# Mock other textual submodules
sys.modules["textual"] = MagicMock()
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()
sys.modules["textual.worker"] = MagicMock()

# Mock external tools
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()
sys.modules["rich"] = MagicMock()

# --- 2. IMPORT MODULE UNDER TEST ---
# patch subprocess.check_call to neutralize bootstrap_dependencies()
with patch("subprocess.check_call"):
    import Aether_Audio_Archivist_Pro as archivist

# --- 3. TEST SUITE ---
class TestArchivist(unittest.TestCase):

    def setUp(self):
        # Prevent directory creation during init
        # We need to mock Path.mkdir.
        # Note: In the module, 'Path' is imported 'from pathlib import Path'.
        # But 'os.getcwd' is also used.

        # We patch 'pathlib.Path.mkdir' globally for the test duration
        self.mkdir_patcher = patch("pathlib.Path.mkdir")
        self.mock_mkdir = self.mkdir_patcher.start()

        # Instantiate
        self.archivist = archivist.Archivist(
            url="http://test.url",
            library="TestLib",
            threads=4,
            engine="cpu"
        )

    def tearDown(self):
        self.mkdir_patcher.stop()

    def test_parse_duration(self):
        """Test the parse_duration method for various formats."""
        # MM:SS
        self.assertEqual(self.archivist.parse_duration("3:45"), 3 * 60 + 45)
        # H:MM:SS
        self.assertEqual(self.archivist.parse_duration("1:00:00"), 3600)
        # Invalid format
        self.assertEqual(self.archivist.parse_duration("invalid"), 0)
        # Empty string
        self.assertEqual(self.archivist.parse_duration(""), 0)
        # None (simulating potential edge case if passed)
        self.assertEqual(self.archivist.parse_duration(None), 0)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("os.getcwd", return_value="/tmp")
    @patch("pathlib.Path.exists", return_value=False)
    def test_save_mission_report(self, mock_exists, mock_getcwd, mock_json_dump, mock_file):
        """Test that the mission report is saved correctly."""

        # Setup dummy stats
        self.archivist.stats = {"total": 10, "complete": 5, "no_match": 2, "failed": 3}
        # Populate dummy tracks data
        self.archivist.tracks = [
            {"title": "Song A", "artist": "Artist A", "status": "COMPLETE"},
            {"title": "Song B", "artist": "Artist B", "status": "COMPLETE"}
        ]
        # Populate metrics
        self.archivist.track_times = {0: 120, 1: 180}
        self.archivist.track_sizes = {0: 1024, 1: 2048}

        # Run method
        self.archivist.save_mission_report(total_time=600.0)

        # Verify file opened for writing
        mock_file.assert_called()
        # Ensure it tried to write to the correct expected path
        # (Exact path depends on mock_getcwd, but we check the call arg structure)

        # Verify JSON structure passed to json.dump
        self.assertTrue(mock_json_dump.called)
        args, _ = mock_json_dump.call_args
        report_data_list = args[0]

        # Expecting a list (history)
        self.assertIsInstance(report_data_list, list)
        self.assertEqual(len(report_data_list), 1)

        report = report_data_list[0]

        # Verify Report Fields
        self.assertEqual(report["playlist_url"], "http://test.url")
        self.assertEqual(report["library"], "TestLib")
        self.assertEqual(report["total_time"], 600.0)
        self.assertEqual(report["stats"]["complete"], 5)

        # Check logic for 'largest_song'
        # Song B (index 1) is 2048 bytes, Song A (index 0) is 1024 bytes.
        self.assertEqual(report["largest_size_bytes"], 2048)
        self.assertEqual(report["largest_song"], "Song B")

        # Check averages
        # Avg = 600.0 / 5 (complete) = 120.0
        self.assertEqual(report["avg_time_per_song"], 120.0)

if __name__ == '__main__':
    unittest.main()
