import sys
import asyncio
import json
import time

QUERIES = [
    "Mozart Symphony No. 40",
    "Beethoven Moonlight Sonata",
    "Bach Cello Suite No. 1",
    "Vivaldi Four Seasons",
    "Tchaikovsky 1812 Overture"
]

def run_yt_dlp_search(query):
    import yt_dlp
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)
        if 'entries' in info:
            return list(info['entries'])
        return []

async def benchmark_api():
    print(f"Benchmarking API with {len(QUERIES)} queries...")
    start = time.time()
    all_results = []

    for query in QUERIES:
        results = await asyncio.to_thread(run_yt_dlp_search, query)
        all_results.extend(results)

    duration = time.time() - start
    print(f"Total time: {duration:.4f}s")
    print(f"Average time per query: {duration / len(QUERIES):.4f}s")

    if all_results:
        sample = all_results[0]
        print("\nSample Result Keys:")
        print(list(sample.keys()))
        print("\nSample Result Data:")
        keys_to_show = ['id', 'url', 'title', 'duration']
        print({k: sample.get(k) for k in keys_to_show})

if __name__ == "__main__":
    asyncio.run(benchmark_api())
