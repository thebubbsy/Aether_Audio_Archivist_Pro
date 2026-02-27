import sys
import unittest
from unittest.mock import MagicMock

# --- PRE-IMPORT MOCKING ---
# We mock heavy dependencies to avoid side effects during import
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()
sys.modules['yt_dlp'] = MagicMock()
sys.modules['rich'] = MagicMock()

# We need a fake Screen class for inheritance
class FakeScreen:
    def __init__(self): pass
    def compose(self): pass
    def query_one(self, *args, **kwargs): pass

class FakeMessage:
    def __init__(self): pass

# Mock textual modules structure
textual = MagicMock()
textual.screen = MagicMock()
textual.screen.Screen = FakeScreen
textual.message = MagicMock()
textual.message.Message = FakeMessage
textual.widgets = MagicMock()
textual.containers = MagicMock()
textual.binding = MagicMock()
textual.app = MagicMock()

# IMPORTANT: Define the specific exception we want to use for the fix verification
class CellDoesNotExist(Exception):
    pass

# Inject the exception into the mock module so it can be imported by the fix later
textual.widgets.data_table = MagicMock()
textual.widgets.data_table.CellDoesNotExist = CellDoesNotExist

sys.modules['textual'] = textual
sys.modules['textual.screen'] = textual.screen
sys.modules['textual.message'] = textual.message
sys.modules['textual.widgets'] = textual.widgets
sys.modules['textual.widgets.data_table'] = textual.widgets.data_table
sys.modules['textual.containers'] = textual.containers
sys.modules['textual.binding'] = textual.binding
sys.modules['textual.app'] = textual.app

# --- END MOCKING ---

try:
    import Aether_Audio_Archivist_Pro as target
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# Mock the DataTable behavior
class MockDataTable:
    def update_cell(self, row, col, value):
        if row == "raise_cell_error":
            raise CellDoesNotExist("Cell not found")
        if row == "raise_other_error":
            raise ValueError("Some other error")

# Subclass Archivist for testing
class TestArchivist(target.Archivist):
    def __init__(self):
        # Bypass original __init__ to avoid setup logic
        self.col_keys = {"STATUS": "status_col"}

    def query_one(self, widget_type):
        return MockDataTable()

def run_test():
    print("Running reproduction test...")
    archivist = TestArchivist()

    # Test 1: CellDoesNotExist (simulated via row key)
    # This represents the expected failure case (UI update fail).
    # Current code: catches everything -> PASS
    # Fixed code: catches CellDoesNotExist -> PASS
    print("Test 1: Raising CellDoesNotExist...")
    try:
        # We need a message object that has the attributes used in on_track_update
        msg = MagicMock()
        msg.index = "raise_cell_error"
        msg.status = "test"
        msg.color = "white"

        archivist.on_track_update(msg)
        print("PASS: CellDoesNotExist caught.")
    except Exception as e:
        print(f"FAIL: CellDoesNotExist NOT caught: {e}")
        return False

    # Test 2: ValueError (simulated via row key)
    # This represents an UNEXPECTED error that should propagate.
    # Current code: catches everything -> FAIL (Bug reproduced)
    # Fixed code: raises ValueError -> PASS
    print("Test 2: Raising ValueError...")
    try:
        msg = MagicMock()
        msg.index = "raise_other_error"
        msg.status = "test"
        msg.color = "white"

        archivist.on_track_update(msg)
        print("FAIL: ValueError caught (Bug reproduced).")
        return False
    except ValueError:
        print("PASS: ValueError raised (Bug fixed).")
        return True
    except Exception as e:
        print(f"FAIL: Wrong exception raised: {e}")
        return False

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
