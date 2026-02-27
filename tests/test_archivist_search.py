import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import asyncio
import json

# -------------------------------------------------------------------------
# MOCKING DEPENDENCIES BEFORE IMPORT
# -------------------------------------------------------------------------
sys.modules["textual"] = MagicMock()
sys.modules["textual.app"] = MagicMock()
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()
sys.modules["textual.screen"] = MagicMock()
sys.modules["textual.message"] = MagicMock()
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()
sys.modules["rich"] = MagicMock()

class MockScreen:
    def __init__(self, *args, **kwargs): pass
    def compose(self): pass
    def on_mount(self): pass
    def query_one(self, *args): return MagicMock()
    def mount(self, *args): pass
    def install_screen(self, *args): pass
    def push_screen(self, *args): pass
    def pop_screen(self, *args): pass
    def log_kernel(self, *args): pass
    def post_message(self, *args): pass
    def notify(self, *args): pass

sys.modules["textual.screen"].Screen = MockScreen
sys.modules["textual.message"].Message = object
sys.modules["textual"].work = lambda func=None, **kwargs: func if func else lambda f: f
sys.modules["textual"].on = lambda *args, **kwargs: lambda f: f

with patch("builtins.print"), patch("subprocess.check_call"):
    import Aether_Audio_Archivist_Pro

class TestArchivistSearch(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.archivist = Aether_Audio_Archivist_Pro.Archivist("http://url", "Library", 1, "cpu")
        self.archivist.log_kernel = MagicMock()

    async def test_search_successful(self):
        expected_results = [{"id": "123", "title": "Song", "duration": 180}]
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (json.dumps(expected_results[0]).encode(), b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await self.archivist._search_track_metadata("query")

        self.assertEqual(results, expected_results)

    async def test_search_json_error(self):
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"INVALID JSON", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await self.archivist._search_track_metadata("query")

        self.assertEqual(results, [])
        self.archivist.log_kernel.assert_called()
        self.assertIn("SEARCH EXCEPTION", self.archivist.log_kernel.call_args[0][0])

    async def test_search_process_error_nonzero_exit(self):
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"Error message")
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await self.archivist._search_track_metadata("query")

        self.assertEqual(results, [])
        self.archivist.log_kernel.assert_called()
        self.assertIn("SEARCH ERROR", self.archivist.log_kernel.call_args[0][0])

    async def test_search_propagates_keyboard_interrupt(self):
        with patch("asyncio.create_subprocess_exec", side_effect=KeyboardInterrupt("Simulated Ctrl+C")):
            with self.assertRaises(KeyboardInterrupt):
                await self.archivist._search_track_metadata("query")

if __name__ == "__main__":
    unittest.main()
