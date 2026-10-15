# YouTube Playlist Downloader

A small Python script that downloads a playlist in order and keeps the files organized.

To download everything from a channel instead of a playlist, use `download_channel.py` and see `CHANNEL_README.md`.

To process the supplied list of 75 Hard channels, use `download_channels_batch.py` with `channels_75_hard.tsv` and see `BATCH_README.md`.

The batch automatically maintains `vlogger_tracker.xlsx`, `download_tracker.csv`, and `vlogger_summary.csv` inside the channel download directory. The Excel workbook includes a vlogger metrics summary and a complete downloaded-video list.

If you use Jupyter or Google Colab, open `YouTube_Playlist_Downloader.ipynb` and run its cells from top to bottom. The notebook includes the same main options as the command-line script.

Use it only for videos you own, videos with a license that permits downloading, or content you otherwise have permission to download. Follow YouTube's terms and applicable law.

## Folder layout

```text
downloads/
├── .downloaded.txt
└── Playlist Name/
    ├── videos/
    │   ├── 001 - First Video [video-id].mp4
    │   └── 002 - Second Video [video-id].mp4
    ├── audio/                 # Used instead of videos in audio-only mode
    ├── thumbnails/
    │   └── 001 - First Video [video-id].webp
    ├── metadata/
    │   └── 001 - First Video [video-id].info.json
    ├── descriptions/
    │   └── 001 - First Video [video-id].description
    └── subtitles/
        └── 001 - First Video [video-id].en.srt
```

The hidden `.downloaded.txt` archive prevents repeat downloads if you run the same command again. Partial downloads can also resume.

## 1. Install prerequisites

You need Python 3.10 or newer. You also need a supported JavaScript runtime because current YouTube extraction requires one. Deno 2.3 or newer is recommended and is enabled by default by yt-dlp. `ffmpeg` is strongly recommended because it combines the best video and audio streams and is required for MP3 conversion.

Install Deno using its official instructions: <https://docs.deno.com/runtime/getting_started/installation/>

Confirm that it is available before running the downloader:

```bash
deno --version
```

### macOS

```bash
brew install python ffmpeg
```

### Windows

Install Python from python.org, then install `ffmpeg` with Windows Package Manager:

```powershell
winget install Gyan.FFmpeg
```

### Ubuntu or Debian

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg
```

## 2. Set up the project

Open a terminal in this folder and run:

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade -r requirements.txt
```

## 3. Download a playlist

Put the playlist URL in quotes:

```bash
python3 download_playlist.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

On Windows, use `py` instead of `python3` if needed.

## Useful options

Download at up to 720p:

```bash
python3 download_playlist.py "PLAYLIST_URL" --resolution 720
```

Download MP3 audio only:

```bash
python3 download_playlist.py "PLAYLIST_URL" --audio-only
```

Choose a destination:

```bash
python3 download_playlist.py "PLAYLIST_URL" --output "/path/to/my/videos"
```

Download items 10 through 20:

```bash
python3 download_playlist.py "PLAYLIST_URL" --start 10 --end 20
```

Download English subtitles when available:

```bash
python3 download_playlist.py "PLAYLIST_URL" --subtitles
```

For a private or age-restricted video that your browser account can legitimately access:

```bash
python3 download_playlist.py "PLAYLIST_URL" --cookies-from-browser chrome
```

Run `python3 download_playlist.py --help` to see every option.

## Updating

YouTube changes regularly, so keep `yt-dlp` and its EJS components current:

```bash
python3 -m pip install --upgrade "yt-dlp[default]"
```

## Notes

- Unavailable or private entries are skipped so the rest of the playlist can continue.
- Filenames include playlist numbers and video IDs to keep ordering stable and avoid duplicate names.
- Videos, audio, thumbnails, metadata, descriptions, and subtitles are kept in separate type folders inside each playlist folder.
- Thumbnails are saved as separate files rather than embedded into the media, ensuring they remain in the `thumbnails` folder.
- If a run stops, repeat the same command to continue.
