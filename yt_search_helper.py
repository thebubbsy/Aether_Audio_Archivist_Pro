import yt_dlp

def perform_youtube_search(query):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(f"ytsearch5:{query}", download=False)
