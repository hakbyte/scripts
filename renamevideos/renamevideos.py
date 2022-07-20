#!/usr/bin/env python3

import argparse
import os
import ffmpeg
import time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from pprint import pprint


@dataclass
class CmdArgs:
    input_files: list[Path]
    prefix: str
    verbose: bool


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
        nargs="?")

    parser.add_argument(
        "-v", "--verbose",
        help="Enable verbose mode",
        action="store_true")

    args = parser.parse_args()

    return CmdArgs(
        input_files=build_video_list(args.input),
        prefix=args.prefix,
        verbose=args.verbose
    )


def build_video_list(path: str, ext: str = ".mp4") -> list[Path]:
    """
    Builds a list containing all video files found under the root dir. By
    default only searches video files with `.mp4` extension.
    """

    file_list = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(ext):
                p = Path(os.path.join(root, f))
                file_list.append(p)

    return file_list


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


def main():
    args = parse_args()
    videos = []
    start = time.perf_counter()
    for input_file in args.input_files:
        if v := parse_video_file(input_file):
            videos.append(v)
    end = time.perf_counter()
    pprint(videos)
    print(f"Duration: {end - start:.2f} seconds")


if __name__ == "__main__":
    main()
