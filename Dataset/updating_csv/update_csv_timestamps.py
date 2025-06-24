#!/usr/bin/env python3
"""
Script to update AVA dataset CSV files by converting frame_idx to timestamps.
Converts frame_idx to timestamp = frame_idx - 1 to match AVA benchmark format.
"""

import pandas as pd
import argparse
import os
from pathlib import Path


def update_csv_timestamps(input_csv_path, output_csv_path=None):
    """
    Update CSV file by converting frame_idx to timestamps (frame_idx - 1).

    Args:
        input_csv_path (str): Path to input CSV file
        output_csv_path (str): Path to output CSV file (optional, defaults to input path)
    """
    try:
        # Read the CSV file
        print(f"Reading CSV file: {input_csv_path}")
        df = pd.read_csv(input_csv_path)

        # Check if frame_idx column exists
        if 'frame_idx' not in df.columns:
            print("Error: 'frame_idx' column not found in CSV file")
            print(f"Available columns: {list(df.columns)}")
            return False

        print(f"Original frame_idx range: {df['frame_idx'].min()} to {df['frame_idx'].max()}")

        # Convert frame_idx to timestamp (frame_idx - 1)
        df['timestamp'] = df['frame_idx'] - 1

        # Drop the original frame_idx column
        df = df.drop('frame_idx', axis=1)

        # Reorder columns to put timestamp first (common AVA format)
        cols = df.columns.tolist()
        if 'timestamp' in cols:
            cols.remove('timestamp')
            cols.insert(1, 'timestamp')
            df = df[cols]

        print(f"New timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Set output path
        if output_csv_path is None:
            output_csv_path = input_csv_path

        # Save the updated CSV
        df.to_csv(output_csv_path, index=False)
        print(f"Updated CSV saved to: {output_csv_path}")
        print(f"Total rows processed: {len(df)}")

        return True

    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Update AVA dataset CSV files by converting frame_idx to timestamps')
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('-o', '--output', help='Path to output CSV file (optional)')
    parser.add_argument('--batch', help='Process all CSV files in a directory', action='store_true')

    args = parser.parse_args()

    if args.batch:
        # Process all CSV files in directory
        input_dir = Path(args.input_csv)
        if not input_dir.is_dir():
            print(f"Error: {input_dir} is not a directory")
            return

        csv_files = list(input_dir.glob('*.csv'))
        if not csv_files:
            print(f"No CSV files found in {input_dir}")
            return

        print(f"Found {len(csv_files)} CSV files to process")

        for csv_file in csv_files:
            print(f"\nProcessing: {csv_file}")
            output_path = csv_file if args.output is None else Path(args.output) / csv_file.name
            success = update_csv_timestamps(str(csv_file), str(output_path))
            if success:
                print(f"✓ Successfully processed {csv_file.name}")
            else:
                print(f"✗ Failed to process {csv_file.name}")
    else:
        # Process single CSV file
        if not os.path.exists(args.input_csv):
            print(f"Error: Input file {args.input_csv} does not exist")
            return

        success = update_csv_timestamps(args.input_csv, args.output)
        if success:
            print("✓ CSV file updated successfully")
        else:
            print("✗ Failed to update CSV file")


if __name__ == "__main__":
    main()

    #python update_csv_timestamps.py C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Dataset\annotations\ava_train.csv