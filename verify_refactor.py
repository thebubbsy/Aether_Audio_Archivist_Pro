import unicodedata

def _sanitise_filename(name: str) -> str:
    """Refactor: NFC-normalized, filesystem-safe filename preservation."""
    name = unicodedata.normalize('NFC', name)
    unsafe = set('<>:"/\\|?*')
    return "".join(c if c not in unsafe else "_" for c in name).strip()

def test_sanitization():
    # Test 1: Japanese characters (NFC preservation)
    name = "夜に駆ける.mp3"
    sanitized = _sanitise_filename(name)
    print(f"Original: {name} -> Sanitized: {sanitized}")
    assert sanitized == "夜に駆ける.mp3"

    # Test 2: Unsafe characters
    name = "Track: One? <Best> / album.mp3"
    sanitized = _sanitise_filename(name)
    print(f"Original: {name} -> Sanitized: {sanitized}")
    assert sanitized == "Track_ One_ _Best_ _ album.mp3"

    # Test 3: NFD to NFC normalization
    # 'e' + combining acute accent (NFD)
    nfd_name = "e\u0301dt.mp3"
    sanitized = _sanitise_filename(nfd_name)
    print(f"NFD: {nfd_name} -> Sanitized (NFC): {sanitized}")
    assert sanitized == unicodedata.normalize('NFC', nfd_name)

if __name__ == "__main__":
    test_sanitization()
    print("Sanitization Verification: SUCCESS")
