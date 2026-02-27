import time
import sys
import subprocess
import json
import yt_dlp

QUERY = "Rick Astley Never Gonna Give You Up"

def test_subprocess():
    start = time.time()
    cmd = [sys.executable, "-m", "yt_dlp", f"ytsearch1:{QUERY}", "--dump-json", "--flat-playlist"]
    subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    end = time.time()
    return end - start

def test_library():
    start = time.time()
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(f"ytsearch1:{QUERY}", download=False)
    end = time.time()
    return end - start

if __name__ == "__main__":
    print("Running benchmarks...")

    # Warmup
    try:
        print("Warming up library...")
        test_library()
    except Exception as e:
        print(f"Library test failed: {e}")
        # sys.exit(1)

    print("Benchmarking subprocess...")
    sub_time = test_subprocess()
    print(f"Subprocess time: {sub_time:.4f}s")

    print("Benchmarking library...")
    lib_time = test_library()
    print(f"Library time:    {lib_time:.4f}s")

    print(f"Speedup: {sub_time / lib_time:.2f}x")
