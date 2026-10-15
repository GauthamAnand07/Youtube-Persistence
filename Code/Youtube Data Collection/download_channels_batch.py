#!/usr/bin/env python3
"""Run the 75 Hard channel downloader across a TSV list of channels."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_VERSION = "2026-10-13.3"


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Download matching regular videos from a list of YouTube channels."
    )
    parser.add_argument(
        "--channels",
        type=Path,
        default=script_dir / "channels_75_hard.tsv",
        help="TSV file containing Channel Name and Channel URL columns",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("channel_downloads"),
        help="Shared destination directory (default: ./channel_downloads)",
    )
    parser.add_argument(
        "--title-contains",
        default="75 Hard",
        metavar="TEXT",
        help='Only download video titles containing this text (default: "75 Hard")',
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=1080,
        help="Maximum video height (default: 1080)",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Save audio as MP3 instead of video",
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
        "--limit-per-channel",
        type=int,
        metavar="N",
        help="Check at most N videos per channel (useful for testing)",
    )
    parser.add_argument(
        "--start-at",
        type=int,
        default=1,
        metavar="N",
        help="Start at channel row N, counting the first data row as 1",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        metavar="N",
        help="Stop after processing N channels",
    )
    parser.add_argument(
        "--channel-delay",
        type=float,
        default=15.0,
        metavar="SECONDS",
        help="Pause between channels (default: 15 seconds)",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop the batch if one channel fails",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which channels would run without downloading",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.resolution <= 0:
        raise SystemExit("--resolution must be greater than 0")
    if args.start_at <= 0:
        raise SystemExit("--start-at must be greater than 0")
    if args.stop_after is not None and args.stop_after <= 0:
        raise SystemExit("--stop-after must be greater than 0")
    if args.limit_per_channel is not None and args.limit_per_channel <= 0:
        raise SystemExit("--limit-per-channel must be greater than 0")
    if args.channel_delay < 0:
        raise SystemExit("--channel-delay cannot be negative")
    if not args.title_contains.strip():
        raise SystemExit("--title-contains cannot be empty")


def read_channels(path: Path) -> list[tuple[str, str]]:
    try:
        file = path.expanduser().open("r", encoding="utf-8-sig", newline="")
    except OSError as error:
        raise SystemExit(f"Could not open channel list: {error}") from error

    channels: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    with file:
        reader = csv.DictReader(file, delimiter="\t")
        required = {"Channel Name", "Channel URL"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise SystemExit(
                'Channel list must have "Channel Name" and "Channel URL" columns.'
            )

        for row_number, row in enumerate(reader, start=2):
            name = (row.get("Channel Name") or "").strip()
            url = (row.get("Channel URL") or "").strip()
            if not name and not url:
                continue
            if not url:
                print(f"Skipping row {row_number}: {name or 'unnamed channel'} has no URL")
                continue
            dedupe_key = url.split("?", 1)[0].rstrip("/").casefold()
            if dedupe_key in seen_urls:
                print(f"Skipping duplicate row {row_number}: {name}")
                continue
            seen_urls.add(dedupe_key)
            channels.append((name or "Unnamed channel", url))

    return channels


def build_command(
    args: argparse.Namespace,
    channel_script: Path,
    url: str,
) -> list[str]:
    command = [
        sys.executable,
        str(channel_script),
        url,
        "--output",
        str(args.output.expanduser()),
        "--title-contains",
        args.title_contains,
        "--resolution",
        str(args.resolution),
    ]
    if args.audio_only:
        command.append("--audio-only")
    if args.subtitles:
        command.append("--subtitles")
    if args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])
    if args.limit_per_channel is not None:
        command.extend(["--limit-per-tab", str(args.limit_per_channel)])
    return command


def refresh_trackers(args: argparse.Namespace, tracker_script: Path) -> bool:
    result = subprocess.run(
        [
            sys.executable,
            str(tracker_script),
            "--output",
            str(args.output.expanduser()),
            "--channels",
            str(args.channels.expanduser()),
        ],
        check=False,
    )
    if result.returncode:
        print(f"Warning: tracker refresh failed with exit code {result.returncode}")
        return False
    return True


def main() -> int:
    args = parse_args()
    validate_args(args)

    channel_script = Path(__file__).resolve().with_name("download_channel.py")
    if not channel_script.is_file():
        raise SystemExit(f"Missing required script: {channel_script}")
    tracker_script = Path(__file__).resolve().with_name("build_download_tracker.py")
    if not tracker_script.is_file():
        raise SystemExit(f"Missing required script: {tracker_script}")

    channels = read_channels(args.channels)
    channels = channels[args.start_at - 1 :]
    if args.stop_after is not None:
        channels = channels[: args.stop_after]
    if not channels:
        raise SystemExit("No channels selected.")

    print(f"Batch downloader: {SCRIPT_VERSION}")
    print(f"Channels selected: {len(channels)}")
    print(f'Title filter: "{args.title_contains}"')
    print("Source: regular Videos tabs only; Shorts and Streams are excluded")
    print(f"Destination: {args.output.expanduser().resolve()}\n")

    if not args.dry_run:
        refresh_trackers(args, tracker_script)

    failures: list[str] = []
    for position, (name, url) in enumerate(channels, start=1):
        print("=" * 72)
        print(f"[{position}/{len(channels)}] {name}")
        print(url)
        print("=" * 72)
        command = build_command(args, channel_script, url)

        if args.dry_run:
            print("Dry run: channel would be processed.\n")
            continue

        try:
            result = subprocess.run(command, check=False)
        except KeyboardInterrupt:
            refresh_trackers(args, tracker_script)
            print("\nBatch stopped. Rerun with --start-at to resume at a row.")
            return 130

        if result.returncode not in (0, 130):
            failures.append(name)
            print(f"Channel finished with exit code {result.returncode}: {name}")
            if args.stop_on_error:
                break
        elif result.returncode == 130:
            refresh_trackers(args, tracker_script)
            print("Batch stopped during a channel download.")
            return 130

        refresh_trackers(args, tracker_script)

        if position < len(channels) and args.channel_delay:
            print(f"Waiting {args.channel_delay:g} seconds before the next channel...\n")
            time.sleep(args.channel_delay)

    print("\nBatch complete.")
    if failures:
        print(f"Channels with errors ({len(failures)}):")
        for name in failures:
            print(f"- {name}")
        print("Rerunning the same command will safely retry failed items.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
