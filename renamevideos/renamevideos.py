#!/usr/bin/env python3

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CmdArgs:
    input_files: list[Path]
    prefix: str
    verbose: bool


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
        input_files=build_file_list(args.input),
        prefix=args.prefix,
        verbose=args.verbose
    )


def build_file_list(path: str, ext: str = ".mp4") -> list[Path]:
    """
    Builds file list containing all video files found under the root dir. By
    default only searches video files with `.mp4` extension.
    """

    file_list = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(ext):
                p = Path(os.path.join(root, f))
                file_list.append(p)

    return file_list


def main():
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
