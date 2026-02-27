import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

# Mock dependencies before import
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

# IMPORTANT: Mock 'work' decorator to be a pass-through
def mock_work(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
sys.modules["textual"].work = mock_work

# Mock Screen class so Archivist can inherit from it
class FakeScreen:
    def __init__(self, *args, **kwargs):
        self._bindings = []
        self.app = MagicMock()

    def query_one(self, *args, **kwargs):
        return MagicMock()

    def log_kernel(self, message):
        pass

sys.modules["textual.screen"].Screen = FakeScreen

# Now import the module
import Aether_Audio_Archivist_Pro as archivist_module

class TestArchivist(unittest.TestCase):
    def setUp(self):
        self.url = "https://open.spotify.com/playlist/test"
        self.library = "TestLib"
        self.threads = 1
        self.engine = "cpu"
        self.archivist = archivist_module.Archivist(self.url, self.library, self.threads, self.engine)

        # Mock UI methods to avoid errors
        self.archivist.query_one = MagicMock()
        self.archivist.log_kernel = MagicMock()
        self.archivist.app = MagicMock()

    async def test_scrape_tracks_logic(self):
        # Mock Playwright
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # Setup the context manager for async_playwright
        mock_playwright_ctx = AsyncMock()
        mock_playwright_ctx.__aenter__.return_value = mock_playwright
        mock_playwright_ctx.__aexit__.return_value = None

        # Setup browser launch
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Setup page interactions
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.click = AsyncMock()

        # Mock finding rows
        mock_row = AsyncMock()
        mock_title = AsyncMock()
        mock_title.inner_text.return_value = "Test Song"

        mock_artist = AsyncMock()
        mock_artist.inner_text.return_value = "Test Artist"

        mock_dur = AsyncMock()
        mock_dur.inner_text.return_value = "3:30"

        # We need to mock the specific call for duration
        def query_selector_side_effect(selector):
            if 'tracklist-row-duration' in selector:
                return mock_dur
            if 'div[dir="auto"]' in selector:
                return mock_title
            return None

        mock_row.query_selector.side_effect = query_selector_side_effect
        mock_row.query_selector_all.return_value = [mock_artist]

        # First pass finds rows, second pass (after scroll) finds same rows (stable)
        # We need enough iterations to break the stability loop (10 times same count)
        mock_page.query_selector_all.side_effect = [[mock_row]] * 20

        with patch("playwright.async_api.async_playwright", return_value=mock_playwright_ctx):
            await self.archivist.scrape_tracks()

        # Verify tracks were added
        self.assertTrue(len(self.archivist.tracks) > 0)
        self.assertEqual(self.archivist.tracks[0]['title'], "Test Song")
        self.assertEqual(self.archivist.tracks[0]['artist'], "Test Artist")

    def test_run_async(self):
        asyncio.run(self.test_scrape_tracks_logic())

if __name__ == '__main__':
    unittest.main()
