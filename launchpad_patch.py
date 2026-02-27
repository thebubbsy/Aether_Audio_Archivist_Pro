import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_launchpad = False
in_compose = False
skip_engine_label = False
skip_engine_select = False

for i, line in enumerate(lines):
    if "class Launchpad(Screen):" in line:
        in_launchpad = True
        new_lines.append(line)
        continue

    if in_launchpad:
        if "def compose(self) -> ComposeResult:" in line:
            in_compose = True
            new_lines.append(line)
            continue

        if in_compose:
            if "Label(\"ENGINE ACCELERATION (NVIDIA GPU / CPU):\")," in line:
                new_lines.append(line)
                new_lines.append("            Select([(\"CPU (SYSTEM STANDARD)\", \"cpu\"), (\"GPU (NVIDIA CUDA)\", \"gpu\")], value=\"cpu\", id=\"engine-select\"),\n")
                new_lines.append("            Label(\"VISUAL THEME (CHROMA-SHIFT):\"),\n")
                new_lines.append("            Select([(\"MATRIX (DEFAULT)\", \"theme-matrix\"), (\"CYBERPUNK (NEON)\", \"theme-cyberpunk\"), (\"MOLTEN (CORE)\", \"theme-molten\")], value=\"theme-matrix\", id=\"theme-select\"),\n")
                skip_engine_select = True # The next line is the Select we want to replace/skip because we added it above
                continue

            if skip_engine_select:
                if "Select([(\"CPU (SYSTEM STANDARD)\", \"cpu\"), (\"GPU (NVIDIA CUDA)\", \"gpu\")], value=\"cpu\", id=\"engine-select\")," in line:
                    skip_engine_select = False
                    continue
                else:
                    # Should not happen based on file structure but just in case
                    skip_engine_select = False
                    new_lines.append(line)
                    continue

            if "id=\"launchpad-box\"" in line:
                in_compose = False
                in_launchpad = False # End of Launchpad modifications for compose
                new_lines.append(line)
                continue

    new_lines.append(line)

# Add the on_mount and on_select_changed handlers
final_lines = []
for line in new_lines:
    final_lines.append(line)
    if "        yield Footer()" in line and "class Launchpad" in "".join(new_lines[:new_lines.index(line)]):
        final_lines.append("\n    def on_mount(self) -> None:\n")
        final_lines.append("        self.add_class(self.app.current_theme)\n")
        final_lines.append("\n    @on(Select.Changed, \"#theme-select\")\n")
        final_lines.append("    def on_theme_change(self, event: Select.Changed) -> None:\n")
        final_lines.append("        new_theme = str(event.value)\n")
        final_lines.append("        self.remove_class(self.app.current_theme)\n")
        final_lines.append("        self.app.current_theme = new_theme\n")
        final_lines.append("        self.add_class(new_theme)\n")

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.writelines(final_lines)
print("Launchpad updated successfully.")
