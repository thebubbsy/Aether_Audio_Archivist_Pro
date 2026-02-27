import asyncio
import yt_dlp
import sys
from datetime import datetime

# Helper function as implemented in Aether_Audio_Archivist_Pro.py
def perform_youtube_search(query):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(f"ytsearch5:{query}", download=False)

async def test_search():
    query = "Rick Astley Never Gonna Give You Up"
    print(f"Testing search for: {query}")

    start = datetime.now()
    try:
        # Simulate asyncio.to_thread call as used in the app
        info = await asyncio.to_thread(perform_youtube_search, query)
        results = info.get("entries", [])

        duration = (datetime.now() - start).total_seconds()
        print(f"Search completed in {duration:.2f}s")
        print(f"Found {len(results)} results")

        if len(results) == 0:
            print("FAIL: No results found")
            sys.exit(1)

        first = results[0]
        # Verify keys needed by the rest of the application
        needed_keys = ['duration', 'title', 'url', 'id']
        missing = [k for k in needed_keys if k not in first]

        if missing:
            print(f"FAIL: Missing keys: {missing}")
            print(f"Available keys: {first.keys()}")
            sys.exit(1)

        print("SUCCESS: Search results have correct structure")
        print(f"Sample: {first['title']} ({first['duration']}s)")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_search())
