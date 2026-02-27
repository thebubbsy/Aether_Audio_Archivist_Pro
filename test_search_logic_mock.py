import asyncio
import sys
import unittest

# Mocking the functions to be in the app
def perform_youtube_search(query):
    # This mock represents the external function call
    # In real execution, this would call yt_dlp
    return {
        'entries': [
            {'id': '123', 'url': 'http://youtube.com/123', 'title': 'Test Video', 'duration': 120}
        ]
    }

async def ingest_worker_snippet(query):
    # Mimicking the async call inside ingest_worker
    info = await asyncio.to_thread(perform_youtube_search, query)
    results = info.get('entries', [])
    return results

class TestSearchLogic(unittest.IsolatedAsyncioTestCase):
    async def test_search_results(self):
        results = await ingest_worker_snippet("Test Query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], '123')
        self.assertEqual(results[0]['duration'], 120)

if __name__ == "__main__":
    unittest.main()
