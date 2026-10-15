# YouTube Channel Downloader

`download_channel.py` checks only a channel's regular Videos tab. Shorts and Streams are excluded. By default, it downloads only items whose titles contain `75 HARD` (case-insensitive). It is separate from the playlist downloader.

Use it only for content you own, content whose license permits downloading, or content you otherwise have permission to download.

## Output layout

```text
channel_downloads/
├── .channel_downloaded.txt
└── Channel Name/
    ├── videos/
    │   └── 2026-10-12 - Video Title [video-id].mp4
    ├── audio/                 # Used instead of videos in audio-only mode
    ├── thumbnails/
    ├── metadata/
    ├── descriptions/
    └── subtitles/
```

The shared `.channel_downloaded.txt` archive prevents duplicates across tabs and skips completed downloads when the script is rerun.

## Requirements

- Python 3.10 or newer
- Deno 2.3 or newer
- `ffmpeg`
- The packages in `requirements.txt`

Install or update the Python package:

```bash
python3 -m pip install --upgrade "yt-dlp[default]"
```

## Download a channel

You can use an `@handle`:

```bash
python3 download_channel.py "@CHANNEL_HANDLE"
```

Or the full channel URL:

```bash
python3 download_channel.py "https://www.youtube.com/@CHANNEL_HANDLE"
```

Both commands download only titles containing `75 HARD`.

You may provide either the channel root or a URL ending in `/videos`. The script always uses the regular Videos tab and excludes Shorts and Streams.

## Useful options

Download at up to 720p:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --resolution 720
```

Download audio as MP3:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --audio-only
```

Test with at most two entries from the Videos tab:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --limit-per-tab 2
```

Use a different title filter if needed later:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --title-contains "another series"
```

Choose a destination:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --output "/path/to/channel-archive"
```

Download English subtitles when available:

```bash
python3 download_channel.py "@CHANNEL_HANDLE" --subtitles
```

Shorts and livestreams are not scanned or downloaded.
