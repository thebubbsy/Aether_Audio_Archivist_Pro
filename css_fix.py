import sys

# We will rewrite the CSS to be more explicit for each theme,
# overriding properties directly instead of using variables,
# to be safe with Textual's parser capabilities which might be limited in this version.

new_css = """
    Screen {
        background: #050505;
        color: #00ff00;
    }

    /* MATRIX THEME (Default) */
    .theme-matrix {
        background: #050505;
        color: #00ff00;
    }
    .theme-matrix #launchpad-box {
        border: heavy #00ff00;
        background: #0a0a0a;
    }
    .theme-matrix Static {
        color: #00ff00;
    }
    .theme-matrix Label {
        color: #88ff88;
    }
    .theme-matrix Input {
        background: #111111;
        color: #ffffff;
        border: solid #00ff00;
    }
    .theme-matrix Select {
        background: #111111;
        color: #ffffff;
        border: solid #00ff00;
    }
    .theme-matrix #init-btn {
        background: #004400;
        color: #ffffff;
        border: solid #00ff00;
    }
    .theme-matrix #table-container {
        border: solid #00ff00;
    }
    .theme-matrix #action-bar {
        background: #111111;
    }
    .theme-matrix #go-btn {
        background: #004400;
        color: #ffffff;
    }
    .theme-matrix #hacker-log {
        border-top: solid #00ff00;
        background: #000000;
        color: #00cc00;
    }
    .theme-matrix DataTable > .datatable--header {
        background: #1a1a1a;
        color: #00ff00;
    }
    .theme-matrix #stats-box {
        border: thick #00ff00;
        background: #050505;
    }
    .theme-matrix #close-stats-btn {
        background: #004400;
        color: #ffffff;
        border: solid #00ff00;
    }

    /* CYBERPUNK THEME */
    .theme-cyberpunk {
        background: #050010;
        color: #00ffff;
    }
    .theme-cyberpunk #launchpad-box {
        border: heavy #ff00ff;
        background: #100020;
    }
    .theme-cyberpunk Static {
        color: #00ffff;
    }
    .theme-cyberpunk Label {
        color: #e0e0e0;
    }
    .theme-cyberpunk Input {
        background: #200040;
        color: #ffffff;
        border: solid #ff00ff;
    }
    .theme-cyberpunk Select {
        background: #200040;
        color: #ffffff;
        border: solid #ff00ff;
    }
    .theme-cyberpunk #init-btn {
        background: #800080;
        color: #ffffff;
        border: solid #ff00ff;
    }
    .theme-cyberpunk #table-container {
        border: solid #ff00ff;
    }
    .theme-cyberpunk #action-bar {
        background: #200040;
    }
    .theme-cyberpunk #go-btn {
        background: #800080;
        color: #ffffff;
    }
    .theme-cyberpunk #hacker-log {
        border-top: solid #ff00ff;
        background: #020005;
        color: #ff00ff;
    }
    .theme-cyberpunk DataTable > .datatable--header {
        background: #200040;
        color: #00ffff;
    }
    .theme-cyberpunk #stats-box {
        border: thick #ff00ff;
        background: #050010;
    }
    .theme-cyberpunk #close-stats-btn {
        background: #800080;
        color: #ffffff;
        border: solid #ff00ff;
    }

    /* MOLTEN THEME */
    .theme-molten {
        background: #050000;
        color: #ff4500;
    }
    .theme-molten #launchpad-box {
        border: heavy #ff4500;
        background: #100000;
    }
    .theme-molten Static {
        color: #ff4500;
    }
    .theme-molten Label {
        color: #ff8c00;
    }
    .theme-molten Input {
        background: #200000;
        color: #ffffff;
        border: solid #ff4500;
    }
    .theme-molten Select {
        background: #200000;
        color: #ffffff;
        border: solid #ff4500;
    }
    .theme-molten #init-btn {
        background: #8b0000;
        color: #ffffff;
        border: solid #ff4500;
    }
    .theme-molten #table-container {
        border: solid #ff4500;
    }
    .theme-molten #action-bar {
        background: #200000;
    }
    .theme-molten #go-btn {
        background: #8b0000;
        color: #ffffff;
    }
    .theme-molten #hacker-log {
        border-top: solid #ff4500;
        background: #050000;
        color: #ffa500;
    }
    .theme-molten DataTable > .datatable--header {
        background: #200000;
        color: #ff4500;
    }
    .theme-molten #stats-box {
        border: thick #ff4500;
        background: #050000;
    }
    .theme-molten #close-stats-btn {
        background: #8b0000;
        color: #ffffff;
        border: solid #ff4500;
    }

    /* General Layout */
    #launchpad-box {
        align: center middle;
        height: auto;
        width: 70;
        padding: 1 3;
    }

    Static {
        text-align: center;
        width: 100%;
        text-style: bold;
    }

    Label {
        margin-top: 1;
        text-style: italic;
    }

    Input {
        margin-bottom: 2;
    }

    Select {
        margin-bottom: 2;
    }

    #init-btn {
        width: 100%;
        text-style: bold;
    }

    #main-container {
        height: 100%;
    }

    #table-container {
        height: 70%;
    }

    #data-table {
        height: 1fr;
    }

    #action-bar {
        height: 3;
        align: center middle;
    }

    #go-btn {
        width: 100%;
        min-height: 1;
        border: none;
        text-style: bold;
    }

    #hacker-log {
        height: 30%;
        padding-left: 1;
    }

    DataTable > .datatable--header {
        text-style: bold;
    }

    #stats-box {
        align: center middle;
        height: auto;
        width: 60;
        padding: 1 3;
    }

    #stats-box Label {
        margin-top: 1;
        width: 100%;
        text-align: left;
    }

    #close-stats-btn {
        margin-top: 2;
        width: 100%;
    }

    #resolve-box {
        align: center middle;
        height: auto;
        width: 80;
        border: heavy #ffff00;
        padding: 1 3;
        background: #0a0a0a;
    }

    #resolve-line-1, #resolve-line-2, #resolve-line-3 {
        color: #ffff00;
    }

    #spacer-a, #spacer-b {
        height: 1;
    }
    """

with open('Aether_Audio_Archivist_Pro.py', 'r') as f:
    content = f.read()

# Replace existing CSS block
start_marker = '    CSS = """'
end_marker = '    """'
start_idx = content.find(start_marker)

if start_idx != -1:
    end_idx = content.find(end_marker, start_idx + len(start_marker))
    if end_idx != -1:
        updated_content = content[:start_idx] + '    CSS = """' + new_css + content[end_idx:]
        with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
            f.write(updated_content)
        print("CSS fixed to use explicit class overrides.")
    else:
        print("Could not find end of CSS block.")
else:
    print("Could not find start of CSS block.")
