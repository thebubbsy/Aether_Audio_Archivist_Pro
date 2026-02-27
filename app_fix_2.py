import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "class AetherApp(App):" in line:
        new_lines.append(line)
    elif "    def __init__(self, url=\"\", library=\"Aether_Archive\", threads=36):" in line:
        new_lines.append(line)
        new_lines.append("        super().__init__()\n")
        new_lines.append("        self.default_url = url\n")
        new_lines.append("        self.default_library = library\n")
        new_lines.append("        self.default_threads = threads\n")
        new_lines.append("        self._current_theme = \"theme-matrix\"\n")
        new_lines.append("\n")
        new_lines.append("    @property\n")
        new_lines.append("    def current_theme(self):\n")
        new_lines.append("        return self._current_theme\n")
        new_lines.append("\n")
        new_lines.append("    @current_theme.setter\n")
        new_lines.append("    def current_theme(self, value):\n")
        new_lines.append("        self._current_theme = value\n")
        skip = True
    elif skip and "def on_mount(self) -> None:" in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.writelines(new_lines)
print("AetherApp fixed with property setters.")
