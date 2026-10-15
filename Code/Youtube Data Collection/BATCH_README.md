# Batch 75 Hard Channel Downloader

This batch pipeline reads `channels_75_hard.tsv` and processes each channel sequentially. It scans only regular Videos tabs and downloads titles containing `75 Hard` case-insensitively. Shorts and Streams are excluded.

The included list contains 94 unique channels. Duplicate rows were removed. `Alex Eubank` was not included because the supplied row did not contain a channel URL.

## Files

- `download_channels_batch.py`: batch runner
- `download_channel.py`: single-channel worker
- `channels_75_hard.tsv`: cleaned channel list
- `build_download_tracker.py`: tracker generator
- `requirements.txt`: Python dependencies

Keep these files together in the same directory.

## Test first

Show the channels without downloading:

```bash
python3 download_channels_batch.py --dry-run
```

Test the first two channels, checking at most five videos per channel:

```bash
python3 download_channels_batch.py --stop-after 2 --limit-per-channel 5
```

## Run the complete batch

```bash
python3 download_channels_batch.py
```

By default, downloads are saved under `channel_downloads/`, organized into a separate folder for each channel and then by file type.

The batch refreshes an Excel workbook and two CSV trackers after every channel:

- `channel_downloads/vlogger_tracker.xlsx`: the main workbook. `Vlogger Summary` shows every vlogger with video count, unique upload days, first/last upload, calendar span, videos per upload day, distinct 75 Hard days found, 75-day coverage, missing challenge days, total/average duration, and total file size. `Downloaded Videos` lists every completed video and its title.
- `channel_downloads/download_tracker.csv`: the detailed video data in CSV format.
- `channel_downloads/vlogger_summary.csv`: the vlogger-level metrics in CSV format, including downloaded titles.

The tracker checks for a completed media file before including a video. Metadata left behind by a failed or partial download is not counted. Challenge-day coverage is based on `DAY 1` through `DAY 75` found in titles, while upload-day metrics use YouTube upload dates.

## Resume or retry

Rerun the same command. The shared `.channel_downloaded.txt` archive skips completed videos and retries incomplete or failed ones.

To start at channel row 25:

```bash
python3 download_channels_batch.py --start-at 25
```

You can also rebuild the trackers without downloading anything:

```bash
python3 build_download_tracker.py --output channel_downloads
```

## Other useful options

Download at up to 720p:

```bash
python3 download_channels_batch.py --resolution 720
```

Choose another destination:

```bash
python3 download_channels_batch.py --output "/path/to/75-hard-archive"
```

Download audio as MP3:

```bash
python3 download_channels_batch.py --audio-only
```

The default 15-second pause between channels helps reduce request-rate pressure. Adjust it only if necessary:

```bash
python3 download_channels_batch.py --channel-delay 30
```
