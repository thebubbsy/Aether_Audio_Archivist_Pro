import sys

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)

    # Update Archivist.on_mount
    if "def on_mount(self) -> None:" in line:
        # Check context to ensure we are in Archivist class or StatsScreen class
        # But wait, we need to know WHICH class we are in.
        pass

# Let's do a more robust approach
final_lines = []
in_archivist = False
in_stats = False
in_archivist_mount = False
in_stats_mount = False # StatsScreen doesn't have on_mount yet

for i, line in enumerate(lines):
    if "class Archivist(Screen):" in line:
        in_archivist = True
        in_stats = False
    elif "class StatsScreen(Screen):" in line:
        in_stats = True
        in_archivist = False

    if in_archivist and "def on_mount(self) -> None:" in line:
        final_lines.append(line)
        final_lines.append("        self.add_class(self.app.current_theme)\n")
        continue

    if in_stats and "def compose(self) -> ComposeResult:" in line:
        # Add on_mount before compose if it doesn't exist, or just insert it into the class
        # Easier to just insert it after __init__ or before compose
        final_lines.append("\n    def on_mount(self) -> None:\n")
        final_lines.append("        self.add_class(self.app.current_theme)\n")
        final_lines.append("\n")
        final_lines.append(line)
        continue

    final_lines.append(line)

with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
    f.writelines(final_lines)
print("Screens updated successfully.")
