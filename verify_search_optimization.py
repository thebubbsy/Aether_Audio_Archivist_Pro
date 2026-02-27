import asyncio
import yt_dlp
import json
import sys

# Mocking the helper function that will be in the main app
def perform_search(query):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(f"ytsearch5:{query}", download=False)

async def main():
    query = "Rick Astley Never Gonna Give You Up"
    print(f"Searching for: {query}")

    try:
        # Simulate asyncio.to_thread call
        info = await asyncio.to_thread(perform_search, query)
        results = info.get('entries', [])

        print(f"Found {len(results)} results.")

        if not results:
            print("No results found!")
            return

        first = results[0]
        required_keys = ['id', 'url', 'title', 'duration']
        missing = [k for k in required_keys if k not in first]

        if missing:
            print(f"FAIL: Missing keys in result: {missing}")
            print(f"Available keys: {first.keys()}")
            sys.exit(1)

        print("SUCCESS: Result structure matches expectations.")
        print(f"First result: {first['title']} ({first['duration']}s)")
        print(f"URL: {first['url']}")
        print(f"ID: {first['id']}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
