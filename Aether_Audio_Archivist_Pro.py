import os
import sys
import asyncio
import json
import random
import subprocess
from pathlib import Path
from datetime import datetime

# ==============================================================================
# AETHER AUDIO ARCHIVIST PRO // UNIFIED COMMAND CENTER
# ARCHITECT: MATTHEW BUBB (SOLE PROGRAMMER)
# ==============================================================================

def bootstrap_dependencies():
    """Ensure system vectors are aligned."""
    print("[*] SYNCING SYSTEM VECTORS (BOOTSTRAPPING)...")
    deps = ["playwright", "yt-dlp", "textual", "rich"]
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
from textual.widgets import Header, Footer, DataTable, Log, Input, Button, Label, Static, Select
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual import work, on
from textual.screen import Screen
from textual.message import Message

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
            Input(value=self.app.default_url, placeholder="https://open.spotify.com/playlist/...", id="url-input"),
            Label("CONCURRENCY THREADS (Surgical Multi-Thread):"),
            Input(value=str(self.app.default_threads), id="threads-input"),
            Label("ENGINE ACCELERATION (NVIDIA GPU / CPU):"),
            Select([("CPU (SYSTEM STANDARD)", "cpu"), ("GPU (NVIDIA CUDA)", "gpu")], value="cpu", id="engine-select"),
            Label("COLLECTION ALIAS (Library Name):"),
            Input(value=self.app.default_library, id="library-input"),
            Button("INITIALIZE MISSION", variant="success", id="init-btn"),
            id="launchpad-box"
        )
        yield Footer()

    @on(Button.Pressed, "#init-btn")
    def start_archivist(self) -> None:
        url = self.query_one("#url-input").value
        threads = self.query_one("#threads-input").value
        engine = self.query_one("#engine-select").value
        library = self.query_one("#library-input").value

        if not url:
            self.app.notify("CRITICAL: SOURCE URL MISSING", severity="error")
            return

        try:
            thread_count = int(threads)
        except ValueError:
            thread_count = 36

        self.app.push_screen(Archivist(url, library, thread_count, engine))

