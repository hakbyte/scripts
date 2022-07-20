#!/usr/bin/env python3

import argparse
import asyncio
import ffmpeg
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


@dataclass
class CmdArgs:
    input_files: list[Path]
    prefix: str
    verbose: int


@dataclass
class VideoInfo:
    path: Path
    fps: int
    resolution: tuple[int, int]
    creation_time: datetime


def parse_args() -> CmdArgs:
    """
    Parses command line arguments and returns a CmdArgs object containing the
    parsed results.
    """

    parser = argparse.ArgumentParser(
        description="Rename video files based on their metadata")

    parser.add_argument(
        "-i", "--input",
        help="Base directory containing video files",
        required=True,
        type=str,
        nargs="?")

    parser.add_argument(
        "-p", "--prefix",
        help="Prefix to add to video files when renaming them",
        type=str,
        default="",
        nargs="?")

    parser.add_argument(
        "-v", "--verbose",
        help="Enable verbose mode",
        default=0,
        action="count")

    args = parser.parse_args()

    return CmdArgs(
        input_files=build_video_list(
            args.input,
            verbose=args.verbose
        ),
        prefix=args.prefix,
        verbose=args.verbose
    )


def find_video_files(root: Path, ext: str = ".mp4") -> Iterator[Path]:
    """
    Recursively searches for video files under a root directory. Only files with
    the provided file extension are returned.
    """

    for path in root.iterdir():
        if path.is_dir():
            yield from find_video_files(path)
        elif path.is_file and path.suffix.lower() == ext:
            yield path


def build_video_list(path: str, verbose: int = 0) -> list[Path]:
    """
    Builds a list containing all video files found under the root dir. By
    default only searches video files with `.mp4` extension.
    """

    video_files = [f for f in find_video_files(Path(path))]

    if verbose >= 1:
        print(f"Found {len(video_files)} video files under `{path}`")

    return video_files


def parse_video_file(filename: Path) -> VideoInfo | None:
    """
    Parses a video file and returns its metadata packaged as a VideoInfo object.
    """

    try:
        # Tries to retrieve video metadata in JSON format
        probe = ffmpeg.probe(filename)
        info = next(s for s in probe.get("streams")
                    if s.get("codec_type") == "video")

        # Build VideoInfo object from JSON metadata
        frame_rate = int(info.get("r_frame_rate").split("/")[0])
        width = int(info.get("width"))
        height = int(info.get("height"))
        timestamp = info.get("tags").get("creation_time")

        return VideoInfo(
            path=filename,
            fps=frame_rate,
            resolution=(width, height),
            creation_time=datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        )
    except ffmpeg.Error as e:
        # TODO: handle error instead of just ignoring it
        pass


def rename_video_file(video_info: VideoInfo, prefix: str = "", dry_run: bool = True, verbose: int = 0) -> None:
    """
    Renames a video file base on its metadata.
    """

    # Build filename from video metadata
    SEP = "_"
    resolution = f"{video_info.resolution[0]}x{video_info.resolution[1]}"
    fps = f"{video_info.fps}fps"
    creation_time = video_info.creation_time.strftime("%Y-%m-%dT%H%M%S")
    metadata = SEP.join([resolution, fps, creation_time])
    prefix = prefix if prefix else video_info.path.stem
    new_filename = prefix + SEP + metadata + video_info.path.suffix.lower()

    # Rename video
    p = Path.joinpath(video_info.path.parent, new_filename)
    if verbose >= 2:
        print(f"Renaming `{video_info.path}` to `{p}`")


async def main():
    """
    Entry point for application logic.
    """

    args = parse_args()
    # Create list of tasks and run them concurrently
    tasks = []
    loop = asyncio.get_running_loop()
    for input_file in args.input_files:
        tasks.append(loop.run_in_executor(None, parse_video_file, input_file))

    if args.verbose >= 1:
        print(f"Extracted metadata from {len(tasks)} video files")

    metadata_tasks = [await task for task in tasks]
    if args.verbose >= 1:
        print(f"Renaming {len(metadata_tasks)} video files...")

    for video in metadata_tasks:
        rename_video_file(video, args.prefix, verbose=args.verbose)

    if args.verbose >= 1:
        print(f"Done!")


#
# Entry point
#

if __name__ == "__main__":
    asyncio.run(main())
