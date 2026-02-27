import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import os

# --- MOCK SETUP ---
class MockScreen:
    def __init__(self, *args, **kwargs):
        pass
    def query_one(self, *args, **kwargs):
        return MagicMock()
    def log_kernel(self, *args, **kwargs):
        pass
    def post_message(self, *args, **kwargs):
        pass

mock_textual = MagicMock()
sys.modules['textual'] = mock_textual
sys.modules['textual.app'] = MagicMock()
sys.modules['textual.widgets'] = MagicMock()
sys.modules['textual.containers'] = MagicMock()
sys.modules['textual.binding'] = MagicMock()
mock_textual_screen = MagicMock()
mock_textual_screen.Screen = MockScreen
sys.modules['textual.screen'] = mock_textual_screen
mock_textual_message = MagicMock()
class MockMessage:
    def __init__(self, *args, **kwargs):
        pass
mock_textual_message.Message = MockMessage
sys.modules['textual.message'] = mock_textual_message

def work_decorator(*args, **kwargs):
    def decorator(func):
        return func
    if args and callable(args[0]):
        return args[0]
    return decorator

mock_textual.work = work_decorator
mock_textual.on = MagicMock(return_value=lambda x: x)

# Mock Playwright module
sys.modules['playwright'] = MagicMock()
mock_playwright_async_api = MagicMock()
sys.modules['playwright.async_api'] = mock_playwright_async_api

# Define Exception classes for Playwright mocks so they can be caught
class MockPlaywrightError(Exception): pass
class MockPlaywrightTimeoutError(Exception): pass

# Assign them to the mocked module
mock_playwright_async_api.Error = MockPlaywrightError
mock_playwright_async_api.TimeoutError = MockPlaywrightTimeoutError

sys.modules['yt_dlp'] = MagicMock()
sys.modules['rich'] = MagicMock()

with patch('subprocess.check_call'):
    import Aether_Audio_Archivist_Pro

class TestScrapeException(unittest.IsolatedAsyncioTestCase):
    async def test_scrape_tracks_exception_swallowing(self):
        url = "http://example.com"
        library = "TestLib"

        archivist = Aether_Audio_Archivist_Pro.Archivist(url, library, 1, "cpu")
        archivist.col_keys = {"STATUS": "mock_status_key", "SEL": "mock_sel_key"}

        archivist.query_one = MagicMock()
        mock_table = MagicMock()
        archivist.query_one.return_value = mock_table
        archivist.log_kernel = MagicMock()

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright_ctx = AsyncMock()
        mock_playwright_ctx.__aenter__.return_value = mock_playwright
        mock_playwright_ctx.__aexit__.return_value = None

        mock_async_playwright_func = sys.modules['playwright.async_api'].async_playwright
        mock_async_playwright_func.side_effect = lambda: mock_playwright_ctx

        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        mock_row_bad = AsyncMock()
        mock_row_bad.query_selector.side_effect = RuntimeError("Unexpected Error in Row Processing")

        mock_page.query_selector_all.return_value = [mock_row_bad]

        with patch('asyncio.sleep', new=AsyncMock()):
            await asyncio.wait_for(archivist.scrape_tracks(), timeout=2.0)

        logs = [str(call.args[0]) for call in archivist.log_kernel.call_args_list]
        print(f"DEBUG LOGS (Unexpected): {logs}")

        error_logged = any("Unexpected Error in Row Processing" in log for log in logs)
        self.assertTrue(error_logged, "Exception should have been logged")

    async def test_scrape_tracks_playwright_exception_swallowing(self):
        url = "http://example.com"
        library = "TestLib"

        archivist = Aether_Audio_Archivist_Pro.Archivist(url, library, 1, "cpu")
        archivist.col_keys = {"STATUS": "mock_status_key", "SEL": "mock_sel_key"}

        archivist.query_one = MagicMock()
        mock_table = MagicMock()
        archivist.query_one.return_value = mock_table
        archivist.log_kernel = MagicMock()

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright_ctx = AsyncMock()
        mock_playwright_ctx.__aenter__.return_value = mock_playwright
        mock_playwright_ctx.__aexit__.return_value = None

        mock_async_playwright_func = sys.modules['playwright.async_api'].async_playwright
        mock_async_playwright_func.side_effect = lambda: mock_playwright_ctx

        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        mock_row_pw = AsyncMock()
        # MockPlaywrightError is defined in module scope from previous setup
        PlaywrightError = sys.modules['playwright.async_api'].Error
        mock_row_pw.query_selector.side_effect = PlaywrightError("Expected Playwright Error")

        mock_page.query_selector_all.return_value = [mock_row_pw]

        with patch('asyncio.sleep', new=AsyncMock()):
            await asyncio.wait_for(archivist.scrape_tracks(), timeout=2.0)

        logs = [str(call.args[0]) for call in archivist.log_kernel.call_args_list]
        print(f"DEBUG LOGS (Playwright): {logs}")

        error_logged = any("Expected Playwright Error" in log for log in logs)
        self.assertFalse(error_logged, "Playwright Error should have been swallowed (ignored)")

if __name__ == '__main__':
    unittest.main()
