import sys

new_css = """
    /* Theme Definitions */
    .theme-matrix {
        --bg-color: #050505;
        --fg-color: #00ff00;
        --panel-bg: #0a0a0a;
        --input-bg: #111111;
        --input-fg: #ffffff;
        --border-color: #00ff00;
        --button-bg: #004400;
        --button-fg: #ffffff;
        --text-muted: #88ff88;
        --header-bg: #1a1a1a;
        --log-bg: #000000;
        --log-fg: #00cc00;
    }

    .theme-cyberpunk {
        --bg-color: #050010;
        --fg-color: #00ffff;
        --panel-bg: #100020;
        --input-bg: #200040;
        --input-fg: #ffffff;
        --border-color: #ff00ff;
        --button-bg: #800080;
        --button-fg: #ffffff;
        --text-muted: #e0e0e0;
        --header-bg: #200040;
        --log-bg: #020005;
        --log-fg: #ff00ff;
    }

    .theme-molten {
        --bg-color: #050000;
        --fg-color: #ff4500;
        --panel-bg: #100000;
        --input-bg: #200000;
        --input-fg: #ffffff;
        --border-color: #ff4500;
        --button-bg: #8b0000;
        --button-fg: #ffffff;
        --text-muted: #ff8c00;
        --header-bg: #200000;
        --log-bg: #050000;
        --log-fg: #ffa500;
    }

    Screen {
        background: var(--bg-color);
        color: var(--fg-color);
    }

    #launchpad-box {
        align: center middle;
        height: auto;
        width: 70;
        border: heavy var(--border-color);
        padding: 1 3;
        background: var(--panel-bg);
    }

    Static {
        text-align: center;
        width: 100%;
        color: var(--fg-color);
        text-style: bold;
    }

    Label {
        margin-top: 1;
        color: var(--text-muted);
        text-style: italic;
    }

    Input {
        background: var(--input-bg);
        color: var(--input-fg);
        border: solid var(--border-color);
        margin-bottom: 2;
    }

    Select {
        margin-bottom: 2;
        border: solid var(--border-color);
        background: var(--input-bg);
        color: var(--input-fg);
    }

    #init-btn {
        width: 100%;
        background: var(--button-bg);
        color: var(--button-fg);
        border: solid var(--border-color);
        text-style: bold;
    }

    #main-container {
        height: 100%;
    }

    #table-container {
        height: 70%;
        border: solid var(--border-color);
    }

    #data-table {
        height: 1fr;
    }

    #action-bar {
        height: 3;
        background: var(--input-bg);
        align: center middle;
    }

    #go-btn {
        width: 100%;
        min-height: 1;
        background: var(--button-bg);
        color: var(--button-fg);
        border: none;
        text-style: bold;
    }

    #hacker-log {
        height: 30%;
        border-top: solid var(--border-color);
        background: var(--log-bg);
        color: var(--log-fg);
        padding-left: 1;
    }

    DataTable > .datatable--header {
        background: var(--header-bg);
        color: var(--fg-color);
        text-style: bold;
    }

    #stats-box {
        align: center middle;
        height: auto;
        width: 60;
        border: thick var(--border-color);
        padding: 1 3;
        background: var(--bg-color);
    }

    #stats-box Label {
        margin-top: 1;
        width: 100%;
        text-align: left;
    }

    #close-stats-btn {
        margin-top: 2;
        width: 100%;
        background: var(--button-bg);
        color: var(--button-fg);
        border: solid var(--border-color);
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

start_marker = '    CSS = """'
end_marker = '    """'
start_idx = content.find(start_marker)

if start_idx != -1:
    # Find the matching closing quotes for the CSS block
    # We search from just after the start_marker
    end_idx = content.find(end_marker, start_idx + len(start_marker))

    if end_idx != -1:
        # Reconstruct the file
        updated_content = content[:start_idx] + '    CSS = """' + new_css + content[end_idx:]

        with open('Aether_Audio_Archivist_Pro.py', 'w') as f:
            f.write(updated_content)
        print("CSS updated successfully.")
    else:
        print("Could not find end of CSS block.")
else:
    print("Could not find start of CSS block.")
