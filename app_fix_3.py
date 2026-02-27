import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    content = f.read()

content = content.replace("self.current_theme", "self.app_visual_theme")
content = content.replace("self.app.current_theme", "self.app.app_visual_theme")
content = content.replace("def current_theme(self)", "def app_visual_theme(self)")
content = content.replace("@current_theme.setter", "@app_visual_theme.setter")
content = content.replace("self._current_theme", "self._app_visual_theme")

# Also need to fix the __init__ logic order because  is not available in App.__init__
# Wait, inside App,  is the app. So  conflict is real.
# Renaming to  should solve it.

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.write(content)
print("Renamed theme property to avoid conflict.")
