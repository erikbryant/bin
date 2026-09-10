#!/usr/bin/env python3

"""
Strict media integrity checker.

Usage:
    ./check-media.py /path/to/media

Requirements:
    ImageMagick:  brew install imagemagick
    FFmpeg:       brew install ffmpeg
    libheif:      brew install libheif
    ExifTool:     brew install exiftool   # optional, for Live Photo metadata

The checker:

    Images:
        Forces ImageMagick to decode the image pixels.

    HEIC/HEIF:
        Also runs heif-convert, providing an independent libheif check.

    Videos:
        Uses FFmpeg to decode every stream to null.

    Live Photos:
        Identifies HEIC/MOV pairs sharing the same filename stem.
        Reports whether both components exist and whether both validate.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".avif",
    ".rw2",
}

HEIC_EXTENSIONS = {
    ".heic",
    ".heif",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".mts",
    ".m2ts",
    ".3gp",
    ".mpeg",
    ".mpg",
}

PDF_EXTENSIONS = {
    ".pdf",
}

SKIPPABLE_EXTENSIONS = {
    ".json",
    ".html",
    ".txt",
    ".amr",  # audio recordings
}

def command_exists(name):
    return shutil.which(name) is not None


def run_command(command):
    """
    Run a command and return:
        (success, stderr)
    """
    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result.returncode == 0, result.stderr.strip()


def validate_image(path):
    """
    Force ImageMagick to read/decode the image.

    'null:' prevents creation of an output file.
    """
    success, error = run_command([
        "magick",
        str(path),
        "-depth", "8",
        "null:",
    ])

    if success:
        return True, ""

    return False, error


def validate_heic(path):
    """
    Validate HEIC/HEIF through both ImageMagick and libheif.

    heif-convert requires an output filename with a recognizable
    image extension, so use a temporary JPG.
    """

    # First validate through ImageMagick.
    ok, error = validate_image(path)

    if not ok:
        return False, "ImageMagick: " + error

    # Then independently validate through libheif.
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "decoded.jpg"

        ok, error = run_command([
            "heif-convert",
            str(path),
            str(output),
        ])

        if not ok:
            return False, "libheif: " + error

    return True, ""


def validate_video(path):
    """
    Decode every stream in the video.

    -map 0 means all streams are selected.
    -f null - means no output file is produced.

    FFmpeg errors are allowed to reach stderr, which lets us capture
    useful corruption information.
    """
    success, error = run_command([
        "ffmpeg",
        "-v", "error",
        "-i", str(path),
        "-map", "0",
        "-f", "null",
        "-",
    ])

    if success:
        return True, ""

    return False, error


def validate_pdf(path):
    """
    Validate file structure and syntax. Does not validate whether
    the file would successfully render.
    """
    success, error = run_command([
        "qpdf",
        "--check", str(path),
    ])

    if success:
        return True, ""

    return False, error


def discover_files(root):
    """
    Recursively discover files without making assumptions about filenames.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename

            if path.is_file():
                yield path


def build_live_photo_map(files):
    """
    Find HEIC/MOV pairs sharing the same basename.

    Example:

        IMG_1234.HEIC
        IMG_1234.MOV

    becomes one Live Photo pair.

    The key is case-insensitive because filesystems and cameras can
    differ in their capitalization conventions.
    """
    by_key = {}

    for path in files:
        ext = path.suffix.lower()

        if ext not in HEIC_EXTENSIONS and ext != ".mov":
            continue

        key = str(path.with_suffix("")).lower()

        if key not in by_key:
            by_key[key] = {}

        if ext in HEIC_EXTENSIONS:
            by_key[key]["heic"] = path
        elif ext == ".mov":
            by_key[key]["mov"] = path

    return {
        key: value
        for key, value in by_key.items()
        if "heic" in value or "mov" in value
    }


def scan_files(files):
    checked = 0
    bad = 0
    skipped = 0

    live_photos = build_live_photo_map(files)

    for path in sorted(files):
        ext = path.suffix.lower()

        if ext in IMAGE_EXTENSIONS:
            media_type = "image"
            validator = validate_image

        elif ext in HEIC_EXTENSIONS:
            media_type = "heic"
            validator = validate_heic

        elif ext in VIDEO_EXTENSIONS:
            media_type = "video"
            validator = validate_video

        elif ext in PDF_EXTENSIONS:
            media_type = "pdf"
            validator = validate_pdf

        elif ext in SKIPPABLE_EXTENSIONS:
            continue

        else:
            skipped += 1
            print(f"UNKNOWN EXTENSION: {path}")
            continue

        checked += 1

        try:
            size = path.stat().st_size
        except OSError:
            size = ""

        ok, error = validator(path)

        # Determine Live Photo relationship.
        key = str(path.with_suffix("")).lower()
        live_info = live_photos.get(key)

        is_live_photo = bool(
            live_info
            and "heic" in live_info
            and "mov" in live_info
        )

        partner = ""

        if is_live_photo:
            if ext in HEIC_EXTENSIONS:
                partner = str(live_info["mov"])
            elif ext == ".mov":
                partner = str(live_info["heic"])

        status = "OK" if ok else "BAD"

        if not ok:
            bad += 1

        if ok:
            # print(f"OK   {path}")
            pass
        else:
            print(f"BAD  {path}")
            if error:
                # Keep terminal output readable.
                print(f"     {error}")

    # Report Live Photos. Suggest that we remove the MOV.
    live_photos_found = 0
    for key, pair in live_photos.items():
        if "heic" in pair and "mov" in pair:
            live_photos_found += 1
            print(f"Live photo found: {pair['heic']} <-> {pair['mov']}")

    return checked, bad, skipped, live_photos_found


def check_dependencies():
    required = ["magick", "ffmpeg", "heif-convert", "qpdf"]

    missing = [
        command
        for command in required
        if not command_exists(command)
    ]

    if missing:
        print(
            "Missing required commands: " + ", ".join(missing),
            file=sys.stderr,
        )
        return False

    return True


def main():
    if len(sys.argv) < 2:
        print("ERROR: At least one directory/file argument is required")
        return 1

    if not check_dependencies():
        return 2

    checked = 0
    bad = 0
    skipped = 0
    live_photos_found = 0

    for name in sys.argv[1:]:
        if Path(name).is_dir():
            files = list(discover_files(name))
        else:
            files = [Path(name)]

        c, b, s, l = scan_files(files)
        checked += c
        bad += b
        skipped += s
        live_photos_found += l

    print()
    print(f"Checked:      {checked}")
    print(f"Unknown:      {skipped}")
    print(f"Bad files:    {bad}")
    print(f"Live Photos:  {live_photos_found}")

    if bad:
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
