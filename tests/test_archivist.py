import unittest
from unittest.mock import MagicMock
import sys

# --- MOCKING INFRASTRUCTURE ---
sys.modules["textual"] = MagicMock()
sys.modules["textual.app"] = MagicMock()
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()
sys.modules["textual.work"] = MagicMock()
sys.modules["textual.on"] = MagicMock()
sys.modules["textual.message"] = MagicMock()

# Define FakeScreen to bypass inheritance issues
class FakeScreen:
    def __init__(self, *args, **kwargs):
        pass
    def compose(self):
        pass
    def on_mount(self):
        pass

mock_screen_module = MagicMock()
mock_screen_module.Screen = FakeScreen
sys.modules["textual.screen"] = mock_screen_module

sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()
sys.modules["rich"] = MagicMock()

import subprocess
original_check_call = subprocess.check_call
subprocess.check_call = MagicMock()

try:
    from Aether_Audio_Archivist_Pro import Archivist
finally:
    subprocess.check_call = original_check_call

class TestArchivist(unittest.TestCase):
    def setUp(self):
        self.archivist = Archivist("http://dummy.url", "dummy_lib", 1, "cpu")

    def test_parse_duration_valid(self):
        """Test valid duration strings."""
        self.assertEqual(self.archivist.parse_duration("2:30"), 150)
        self.assertEqual(self.archivist.parse_duration("02:30"), 150)
        self.assertEqual(self.archivist.parse_duration("1:01:01"), 3661)
        self.assertEqual(self.archivist.parse_duration("01:01:01"), 3661)
        self.assertEqual(self.archivist.parse_duration("0:00"), 0)

    def test_parse_duration_invalid(self):
        """Test invalid duration strings that currently return 0."""
        self.assertEqual(self.archivist.parse_duration("invalid"), 0)
        self.assertEqual(self.archivist.parse_duration(""), 0)
        self.assertEqual(self.archivist.parse_duration("::"), 0)
        self.assertEqual(self.archivist.parse_duration("12:34:56:78"), 0)
        self.assertEqual(self.archivist.parse_duration("1"), 0) # Assumes MM:SS min split

    def test_parse_duration_edge_cases(self):
        """Test edge cases."""
        self.assertEqual(self.archivist.parse_duration(None), 0)
        self.assertEqual(self.archivist.parse_duration(123), 0)
        # Test with negative numbers embedded in string if parser allows (current impl uses int() which handles negatives)
        # int("-1") is -1.
        # " -1:00 " -> split -> "-1", "00 " -> -60.
        # The logic: int("-1") * 60 + int("00") = -60.
        # This behavior is debatable but we test CURRENT behavior.
        self.assertEqual(self.archivist.parse_duration("-1:00"), -60)

if __name__ == '__main__':
    unittest.main()
