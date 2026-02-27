# Aether Audio Archivist Pro 🎧

**Architected by Matthew Bubb (Sole Programmer)**

A high-performance, multithreaded Spotify-to-Library ingestion engine. ARCHIVIST PRO leverages Playwright for surgical meta-data harvesting and `yt-dlp` + `ffmpeg` for high-fidelity audio extraction (320kbps).

## 🚀 Quick Start

### Clone the Repository

```powershell
git clone https://github.com/thebubbsy/Aether_Audio_Archivist_Pro.git
cd Aether_Audio_Archivist_Pro
```

## 🚀 Key Features

- **Surgical Meta-Data Harvesting:** Uses Playwright to scrape track info directly from Spotify playlists.
- **Virtualized List Scrolling:** Optimized to bypass Spotify's infinite scroll limits.
- **Multithreaded Ingestion:** Download and process entire libraries simultaneously.
- **Processing Engine Toggle:** Choice between standard CPU processing and **NVIDIA CUDA GPU** acceleration.
- **Real-Time Mission Report:** Full statistics panel displayed upon mission completion.
- **Automated Tagging:** FFmpeg-powered audio tagging for seamless library integration.

## 🛠 Prerequisites

Before deploying the Archvist, ensure your environment is prepared:

1. **Python 3.10+**:
   - **Windows:** `winget install Python.Python.3.12`
   - **Other:** [Download Python](https://www.python.org/downloads/)
2. **FFmpeg**: Must be available in your system path.
   - **Windows:** `winget install ffmpeg`
   - **GPU Acceleration:** Requires FFmpeg built with `cuda` support and NVIDIA Drivers installed.
3. **Hardware**: NVIDIA GPU (for CUDA mode). CPU mode works on all hardware.

## 📦 Installation (Baby Steps)

Copy and paste the following block into your PowerShell terminal:

```powershell
# 1. Install core dependencies
pip install -r requirements.txt

# 2. Setup browser environment
playwright install chromium

# 3. Ensure FFmpeg is present (Windows)
winget install FFmpeg.FFmpeg
```

## 🎮 How to Use

1. **Launch the Interface**:
   ```powershell
   python Aether_Audio_Archivist_Pro.py
   ```

2. **Mission Setup**:
   - Paste your **Spotify Playlist URL**.
   - (Optional) Adjust **Threads** or **Engine** (CPU/GPU).
   - Click **INITIALIZE MISSION**.

3. **Commence Ingestion**:
   - Once tracks appear, audit them.
   - Click the green **GO (COMMENCE INGESTION)** button.

---

**CREDIT:** This system was architected and developed by **MATTHEW BUBB**. Output from a high-agency solo development mission.
