import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os
sys.path.append(os.getcwd())
from pathlib import Path

# Mock modules BEFORE importing the SUT
sys.modules['textual'] = MagicMock()
sys.modules['textual.app'] = MagicMock()
sys.modules['textual.widgets'] = MagicMock()
sys.modules['textual.containers'] = MagicMock()
sys.modules['textual.binding'] = MagicMock()
sys.modules['textual.screen'] = MagicMock()
sys.modules['textual.message'] = MagicMock()
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()
sys.modules['rich'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock() # Mock yt_dlp entire module to control it

# Define Screen mock class to avoid MagicMock inheritance issues
class MockScreen:
    def __init__(self):
        pass

sys.modules['textual.screen'].Screen = MockScreen

# Import SUT
import Aether_Audio_Archivist_Pro

class TestArchivistMethods(unittest.TestCase):
    def setUp(self):
        # We need to ensure Archivist uses our MockScreen
        # But Aether_Audio_Archivist_Pro.Archivist already inherited from whatever Screen was at import time
        # Check what Archivist inherits from
        # print(Aether_Audio_Archivist_Pro.Archivist.__bases__)

        self.archivist = Aether_Audio_Archivist_Pro.Archivist("http://url", "Library", 36, "cpu")
        # Ensure executor is a mock so we don't spawn threads
        self.archivist.executor = MagicMock()

    def test_search_yt(self):
        # We need to mock yt_dlp.YoutubeDL used inside the module
        # Since we mocked the whole yt_dlp module, Aether_Audio_Archivist_Pro.yt_dlp is a MagicMock
        mock_ydl_module = Aether_Audio_Archivist_Pro.yt_dlp
        mock_ydl_cls = mock_ydl_module.YoutubeDL
        mock_ydl_instance = mock_ydl_cls.return_value
        mock_ydl_instance.__enter__.return_value = mock_ydl_instance

        mock_ydl_instance.extract_info.return_value = {'entries': [{'id': '1', 'title': 'Song'}]}

        results = self.archivist._search_yt("query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Song')

        mock_ydl_instance.extract_info.assert_called_with("ytsearch5:query", download=False)

    def test_download_yt_cpu(self):
        mock_ydl_module = Aether_Audio_Archivist_Pro.yt_dlp
        mock_ydl_cls = mock_ydl_module.YoutubeDL
        # Reset mock
        mock_ydl_cls.reset_mock()

        mock_ydl_instance = mock_ydl_cls.return_value
        mock_ydl_instance.__enter__.return_value = mock_ydl_instance

        dest_path = Path("/path/to/Song.mp3")
        self.archivist._download_yt("http://video", dest_path, "Artist", "Title", "cpu")

        # Verify calls
        mock_ydl_cls.assert_called()
        opts = mock_ydl_cls.call_args[0][0]
        self.assertEqual(opts['outtmpl'], "/path/to/Song")

        ffmpeg_args = opts['postprocessor_args']['ffmpeg']
        self.assertIn("artist=Artist", ffmpeg_args)

        mock_ydl_instance.download.assert_called_with(["http://video"])

    def test_download_yt_gpu(self):
        mock_ydl_module = Aether_Audio_Archivist_Pro.yt_dlp
        mock_ydl_cls = mock_ydl_module.YoutubeDL
        mock_ydl_cls.reset_mock()

        mock_ydl_instance = mock_ydl_cls.return_value
        mock_ydl_instance.__enter__.return_value = mock_ydl_instance

        dest_path = Path("/path/to/Song.mp3")
        self.archivist._download_yt("http://video", dest_path, "Artist", "Title", "gpu")

        opts = mock_ydl_cls.call_args[0][0]
        ffmpeg_args = opts['postprocessor_args']['ffmpeg']
        self.assertIn("-hwaccel", ffmpeg_args)
        self.assertIn("cuda", ffmpeg_args)

if __name__ == '__main__':
    unittest.main()
