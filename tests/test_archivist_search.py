import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Create a fake textual module structure
class FakeScreen:
    BINDINGS = []
    def __init__(self, *args, **kwargs):
        pass
    def compose(self):
        yield MagicMock()
    def on_mount(self):
        pass

fake_textual = MagicMock()
fake_textual.screen.Screen = FakeScreen
fake_textual.app.App = MagicMock
fake_textual.widgets = MagicMock()
fake_textual.containers = MagicMock()
fake_textual.binding = MagicMock()
fake_textual.message = MagicMock()
fake_textual.work = MagicMock()
fake_textual.on = MagicMock()

sys.modules['textual'] = fake_textual
sys.modules['textual.app'] = fake_textual.app
sys.modules['textual.widgets'] = fake_textual.widgets
sys.modules['textual.containers'] = fake_textual.containers
sys.modules['textual.binding'] = fake_textual.binding
sys.modules['textual.screen'] = fake_textual.screen
sys.modules['textual.message'] = fake_textual.message
sys.modules['rich'] = MagicMock()
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()

# Now import the app
import Aether_Audio_Archivist_Pro as app

class TestArchivistSearch(unittest.TestCase):
    @patch('yt_dlp.YoutubeDL')
    @patch('pathlib.Path.mkdir')  # Prevent directory creation
    def test_search_youtube_api_returns_results(self, mock_mkdir, mock_ydl_cls):
        # Setup the mock for YoutubeDL context manager
        mock_instance = mock_ydl_cls.return_value
        mock_instance.__enter__.return_value = mock_instance

        # Setup return value
        mock_instance.extract_info.return_value = {
            'entries': [
                {'id': '123', 'url': 'http://test', 'title': 'Test Song', 'duration': 300}
            ]
        }

        # Instantiate Archivist
        archivist = app.Archivist("http://dummy", "TestLib", 1, "cpu")

        # Call the method
        results = archivist._search_youtube_api("Test Query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], '123')
        self.assertEqual(results[0]['title'], 'Test Song')

    @patch('yt_dlp.YoutubeDL')
    @patch('pathlib.Path.mkdir')
    def test_search_youtube_api_handles_empty_results(self, mock_mkdir, mock_ydl_cls):
        mock_instance = mock_ydl_cls.return_value
        mock_instance.__enter__.return_value = mock_instance

        mock_instance.extract_info.return_value = {}

        archivist = app.Archivist("http://dummy", "TestLib", 1, "cpu")

        results = archivist._search_youtube_api("Test Query")
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()
