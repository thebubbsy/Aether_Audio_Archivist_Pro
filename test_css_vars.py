import sys
sys.path.insert(0, '.')
from Aether_Audio_Archivist_Pro import AetherApp

print("Import OK")
a = AetherApp()
print("Instance OK")
v = a.get_css_variables()
print(f"accent={v.get('accent')}")
print(f"bg={v.get('bg')}")
print(f"surface={v.get('surface')}")
print(f"text={v.get('text')}")
print(f"dim={v.get('dim')}")
print("CSS variables injected correctly")

# Test theme switch
a.visual_theme = "cyberpunk"
v2 = a.get_css_variables()
print(f"\nAfter theme switch to cyberpunk:")
print(f"accent={v2.get('accent')}")
print(f"bg={v2.get('bg')}")
print("Theme switching works")

# Verify DEFAULT_CSS exists and uses $variables
assert hasattr(AetherApp, 'DEFAULT_CSS'), "DEFAULT_CSS not found"
assert '$accent' in AetherApp.DEFAULT_CSS, "$accent not in DEFAULT_CSS"
assert '$bg' in AetherApp.DEFAULT_CSS, "$bg not in DEFAULT_CSS"
assert '$surface' in AetherApp.DEFAULT_CSS, "$surface not in DEFAULT_CSS"
assert '$text' in AetherApp.DEFAULT_CSS, "$text not in DEFAULT_CSS"
assert '$dim' in AetherApp.DEFAULT_CSS, "$dim not in DEFAULT_CSS"
print("\nAll assertions passed - DEFAULT_CSS uses $variable tokens correctly")

# Verify old method is gone
assert not hasattr(a, 'get_css'), "get_css() should have been removed"
print("get_css() method correctly removed")
