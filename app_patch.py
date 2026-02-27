import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "def __init__(self, url=\"\", library=\"Aether_Archive\", threads=36):" in line:
        new_lines.append(line)
        new_lines.append("        super().__init__()\n")
        new_lines.append("        self.default_url = url\n")
        new_lines.append("        self.default_library = library\n")
        new_lines.append("        self.default_threads = threads\n")
        new_lines.append("        self.current_theme = \"theme-matrix\"\n")
    elif "super().__init__()" in line and "def __init__" in new_lines[-2]:
        continue # Skip the original super init line
    elif "self.default_url = url" in line and "def __init__" in new_lines[-3]:
        continue
    elif "self.default_library = library" in line and "def __init__" in new_lines[-4]:
        continue
    elif "self.default_threads = threads" in line and "def __init__" in new_lines[-5]:
        continue
    else:
        new_lines.append(line)

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.writelines(new_lines)
print("AetherApp updated successfully.")
