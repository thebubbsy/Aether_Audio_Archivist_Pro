import sys

new_block = """
                results = []
                for query in queries:
                    if results:
                        break
                    try:
                        # OPTIMIZED: Use yt_dlp directly via thread to avoid subprocess overhead
                        info = await asyncio.to_thread(perform_youtube_search, query)
                        results = info.get("entries", [])
                    except:
                        continue"""

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    lines = f.readlines()

# Find the start of the queries definition to locate where to insert/fix
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'queries = [' in line:
        start_idx = i
    if 'spotify_dur = self.parse_duration' in line and start_idx != -1:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    # We found the range. The queries definition ends with ']'
    # We want to keep the queries definition, but replace everything after it up to spotify_dur

    # Locate end of queries list
    queries_end = -1
    for i in range(start_idx, end_idx):
        if ']' in lines[i]:
            queries_end = i
            break

    if queries_end != -1:
        # Replace from queries_end + 1 to end_idx - 1
        lines[queries_end+1:end_idx] = [new_block + "\n"]

        with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
            f.writelines(lines)
        print("Fixed search block successfully.")
    else:
        print("Could not find end of queries list.")
else:
    print(f"Could not find block boundaries. Start: {start_idx}, End: {end_idx}")
