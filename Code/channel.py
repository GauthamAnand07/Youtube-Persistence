#!/usr/bin/env python3
"""Download all public media from a YouTube channel in an organized layout."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SCRIPT_VERSION = "2026-10-12.4"
CHANNEL_TABS = {"videos", "shorts", "streams", "featured", "playlists", "community"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download matching regular videos from a YouTube channel's Videos tab."
    )
    parser.add_argument(
        "channel",
        help="Channel URL or @handle, such as https://youtube.com/@OpenAI or @OpenAI",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("channel_downloads"),
        help="Destination directory (default: ./channel_downloads)",
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
        help="Use cookies from a browser for content you can access there",
    )
    parser.add_argument(
        "--limit-per-tab",
        type=int,
        metavar="N",
        help="Check at most N items from the Videos tab (useful for testing)",
    )
    parser.add_argument(
        "--title-contains",
        default="75 HARD",
        metavar="TEXT",
        help='Only download titles containing this text (default: "75 HARD")',
    )
    return parser.parse_args()


def normalize_channel_url(value: str) -> str:
    value = value.strip()
    if value.startswith("@"):
        if not re.fullmatch(r"@[^\s/?#]+", value):
            raise SystemExit("The channel @handle contains unsupported characters.")
        return f"https://www.youtube.com/{value}"

    parsed = urlparse(value if "://" in value else f"https://{value}")
    hostname = (parsed.hostname or "").lower()
    if hostname not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        raise SystemExit("Please provide a YouTube channel URL or @handle.")

    parts = [part for part in parsed.path.split("/") if part]
    if parts and parts[-1].lower() in CHANNEL_TABS:
        parts.pop()
    if not parts:
        raise SystemExit("The URL does not identify a YouTube channel.")

    path = "/" + "/".join(parts)
    return urlunparse(("https", "www.youtube.com", path, "", "", ""))


def detect_js_runtime() -> tuple[str, str]:
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
        "Install Deno 2.3 or newer, then run this script again:\n"
        "https://docs.deno.com/runtime/getting_started/installation/"
    )


def build_options(
    args: argparse.Namespace,
    js_runtime: tuple[str, str],
) -> dict:
    output_dir = args.output.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    channel_dir = output_dir / "%(channel,uploader|Unknown Channel)s"
    filename = "%(upload_date>%Y-%m-%d|unknown-date)s - %(title)s [%(id)s].%(ext)s"
    media_folder = "audio" if args.audio_only else "videos"

    options: dict = {
        "outtmpl": {
            "default": str(channel_dir / media_folder / filename),
            "thumbnail": str(channel_dir / "thumbnails" / filename),
            "description": str(channel_dir / "descriptions" / filename),
            "infojson": str(channel_dir / "metadata" / filename),
            "subtitle": str(channel_dir / "subtitles" / filename),
        },
        "download_archive": str(output_dir / ".channel_downloaded.txt"),
        "js_runtimes": {js_runtime[0]: {"path": js_runtime[1]}},
        # Use yt-dlp's video-only title matcher. A custom match_filter can also
        # be called on the channel container and accidentally reject the tab.
        "matchtitle": f"(?i){re.escape(args.title_contains.strip())}",
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
        "extractor_retries": 5,
        # Large channel downloads can hit YouTube guest-session rate limits.
        "sleep_interval": 5,
        "max_sleep_interval": 10,
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
    if args.limit_per_tab is not None:
        options["playlistend"] = args.limit_per_tab

    return options


def validate_args(args: argparse.Namespace) -> None:
    if args.resolution <= 0:
        raise SystemExit("--resolution must be greater than 0")
    if args.limit_per_tab is not None and args.limit_per_tab <= 0:
        raise SystemExit("--limit-per-tab must be greater than 0")
    if not args.title_contains.strip():
        raise SystemExit("--title-contains cannot be empty")


def main() -> int:
    args = parse_args()
    validate_args(args)
    channel_url = f"{normalize_channel_url(args.channel)}/videos"
    js_runtime = detect_js_runtime()
    options = build_options(args, js_runtime)

    try:
        import yt_dlp
    except ImportError:
        print(
            "Missing dependency: yt-dlp\n"
            "Install it with: python3 -m pip install --upgrade 'yt-dlp[default]'",
            file=sys.stderr,
        )
        return 1

    print(f"Channel: {channel_url}")
    print(f"Destination: {args.output.expanduser().resolve()}")
    print(f"Channel downloader: {SCRIPT_VERSION}")
    print(f"JavaScript runtime: {js_runtime[0]} ({js_runtime[1]})")
    print("Source: regular channel videos only (Shorts and Streams are excluded)")
    print(f'Collecting titles containing: "{args.title_contains}"')
    print("Press Ctrl+C to stop safely; rerun the same command to resume.\n")

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            error_code = downloader.download([channel_url])
    except KeyboardInterrupt:
        print("\nStopped. Run the same command later to resume.", file=sys.stderr)
        return 130
    except yt_dlp.utils.DownloadError as error:
        print(f"\nDownload failed: {error}", file=sys.stderr)
        return 1

    if error_code:
        print("\nFinished with one or more skipped/failed items.", file=sys.stderr)
        return 1

    print("\nChannel download complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
