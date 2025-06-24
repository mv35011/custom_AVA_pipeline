#!/usr/bin/env python3
"""
Script to rename image files in AVA dataset rawframes directory.
Converts img_XXXXX to img_XXXX-1 to match AVA benchmark format.
Example: img_00323 -> img_00322
"""

import os
import re
import argparse
from pathlib import Path
import shutil


def rename_images_in_directory(directory_path, dry_run=False):
    """
    Rename all image files in a directory by subtracting 1 from the frame number.

    Args:
        directory_path (str): Path to directory containing images
        dry_run (bool): If True, only show what would be renamed without actually renaming

    Returns:
        tuple: (success_count, error_count)
    """
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Error: Directory {directory_path} does not exist")
        return 0, 1

    # Pattern to match image files like img_00323.jpg, img_12345.png, etc.
    pattern = re.compile(r'^img_(\d+)(\.[^.]+)$')

    image_files = []
    for file in directory.iterdir():
        if file.is_file() and pattern.match(file.name):
            image_files.append(file)

    if not image_files:
        print(f"No image files matching pattern 'img_XXXXX.*' found in {directory_path}")
        return 0, 0

    print(f"Found {len(image_files)} image files to rename in {directory_path}")

    success_count = 0
    error_count = 0

    # Sort files by frame number to process in order
    image_files.sort(key=lambda x: int(pattern.match(x.name).group(1)))

    for file_path in image_files:
        try:
            match = pattern.match(file_path.name)
            if not match:
                continue

            frame_num = int(match.group(1))
            extension = match.group(2)

            # Calculate new frame number (subtract 1)
            new_frame_num = frame_num - 1

            # Skip if new frame number would be negative
            if new_frame_num < 0:
                print(f"Warning: Skipping {file_path.name} - would result in negative frame number")
                continue

            # Format new filename with same zero-padding as original
            original_padding = len(match.group(1))
            new_filename = f"img_{new_frame_num:0{original_padding}d}{extension}"
            new_file_path = file_path.parent / new_filename

            if dry_run:
                print(f"Would rename: {file_path.name} -> {new_filename}")
            else:
                # Check if destination file already exists
                if new_file_path.exists():
                    print(f"Warning: Destination file {new_filename} already exists, skipping {file_path.name}")
                    error_count += 1
                    continue

                # Rename the file
                file_path.rename(new_file_path)
                print(f"Renamed: {file_path.name} -> {new_filename}")

            success_count += 1

        except Exception as e:
            print(f"Error renaming {file_path.name}: {str(e)}")
            error_count += 1

    return success_count, error_count


def process_rawframes_directory(rawframes_path, dry_run=False):
    """
    Process the entire rawframes directory structure.
    Expected structure: rawframes/video_id/img_XXXXX.jpg

    Args:
        rawframes_path (str): Path to rawframes directory
        dry_run (bool): If True, only show what would be renamed
    """
    rawframes_dir = Path(rawframes_path)
    if not rawframes_dir.exists():
        print(f"Error: Rawframes directory {rawframes_path} does not exist")
        return

    print(f"Processing rawframes directory: {rawframes_path}")
    if dry_run:
        print("DRY RUN MODE - No files will be actually renamed")

    total_success = 0
    total_errors = 0
    processed_dirs = 0

    # Iterate through video directories
    for video_dir in rawframes_dir.iterdir():
        if video_dir.is_dir():
            print(f"\nProcessing video directory: {video_dir.name}")
            success, errors = rename_images_in_directory(str(video_dir), dry_run)
            total_success += success
            total_errors += errors
            processed_dirs += 1

    print(f"\n{'DRY RUN ' if dry_run else ''}SUMMARY:")
    print(f"Processed directories: {processed_dirs}")
    print(f"Successfully {'would be ' if dry_run else ''}renamed: {total_success} files")
    print(f"Errors: {total_errors}")


def main():
    parser = argparse.ArgumentParser(
        description='Rename AVA dataset rawframes images by subtracting 1 from frame numbers')
    parser.add_argument('rawframes_path', help='Path to rawframes directory or specific video directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without actually renaming')
    parser.add_argument('--single-dir', action='store_true',
                        help='Process single directory instead of entire rawframes structure')

    args = parser.parse_args()

    if not os.path.exists(args.rawframes_path):
        print(f"Error: Path {args.rawframes_path} does not exist")
        return

    if args.single_dir:
        # Process single directory
        success, errors = rename_images_in_directory(args.rawframes_path, args.dry_run)
        print(f"\n{'DRY RUN ' if args.dry_run else ''}SUMMARY:")
        print(f"Successfully {'would be ' if args.dry_run else ''}renamed: {success} files")
        print(f"Errors: {errors}")
    else:
        # Process entire rawframes directory structure
        process_rawframes_directory(args.rawframes_path, args.dry_run)


if __name__ == "__main__":
    main()
    #python rename_frames.py C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Dataset\rawframes\
