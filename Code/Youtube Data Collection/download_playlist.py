#!/usr/bin/env python3
"""Download a YouTube playlist into a clean, ordered folder structure."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_VERSION = "2026-10-12.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a YouTube playlist in playlist order."
    )
    parser.add_argument("url", help="YouTube playlist URL")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("downloads"),
        help="Destination directory (default: ./downloads)",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Save audio as MP3 instead of downloading video",
    )
    parser.add_argument(
        "--audio-quality",
        choices=["0", "2", "5", "7", "9"],
        default="2",
        help="MP3 VBR quality: 0 is best, 9 is smallest (default: 2)",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=1080,
        help="Maximum video height, such as 720 or 1080 (default: 1080)",
    )
    parser.add_argument(
        "--subtitles",
        action="store_true",
        help="Download English subtitles when available",
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["brave", "chrome", "chromium", "edge", "firefox", "opera", "safari", "vivaldi"],
        help="Use cookies from a browser for videos you can access there",
    )
    parser.add_argument(
        "--start",
        type=int,
        metavar="N",
        help="Start at playlist item N",
    )
    parser.add_argument(
        "--end",
        type=int,
        metavar="N",
        help="Stop at playlist item N",
    )
    return parser.parse_args()


def detect_js_runtime() -> tuple[str, str]:
    """Find a JavaScript runtime supported by yt-dlp, in preference order."""
    for runtime, executable in (
        ("deno", "deno"),
        ("node", "node"),
        ("quickjs", "qjs"),
    ):
        path = shutil.which(executable)
        if path:
            return runtime, path

    raise SystemExit(
        "No supported JavaScript runtime was found.\n"
        "YouTube downloads now require one for reliable format extraction.\n"
        "Install Deno 2.3 or newer (recommended), then run this script again:\n"
        "https://docs.deno.com/runtime/getting_started/installation/"
    )


def build_options(args: argparse.Namespace, js_runtime: tuple[str, str]) -> dict:
    output_dir = args.output.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keep each playlist together, then separate files by type. The video ID
    # prevents collisions when two videos have the same title.
    playlist_dir = output_dir / "%(playlist_title|Single Videos)s"
    filename = "%(playlist_index)03d - %(title)s [%(id)s].%(ext)s"
    media_folder = "audio" if args.audio_only else "videos"
    output_templates = {
        "default": str(playlist_dir / media_folder / filename),
        "thumbnail": str(playlist_dir / "thumbnails" / filename),
        "description": str(playlist_dir / "descriptions" / filename),
        "infojson": str(playlist_dir / "metadata" / filename),
        "subtitle": str(playlist_dir / "subtitles" / filename),
    }

    options: dict = {
        "outtmpl": output_templates,
        "download_archive": str(output_dir / ".downloaded.txt"),
        "js_runtimes": {js_runtime[0]: {"path": js_runtime[1]}},
        "ignoreerrors": True,
        "continuedl": True,
        "noplaylist": False,
        "windowsfilenames": True,
        "writedescription": True,
        "writeinfojson": True,
        "writethumbnail": True,
        "embedmetadata": True,
        "retries": 10,
        "fragment_retries": 10,
        "sleep_interval": 1,
        "max_sleep_interval": 3,
        "quiet": False,
        "no_warnings": False,
    }

    if args.audio_only:
        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": args.audio_quality,
                    },
                    {"key": "FFmpegMetadata"},
                ],
            }
        )
    else:
        options.update(
            {
                "format": (
                    f"bestvideo[height<={args.resolution}]+bestaudio/"
                    f"best[height<={args.resolution}]/best"
                ),
                "merge_output_format": "mp4",
            }
        )

    if args.subtitles:
        options.update(
            {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en", "en.*"],
                "subtitlesformat": "srt/best",
            }
        )

    if args.cookies_from_browser:
        options["cookiesfrombrowser"] = (args.cookies_from_browser,)
    if args.start is not None:
        options["playliststart"] = args.start
    if args.end is not None:
        options["playlistend"] = args.end

    return options


def validate_args(args: argparse.Namespace) -> None:
    if args.resolution <= 0:
        raise SystemExit("--resolution must be greater than 0")
    if args.start is not None and args.start <= 0:
        raise SystemExit("--start must be greater than 0")
    if args.end is not None and args.end <= 0:
        raise SystemExit("--end must be greater than 0")
    if args.start is not None and args.end is not None and args.start > args.end:
        raise SystemExit("--start cannot be greater than --end")


def main() -> int:
    args = parse_args()
    validate_args(args)
    js_runtime = detect_js_runtime()
    options = build_options(args, js_runtime)

    try:
        import yt_dlp
    except ImportError:
        print(
            "Missing dependency: yt-dlp\n"
            "Install it with: python3 -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    print(f"Destination: {args.output.expanduser().resolve()}")
    print(f"Downloader script: {SCRIPT_VERSION}")
    print(f"JavaScript runtime: {js_runtime[0]} ({js_runtime[1]})")
    print("Starting playlist download. Press Ctrl+C to stop safely.\n")

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            error_code = downloader.download([args.url])
    except KeyboardInterrupt:
        print("\nStopped. Run the same command later to resume.", file=sys.stderr)
        return 130
    except yt_dlp.utils.DownloadError as error:
        print(f"\nDownload failed: {error}", file=sys.stderr)
        return 1

    if error_code:
        print("\nFinished with one or more skipped/failed items.", file=sys.stderr)
        return 1

    print("\nPlaylist download complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