class Archivist(Screen):
    """The Operational Command Center."""

    BINDINGS = [
        Binding("space", "toggle_select", "Toggle Selected"),
        Binding("a", "select_all", "Select Global All"),
        Binding("n", "select_none", "Deselect All"),
        Binding("enter", "start_ingest", "COMMENCE INGESTION"),
        Binding("escape", "app.pop_screen", "Back to Launchpad"),
    ]

    def __init__(self, url: str, library: str, threads: int, engine: str):
        super().__init__()
        self.url = url
        self.library = library
        self.threads = threads
        self.engine = engine
        self.tracks = []
        self.target_dir = Path(os.getcwd()) / "Audio_Libraries" / self.library
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(threads)
        self.is_scraping = True
        self.col_keys = {}
        self.stats = {"total": 0, "complete": 0, "no_match": 0, "failed": 0}
        self.pending_tasks = 0
        self.mission_start = datetime.now()
        self.track_times = {}
        self.track_sizes = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="table-container"):
                yield DataTable(id="data-table")
                with Horizontal(id="action-bar"):
                    yield Button("GO (COMMENCE INGESTION)", id="go-btn", variant="success")
            yield Log(id="hacker-log", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        self.col_keys["SEL"] = table.add_column("SEL")
        self.col_keys["STATUS"] = table.add_column("STATUS")
        self.col_keys["ARTIST"] = table.add_column("ARTIST")
        self.col_keys["TITLE"] = table.add_column("TITLE")
        self.col_keys["DUR"] = table.add_column("DUR")

        table.cursor_type = "row"
        self.log_kernel("SYSTEM INITIALIZED. WELCOME, ARCHITECT BUBB.")
        self.scrape_tracks()

    def log_kernel(self, message: str):
        log_widget = self.query_one(Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_widget.write_line(f"[{timestamp}] {message}")

    @work(exclusive=True)
    async def scrape_tracks(self):
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

                self.log_kernel("HARVESTING VECTORS (REAL-TIME PROPAGATION)...")

                # Infinite Scroll Engine
                last_count = -1
                stable_count = 0
                while stable_count < 10: # More aggressive stability check
                    # Find current rows to scroll the last one into view
                    rows = await page.query_selector_all('[data-testid="tracklist-row"]')
                    if rows:
                        try:
                            await rows[-1].scroll_into_view_if_needed()
                        except:
                            pass

                    # Additional scrolling to ensure we hit the bottom
                    await page.mouse.wheel(0, 5000)
                    for _ in range(4):
                         await page.keyboard.press("PageDown")
                         await asyncio.sleep(0.5)

                    # Re-query rows in current viewport for processing
                    rows = await page.query_selector_all('[data-testid="tracklist-row"]')
                    for row in rows:
                        try:
                            title_elem = await row.query_selector('div[dir="auto"]')
                            title = await title_elem.inner_text() if title_elem else "Unknown"

                            artist_elems = await row.query_selector_all('a[href*="/artist/"]')
                            artists = ", ".join([await a.inner_text() for a in artist_elems])

                            # Surgical ID creation to handle virtualized list duplicates
                            track_id = f"{artists}_{title}".strip()
                            if track_id and track_id not in processed_ids:
                                processed_ids.add(track_id)

                                dur_elem = await row.query_selector('div[data-testid="tracklist-row-duration"]')
                                duration = "0:00"
                                if dur_elem:
                                    duration = await dur_elem.inner_text()
                                else:
                                    # Tighten fallback to avoid album names with colons
                                    potential_durs = await row.query_selector_all('div:has-text(":")')
                                    for p in potential_durs:
                                        text = await p.inner_text()
                                        if dur_regex.match(text.strip()):
                                            duration = text.strip()
                                            break

                                idx = len(self.tracks)
                                self.tracks.append({
                                    "artist": artists,
                                    "title": title,
                                    "duration": duration,
                                    "selected": True,
                                    "status": "WAITING FOR PROPAGATION OF PLAYLIST ITEMS"
                                })
                                table.add_row("[X]", "[yellow]WAITING FOR PROPAGATION[/]", artists, title[:40], duration, key=str(idx))
                        except Exception: continue

                    current_count = len(self.tracks)
                    if current_count == last_count:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_count = current_count
                        if current_count > 0:
                            self.log_kernel(f"PROPAGATED {current_count} VECTORS...")

                self.is_scraping = False
                self.log_kernel(f"COMPLETE HARVEST: {len(self.tracks)} TRACK DESCRIPTORS.")

                # Flip statuses only after full harvest
                status_key = self.col_keys["STATUS"]
                for i in range(len(self.tracks)):
                    self.tracks[i]["status"] = "QUEUED"
                    try:
                        table.update_cell(str(i), status_key, "[white]QUEUED[/]")
                    except: pass

                self.log_kernel("VECTORS SYNCHRONIZED. READY FOR INGESTION.")
            except Exception as e:
                self.log_kernel(f"CRITICAL SCRAPE FAILURE: {e}")
                import traceback
                self.log_kernel(traceback.format_exc())
            finally:
                await browser.close()

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
            self.app.notify("WARNING: STILL PROXIMITING VECTORS", severity="warning")
            return

        selected = [i for i, t in enumerate(self.tracks) if t["selected"]]
        if not selected:
             self.app.notify("ERROR: NO VECTORS SELECTED", severity="error")
             return

        self.stats = {"total": len(selected), "complete": 0, "no_match": 0, "failed": 0}
        self.pending_tasks = len(selected)
        self.log_kernel(f"COMMENCING THREADED INGESTION (DEPTH: {self.threads}, ENGINE: {self.engine.upper()}).")
        for idx in selected:
            self.ingest_worker(idx)

    @work
    async def ingest_worker(self, index: int):
        async with self.semaphore:
            track = self.tracks[index]
            self.tracks[index]["status"] = "ARCHIVING"
            self.post_message(TrackUpdate(index, "ARCHIVING", "cyan"))
            track_start = datetime.now()

            try:
                # High-Fidelity Logic with fallback queries
                queries = [
                    f"{track['artist']} {track['title']} official audio",
                    f"{track['artist']} {track['title']} official video",
                    f"{track['artist']} {track['title']} lyrics",
                    f"{track['artist']} {track['title']}"
                ]

                results = []
                for query in queries:
                    if results:
                        break
                    try:
                        search_cmd = [sys.executable, "-m", "yt_dlp", f"ytsearch5:{query}", "--dump-json", "--flat-playlist"]
                        proc = await asyncio.create_subprocess_exec(*search_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                        stdout, _ = await proc.communicate()
                        results = [json.loads(line) for line in stdout.decode().strip().split("\n") if line]
                    except:
                        continue

                spotify_dur = self.parse_duration(track['duration'])

                best = None
                min_diff = 999
                for entry in results:
                    duration = entry.get('duration', 0)
                    if duration > 0:
                        diff = abs(duration - spotify_dur)
                        if diff < 30 and diff < min_diff:
                            min_diff, best = diff, entry

                if not best:
                    if results:
                        self.tracks[index]["status"] = "AWAITING USER DECISION"
                        self.post_message(TrackUpdate(index, "AWAITING USER DECISION", "yellow"))
                        self.post_message(ResolveFailed(index, track, results[:3]))
                        await asyncio.sleep(0.5)
                        while self.tracks[index].get("youtube_url") is None and self.tracks[index]["status"] == "AWAITING USER DECISION":
                            await asyncio.sleep(0.2)

                        if self.tracks[index].get("youtube_url"):
                            best = {"url": self.tracks[index]["youtube_url"], "id": self.tracks[index].get("youtube_id", "manual")}
                        else:
                            self.tracks[index]["status"] = "NO MATCH"
                            self.stats["no_match"] += 1
                            self.post_message(TrackUpdate(index, "NO MATCH", "orange"))
                            return
                    else:
                        self.tracks[index]["status"] = "NO MATCH"
                        self.stats["no_match"] += 1
                        self.post_message(TrackUpdate(index, "NO MATCH", "orange"))
                        return

                # Sanitize filename
                final_name = "".join([c if c.isalnum() or c in " -_." else "_" for c in f"{track['artist']} - {track['title']}.mp3"])
                dest = self.target_dir / final_name
                temp_path = self.target_dir / f"tmp_{best['id']}.mp3"

                # High-Quality Download (320kbps MP3)
                encoder_args = ["--audio-quality", "0"]
                gpu_args = []
                if self.engine == "gpu":
                     self.log_kernel(f"GPU MODE: ENGAGING NVIDIA CUDA ACCELERATION FOR {track['title']}")
                     gpu_args = ["--postprocessor-args", "ffmpeg:-hwaccel cuda"]
                else:
                     self.log_kernel(f"CPU MODE: PROCESSING {track['title']} (NO GPU ACCELERATION)")

                dl_cmd = [
                    sys.executable, "-m", "yt_dlp", best['url'],
                    "--extract-audio", "--audio-format", "mp3",
                    "--output", str(temp_path.with_suffix("")), "--no-playlist"
                ] + encoder_args + gpu_args
                proc = await asyncio.create_subprocess_exec(*dl_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

                # Tagging (FFmpeg) with Metadata and Hardware Acceleration support
                tag_prefix = ["ffmpeg"]
                if self.engine == "gpu":
                    tag_prefix = ["ffmpeg", "-hwaccel", "cuda"]

                tag_cmd = tag_prefix + [
                    "-i", str(temp_path),
                    "-metadata", f"artist={track['artist']}", "-metadata", f"title={track['title']}",
                    "-codec", "copy", str(dest), "-y"
                ]
                proc = await asyncio.create_subprocess_exec(*tag_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

                if temp_path.exists(): os.remove(temp_path)

                # Track metrics
                elapsed = (datetime.now() - track_start).total_seconds()
                self.track_times[index] = elapsed
                if dest.exists():
                    self.track_sizes[index] = dest.stat().st_size

                self.tracks[index]["status"] = "COMPLETE"
                self.stats["complete"] += 1
                self.post_message(TrackUpdate(index, "COMPLETE", "green"))
                self.log_kernel(f"COMPLETE: {track['title']} ({elapsed:.1f}s)")

            except Exception as e:
                self.tracks[index]["status"] = "FAILED"
                self.stats["failed"] += 1
                self.post_message(TrackUpdate(index, "FAILED", "red"))
                self.log_kernel(f"FAIL: {track['title']} ({e})")
            finally:
                self.pending_tasks -= 1
                if self.pending_tasks == 0:
                    mission_end = datetime.now()
                    total_time = (mission_end - self.mission_start).total_seconds()
                    self.save_mission_report(total_time)
                    self.app.push_screen(StatsScreen(self.stats, self.track_times, self.track_sizes, total_time))

    def on_track_update(self, message: TrackUpdate) -> None:
        table = self.query_one(DataTable)
        try:
            table.update_cell(str(message.index), self.col_keys["STATUS"], f"[{message.color}]{message.status}[/]")
        except: pass

    def on_resolve_failed(self, message: ResolveFailed) -> None:
        self.app.push_screen(ResolveMatchScreen(message.index, message.track, message.results, self))

    def parse_duration(self, d_str):
        try:
            parts = d_str.split(":")
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except: return 0
        return 0

    def save_mission_report(self, total_time):
        import hashlib
        playlist_id = hashlib.md5(self.url.encode()).hexdigest()[:8]
        history_file = Path(os.getcwd()) / "mission_history.json"

        avg_time = total_time / max(self.stats["complete"], 1)
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
            "total_time": round(total_time, 2),
            "avg_time_per_song": round(avg_time, 2),
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
            with open(history_file, 'r') as f:
                history = json.load(f)

        history.append(report)
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        self.log_kernel(f"MISSION REPORT SAVED: {history_file}")

class ResolveMatchScreen(Screen):
    """Screen to resolve failed track matches by showing user options."""
    def __init__(self, index: int, track: dict, results: list, parent: Screen):
        super().__init__()
        self.index = index
        self.track = track
        self.results = results
        self.parent = parent

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
                self.parent.tracks[self.index]["youtube_url"] = None
            elif 1 <= choice <= len(self.results):
                selected = self.results[choice - 1]
                self.parent.tracks[self.index]["youtube_url"] = selected.get('url')
                self.parent.tracks[self.index]["youtube_id"] = selected.get('id')
            self.app.pop_screen()

class StatsScreen(Screen):
    """The Mission Summary Vanguard."""
    def __init__(self, stats: dict, track_times: dict = None, track_sizes: dict = None, total_time: float = 0):
        super().__init__()
        self.stats = stats
        self.track_times = track_times or {}
        self.track_sizes = track_sizes or {}
        self.total_time = total_time

    def compose(self) -> ComposeResult:
        total = self.stats["total"]
        complete = self.stats["complete"]
        no_match = self.stats["no_match"]
        failed = self.stats["failed"]

        avg_time = self.total_time / max(complete, 1)
        largest_size = max(self.track_sizes.values()) if self.track_sizes else 0
        largest_mb = largest_size / (1024 * 1024)

        time_str = f"{int(self.total_time // 60)}m {int(self.total_time % 60)}s"
        avg_time_str = f"{int(avg_time // 60)}m {int(avg_time % 60)}s" if avg_time > 0 else "0s"

        yield Container(
            Static("==================================================", id="stats-line-1"),
            Static("         INGESTION MISSION REPORT: COMPLETE       ", id="stats-line-2"),
            Static("==================================================", id="stats-line-3"),
            Label(f"TOTAL VECTORS TARGETED: {total}"),
            Label(f"SUCCESSFULLY ARCHIVED:  [bold green]{complete}[/]"),
            Label(f"NO MATCH FOUND:         [bold yellow]{no_match}[/]"),
            Label(f"SYSTEM FAILURES:        [bold red]{failed}[/]"),
            Static("", id="spacer-1"),
            Label(f"TOTAL MISSION TIME:     [bold cyan]{time_str}[/]"),
            Label(f"AVG TIME PER TRACK:     [bold cyan]{avg_time_str}[/]"),
            Label(f"LARGEST TRACK SIZE:     [bold magenta]{largest_mb:.2f} MB[/]"),
            Static("", id="spacer-2"),
            Label("[dim]Full report saved to mission_history.json[/]"),
            Button("ACKNOWLEDGMENTS (BACK TO OPS)", variant="primary", id="close-stats-btn"),
            id="stats-box"
        )

    @on(Button.Pressed, "#close-stats-btn")
    def close_stats(self) -> None:
        self.app.pop_screen()

class AetherApp(App):
    """The High-Agency Ingestion Vanguard."""

    TITLE = "AETHER AUDIO ARCHIVIST PRO // MATTHEW BUBB"
    SUB_TITLE = "SOLO ARCHITECT: MATTHEW BUBB"

    CSS_PATH = "Aether_Audio_Archivist_Pro.tcss"

    def __init__(self, url="", library="Aether_Archive", threads=36):
        super().__init__()
        self.default_url = url
        self.default_library = library
        self.default_threads = threads

    def on_mount(self) -> None:
        self.push_screen(Launchpad())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="")
    parser.add_argument("--library", default="Aether_Archive")
    parser.add_argument("--threads", type=int, default=36)
    args = parser.parse_args()

    app = AetherApp(url=args.url, library=args.library, threads=args.threads)
    app.run()
