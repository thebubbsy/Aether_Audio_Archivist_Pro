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

async def benchmark_subprocess():
    print(f"Benchmarking subprocess with {len(QUERIES)} queries...")
    start = time.time()
    all_results = []

    for query in QUERIES:
        search_cmd = [sys.executable, "-m", "yt_dlp", f"ytsearch5:{query}", "--dump-json", "--flat-playlist"]
        proc = await asyncio.create_subprocess_exec(*search_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        results = [json.loads(line) for line in stdout.decode().strip().split("\n") if line]
        all_results.extend(results)

    duration = time.time() - start
    print(f"Total time: {duration:.4f}s")
    print(f"Average time per query: {duration / len(QUERIES):.4f}s")

    if all_results:
        sample = all_results[0]
        print("\nSample Result Keys:")
        print(list(sample.keys()))
        print("\nSample Result Data:")
        # Print a subset of keys to verify content
        keys_to_show = ['id', 'url', 'title', 'duration']
        print({k: sample.get(k) for k in keys_to_show})

if __name__ == "__main__":
    asyncio.run(benchmark_subprocess())
