import sys
import asyncio
import time
from unittest.mock import MagicMock

# Mock dependencies to allow Aether_Audio_Archivist_Pro to import
sys.modules['textual'] = MagicMock()
sys.modules['textual.app'] = MagicMock()
sys.modules['textual.widgets'] = MagicMock()
sys.modules['textual.containers'] = MagicMock()
sys.modules['textual.binding'] = MagicMock()
sys.modules['textual.screen'] = MagicMock()
sys.modules['textual.message'] = MagicMock()
sys.modules['rich'] = MagicMock()
sys.modules['playwright'] = MagicMock()
sys.modules['playwright.async_api'] = MagicMock()

# Import the module
import Aether_Audio_Archivist_Pro as app

# Mock Screen since Archivist inherits from it
class MockScreen:
    def __init__(self, *args, **kwargs):
        pass

app.Screen = MockScreen
# Re-define Archivist to use MockScreen if needed, but since we imported it,
# we might need to patch it or just use the method directly if it's not bound to complex state.
# However, the method is an instance method.

# Let's instantiate Archivist.
# We need to mock the constructor to avoid side effects like directory creation if we don't want them,
# but the constructor does create dirs. Let's let it or mock Path.
# Ideally we just want to test _search_youtube_api.

async def verify():
    print("Verifying optimization...")

    # Instantiate Archivist with dummy values
    archivist = app.Archivist("http://dummy", "TestLib", 1, "cpu")

    queries = [
        "Mozart Symphony No. 40",
        "Beethoven Moonlight Sonata",
        "Bach Cello Suite No. 1",
        "Vivaldi Four Seasons",
        "Tchaikovsky 1812 Overture"
    ]

    start = time.time()
    for query in queries:
        # Use the method directly via asyncio.to_thread as the app does
        results = await asyncio.to_thread(archivist._search_youtube_api, query)

        if not results:
            print(f"WARNING: No results for {query}")
        else:
            # Verify structure
            first = results[0]
            required_keys = ['id', 'url', 'title', 'duration']
            missing = [k for k in required_keys if k not in first]
            if missing:
                print(f"ERROR: Missing keys in result: {missing}")
                return

    duration = time.time() - start
    print(f"Total time (Optimization): {duration:.4f}s")
    print(f"Average time per query: {duration / len(queries):.4f}s")
    print("Verification passed: Structure is correct and code runs.")

if __name__ == "__main__":
    asyncio.run(verify())
