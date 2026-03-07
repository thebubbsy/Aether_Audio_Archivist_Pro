import asyncio
import yt_dlp
from pathlib import Path
import os
import time

# Mocking the log system
def log_kernel(msg):
    print(f"[*] {msg}")

async def _dl_api_v2(url: str, opts: dict) -> bool:
    def _run_ydl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return True
    try:
        return await asyncio.to_thread(_run_ydl)
    except Exception as e:
        raise e

async def test_download():
    log_kernel("Starting test download with new pipeline logic...")
    
    # Use a short, reliable CC audio for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Roll for testing (often available)
    # Alternatively, a known shorter CC track if Rickroll is blocked
    # test_url = "https://www.youtube.com/watch?v=5qap5aO4i9A" # Lofi
    
    out_stem = Path("c:/temp/test_dl_item")
    out_path = out_stem.with_suffix(".mp3")
    
    if out_path.exists():
        out_path.unlink()
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': str(out_stem) + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': {
            'ffmpeg': [
                '-hwaccel', 'auto', 
                '-threads', '0', 
                '-acodec', 'libmp3lame'
            ]
        },
        'quiet': False, # Show output for debugging
        'no_warnings': False,
        'noplaylist': True,
    }

    try:
        log_kernel(f"Attempting download of {test_url}")
        ok = await asyncio.wait_for(_dl_api_v2(test_url, ydl_opts), timeout=120)
        if ok and out_path.exists():
            log_kernel(f"SUCCESS: Downloaded and converted to {out_path}")
            log_kernel(f"File size: {os.path.getsize(out_path) / 1024:.2f} KB")
        else:
            log_kernel("FAILURE: File not found after download.")
    except Exception as e:
        log_kernel(f"EXCEPTION: {e}")
    finally:
        # Cleanup
        if out_path.exists():
            # out_path.unlink() # Keep for a moment to check?
            pass
        # delete webm/m4a if they exist
        for ext in ['.webm', '.m4a']:
            p = out_stem.with_suffix(ext)
            if p.exists(): p.unlink()

if __name__ == "__main__":
    asyncio.run(test_download())
