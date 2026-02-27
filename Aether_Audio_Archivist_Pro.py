import os
import sys
import asyncio
import json
import random
import subprocess
import functools
import re
import yt_dlp
from pathlib import Path
from datetime import datetime

# ARCHITECT: MATTHEW BUBB (SOLE PROGRAMMER)
# ==============================================================================

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DUR_REGEX = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$')

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
from textual.widgets import Header, Footer, DataTable, Log, Input, Button, Label, Static, Select, ProgressBar
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual.reactive import reactive
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
            Label("VISUAL VECTOR (Theme Selection):"),
            Select([("MATRIX (GREEN)", "matrix"), ("CYBERPUNK (NEON)", "cyberpunk"), ("MOLTEN (RED)", "molten")], value=self.app.visual_theme, id="theme-select"),
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
        theme = self.query_one("#theme-select").value
        self.app.visual_theme = theme
        
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

    def __init__(self, url="", library="Aether_Archive", threads=36, engine="cpu"):
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
        self.semaphore = asyncio.Semaphore(threads)
        self.is_ingesting = False
        self.harvest_dur = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="table-container"):
                yield DataTable(id="data-table")
                yield ProgressBar(id="ingest-progress", total=100, show_eta=True)
            yield Log(id="hacker-log", highlight=True)
        with Horizontal(id="action-bar"):
             yield Button("GO (COMMENCE INGESTION)", id="go-btn", variant="success")
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
                            table.add_row("[X]", "[yellow]WAITING FOR PROPAGATION[/]", track_data['artists'], track_data['title'][:40], track_data['duration'], key=str(idx))
                    
                    current_count = len(self.tracks)
                    if current_count == last_count:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_count = current_count
                        if current_count > 0:
                            self.log_kernel(f"PROPAGATED {current_count} VECTORS...")
                    
                    # PROACTIVE MATCHING: Resolve vectors immediately
                    for i in range(len(self.tracks)):
                        if self.tracks[i]["status"] == "WAITING FOR PROPAGATION":
                            self.tracks[i]["status"] = "MATCHING"
                            table.update_cell(str(i), self.col_keys["STATUS"], "[cyan]MATCHING[/]")
                            # Run matching in background worker to avoid blocking the harvest loop
                            self.match_vector(i)

                self.is_scraping = False
                self.harvest_dur = (datetime.now() - self.harvest_start).total_seconds()
                self.log_kernel(f"COMPLETE HARVEST: {len(self.tracks)} TRACK DESCRIPTORS IN {self.harvest_dur:.1f}s.")
                self.log_kernel("VECTORS SYNCHRONIZED. READY FOR INGESTION.")
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
            self.app.notify("WARNING: STILL PROXIMITING VECTORS", severity="warning")
            return
        
        if self.is_ingesting:
            self.app.notify("WARNING: INGESTION ALREADY COMMENCED", severity="warning")
            return
            
        selected = [i for i, t in enumerate(self.tracks) if t["selected"]]
        if not selected:
             self.app.notify("ERROR: NO VECTORS SELECTED", severity="error")
             return
        
        self.is_ingesting = True
        self.query_one(ProgressBar).update(total=len(selected), progress=0)
        
        # Reset stats without replacing the dictionary object reference
        self.stats.update({"total": len(selected), "complete": 0, "no_match": 0, "failed": 0})
        self.track_times.clear()
        self.track_sizes.clear()
        
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
                # [PHASE 1] SURGICAL SEARCH (USE PRE-MATCHED IF AVAILABLE)
                best = track.get("youtube_best")
                if not best:
                    best = await self.search_track(index, track)
                
                if not best:
                    # search_track already called mark_no_match
                    return

                # [PHASE 2] HIGH-QUALITY DOWNLOAD
                temp_path = await self.download_track(index, track, best)
                if not temp_path:
                    # Signal dropout during capture
                    self.tracks[index]["status"] = "FAILED"
                    self.stats["failed"] += 1
                    self.post_message(TrackUpdate(index, "FAILED", "red"))
                    self.query_one(ProgressBar).advance(1)
                    self.log_kernel(f"SIGNAL LOSS: {track['title']} (Download Failed)")
                    return

                # [PHASE 3] METADATA TAGGING
                elapsed = (datetime.now() - track_start).total_seconds()
                success = await self.tag_track(index, track, temp_path, elapsed)
                if not success:
                    # Tagging failure is still a system failure
                    self.tracks[index]["status"] = "FAILED"
                    self.stats["failed"] += 1
                    self.post_message(TrackUpdate(index, "FAILED", "red"))
                    self.query_one(ProgressBar).advance(1)
                    return
                
            except Exception as e:
                self.tracks[index]["status"] = "FAILED"
                self.stats["failed"] += 1
                self.post_message(TrackUpdate(index, "FAILED", "red"))
                self.query_one(ProgressBar).advance(1)
                self.log_kernel(f"FAIL: {track['title']} ({e})")
            finally:
                self.pending_tasks -= 1
                if self.pending_tasks == 0:
                    mission_end = datetime.now()
                    total_time = (mission_end - self.mission_start).total_seconds()
                    await self.close_mission(total_time)

    async def search_track(self, index, track):
        """Phase 1: High-Fidelity Search Vector."""
        queries = [
            f"{track['artist']} {track['title']} official audio",
            f"{track['artist']} {track['title']} official video",
            f"{track['artist']} {track['title']} lyrics",
            f"{track['artist']} {track['title']}"
        ]
        
        results = []
        for query in queries:
            if results: break
            try: results = await self.perform_youtube_search(query)
            except: continue
        
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
                while self.tracks[index].get("youtube_url") is None and self.tracks[index]["status"] == "AWAITING USER DECISION":
                    await asyncio.sleep(0.2)
                
                if self.tracks[index].get("youtube_url"):
                    best = {"url": self.tracks[index]["youtube_url"], "id": self.tracks[index].get("youtube_id", "manual")}
                else:
                    self.mark_no_match(index)
                    return None
            else:
                self.mark_no_match(index)
                return None
        return best

    def mark_no_match(self, index):
        self.tracks[index]["status"] = "NO MATCH"
        self.stats["no_match"] += 1
        self.query_one(ProgressBar).advance(1)
        self.post_message(TrackUpdate(index, "NO MATCH", "orange"))

    async def download_track(self, index, track, best):
        """Phase 2: Encrypted Signal Capture (Download)."""
        temp_path = self.target_dir / f"tmp_{best['id']}.mp3"
        encoder_args = ["--audio-quality", "0"]
        gpu_args = []
        
        if self.engine == "gpu":
             self.log_kernel(f"GPU MODE: ENGAGING NVIDIA CUDA FOR {track['title']}")
             gpu_args = ["--postprocessor-args", "ffmpeg:-hwaccel cuda"]
        else:
             self.log_kernel(f"CPU MODE: PROCESSING {track['title']}")
        
        dl_cmd = [
            sys.executable, "-m", "yt_dlp", best['url'],
            "--extract-audio", "--audio-format", "mp3", 
            "--output", str(temp_path.with_suffix("")), "--no-playlist"
        ] + encoder_args + gpu_args
        
        proc = await asyncio.create_subprocess_exec(*dl_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return temp_path if await asyncio.to_thread(lambda: temp_path.exists()) else None

    async def tag_track(self, index, track, temp_path, elapsed):
        """Phase 3: Metadata Imprinting and Finalization."""
        final_name = "".join([c if c.isalnum() or c in " -_." else "_" for c in f"{track['artist']} - {track['title']}.mp3"])
        dest = self.target_dir / final_name
        
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
        
        if await asyncio.to_thread(lambda: temp_path.exists()):
            await asyncio.to_thread(os.remove, temp_path)
        
        if await asyncio.to_thread(lambda: os.path.exists(dest)):
            stat = await asyncio.to_thread(os.stat, dest)
            self.track_sizes[index] = stat.st_size
            self.track_times[index] = elapsed
            self.tracks[index]["status"] = "COMPLETE"
            self.stats["complete"] += 1
            self.post_message(TrackUpdate(index, "COMPLETE", "green"))
            self.query_one(ProgressBar).advance(1)
            self.log_kernel(f"COMPLETE: {track['title']} ({elapsed:.1f}s)")
            return True
        else:
            self.log_kernel(f"TAGGING FAILURE: {track['title']} (Output not found)")
            return False

    async def close_mission(self, total_time):
        total_time = round(total_time, 2)
        await self.save_mission_report(total_time)
        try:
            # Convenience: Open Explorer window to the target directory
            await asyncio.to_thread(os.startfile, str(self.target_dir))
        except:
            pass
        self.app.push_screen(StatsScreen(self.stats, self.track_times, self.track_sizes, total_time, self.harvest_dur))

    def on_track_update(self, message: TrackUpdate) -> None:
        table = self.query_one(DataTable)
        try:
            table.update_cell(str(message.index), self.col_keys["STATUS"], f"[{message.color}]{message.status}[/]")
        except: pass
    
    def on_resolve_failed(self, message: ResolveFailed) -> None:
        self.app.push_screen(ResolveMatchScreen(message.index, message.track, message.results, self))

    async def perform_youtube_search(self, query: str) -> list:
        """Surgical search vector using direct yt-dlp library access."""
        def run_search():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
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
    
    async def save_mission_report(self, total_time):
        """Asynchronous mission debriefing."""
        import hashlib
        playlist_id = hashlib.md5(self.url.encode()).hexdigest()[:8]
        history_file = Path(os.getcwd()) / "mission_history.json"
        
        def _write_report_to_disk():
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
                "harvest_duration_seconds": round(self.harvest_dur, 2),
                "total_time_seconds": round(total_time, 2),
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
            return history_file

        saved_path = await asyncio.to_thread(_write_report_to_disk)
        self.log_kernel(f"MISSION REPORT SAVED: {saved_path}")

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
    def __init__(self, stats: dict, track_times: dict = None, track_sizes: dict = None, total_time: float = 0, harvest_dur: float = 0):
        super().__init__()
        self.stats = stats
        self.track_times = track_times or {}
        self.track_sizes = track_sizes or {}
        self.total_time = total_time
        self.harvest_dur = harvest_dur

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
            Label(f"HARVEST DURATION:      [bold yellow]{self.harvest_dur:.1f}s[/]"),
            Label(f"INGESTION TIME:        [bold cyan]{time_str}[/]"),
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

    def get_css(self) -> str:
        t = self.THEMES[self.visual_theme]
        return f"""
        Screen {{
            background: {t['bg']};
            color: {t['text']};
        }}

        #launchpad-box {{
            align: center middle;
            height: auto;
            width: 70;
            border: heavy {t['accent']};
            padding: 1 3;
            background: {t['surface']};
        }}

        Static {{
            text-align: center;
            width: 100%;
            color: {t['accent']};
            text-style: bold;
        }}

        Label {{
            margin-top: 1;
            color: {t['dim']};
            text-style: italic;
        }}

        Input {{
            background: {t['bg']};
            color: #ffffff;
            border: solid {t['accent']};
            margin-bottom: 2;
        }}

        #init-btn {{
            width: 100%;
            background: {t['dim']};
            color: #ffffff;
            border: solid {t['accent']};
            text-style: bold;
        }}

        #main-container {{
            height: 100%;
        }}

        #table-container {{
            height: 70%;
            border: solid {t['accent']};
        }}

        #data-table {{
            height: 1fr;
        }}

        #action-bar {{
            dock: bottom;
            height: 3;
            background: transparent;
            align: right middle;
            padding-right: 2;
            margin-bottom: 2;
        }}

        #go-btn {{
            width: 30;
            min-height: 3;
            background: {t['accent']};
            color: {t['bg']};
            border: heavy {t['dim']};
            text-style: bold;
        }}

        #ingest-progress {{
            width: 100%;
            margin-top: 1;
            color: {t['accent']};
        }}

        #ingest-progress > .bar--bar {{
            color: {t['bg']};
            background: {t['bg']};
        }}

        #ingest-progress > .bar--complete {{
            background: {t['accent']};
        }}

        #hacker-log {{
            height: 30%;
            border-top: solid {t['accent']};
            background: #000000;
            color: {t['accent']};
            padding-left: 1;
        }}

        DataTable > .datatable--header {{
            background: {t['surface']};
            color: {t['accent']};
            text-style: bold;
        }}

        #stats-box {{
            align: center middle;
            height: auto;
            width: 60;
            border: thick {t['accent']};
            padding: 1 3;
            background: {t['bg']};
        }}

        #stats-box Label {{
            margin-top: 1;
            width: 100%;
            text-align: left;
        }}

        #close-stats-btn {{
            margin-top: 2;
            width: 100%;
        }}

        #resolve-box {{
            align: center middle;
            height: auto;
            width: 80;
            border: heavy #ffff00;
            padding: 1 3;
            background: {t['surface']};
        }}

        #resolve-line-1, #resolve-line-2, #resolve-line-3 {{
            color: #ffff00;
        }}

        #spacer-a, #spacer-b {{
            height: 1;
        }}
        """

    def watch_visual_theme(self) -> None:
        self.css = self.get_css()


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
