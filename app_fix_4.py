import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    content = f.read()

content = content.replace("@app_visual_theme.setter\n    def current_theme(self, value):", "@app_visual_theme.setter\n    def app_visual_theme(self, value):")

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.write(content)
print("Corrected property setter name.")
