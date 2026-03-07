import sys
from unittest.mock import MagicMock

# Define dummy classes to allow inheritance
class MockScreen:
    def __init__(self, *args, **kwargs):
        pass

class MockApp:
    def __init__(self, *args, **kwargs):
        pass

# Mock dependencies that trigger installation or browser launch on import
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()

# Mock textual modules
textual_mock = MagicMock()
textual_mock.screen.Screen = MockScreen
textual_mock.app.App = MockApp
sys.modules["textual"] = textual_mock
sys.modules["textual.app"] = textual_mock.app
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()
sys.modules["textual.screen"] = textual_mock.screen
sys.modules["textual.message"] = MagicMock()
sys.modules["textual.work"] = MagicMock()
sys.modules["textual.on"] = MagicMock()

sys.modules["rich"] = MagicMock()
