import os
import sys
import asyncio
import json
import random
import subprocess
import functools
import re
import math
import signal
import unicodedata
import urllib.request
from io import BytesIO
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime
import traceback
import yt_dlp

# ARCHITECT: MATTHEW BUBB (SOLE PROGRAMMER)
# ==============================================================================

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DUR_REGEX = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$')

def bootstrap_dependencies():
    """Ensure system vectors are aligned."""
    # Frozen EXE mode: all deps are bundled, just configure paths
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
        ffmpeg_dir = bundle_dir / "ffmpeg_bundle"
        if ffmpeg_dir.exists():
            os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
        pw_dir = bundle_dir / "playwright_browser"
        if pw_dir.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(pw_dir)
        return

    print("[*] SYNCING SYSTEM VECTORS (BOOTSTRAPPING)...")
    deps = ["playwright", "yt-dlp", "textual", "rich", "mutagen", "Pillow"]
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "-q"])
    
    # Playwright browser validation
    try:
        from playwright.async_api import async_playwright
        async def check_playwright():
            async with async_playwright() as p:
                try:
                    await p.chromium.launch()
                except Exception:
                    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        asyncio.run(check_playwright())
    except Exception:
        pass

# Initialize environment
bootstrap_dependencies()

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Log, Input, Button, Label, Static, Select, ProgressBar
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual.reactive import reactive
from textual import work, on
from textual.screen import Screen
from textual.message import Message
from textual.widget import Widget
from textual.strip import Strip
from rich.text import Text
from rich.segment import Segment
from rich.style import Style

# ── Optional dependencies (gracefully degrade if unavailable) ──
try:
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, APIC, TDRC, ID3NoHeaderError
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

try:
    from PIL import Image
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# ── Constants ──────────────────────────────────────────────────
BLOCKLIST_TERMS = frozenset([
    'podcast', 'mix', 'compilation', 'full album', 'hour', 'hrs',
    'mashup', 'megamix', 'medley', 'karaoke', 'instrumental only',
])

STATUS_MAP = {
    "WAITING FOR PROPAGATION": ("[ WAIT ]", "yellow"),
    "MATCHING":                ("[ SRCH ]", "cyan"),
    "QUEUED":                  ("[ REDY ]", "bright_white"),
    "ARCHIVING":               ("[ ARCH ]", "bright_cyan"),
    "COMPLETE":                ("[ DONE ]", "bright_green"),
    "FAILED":                  ("[ FAIL ]", "bright_red"),
    "NO MATCH":                ("[ MISS ]", "orange1"),
    "AWAITING USER DECISION":  ("[ USER ]", "bright_yellow"),
    "ALREADY ARCHIVED":        ("[ SKIP ]", "green"),
}

_SEARCH_CACHE: dict = {}

# ── Helper functions ───────────────────────────────────────────
def _is_blocked(title: str) -> bool:
    """P17: Filter podcast/mix/compilation results."""
    t = title.lower()
    return any(term in t for term in BLOCKLIST_TERMS)

def _score_result(result: dict, track: dict, spotify_dur: int) -> float:
    """P15: Multi-signal scorer — duration 60%, title 30%, views 10%."""
    dur = result.get('duration', 0) or 0
    title = result.get('title', '').lower()
    dur_diff = abs(dur - spotify_dur)
    if dur_diff > 90:
        dur_score = 0.0
    elif dur_diff > 30:
        dur_score = 0.3 * (1.0 - (dur_diff - 30) / 60.0)
    else:
        dur_score = 1.0 - (dur_diff / 30.0) * 0.3
    search_str = f"{track.get('artist','')} {track.get('title','')}".lower()
    title_score = SequenceMatcher(None, search_str, title).ratio()
    views = result.get('view_count', 0) or 0
    view_score = min(math.log10(max(views, 1)) / 8.0, 1.0)
    return (dur_score * 0.60) + (title_score * 0.30) + (view_score * 0.10)

def _sanitise_filename(name: str) -> str:
    """Refactor: NFC-normalized, filesystem-safe filename preservation."""
    name = unicodedata.normalize('NFC', name)
    unsafe = set('<>:"/\\|?*')
    return "".join(c if c not in unsafe else "_" for c in name).strip()

