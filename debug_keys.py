import yt_dlp
import json

def run_yt_dlp_search(query):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)
        if 'entries' in info:
            entries = list(info['entries'])
            if entries:
                print(f"Keys for {query}:")
                print(list(entries[0].keys()))
            else:
                print(f"No entries for {query}")

run_yt_dlp_search("Mozart Symphony No. 40")
