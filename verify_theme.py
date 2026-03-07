import json
import os
from pathlib import Path
from Aether_Audio_Archivist_Pro import AetherApp

def test_theme_persistence():
    state_file = Path(os.getcwd()) / "session_state.json"
    if state_file.exists():
        state_file.unlink()

    # Test 1: Save theme
    app = AetherApp()
    app.visual_theme = "cyberpunk"
    app.save_session_state()
    
    assert state_file.exists(), "session_state.json was not created"
    with open(state_file, "r") as f:
        state = json.load(f)
        assert state["visual_theme"] == "cyberpunk", f"Expected cyberpunk, got {state['visual_theme']}"
    print("Test 1 (Save): SUCCESS")

    # Test 2: Load theme
    app2 = AetherApp()
    assert app2.visual_theme == "cyberpunk", f"Expected loaded theme cyberpunk, got {app2.visual_theme}"
    print("Test 2 (Load): SUCCESS")

    # Cleanup
    if state_file.exists():
        state_file.unlink()

if __name__ == "__main__":
    try:
        test_theme_persistence()
        print("Theme Persistence Verification: SUCCESS")
    except Exception as e:
        print(f"Theme Persistence Verification: FAILED - {e}")
        exit(1)