def _fetch_art(thumbnail_url: str) -> bytes | None:
    """P37: Fetch and resize album art thumbnail."""
    if not PILLOW_OK or not thumbnail_url:
        return None
    try:
        req = urllib.request.Request(thumbnail_url, headers={'User-Agent': DEFAULT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        img = Image.open(BytesIO(data)).convert('RGB').resize((500, 500), Image.LANCZOS)
        out = BytesIO()
        img.save(out, format='JPEG', quality=85)
        return out.getvalue()
    except Exception:
        return None

def _make_ratio_bar(complete: int, no_match: int, failed: int, total: int, width: int = 38) -> Text:
    """P28: ASCII proportion bar for StatsScreen."""
    if total == 0:
        return Text("─" * width, style="dim")
    c_w = int((complete / total) * width)
    n_w = int((no_match / total) * width)
    f_w = max(width - c_w - n_w, 0)
    bar = Text()
    bar.append("█" * c_w, style="bright_green")
    bar.append("▓" * n_w, style="yellow")
    bar.append("░" * f_w, style="red")
    return bar

# ── MiniSparkline Widget (P21) ──────────────────────────────────
class MiniSparkline(Widget):
    """Refined throughput monitor using Rich Segment API."""
    DEFAULT_CSS = "MiniSparkline { height: 1; width: 24; }"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._events: list[float] = []

    def push_event(self) -> None:
        self._events.append(datetime.now().timestamp())
        self.refresh()

    def render_line(self, y: int) -> Strip:
        if y != 0:
            return Strip.blank(self.size.width)
        now = datetime.now().timestamp()
        self._events = [e for e in self._events if now - e < 60]
        width = self.size.width
        if not self._events:
            return Strip([Segment("▬" * width, Style(color="#333333"))])
        buckets = [0] * width
        for e in self._events:
            idx = min(width - 1, int((now - e) / (60 / width)))
            buckets[width - 1 - idx] += 1
        mx = max(buckets) or 1
        blocks = " ▂▃▄▅▆▇█"
        segments = []
        for v in buckets:
            bi = int((v / mx) * (len(blocks) - 1))
            char = blocks[bi]
            color = "bright_green" if bi > 4 else "green"
            segments.append(Segment(char, Style(color=color)))
        return Strip(segments)

def render_status_badge(status: str) -> Text:
    """Fixed-width status badging with architect aesthetics."""
    badge_data = STATUS_MAP.get(status, ("[ ???? ]", "white"))
    label, color = badge_data
    # Sentinel character logic: ■ prefix for that premium TUI feel
    return Text.assemble(("■ ", color), (f"{label:<12}", f"bold {color}"))

class TrackUpdate(Message):
    """Event vector for track status synchronization."""
    def __init__(self, index: int, status: str, color: str = "white") -> None:
        self.index = index
        self.status = status
        self.color = color
        super().__init__()

class ResolveFailed(Message):
    """Request user input to resolve a failed match."""
    def __init__(self, index: int, track: dict, results: list) -> None:
        self.index = index
        self.track = track
        self.results = results
        super().__init__()

class Launchpad(Screen):
    """The High-Fidelity Command Interface."""
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("==================================================", id="title-line-1"),
            Static("      AETHER AUDIO ARCHIVIST PRO // M. BUBB       ", id="title-line-2"),
            Static("==================================================", id="title-line-3"),
            Label("SPOTIFY PLAYLIST SOURCE (URL):"),
            Horizontal(
                Input(value=self.app.default_url, placeholder="https://open.spotify.com/playlist/...", id="url-input"),
                Button("PASTE", variant="warning", id="paste-btn"),
                id="url-row"
            ),
            Label("CONCURRENCY THREADS (Surgical Multi-Thread):"),
            Input(value=str(self.app.default_threads), id="threads-input"),
            Label("ENGINE ACCELERATION (NVIDIA GPU / CPU):"),
            Select([("CPU (SYSTEM STANDARD)", "cpu"), ("GPU (NVIDIA CUDA)", "gpu")], value="cpu", id="engine-select"),
            Label("VISUAL VECTOR (Theme Selection):"),
            Select([("MATRIX (GREEN)", "matrix"), ("CYBERPUNK (NEON)", "cyberpunk"), ("MOLTEN (RED)", "molten")], value=self.app.visual_theme, id="theme-select"),
            Label("COLLECTION ALIAS (Library Name):"),
            Input(value=self.app.default_library, id="library-input"),
            Horizontal(
                Button("INITIALIZE MISSION", variant="success", id="init-btn"),
                Button("WATCHDOG MODE", variant="error", id="watchdog-btn"),
                id="launch-btns"
            ),
            Label("[dim][H] HISTORY  |  WATCHDOG: Auto-detect clipboard URLs[/]"),
            id="launchpad-box"
        )
        yield Footer()

    BINDINGS = [
        Binding("h", "mission_history", "History Archive"),
    ]

    def action_mission_history(self) -> None:
        self.app.push_screen(MissionHistoryScreen())

    @on(Select.Changed, "#theme-select")
    def update_theme_preview(self, event: Select.Changed) -> None:
        self.app.visual_theme = str(event.value)

    @on(Button.Pressed, "#paste-btn")
    def paste_clipboard(self) -> None:
        """Read system clipboard and populate the URL input."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=3
            )
            clip = result.stdout.strip()
            if clip:
                self.query_one("#url-input").value = clip
                self.app.notify("Clipboard pasted", severity="information")
            else:
                self.app.notify("Clipboard is empty", severity="warning")
        except Exception:
            self.app.notify("Failed to read clipboard", severity="error")

    @on(Button.Pressed, "#init-btn")
    def start_archivist(self) -> None:
        url = self.query_one("#url-input").value
        threads = self.query_one("#threads-input").value
        engine = self.query_one("#engine-select").value
        library = self.query_one("#library-input").value
        theme = self.query_one("#theme-select").value
        self.app.visual_theme = theme
        
        if not url:
            self.app.notify("CRITICAL: SOURCE URL MISSING", severity="error")
            return
        if "open.spotify.com/playlist/" not in url:
            self.app.notify("ERROR: Must be a Spotify PLAYLIST URL", severity="error")
            return
            
        try:
            thread_count = int(threads)
        except ValueError:
            thread_count = 36
            
        self.app.push_screen(Archivist(url, library, thread_count, engine))

    @on(Button.Pressed, "#watchdog-btn")
    def start_watchdog(self) -> None:
        threads = self.query_one("#threads-input").value
        engine = self.query_one("#engine-select").value
        library = self.query_one("#library-input").value
        theme = self.query_one("#theme-select").value
        self.app.visual_theme = theme
        try:
            thread_count = int(threads)
        except ValueError:
            thread_count = 36
        self.app.push_screen(WatchdogScreen(library, thread_count, engine))

def _write_failure_log(entry: dict) -> None:
    """Append a structured failure entry to failure_log.json for debugging."""
    log_path = Path(os.getcwd()) / "failure_log.json"
    history = []
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
                if not isinstance(history, list): history = []
        except (json.JSONDecodeError, UnicodeDecodeError):
            history = []
    history.append(entry)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

class WatchdogScreen(Screen):
    """Clipboard Watchdog — collect Spotify URLs, then process on demand."""
    
    BINDINGS = [
        Binding("escape", "stop_watchdog", "Stop Watchdog"),
        Binding("enter", "process_all", "Process All"),
        Binding("d", "remove_selected", "Remove Selected"),
    ]

    def __init__(self, library: str = "Aether_Archive", threads: int = 36, engine: str = "cpu"):
        super().__init__()
        self.library = library
        self.threads = threads
        self.engine = engine
        self._seen_urls: set = set()
        self._url_list: list = []          # [{url, status}]
        self._processed: int = 0
        self._failed_count: int = 0
        self._last_clip: str = ""
        self._poll_timer = None
        self._is_running: bool = False     # True when processing queue
        self._current_idx: int = -1        # Index currently being processed

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("=" * 56, id="wd-line-1"),
            Static("    WATCHDOG MODE // CLIPBOARD URL COLLECTOR    ", id="wd-line-2"),
            Static("=" * 56, id="wd-line-3"),
            Label("[bold]STATUS:[/] [bold ansi_bright_green]SCANNING CLIPBOARD[/]  |  Copy Spotify playlist URLs", id="wd-status"),
            Label("COLLECTED: 0  |  PROCESSED: 0  |  FAILED: 0", id="wd-counts"),
            DataTable(id="wd-table"),
            Log(id="wd-log", highlight=True),
            Horizontal(
                Button("PROCESS ALL", variant="success", id="wd-go-btn"),
                Button("CLEAR LIST", variant="warning", id="wd-clear-btn"),
                Button("BACK", variant="error", id="wd-back-btn"),
                id="wd-btn-row"
            ),
            id="watchdog-box"
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#wd-table", DataTable)
        table.add_column("#", width=4, key="idx")
        table.add_column("PLAYLIST URL", key="url")
        table.add_column("STATUS", width=14, key="status")
        table.cursor_type = "row"
        self._wd_log("WATCHDOG ONLINE. Clipboard scanning every 1.5s.")
        self._wd_log(f"Library: {self.library}  |  Threads: {self.threads}  |  Engine: {self.engine.upper()}")
        self._wd_log("Copy Spotify playlist URLs. Press ENTER or PROCESS ALL when ready.")
        self._poll_timer = self.set_interval(1.5, self._poll_clipboard)

    def _wd_log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self.query_one("#wd-log", Log).write_line(f"[{ts}] {msg}")
        except Exception:
            pass

    def _update_counts(self) -> None:
        queued = sum(1 for u in self._url_list if u["status"] == "QUEUED")
        try:
            self.query_one("#wd-counts").update(
                f"COLLECTED: {len(self._url_list)}  |  PROCESSED: {self._processed}  |  FAILED: {self._failed_count}"
            )
        except Exception:
            pass

    def _poll_clipboard(self) -> None:
        """Read clipboard and check for new Spotify URLs."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=3
            )
            clip = result.stdout.strip()
        except Exception:
            return

        if not clip or clip == self._last_clip:
            return
        self._last_clip = clip

        urls = re.findall(r'https?://open\.spotify\.com/playlist/[A-Za-z0-9]+[^\s]*', clip)
        new_urls = [u for u in urls if u not in self._seen_urls]

        if not new_urls:
            return

        table = self.query_one("#wd-table", DataTable)
        for url in new_urls:
            self._seen_urls.add(url)
            idx = len(self._url_list)
            self._url_list.append({"url": url, "status": "QUEUED"})
            table.add_row(str(idx + 1), url[:60], "QUEUED", key=str(idx))
            self._wd_log(f"DETECTED: {url[:70]}")
            self.app.notify("Playlist URL collected", severity="information")

        self._update_counts()

    @on(Button.Pressed, "#wd-go-btn")
    def action_process_all(self) -> None:
        """Start processing all QUEUED URLs sequentially."""
        queued = [i for i, u in enumerate(self._url_list) if u["status"] == "QUEUED"]
        if not queued:
            self.app.notify("No URLs queued to process", severity="warning")
            return
        if self._is_running:
            self.app.notify("Already processing", severity="warning")
            return
        self._is_running = True
        self._wd_log(f"COMMENCING SEQUENTIAL PROCESSING OF {len(queued)} PLAYLISTS.")
        try:
            self.query_one("#wd-status").update(
                "[bold]STATUS:[/] [bold ansi_bright_yellow]PROCESSING...[/]"
            )
        except Exception:
            pass
        self._process_next_queued()

    def _process_next_queued(self) -> None:
        """Find the next QUEUED URL and launch Archivist for it."""
        for i, entry in enumerate(self._url_list):
            if entry["status"] == "QUEUED":
                self._current_idx = i
                entry["status"] = "PROCESSING"
                table = self.query_one("#wd-table", DataTable)
                try:
                    table.update_cell(str(i), "status", "PROCESSING")
                except Exception:
                    pass
                self._wd_log(f"LAUNCHING: [{i+1}] {entry['url'][:60]}")
                self.app.push_screen(
                    Archivist(entry["url"], self.library, self.threads, self.engine, auto_ingest=True)
                )
                return
        # No more queued — done
        self._is_running = False
        self._wd_log(f"ALL PLAYLISTS PROCESSED. Total: {self._processed}, Failed: {self._failed_count}")
        try:
            self.query_one("#wd-status").update(
                "[bold]STATUS:[/] [bold ansi_bright_green]COMPLETE[/]  |  Watching for more URLs..."
            )
        except Exception:
            pass

    def on_screen_resume(self) -> None:
        """Called when Archivist pops back to this screen."""
        if self._current_idx >= 0 and self._current_idx < len(self._url_list):
            entry = self._url_list[self._current_idx]
            entry["status"] = "DONE"
            self._processed += 1
            table = self.query_one("#wd-table", DataTable)
            try:
                table.update_cell(str(self._current_idx), "status", "DONE")
            except Exception:
                pass
            self._wd_log(f"COMPLETE: [{self._current_idx+1}] {entry['url'][:60]}")

        self._update_counts()
        self._current_idx = -1

        if self._is_running:
            self.call_later(self._process_next_queued)

    @on(Button.Pressed, "#wd-clear-btn")
    def clear_list(self) -> None:
        if self._is_running:
            self.app.notify("Cannot clear while processing", severity="warning")
            return
        self._url_list.clear()
        self._seen_urls.clear()
        self._processed = 0
        self._failed_count = 0
        table = self.query_one("#wd-table", DataTable)
        table.clear()
        self._update_counts()
        self._wd_log("LIST CLEARED.")

    def action_remove_selected(self) -> None:
        if self._is_running:
            return
        table = self.query_one("#wd-table", DataTable)
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            idx = int(str(row_key))
            if idx < len(self._url_list) and self._url_list[idx]["status"] == "QUEUED":
                url = self._url_list[idx]["url"]
                self._url_list[idx]["status"] = "REMOVED"
                self._seen_urls.discard(url)
                table.remove_row(str(idx))
                self._wd_log(f"REMOVED: {url[:60]}")
                self._update_counts()
        except Exception:
            pass

    @on(Button.Pressed, "#wd-back-btn")
    def action_stop_watchdog(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
        self._wd_log("WATCHDOG TERMINATED.")
        self.app.pop_screen()

class Archivist(Screen):
    """The Operational Command Center."""
    
    BINDINGS = [
        Binding("space", "toggle_select", "Toggle Selected"),
        Binding("a", "select_all", "Select Global All"),
        Binding("n", "select_none", "Deselect All"),
        Binding("s", "toggle_autoscroll", "Toggle Auto-Scroll"),
        Binding("enter", "start_ingest", "COMMENCE INGESTION"),
        Binding("escape", "app.pop_screen", "Back to Launchpad"),
    ]

    auto_scroll = reactive(True)

    def __init__(self, url="", library="Aether_Archive", threads=36, engine="cpu", auto_ingest=False):
        super().__init__()
        # Robust Sanitization: Strip accidental leading characters (like 'vhttps')
        if "http" in url:
            url = url[url.find("http"):]
        
        self.url = url.strip()
        self.library = "".join([c for c in library if c.isalnum() or c in " -_"]).strip() or "Aether_Archive"
        self.threads = threads
        self.engine = engine # Keep engine as it's passed from Launchpad
        self.target_dir = Path(os.getcwd()) / "Audio_Libraries" / self.library
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.tracks = []
        self.is_scraping = True
        self.mission_start = datetime.now()
        self.stats = {"total": 0, "complete": 0, "no_match": 0, "failed": 0}
        self.track_times = {}
        self.track_sizes = {}
        self.pending_tasks = 0
        self.col_keys = {}
        self.semaphore = None # Replaced by Queue
        self.is_ingesting = False
        self.gpu_failures = 0
        self.live_timer = None
        self.harvest_start = None
        self.ingest_start = None
        self.harvest_dur = 0
        self.live_harvest_time = 0
        self.live_ingest_time = 0
        self.total_size_bytes = 0
        self.track_speeds: dict[int, float] = {}   # P27: live KB/s per track
        self._running_size: int = 0                # P7:  incremental total
        self._matched_set: set = set()             # Implement matched_set in scrape_tracks
        self._dispatched: set = set()              # P2: TRACK DISPATCH SET
        self.ingest_queue = asyncio.Queue()
        self.worker_tasks = []
        self.auto_ingest = auto_ingest
        self.exit_handled = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="table-container"):
                yield DataTable(id="data-table")
                yield ProgressBar(id="ingest-progress", total=100, show_eta=True)
            yield Log(id="hacker-log", highlight=True)
        with Horizontal(id="action-bar"):
             yield Label("HARVEST: 0.0s", id="harvest-timer")
             yield Label("INGEST: 0.0s", id="ingest-timer")
             yield Label("SIZE: 0.00 MB", id="total-size-label")
             yield Label("RATE: 0/min", id="rate-label")         # P25
             yield MiniSparkline(id="sparkline")                # P21
             yield Label("[ ↓ LIVE ]", id="scroll-indicator")
             yield Button("GO (COMMENCE INGESTION)", id="go-btn", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        self.col_keys["SEL"]    = table.add_column("SEL", width=5)
        self.col_keys["STATUS"] = table.add_column("STATUS", width=16)
        self.col_keys["ARTIST"] = table.add_column("ARTIST")
        self.col_keys["TITLE"]  = table.add_column("TITLE")
        self.col_keys["DUR"]    = table.add_column("DUR", width=7)
        self.col_keys["SPEED"]  = table.add_column("SPEED", width=9)  # P27
        table.cursor_type = "row"
        self.log_kernel("SYSTEM INITIALIZED. WELCOME, ARCHITECT BUBB.")
        self.live_timer = self.set_interval(0.25, self.update_timers)  # P7: 4Hz not 10Hz
        
        # Register signal handlers for graceful exit
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, self.handle_exit)
        except Exception:
            pass
            
        self.scrape_tracks()
    
    def update_timers(self) -> None:  # P7: runs at 4 Hz
        if self.harvest_start and not hasattr(self, 'harvest_dur_fixed'):
            self.live_harvest_time = (datetime.now() - self.harvest_start).total_seconds()
            self.query_one("#harvest-timer").update(f"HARVEST: {self.live_harvest_time:.1f}s")
        if self.is_ingesting and self.ingest_start:
            self.live_ingest_time = (datetime.now() - self.ingest_start).total_seconds()
            self.query_one("#ingest-timer").update(f"INGEST: {self.live_ingest_time:.1f}s")
            # P25: live throughput rate
            completed = self.stats.get("complete", 0)
            rate = (completed / max(self.live_ingest_time, 1)) * 60
            self.query_one("#rate-label").update(f"RATE: {rate:.1f}/min")
        # P7: running sum, no full dict re-scan each tick
        size_mb = self._running_size / (1024 * 1024)
        self.query_one("#total-size-label").update(f"SIZE: {size_mb:.2f} MB")
        
        # Auto-scroll indicator update
        indicator = self.query_one("#scroll-indicator")
        if self.auto_scroll:
            indicator.update("[ ↓ LIVE ]")
            indicator.styles.color = "ansi_bright_cyan"
            indicator.styles.text_style = "bold"
        else:
            indicator.update("[ PAUSED ]")
            indicator.styles.color = "ansi_default"
            indicator.styles.text_style = "none"

    def save_checkpoint(self) -> None:
        """Write session persistence vector to disk."""
        checkpoint_path = Path(os.getcwd()) / "session_state.json"
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "url": self.url,
                "library": self.library,
                "stats": self.stats,
                "tracks": [
                    {"artist": t["artist"], "title": t["title"], "status": t["status"]}
                    for t in list(self.tracks) # ROBUST: Copy to avoid concurrent mutation errors
                ]
            }
            with open(checkpoint_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log_kernel(f"CHECKPOINT ERROR: {e}")

    def handle_exit(self, sig=None, frame=None) -> None:
        """Graceful shutdown protocol."""
        if self.exit_handled: return
        self.exit_handled = True
        self.log_kernel("GRACEFUL SHUTDOWN INITIATED. CLEANING VECTORS...")
        
        # Cancel workers
        for task in self.worker_tasks:
            task.cancel()
            
        # Cleanup temp files
        try:
            for f in self.target_dir.glob("tmp_*.mp3"):
                f.unlink(missing_ok=True)
        except Exception as e:
            self.log_kernel(f"CLEANUP ERR: {e}")
            
        self.save_checkpoint()
        self.app.exit()

    def log_kernel(self, message: str):
        log_widget = self.query_one(Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_widget.write_line(f"[{timestamp}] {message}")
        if self.auto_scroll:
            log_widget.scroll_end(animate=False)

    def action_toggle_autoscroll(self) -> None:
        self.auto_scroll = not self.auto_scroll
        self.log_kernel(f"AUTO-SCROLL: {'ENGAGED' if self.auto_scroll else 'DISENGAGED'}")

    @work(exclusive=True)
    async def scrape_tracks(self):
        self.harvest_start = datetime.now()
        import re
        dur_regex = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$')
        self.log_kernel(f"DEPLOYING PROXIES TO: {self.url}")
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            try:
                await page.goto(self.url, timeout=60000)
                await page.wait_for_load_state("load")
                
                # Dismiss cookie wall
                try: await page.click('button#onetrust-accept-btn-handler', timeout=3000)
                except: pass

                await page.wait_for_selector('[data-testid="tracklist-row"]', timeout=30000)
                
                table = self.query_one(DataTable)
                processed_ids = set()
                
                self.log_kernel("HARVESTING VECTORS (BULK JS EXTRACTION)...")
                
                # Infinite Scroll Engine with Bulk Extraction
                last_count = -1
                stable_count = 0
                while stable_count < 10:
                    rows_count = await page.evaluate('''() => {
                        const rows = document.querySelectorAll('[data-testid="tracklist-row"]');
                        if (rows.length > 0) {
                            rows[rows.length - 1].scrollIntoView();
                        }
                        return rows.length;
                    }''')
                    
                    await page.mouse.wheel(0, 5000)
                    for _ in range(2):
                         await page.keyboard.press("PageDown")
                         # Reduced delay for snappier propagation
                         await asyncio.sleep(0.1)
                    
                    # 20x Speedup: Extract all visible track data in one JS execution
                    extracted_tracks = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('[data-testid="tracklist-row"]')).map(row => {
                            const titleElem = row.querySelector('div[dir="auto"]');
                            const artistElems = row.querySelectorAll('a[href*="/artist/"]');
                            const durElem = row.querySelector('div[data-testid="tracklist-row-duration"]');
                            
                            // Fallback for duration if standard testid missing (virtualization artifact)
                            let duration = durElem ? durElem.innerText : "0:00";
                            if (duration === "0:00") {
                                const potentialDurs = Array.from(row.querySelectorAll('div')).filter(d => d.innerText.includes(':'));
                                const durRegex = /^\\d{1,2}:\\d{2}(:\\d{2})?$/;
                                for (const p of potentialDurs) {
                                    if (durRegex.test(p.innerText.trim())) {
                                        duration = p.innerText.trim();
                                        break;
                                    }
                                }
                            }

                            return {
                                title: titleElem ? titleElem.innerText : "Unknown",
                                artists: Array.from(artistElems).map(a => a.innerText).join(", "),
                                duration: duration
                            };
                        });
                    }''')

                    table = self.query_one(DataTable)
                    for track_data in extracted_tracks:
                        track_id = f"{track_data['artists']}_{track_data['title']}".strip()
                        if track_id and track_id not in processed_ids:
                            processed_ids.add(track_id)
                            idx = len(self.tracks)
                            self.tracks.append({
                                "artist": track_data['artists'],
                                "title": track_data['title'],
                                "duration": track_data['duration'],
                                "selected": True,
                                "status": "WAITING FOR PROPAGATION"
                            })
                            table.add_row(
                                "[X]", 
                                render_status_badge("WAITING FOR PROPAGATION"), 
                                track_data['artists'], 
                                track_data['title'][:40], 
                                track_data['duration'], 
                                "", 
                                key=str(idx)
                            )
                    
                    current_count = len(self.tracks)
                    if current_count == last_count:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_count = current_count
                        if current_count > 0:
                            self.log_kernel(f"PROPAGATED {current_count} VECTORS...")
                    
                    # P2: FIXED O(N²) — only dispatch each index once via matched_set
                    for i in range(len(self.tracks)):
                        if i not in self._dispatched and self.tracks[i]["status"] == "WAITING FOR PROPAGATION":
                            self._dispatched.add(i)
                            self.tracks[i]["status"] = "MATCHING"
                            table.update_cell(str(i), self.col_keys["STATUS"], render_status_badge("MATCHING"))
                            self.match_vector(i)

                self.is_scraping = False
                self.harvest_dur = (datetime.now() - self.harvest_start).total_seconds()
                self.harvest_dur_fixed = True
                self.log_kernel(f"COMPLETE HARVEST: {len(self.tracks)} TRACK DESCRIPTORS IN {self.harvest_dur:.1f}s.")
                self.log_kernel("VECTORS SYNCHRONIZED. READY FOR INGESTION.")
                if self.auto_ingest:
                    self.log_kernel("WATCHDOG: AUTO-SELECTING ALL VECTORS.")
                    self.action_select_all()
                    self.log_kernel("WATCHDOG: AUTO-INGESTION ENGAGED.")
                    self.call_later(self.action_start_ingest)
            except Exception as e:
                self.log_kernel(f"CRITICAL SCRAPE FAILURE: {e}")
                import traceback
                self.log_kernel(traceback.format_exc())
            finally:
                await browser.close()

    @work
    async def match_vector(self, index: int):
        """Threaded background matching for harvested vectors."""
        track = self.tracks[index]
        try:
            best = await self.search_track(index, track)
            if best:
                self.tracks[index]["youtube_best"] = best
                self.tracks[index]["status"] = "QUEUED"
                self.post_message(TrackUpdate(index, "QUEUED", "white"))
        except Exception as e:
            self.log_kernel(f"MATCH ERROR [{index}]: {e}")
            self.mark_no_match(index)

    @on(Button.Pressed, "#go-btn")
    def start_ingest_btn(self) -> None:
        self.action_start_ingest()

    def action_toggle_select(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count == 0: return
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            idx = int(row_key.value)
            self.tracks[idx]["selected"] = not self.tracks[idx]["selected"]
            val = "[bold green][X][/]" if self.tracks[idx]["selected"] else "[ ]"
            table.update_cell(row_key, self.col_keys["SEL"], val)
        except: pass

    def action_select_all(self) -> None:
        table = self.query_one(DataTable)
        sel_key = self.col_keys["SEL"]
        for i, track in enumerate(self.tracks):
            track["selected"] = True
            try: table.update_cell(str(i), sel_key, "[bold green][X][/]")
            except: pass
        self.log_kernel("GLOBAL SELECTION: ALL VECTORS ENGAGED.")

    def action_select_none(self) -> None:
        table = self.query_one(DataTable)
        sel_key = self.col_keys["SEL"]
        for i, track in enumerate(self.tracks):
            track["selected"] = False
            try: table.update_cell(str(i), sel_key, "[ ]")
            except: pass
        self.log_kernel("GLOBAL SELECTION: ALL VECTORS DISENGAGED.")

    def action_start_ingest(self) -> None:
        if self.is_scraping:
            self.app.notify("WARNING: STILL HARVESTING VECTORS", severity="warning"); return
        if self.is_ingesting:
            self.app.notify("WARNING: INGESTION ALREADY ACTIVE", severity="warning"); return
        selected = [i for i, t in enumerate(self.tracks) if t.get("selected")]
        if not selected:
            self.app.notify("ERROR: NO VECTORS SELECTED", severity="error"); return
        self.is_ingesting = True
        self.ingest_start = datetime.now()
        self.query_one(ProgressBar).update(total=len(selected), progress=0)
        self.stats.update({"total": len(selected), "complete": 0, "no_match": 0, "failed": 0})
        self.track_times.clear(); self.track_sizes.clear()
        self.pending_tasks = len(selected)
        self.log_kernel(f"COMMENCING QUEUE-POOL INGESTION (POOL: {self.threads}, ENGINE: {self.engine.upper()}).")
        
        # Initialize Workers
        for _ in range(min(self.threads, len(selected))):
            self.worker_tasks.append(asyncio.create_task(self.drain_worker()))
            
        for idx in selected:
            self.ingest_queue.put_nowait(idx)
            
    async def drain_worker(self) -> None:
        """Consumer coroutine: Drains the ingest_queue with persistence logic."""
        while True:
            try:
                index = await self.ingest_queue.get()
                await self._process_track(index)
                self.ingest_queue.task_done()
                
                # Check if we are done
                if self.ingest_queue.empty() and self.pending_tasks == 0:
                    ingest_dur = (datetime.now() - self.ingest_start).total_seconds()
                    await self.close_mission(ingest_dur)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_kernel(f"DRAIN WORKER ERROR: {e}")
            finally:
                # Small yield to prevent CPU pinning if errors occur rapidly
                await asyncio.sleep(0.01)


    async def _process_track(self, index: int) -> None:
        track = self.tracks[index]
        track_start = datetime.now()
        try:
            # P14: Dedup — skip if already in library
            if self._already_archived(index, track):
                return
            self.tracks[index]["status"] = "ARCHIVING"
            self.post_message(TrackUpdate(index, "ARCHIVING", "bright_cyan"))
            best = track.get("youtube_best") or await self.search_track(index, track)
            if not best:
                return
            temp_path = await self.download_with_retry(index, track, best)
            if not temp_path:
                self.tracks[index]["status"] = "FAILED"
                self.stats["failed"] += 1
                self.post_message(TrackUpdate(index, "FAILED", "bright_red"))
                self.query_one(ProgressBar).advance(1)
                self.log_kernel(f"SIGNAL LOSS: {track['title']}")
                _write_failure_log({
                    "timestamp": datetime.now().isoformat(),
                    "phase": "download",
                    "track_index": index,
                    "artist": track.get("artist", "?"),
                    "title": track.get("title", "?"),
                    "youtube_url": best.get("url", "?"),
                    "error": "Download returned no file (SIGNAL LOSS)",
                })
                return
            elapsed = (datetime.now() - track_start).total_seconds()
            await self.tag_track(index, track, temp_path, best, elapsed)
        except Exception as e:
            self.tracks[index]["status"] = "FAILED"
            self.stats["failed"] += 1
            self.post_message(TrackUpdate(index, "FAILED", "bright_red"))
            self.query_one(ProgressBar).advance(1)
            self.log_kernel(f"FAIL [{index}]: {track.get('title','?')} — {e}")
            _write_failure_log({
                "timestamp": datetime.now().isoformat(),
                "phase": "process_track",
                "track_index": index,
                "artist": track.get("artist", "?"),
                "title": track.get("title", "?"),
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
        finally:
            self.pending_tasks -= 1

    def _already_archived(self, index: int, track: dict) -> bool:
        """P14: Check if track file exists before downloading."""
        safe = _sanitise_filename(f"{track['artist']} - {track['title']}.mp3")
        if (self.target_dir / safe).exists():
            self.tracks[index]["status"] = "ALREADY ARCHIVED"
            self.stats["complete"] += 1
            self.post_message(TrackUpdate(index, "ALREADY ARCHIVED", "green"))
            self.query_one(ProgressBar).advance(1)
            self.log_kernel(f"SKIP (exists): {track['title']}")
            return True
        return False

    async def search_track(self, index: int, track: dict) -> dict | None:
        """P15/16/17/18: Scored multi-signal search with blocklist and expanded fallbacks."""
        artist, title = track.get('artist', ''), track.get('title', '')
        queries = [
            f"{artist} {title} official audio",
            f"{artist} {title} official video",
            f"{title} {artist} audio",
            f"{artist} {title} lyrics",
            f"{artist} {title}",
        ]
        results = []
        for q in queries:
            if results:
                break
            
            # P16: Check cache before search
            if q in _SEARCH_CACHE:
                results = _SEARCH_CACHE[q]
                break

            try:
                async with asyncio.timeout(120): # IMPLEMENT: timeout(120) guard
                    results = await self.perform_youtube_search(q)
                    if results:
                        _SEARCH_CACHE[q] = results
            except asyncio.TimeoutError:
                self.log_kernel(f"SEARCH TIMEOUT for: {q}")
                continue
            except Exception:
                continue

        # P17: filter blocklist
        results = [r for r in results if not _is_blocked(r.get('title', ''))]
        spotify_dur = self.parse_duration(track['duration'])

        # P15: score all candidates
        scored = sorted(
            [(s, e) for e in results if (s := _score_result(e, track, spotify_dur)) > 0.15],
            key=lambda x: x[0], reverse=True
        )
        if scored:
            # Auto-accept the top result if it scores well enough (>0.4)
            # Only trigger ambiguity screen if the top score is marginal
            if scored[0][0] >= 0.4 or len(scored) == 1:
                self.tracks[index]["status"] = "QUEUED"
                self.post_message(TrackUpdate(index, "QUEUED", "bright_white"))
                return scored[0][1]
            # Multiple close matches with low confidence — let user decide
            self.tracks[index]["status"] = "AWAITING USER DECISION"
            self.post_message(TrackUpdate(index, "AWAITING USER DECISION", "bright_yellow"))
            self.post_message(ResolveFailed(index, track, results[:3]))
            while self.tracks[index].get("youtube_url") is None and \
                  self.tracks[index]["status"] == "AWAITING USER DECISION":
                await asyncio.sleep(0.2)
            if self.tracks[index].get("youtube_url"):
                return {"url": self.tracks[index]["youtube_url"],
                        "id":  self.tracks[index].get("youtube_id", "manual"),
                        "thumbnail": None}
        self.mark_no_match(index)
        return None

    def mark_no_match(self, index: int) -> None:
        self.tracks[index]["status"] = "NO MATCH"
        self.stats["no_match"] += 1
        self.query_one(ProgressBar).advance(1)
        self.post_message(TrackUpdate(index, "NO MATCH", "orange1"))

    async def download_with_retry(self, index: int, track: dict, best: dict) -> Path | None:
        """P8/9/10/11/6: yt-dlp Python API, smart format, correct flags, retry+timeout."""
        track_id = best.get('id', 'tmp')
        out_stem = self.target_dir / f"tmp_{track_id}"
        out_path = out_stem.with_suffix('.mp3')
        url = best.get('url') or best.get('webpage_url') or f"https://youtube.com/watch?v={track_id}"

        for attempt in range(3):
            if attempt:
                wait = 2 ** attempt
                self.log_kernel(f"RETRY [{attempt}] {track['title']} — backoff {wait}s")
                await asyncio.sleep(wait)
            try:
                async with asyncio.timeout(120): # IMPLEMENT: asyncio.timeout(120)
                    ok = await self._dl_api(index, url, out_stem)
                    if ok and out_path.exists():
                        return out_path
            except asyncio.TimeoutError:
                self.log_kernel(f"TIMEOUT [{index}]: {track['title']}")
            except Exception as e:
                self.log_kernel(f"DL ERR [{index}]: {e}")
        return None

    async def _dl_api(self, index: int, url: str, out_stem: Path) -> bool:
        """P8: yt-dlp Python API (no subprocess). P9: smart format. P10: correct threads."""
        def _run():
            opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'outtmpl': str(out_stem) + '.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'mp3', 'preferredquality': '0'}],
                'postprocessor_args': {
                    'ffmpeg': [
                        '-threads', '0',
                        '-hwaccel', 'auto' if self.engine == 'gpu' else 'none' # P: Engine Vector
                    ]
                },
                'quiet': True, 'no_warnings': True, 'noplaylist': True,
                'progress_hooks': [self._make_progress_hook(index)],
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return True
        try:
            await asyncio.to_thread(_run)
            return True
        except Exception as e:
            self.log_kernel(f"API DL: {e}")
            return False

    def _make_progress_hook(self, index: int):
        """P27: Feed live KB/s into SPEED column via call_from_thread."""
        def hook(d):
            if d.get('status') == 'downloading':
                speed = d.get('speed', 0) or 0
                try:
                    self.app.call_from_thread(self._update_speed_cell, index, speed)
                except Exception:
                    pass
        return hook

    def _update_speed_cell(self, index: int, speed: float) -> None:
        try:
            kb = speed / 1024
            self.query_one(DataTable).update_cell(
                str(index), self.col_keys["SPEED"], f"{kb:.0f}KB/s"
            )
        except Exception:
            pass

    async def tag_track(self, index: int, track: dict, temp_path: Path,
                        best: dict, elapsed: float) -> bool:
        """P34/35/36/37: In-place mutagen tagging, full ID3, Unicode filename, album art."""
        safe_name = _sanitise_filename(f"{track['artist']} - {track['title']}.mp3")
        dest = self.target_dir / safe_name

        def _tag_and_move():
            if dest.exists():
                dest.unlink()
            temp_path.rename(dest)
            if not dest.exists():
                return False
            if MUTAGEN_OK:
                try:
                    try:
                        tags = ID3(str(dest))
                    except ID3NoHeaderError:
                        tags = ID3()
                    
                    tags.clear()
                    # TIT2: Title, TPE1: Artist, TALB: Album (Library), TRCK: Track Num, TDRC: Year
                    tags.add(TIT2(encoding=3, text=track['title']))
                    tags.add(TPE1(encoding=3, text=track['artist']))
                    tags.add(TALB(encoding=3, text=self.library))
                    
                    idx_str = str(track.get('track_num', index + 1))
                    tags.add(TRCK(encoding=3, text=idx_str))
                    
                    # TDRC: Date (Year)
                    year = (best.get('upload_date') or "")[:4]
                    if year:
                        tags.add(TDRC(encoding=3, text=year))

                    # APIC: Album Art (YouTube Thumbnail)
                    # Use existing art fetcher which handles Pillow scaling
                    art = _fetch_art(best.get('thumbnail'))
                    if art:
                        tags.add(APIC(
                            encoding=3, mime='image/jpeg', type=3,
                            desc='Cover', data=art
                        ))
                    
                    tags.save(str(dest), v2_version=3)
                except Exception as e:
                    self.app.call_from_thread(self.log_kernel, f"MUTAGEN OVERRIDE ERR: {e}")
            return True

        success = await asyncio.to_thread(_tag_and_move)
        if success:
            stat = await asyncio.to_thread(os.stat, dest)
            self.track_sizes[index] = stat.st_size
            self._running_size += stat.st_size          # P7: incremental sum
            self.track_times[index] = elapsed
            self.tracks[index]["status"] = "COMPLETE"
            self.stats["complete"] += 1
            self.post_message(TrackUpdate(index, "COMPLETE", "bright_green"))
            self.query_one(ProgressBar).advance(1)
            # P27: replace speed with final file size
            size_mb = stat.st_size / (1024 * 1024)
            try:
                self.query_one(DataTable).update_cell(
                    str(index), self.col_keys["SPEED"], f"{size_mb:.2f}MB"
                )
            except Exception:
                pass
            # P21: feed sparkline
            try:
                self.query_one(MiniSparkline).push_event()
            except Exception:
                pass
            self.log_kernel(f"COMPLETE: {track['title']} ({elapsed:.1f}s, {size_mb:.2f}MB)")
            return True
        self.log_kernel(f"TAG FAIL: {track['title']}")
        return False

    async def close_mission(self, ingest_dur):
        ingest_dur = round(ingest_dur, 2)
        await self.save_mission_report(ingest_dur)
        try:
            # Convenience: Open Explorer window to the target directory
            await asyncio.to_thread(os.startfile, str(self.target_dir))
        except:
            pass
        self.app.push_screen(StatsScreen(self.stats, self.track_times, self.track_sizes, ingest_dur, self.harvest_dur, self.tracks))

    def on_track_update(self, message: TrackUpdate) -> None:
        table = self.query_one(DataTable)
        try:
            table.update_cell(str(message.index), self.col_keys["STATUS"], render_status_badge(message.status))
            self.save_checkpoint() # P: Session checkpoint after state change
        except: pass
    
    def on_resolve_failed(self, message: ResolveFailed) -> None:
        self.app.push_screen(ResolveMatchScreen(message.index, message.track, message.results, self))

    async def perform_youtube_search(self, query: str) -> list:
        """Surgical search vector using direct yt-dlp library access."""
        def run_search():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Direct library usage is significantly faster than subprocess
                result = ydl.extract_info(f"ytsearch5:{query}", download=False)
                return result.get('entries', [])
        
        return await asyncio.to_thread(run_search)

    @staticmethod
    def parse_duration(d_str):
        """Surgical parsing of temporal vectors."""
        try:
            parts = d_str.split(":")
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except: return 0
        return 0
    
    async def save_mission_report(self, ingest_dur):
        """Asynchronous mission debriefing."""
        import hashlib
        playlist_id = hashlib.md5(self.url.encode()).hexdigest()[:8]
        history_file = Path(os.getcwd()) / "mission_history.json"
        
        def _write_report_to_disk():
            combined_time = self.harvest_dur + ingest_dur
            avg_time = combined_time / max(self.stats["complete"], 1)
            total_size = sum(self.track_sizes.values())
            avg_size = total_size / max(self.stats["complete"], 1)
            largest_size = max(self.track_sizes.values()) if self.track_sizes else 0
            largest_track = None
            if largest_size > 0:
                for idx, size in self.track_sizes.items():
                    if size == largest_size:
                        largest_track = self.tracks[idx]["title"]
                        break
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "playlist_id": playlist_id,
                "playlist_url": self.url,
                "library": self.library,
                "engine": self.engine,
                "harvest_duration_seconds": round(self.harvest_dur, 2),
                "ingest_duration_seconds": round(ingest_dur, 2),
                "combined_logic_duration": round(combined_time, 2),
                "avg_time_per_song": round(avg_time, 2),
                "total_collection_size_bytes": total_size,
                "avg_track_size_bytes": round(avg_size, 2),
                "stats": self.stats,
                "largest_song": largest_track,
                "largest_size_bytes": largest_size,
                "tracks": [
                    {
                        "title": t["title"],
                        "artist": t["artist"],
                        "status": t["status"],
                        "time_seconds": self.track_times.get(i, 0),
                        "size_bytes": self.track_sizes.get(i, 0)
                    }
                    for i, t in enumerate(self.tracks)
                ]
            }
            
            history = []
            if history_file.exists():
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        if not isinstance(history, list): history = []
                except (json.JSONDecodeError, UnicodeDecodeError):
                    history = []
            
            history.append(report)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
            return history_file

        saved_path = await asyncio.to_thread(_write_report_to_disk)
        self.log_kernel(f"MISSION REPORT SAVED: {saved_path}")

class MissionHistoryScreen(Screen):
    """Surgical display of past ingestion operations."""
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back to Ops Interface"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("==================================================", id="history-line-1"),
            Static("          GLOBAL MISSION HISTORY ARCHIVE          ", id="history-line-2"),
            Static("==================================================", id="history-line-3"),
            DataTable(id="history-table"),
            id="history-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("DATE", width=20)
        table.add_column("LIBRARY (COLLECTION)")
        table.add_column("SUCCESS")
        table.add_column("MISS")
        table.add_column("FAIL")
        table.add_column("SIZE (MB)", width=10)
        table.cursor_type = "row"

        history_file = Path(os.getcwd()) / "mission_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                # Sort by timestamp descending (newest first)
                history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                for entry in history:
                    ts = entry.get("timestamp", "").replace("T", " ")[:19]
                    lib = entry.get("library", "Unknown")
                    stats = entry.get("stats", {})
                    success = stats.get("complete", 0)
                    miss = stats.get("no_match", 0)
                    failed = stats.get("failed", 0)
                    size_bytes = entry.get("total_collection_size_bytes", 0)
                    size_mb = size_bytes / (1024 * 1024)
                    table.add_row(
                        ts, lib, 
                        f"[bold green]{success}[/]", 
                        f"[orange1]{miss}[/]", 
                        f"[bright_red]{failed}[/]", 
                        f"{size_mb:.2f}"
                    )
            except Exception as e:
                self.app.notify(f"HISTORY PARSE ERROR: {e}", severity="error")

class ResolveMatchScreen(Screen):
    """Screen to resolve failed track matches by showing user options."""
    def __init__(self, index: int, track: dict, results: list, archivist: Screen):
        super().__init__()
        self.index = index
        self.track = track
        self.results = results
        self.archivist = archivist

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="resolve-box"):
            yield Static("==================================================", id="resolve-line-1")
            yield Static("           SEARCH RESULT AMBIGUITY DETECTED        ", id="resolve-line-2")
            yield Static("==================================================", id="resolve-line-3")
            yield Label(f"[bold cyan]{self.track['artist']} - {self.track['title']}[/]")
            yield Label("[white]Select which result matches this song:[/]")
            yield Static("", id="spacer-a")
            
            for i, result in enumerate(self.results, 1):
                title = result.get('title', 'Unknown')[:60]
                duration = result.get('duration', 0)
                dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
                yield Button(f"[{i}] {title} ({dur_str})", id=f"opt-{i}", variant="primary" if i == 1 else "default")
            
            yield Static("", id="spacer-b")
            yield Button("[0] SKIP (Mark as No Match)", id="opt-0", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id and btn_id.startswith("opt-"):
            choice = int(btn_id.split("-")[1])
            if choice == 0:
                self.archivist.tracks[self.index]["youtube_url"] = None
            elif 1 <= choice <= len(self.results):
                selected = self.results[choice - 1]
                self.archivist.tracks[self.index]["youtube_url"] = selected.get('url')
                self.archivist.tracks[self.index]["youtube_id"] = selected.get('id')
            self.app.pop_screen()

class StatsScreen(Screen):
    """The Mission Summary Vanguard."""
    def __init__(self, stats: dict, track_times: dict = None, track_sizes: dict = None,
                 ingest_dur: float = 0, harvest_dur: float = 0, tracks: list = None):
        super().__init__()
        self.stats = stats
        self.track_times = track_times or {}
        self.track_sizes = track_sizes or {}
        self.ingest_dur = ingest_dur
        self.harvest_dur = harvest_dur
        self.tracks = tracks or []

    def _fmt_time(self, seconds: float) -> str:
        """Format seconds into human-readable duration."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        m, s = divmod(int(seconds), 60)
        if m < 60:
            return f"{m}m {s}s"
        h, m = divmod(m, 60)
        return f"{h}h {m}m {s}s"

    def _track_name(self, idx: int) -> str:
        """Get display name for a track by index."""
        if idx < len(self.tracks):
            t = self.tracks[idx]
            return f"{t.get('artist', '?')} - {t.get('title', '?')}"
        return f"Track #{idx}"

    def compose(self) -> ComposeResult:
        total = self.stats["total"]
        complete = self.stats["complete"]
        no_match = self.stats["no_match"]
        failed = self.stats["failed"]
        success_rate = (complete / max(total, 1)) * 100

        # ── Time Metrics ──
        combined_time = self.harvest_dur + self.ingest_dur
        avg_time = self.ingest_dur / max(complete, 1)
        times_list = sorted(self.track_times.values()) if self.track_times else []
        median_time = times_list[len(times_list) // 2] if times_list else 0
        fastest_time = min(times_list) if times_list else 0
        slowest_time = max(times_list) if times_list else 0
        fastest_idx = min(self.track_times, key=self.track_times.get) if self.track_times else None
        slowest_idx = max(self.track_times, key=self.track_times.get) if self.track_times else None

        # ── Size Metrics ──
        total_size = sum(self.track_sizes.values())
        total_mb = total_size / (1024 * 1024)
        total_gb = total_size / (1024 * 1024 * 1024)
        avg_size = total_size / max(complete, 1)
        avg_mb = avg_size / (1024 * 1024)
        sizes_list = sorted(self.track_sizes.values()) if self.track_sizes else []
        smallest_size = min(sizes_list) if sizes_list else 0
        largest_size = max(sizes_list) if sizes_list else 0
        largest_idx = max(self.track_sizes, key=self.track_sizes.get) if self.track_sizes else None
        smallest_idx = min(self.track_sizes, key=self.track_sizes.get) if self.track_sizes else None
        median_size = sizes_list[len(sizes_list) // 2] if sizes_list else 0

        # ── Throughput ──
        throughput_rate = (complete / max(self.ingest_dur, 1)) * 60  # tracks/min
        data_rate = (total_size / max(self.ingest_dur, 1)) / 1024   # KB/s

        # ── Ratio Bar ──
        ratio_bar = _make_ratio_bar(complete, no_match, failed, total, width=44)

        # ── Build Labels ──
        labels = []

        # Header
        labels.append(Static("=" * 56, id="stats-line-1"))
        labels.append(Static("       INGESTION MISSION REPORT: COMPLETE          ", id="stats-line-2"))
        labels.append(Static("=" * 56, id="stats-line-3"))

        # Outcome Summary
        labels.append(Label(f"TOTAL VECTORS TARGETED:   [bold]{total}[/]"))
        labels.append(Label(f"SUCCESSFULLY ARCHIVED:    [bold green]{complete}[/]  ({success_rate:.1f}%)"))
        labels.append(Label(f"NO MATCH FOUND:           [bold yellow]{no_match}[/]"))
        labels.append(Label(f"SYSTEM FAILURES:          [bold red]{failed}[/]"))
        labels.append(Static("", id="spacer-1"))

        # Ratio Bar
        labels.append(Label(Text.assemble(
            ("MISSION RATIO:  ", "bold"),
            ratio_bar,
        )))
        labels.append(Static("", id="spacer-1b"))

        # Time Breakdown
        labels.append(Static("── TEMPORAL ANALYSIS ──────────────────────────────"))
        labels.append(Label(f"HARVEST (SCRAPE):          [bold yellow]{self._fmt_time(self.harvest_dur)}[/]"))
        labels.append(Label(f"INGESTION (DOWNLOAD):      [bold cyan]{self._fmt_time(self.ingest_dur)}[/]"))
        labels.append(Label(f"TOTAL MISSION WALL CLOCK:  [bold green]{self._fmt_time(combined_time)}[/]"))
        labels.append(Label(f"AVG TIME PER TRACK:        [bold cyan]{self._fmt_time(avg_time)}[/]"))
        labels.append(Label(f"MEDIAN TIME PER TRACK:     [bold cyan]{self._fmt_time(median_time)}[/]"))
        labels.append(Label(f"THROUGHPUT:                [bold green]{throughput_rate:.1f} tracks/min[/]"))

        if fastest_idx is not None:
            labels.append(Label(f"FASTEST TRACK:             [bold green]{self._fmt_time(fastest_time)}[/]  {self._track_name(fastest_idx)[:35]}"))
        if slowest_idx is not None:
            labels.append(Label(f"SLOWEST TRACK:             [bold red]{self._fmt_time(slowest_time)}[/]  {self._track_name(slowest_idx)[:35]}"))

        labels.append(Static("", id="spacer-2"))

        # Size Breakdown
        labels.append(Static("── STORAGE ANALYSIS ──────────────────────────────"))
        size_display = f"{total_gb:.2f} GB" if total_gb >= 1.0 else f"{total_mb:.2f} MB"
        labels.append(Label(f"TOTAL COLLECTION SIZE:     [bold magenta]{size_display}[/]"))
        labels.append(Label(f"AVG TRACK SIZE:            [bold magenta]{avg_mb:.2f} MB[/]"))
        labels.append(Label(f"MEDIAN TRACK SIZE:         [bold magenta]{median_size / (1024*1024):.2f} MB[/]"))
        labels.append(Label(f"DATA THROUGHPUT:           [bold magenta]{data_rate:.1f} KB/s[/]"))

        if largest_idx is not None:
            labels.append(Label(f"LARGEST TRACK:             [bold magenta]{largest_size / (1024*1024):.2f} MB[/]  {self._track_name(largest_idx)[:35]}"))
        if smallest_idx is not None:
            labels.append(Label(f"SMALLEST TRACK:            [bold magenta]{smallest_size / (1024*1024):.2f} MB[/]  {self._track_name(smallest_idx)[:35]}"))

        labels.append(Static("", id="spacer-3"))
        labels.append(Label("[dim]Full report saved to mission_history.json[/]"))
        labels.append(Button("ACKNOWLEDGMENTS (BACK TO OPS)", variant="primary", id="close-stats-btn"))

        yield Container(*labels, id="stats-box")

    @on(Button.Pressed, "#close-stats-btn")
    def close_stats(self) -> None:
        self.app.pop_screen()

class AetherApp(App):
    """The High-Agency Ingestion Vanguard."""
    
    TITLE = "AETHER AUDIO ARCHIVIST PRO // MATTHEW BUBB"
    SUB_TITLE = "SOLO ARCHITECT: MATTHEW BUBB"
    
    # ==========================================================================
    # CHROMA-SHIFT DESIGN SYSTEM
    # ==========================================================================
    THEMES = {
        "matrix": {
            "bg": "#050505",
            "surface": "#0a0a0a",
            "accent": "#00ff00",
            "text": "#00ff00",
            "dim": "#004400"
        },
        "cyberpunk": {
            "bg": "#0d0221",
            "surface": "#0f084b",
            "accent": "#00f5d4",
            "text": "#fee440",
            "dim": "#9b5de5"
        },
        "molten": {
            "bg": "#1a0f0f",
            "surface": "#2d1616",
            "accent": "#ff4d4d",
            "text": "#ffcc00",
            "dim": "#800000"
        }
    }

    visual_theme = reactive("matrix")

    # ==========================================================================
    # STATIC CSS — Parsed once at init. Theme colors injected via $variables.
    # ==========================================================================
    DEFAULT_CSS = """
    Screen {
        background: $bg;
        color: $text;
    }

    #launchpad-box {
        align: center middle;
        height: auto;
        width: 70;
        border: heavy $accent;
        padding: 1 3;
        background: $surface;
    }

    Static {
        text-align: center;
        width: 100%;
        color: $accent;
        text-style: bold;
    }

    Label {
        margin-top: 1;
        color: $dim;
        text-style: italic;
    }

    Input {
        background: $bg;
        color: #ffffff;
        border: solid $accent;
        margin-bottom: 2;
    }

    #init-btn {
        width: 100%;
        background: $dim;
        color: #ffffff;
        border: solid $accent;
        text-style: bold;
    }

    #url-row {
        height: auto;
        width: 100%;
    }

    #url-row Input {
        width: 1fr;
    }

    #paste-btn {
        width: 12;
        min-height: 3;
        margin-left: 1;
    }

    #main-container {
        height: 1fr;
    }

    #table-container {
        height: 70%;
        border: solid $accent;
    }

    #data-table {
        height: 1fr;
    }

    #action-bar {
        dock: bottom;
        height: 3;
        background: $surface;
        align: right middle;
        padding-right: 2;
        border-top: solid $dim;
    }

    #harvest-timer, #ingest-timer, #total-size-label, #rate-label {
        color: $accent;
        text-style: bold;
        margin-right: 2;
        width: auto;
    }
    
    #scroll-indicator {
        margin-right: 2;
        width: 12;
        text-align: center;
    }

    #go-btn {
        width: 30;
        min-height: 3;
        background: $accent;
        color: $bg;
        border: heavy $dim;
        text-style: bold;
    }

    #ingest-progress {
        width: 100%;
        margin-top: 1;
        color: $accent;
    }

    #ingest-progress > .bar--bar {
        color: $bg;
        background: $bg;
    }

    #ingest-progress > .bar--complete {
        background: $accent;
    }

    #hacker-log {
        height: 30%;
        border-top: solid $accent;
        background: #000000;
        color: $accent;
        padding-left: 1;
    }

    DataTable > .datatable--header {
        background: $surface;
        color: $accent;
        text-style: bold;
    }

    #stats-box {
        align: center middle;
        height: auto;
        width: 70;
        max-height: 90%;
        border: thick $accent;
        padding: 1 3;
        background: $bg;
        overflow-y: auto;
    }

    #stats-box Label {
        margin-top: 0;
        width: 100%;
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
        background: $surface;
    }

    #resolve-line-1, #resolve-line-2, #resolve-line-3 {
        color: #ffff00;
    }

    #spacer-a, #spacer-b {
        height: 1;
    }

    #history-container {
        padding: 1 3;
        border: solid $accent;
        height: 100%;
        background: $bg;
    }
    
    #history-table {
        margin-top: 1;
        height: 1fr;
        border: solid $dim;
    }

    #history-line-1, #history-line-2, #history-line-3 {
        color: $accent;
    }

    #launch-btns {
        height: auto;
        width: 100%;
    }

    #launch-btns Button {
        width: 1fr;
    }

    #watchdog-btn {
        margin-left: 1;
    }

    #watchdog-box {
        height: 100%;
        padding: 1 3;
        border: solid $accent;
        background: $bg;
    }

    #wd-line-1, #wd-line-2, #wd-line-3 {
        color: $accent;
    }

    #wd-status {
        margin-top: 1;
        color: $accent;
    }

    #wd-counts {
        color: $dim;
        text-style: bold;
    }

    #wd-log {
        height: 1fr;
        border: solid $dim;
        background: #000000;
        color: $accent;
        margin-top: 1;
        padding-left: 1;
    }

    #wd-table {
        height: 40%;
        border: solid $dim;
        margin-top: 1;
    }

    #wd-btn-row {
        height: auto;
        width: 100%;
        margin-top: 1;
    }

    #wd-btn-row Button {
        width: 1fr;
        margin-right: 1;
    }
    """

    def get_css_variables(self) -> dict[str, str]:
        """Inject theme color tokens into the CSS variable system."""
        variables = super().get_css_variables()
        t = self.THEMES[self.visual_theme]
        variables["accent"] = t["accent"]
        variables["bg"] = t["bg"]
        variables["surface"] = t["surface"]
        variables["text"] = t["text"]
        variables["dim"] = t["dim"]
        return variables

    def watch_visual_theme(self) -> None:
        if self._running:
            self.update_theme_vars()
            self.save_session_state()


    def __init__(self, url="", library="Aether_Archive", threads=36):
        super().__init__()
        self.default_url = url
        self.default_library = library
        self.default_threads = threads
        self._load_session_state()

    def _load_session_state(self) -> None:
        """Load persistent application state from disk."""
        try:
            state_file = Path(os.getcwd()) / "session_state.json"
            if state_file.exists():
                with open(state_file, "r", encoding='utf-8') as f:
                    state = json.load(f)
                    self.visual_theme = state.get("visual_theme", "matrix")
        except (Exception, json.JSONDecodeError):
            pass

    def save_session_state(self) -> None:
        """Persist application state to disk."""
        try:
            state_file = Path(os.getcwd()) / "session_state.json"
            state = {"visual_theme": self.visual_theme}
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def on_mount(self) -> None:
        self.update_theme_vars()
        self.push_screen(Launchpad())

    def update_theme_vars(self) -> None:
        """Surgically update CSS variables on the screen style object."""
        try:
            t = self.THEMES[self.visual_theme]
            self.screen.styles.css_variables = {
                "accent": t["accent"],
                "bg": t["bg"],
                "surface": t["surface"],
                "text": t["text"],
                "dim": t["dim"]
            }
        except Exception:
            # Fallback if screen is not yet available
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="")
    parser.add_argument("--threads", type=int, default=36)
    args = parser.parse_args()
    
    app = AetherApp(url=args.url, threads=args.threads)
    app.run()
