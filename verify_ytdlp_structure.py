import yt_dlp
import json

QUERY = "Rick Astley Never Gonna Give You Up"

def search_yt(q):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(f"ytsearch5:{q}", download=False)

info = search_yt(QUERY)
print(f"Type: {type(info)}")
if 'entries' in info:
    print(f"Entries count: {len(info['entries'])}")
    first = info['entries'][0]
    print(f"First entry keys: {first.keys()}")
    print(f"First entry duration: {first.get('duration')}")
    print(f"First entry title: {first.get('title')}")
    print(f"First entry url: {first.get('url')}")
    print(f"First entry id: {first.get('id')}")
else:
    print("No entries found")
