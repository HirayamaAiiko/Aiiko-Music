# Aiiko Music

A desktop music player for your own music library and I'm so cooking .

Aiiko Music is a local music player for Windows, designed around personal music collections. It brings playback, albums, artists, playlists, lyrics and metadata together in one place.

## Features

- Local music library
- Album and artist browsing
- Playlist management
- Queue and shuffle playback
- Gapless playback
- Lyrics support, including `.lrc` files
- Metadata editing
- Album artwork
- Audio visualizer
- Discord Rich Presence
- Keyboard shortcuts
- Library-wide search
- Floating mini player
- Appearance and accent customization
- Last.fm scrrobbling

## Screenshots

Waiing

## Supported Audio

Aiiko Music supports common audio formats through its playback engine, including:

- MP3
- FLAC
- WAV
- OGG
- M4A

Format support may depend on the capabilities of the playback engine.

## Built With

Aiiko Music is built with Python and Qt.

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [PyQt-Frameless-Window](https://github.com/zhiyiYo/PyQt-Frameless-Window)
- [BASS](https://www.un4seen.com/bass.html)
- [Mutagen](https://mutagen.readthedocs.io/)
- [pyqtgraph](https://www.pyqtgraph.org/)
- [Pillow](https://python-pillow.org/)

Check requeriments.txt
Third-party libraries and components are maintained by their respective authors and are subject to their own licenses.

## Installation

The easiest way to use Aiiko Music is to download the latest release:

[Download Aiiko Music](https://github.com/HirayamaAiiko/Aiiko-Music/releases)

To run the project from source:

```bash
git clone https://github.com/HirayamaAiiko/Aiiko-Music.git
cd Aiiko-Music
pip install -r requirements.txt
python main.py
```

Aiiko Music currently targets Windows.

## BASS Licensing

Aiiko Music uses **BASS** by Un4seen Developments Ltd. for audio playback.

BASS is free for non-commercial use. Commercial distribution requires an appropriate BASS license.

Please refer to the [BASS licensing terms](https://www.un4seen.com/bass.html) before redistributing Aiiko Music commercially.

## License

Aiiko Music is licensed under the **GNU General Public License v3.0**.

See [`LICENSE`](LICENSE) for the complete license text.

Third-party components used by Aiiko Music remain subject to their respective licenses. BASS, in particular, is distributed under separate licensing terms and is not covered by the GPL.

## Credits

Aiiko Music is developed by **Aiiko Hirayama**.

Thanks to the authors and maintainers of the open-source projects and libraries used by Aiiko Music.

---

**Aiiko Music v1.0.1**

[Repository](https://github.com/HirayamaAiiko/Aiiko-Music) · [Releases](https://github.com/HirayamaAiiko/Aiiko-Music/releases) · [Issues](https://github.com/HirayamaAiiko/Aiiko-Music/issues)
