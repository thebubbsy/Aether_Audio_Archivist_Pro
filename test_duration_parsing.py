import re

def parse_duration(d_str):
    import re
    try:
        # Format: "MM:SS" or "HH:MM:SS"
        if ":" in d_str:
            parts = d_str.split(":")
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        # Format: "X minutes Y seconds" or "X min Y sec"
        match = re.search(r'(\d+)\s*(?:minutes?|mins?)\s*(\d+)?\s*(?:seconds?|secs?)?', d_str, re.IGNORECASE)
        if match:
            mins = int(match.group(1))
            secs = int(match.group(2)) if match.group(2) else 0
            return mins * 60 + secs

    except: return 0
    return 0

test_cases = [
    ("3:43", 223),
    ("3 minutes 43 seconds", 223),
    ("3 mins 43 secs", 223),
    ("3 min", 180),
    ("1:03:43", 3823)
]

print("Running Duration Parsing Tests...")
for input_str, expected in test_cases:
    result = parse_duration(input_str)
    print(f"Input: '{input_str}' -> Parsed: {result} (Expected: {expected}) - {'PASS' if result == expected else 'FAIL'}")
