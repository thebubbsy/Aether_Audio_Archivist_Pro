import unittest
from unittest.mock import MagicMock, patch
import sys

# 1. Helper for decorators
def pass_through_decorator(*args, **kwargs):
    # This handles @on(event, selector) or @work(exclusive=True)
    def decorator(func):
        return func
    return decorator

# Handle @work (no args)
def work_decorator(func=None, **kwargs):
    if func:
        return func
    def decorator(f):
        return f
    return decorator

# 2. Mock dependencies *before* import
mock_playwright = MagicMock()
sys.modules["playwright"] = mock_playwright
sys.modules["playwright.async_api"] = MagicMock()

mock_ytdlp = MagicMock()
sys.modules["yt_dlp"] = mock_ytdlp

mock_rich = MagicMock()
sys.modules["rich"] = mock_rich

# 3. Mock Textual and its submodules
mock_textual = MagicMock()
# Assign pass-through decorators
mock_textual.on = pass_through_decorator
mock_textual.work = work_decorator

sys.modules["textual"] = mock_textual
sys.modules["textual.app"] = MagicMock()
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()
sys.modules["textual.message"] = MagicMock()

# 4. Create a FakeScreen for inheritance
class FakeScreen:
    def __init__(self, *args, **kwargs):
        pass
    def compose(self):
        pass

# Assign FakeScreen to textual.screen.Screen so Aether can import it
sys.modules["textual.screen"] = MagicMock()
sys.modules["textual.screen"].Screen = FakeScreen

# 5. Now import the module under test
# We suppress print because bootstrap_dependencies prints to stdout
with patch("builtins.print"):
    import Aether_Audio_Archivist_Pro as app_module

class TestLaunchpadValidation(unittest.TestCase):
    def setUp(self):
        # Mock Archivist class to prevent instantiation side effects (like mkdir)
        self.original_archivist = app_module.Archivist
        app_module.Archivist = MagicMock()

        # Create an instance of Launchpad
        self.launchpad = app_module.Launchpad()

        # Mock the app attribute usually injected by Textual
        self.launchpad.app = MagicMock()
        self.launchpad.app.default_url = "http://default"
        self.launchpad.app.default_threads = 36
        self.launchpad.app.default_library = "TestLib"

        # Mock query_one to return a mock that we can configure per test
        self.mock_query_one = MagicMock()
        self.launchpad.query_one = self.mock_query_one

    def tearDown(self):
        # Restore Archivist
        app_module.Archivist = self.original_archivist

    def test_start_archivist_empty_url(self):
        """Test that an error notification is shown when URL is empty."""
        def side_effect(selector):
            mock_widget = MagicMock()
            if selector == "#url-input":
                mock_widget.value = ""
            elif selector == "#threads-input":
                mock_widget.value = "10"
            elif selector == "#engine-select":
                mock_widget.value = "cpu"
            elif selector == "#library-input":
                mock_widget.value = "MyLib"
            return mock_widget

        self.mock_query_one.side_effect = side_effect

        # Execute
        self.launchpad.start_archivist()

        # Verify
        self.launchpad.app.notify.assert_called_with("CRITICAL: SOURCE URL MISSING", severity="error")
        self.launchpad.app.push_screen.assert_not_called()

    def test_start_archivist_invalid_threads(self):
        """Test that invalid thread count defaults to 36."""
        def side_effect(selector):
            mock_widget = MagicMock()
            if selector == "#url-input":
                mock_widget.value = "http://valid.url"
            elif selector == "#threads-input":
                mock_widget.value = "not_a_number"
            elif selector == "#engine-select":
                mock_widget.value = "cpu"
            elif selector == "#library-input":
                mock_widget.value = "MyLib"
            return mock_widget

        self.mock_query_one.side_effect = side_effect

        # Execute
        self.launchpad.start_archivist()

        # Verify
        self.launchpad.app.push_screen.assert_called()

        # Verify Archivist was initialized with default threads (36)
        app_module.Archivist.assert_called_with(
            "http://valid.url",
            "MyLib",
            36,
            "cpu"
        )

    def test_start_archivist_valid_input(self):
        """Test successful initialization with valid inputs."""
        def side_effect(selector):
            mock_widget = MagicMock()
            if selector == "#url-input":
                mock_widget.value = "http://valid.url"
            elif selector == "#threads-input":
                mock_widget.value = "42"
            elif selector == "#engine-select":
                mock_widget.value = "gpu"
            elif selector == "#library-input":
                mock_widget.value = "MyLib"
            return mock_widget

        self.mock_query_one.side_effect = side_effect

        # Execute
        self.launchpad.start_archivist()

        # Verify
        self.launchpad.app.push_screen.assert_called()

        # Verify Archivist was initialized with provided values
        app_module.Archivist.assert_called_with(
            "http://valid.url",
            "MyLib",
            42,
            "gpu"
        )

if __name__ == "__main__":
    unittest.main()
