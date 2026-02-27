import re

dur_regex = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$')

inputs = [
    "3:43",
    "03:43",
    "1:03:43",
    "3 minutes 43 seconds",
    "   3:43   ",
    "invalid",
    "12:34"
]

print("Regex Testing:")
for i in inputs:
    match = dur_regex.match(i.strip())
    print(f"'{i}': {bool(match)}")

def parse_duration(d_str):
    try:
        parts = d_str.split(":")
        if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except: return 0
    return 0

print("\nParse Duration Testing:")
for i in inputs:
    if dur_regex.match(i.strip()):
        print(f"'{i}': {parse_duration(i.strip())}")
