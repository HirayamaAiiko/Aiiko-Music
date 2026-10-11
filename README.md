<p align="center">
  <img src="images/now_playing.png" alt="Aiiko Music - Now Playing" width="100%">
</p>

<h1 align="center">Aiiko Music</h1>

<p align="center">
  <strong>A desktop music player for your own music library.</strong>
</p>

<p align="center">
  <a href="https://github.com/HirayamaAiiko/Aiiko-Music/releases"><img src="https://img.shields.io/github/v/release/HirayamaAiiko/Aiiko-Music?label=Release&color=0078D6" alt="Latest Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue.svg" alt="License"></a>
</p>

<p align="center">
  Aiiko Music is a local music player for Windows, designed around personal music collections. It brings playback, albums, artists, playlists, lyrics, and metadata together in one place.
</p>

---

## Features

### Audio & Playback
- **10-band equalizer** with custom tuning
- **Gapless playback** for uninterrupted listening
- **Queue and shuffle playback** modes
- **Audio visualizer**

### Library & Organization
- **Local music library** management
- **Album and artist browsing**
- **Playlist management**
- **Library-wide search** to find tracks instantly

### Lyrics & Metadata
- **Lyrics support**, including local `.lrc` files and an integrated online finder
- **Advanced lyrics editor** with synchronization tools
- **Metadata editor** for tagging your collection
- **Album artwork** display and handling

### Experience & Customization
- **Floating mini player**
- **Fullscreen viewer**
- **Appearance & accent customization**
- **Discord Rich Presence**
- **Last.fm scrobbling**
- **Keyboard shortcuts**

---

## Screenshots

<p align="center">
  <img src="images/library.png" alt="Aiiko Music - Library" width="48%">
  <img src="images/home.png" alt="Aiiko Music - Home & Player" width="48%">
</p>

<p align="center">
  <img src="images/universal_search.png" alt="Aiiko Music - Universal Search" width="48%">
  <img src="images/artist_detail.png" alt="Aiiko Music - Artist Detail" width="48%">
</p>

<p align="center">
  <img src="images/artist.png" alt="Aiiko Music - Artists View" width="48%">
  <img src="images/playlist.png" alt="Aiiko Music - Playlists" width="48%">
</p>

### Lyrics Editor

Advanced lyrics editor and search tool with fine-tuned line timing:

<p align="center">
  <img src="images/lyrics_edit.png" alt="Aiiko Music - Lyrics Editor" width="85%">
</p>

---

## Supported Audio

Aiiko Music supports common audio formats through its playback engine:

<p align="center">
  <img src="images/icons/mp3.svg" width="56" alt="MP3">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/flac.svg" width="56" alt="FLAC">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/wav.svg" width="56" alt="WAV">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/ogg.svg" width="56" alt="OGG">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/acc.svg" width="56" alt="AAC">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/m4a.svg" width="56" alt="M4A">&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/icons/aiiko.svg" width="56" alt="AIIKO">
</p>

> *Format support may depend on the capabilities of the playback engine.*

---

## Built With

Aiiko Music is built with Python and Qt, leveraging modern libraries for playback, UI, and audio processing:

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Core application framework
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) — Fluent Design UI components
- [PyQt-Frameless-Window](https://github.com/zhiyiYo/PyQt-Frameless-Window) — Modern frameless window management
- [BASS](https://www.un4seen.com/bass.html) — Low-latency audio playback engine
- [Mutagen](https://mutagen.readthedocs.io/) — Audio metadata and tagging
- [pyqtgraph](https://www.pyqtgraph.org/) — Real-time audio visualization
- [Pillow](https://python-pillow.org/) — Image processing and album artwork

For a full list of dependencies, see [`requirements.txt`](requirements.txt). Third-party libraries and components are maintained by their respective authors and are subject to their own licenses.

---

## Installation & Download (Windows 10 & 11)

### Option 1: Standalone Release (Recommended)

The easiest way to use Aiiko Music is to download the latest executable release:

👉 **[Download Aiiko Music](https://github.com/HirayamaAiiko/Aiiko-Music/releases)**

1. Extract the downloaded `.zip` file to a folder.
2. Launch the `.exe` and follow the on-screen setup prompts displayed on first run.

### Option 2: Running from Source

To run the project directly from source:

```bash
# Clone the repository
git clone https://github.com/HirayamaAiiko/Aiiko-Music.git
cd Aiiko-Music

# Install required dependencies
pip install -r requirements.txt

# Run the application
python app/main.py
