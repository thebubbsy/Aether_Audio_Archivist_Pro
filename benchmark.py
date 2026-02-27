import sys
import asyncio
import json
import time
import yt_dlp

QUERIES = [
    "Mozart Symphony No. 40",
    "Beethoven Moonlight Sonata",
]

async def benchmark_subprocess():
    start = time.time()
    for query in QUERIES:
        search_cmd = [sys.executable, "-m", "yt_dlp", f"ytsearch5:{query}", "--dump-json", "--flat-playlist"]
        proc = await asyncio.create_subprocess_exec(*search_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        results = [json.loads(line) for line in stdout.decode().strip().split("\n") if line]
    return time.time() - start

def run_yt_dlp_search(query):
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
    start = time.time()
    for query in QUERIES:
        results = await asyncio.to_thread(run_yt_dlp_search, query)
    return time.time() - start

async def main():
    print("Running Benchmark (2 queries)...")

    print("Benchmarking Subprocess...")
    t_sub = await benchmark_subprocess()
    print(f"Subprocess time: {t_sub:.4f}s")

    print("Benchmarking API (in thread)...")
    t_api = await benchmark_api()
    print(f"API time: {t_api:.4f}s")

    if t_api > 0:
        print(f"Speedup: {t_sub / t_api:.2f}x")

if __name__ == "__main__":
    asyncio.run(main())
