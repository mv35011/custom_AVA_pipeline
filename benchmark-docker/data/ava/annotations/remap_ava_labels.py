#!/usr/bin/env python3
"""
AVA Dataset Label Remapping Script

This script remaps custom class IDs in AVA dataset files to sequential IDs starting from 0.
It processes:
1. label_map.txt - Creates a new mapping from 0 to N-1
2. ava_train_v2.2.csv and ava_val_v2.2.csv - Updates class IDs in annotation files

Usage:
    python remap_ava_labels.py [--input_dir /path/to/annotations] [--backup]
"""

import os
import sys
import argparse
import pandas as pd
from collections import OrderedDict
import shutil
from datetime import datetime
import numpy as np


def create_label_mapping(label_map_path):
    """
    Read the original label_map.txt and create a mapping from original IDs to sequential IDs.

    Args:
        label_map_path (str): Path to the original label_map.txt file

    Returns:
        tuple: (original_to_new_mapping, new_to_label_mapping)
    """
    original_to_new = {}
    new_to_label = {}

    print(f"Reading label map from: {label_map_path}")

    try:
        with open(label_map_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Sort lines by original ID to ensure consistent mapping
        id_label_pairs = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(' ', 1)
            if len(parts) != 2:
                print(f"Warning: Skipping malformed line: {line}")
                continue

            original_id = int(parts[0])
            label = parts[1]
            id_label_pairs.append((original_id, label))

        # Sort by original ID
        id_label_pairs.sort(key=lambda x: x[0])

        # Create mappings
        for new_id, (original_id, label) in enumerate(id_label_pairs):
            original_to_new[original_id] = new_id
            new_to_label[new_id] = label

        print(f"Created mapping for {len(original_to_new)} classes")
        print(f"Original ID range: {min(original_to_new.keys())} - {max(original_to_new.keys())}")
        print(f"New ID range: 0 - {len(original_to_new) - 1}")

        return original_to_new, new_to_label

    except FileNotFoundError:
        print(f"Error: Label map file not found: {label_map_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading label map: {e}")
        sys.exit(1)


def create_new_label_map(new_to_label, output_path):
    """
    Create a new label_map.txt with sequential IDs starting from 0.

    Args:
        new_to_label (dict): Mapping from new sequential IDs to labels
        output_path (str): Path for the new label map file
    """
    print(f"Creating new label map: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for new_id in sorted(new_to_label.keys()):
                f.write(f"{new_id} {new_to_label[new_id]}\n")

        print(f"Successfully created new label map with {len(new_to_label)} classes")

    except Exception as e:
        print(f"Error creating new label map: {e}")
        sys.exit(1)


def remap_csv_file(csv_path, original_to_new, output_path):
    """
    Remap class IDs in a CSV file (ava_train_v2.2.csv or ava_val_v2.2.csv) and remove header row.

    Expected CSV format: video_id,timestamp_start,timestamp_end,class_id,x1,y1,x2,y2

    Args:
        csv_path (str): Path to the original CSV file
        original_to_new (dict): Mapping from original IDs to new sequential IDs
        output_path (str): Path for the remapped CSV file
    """
    print(f"Processing CSV file: {csv_path}")

    try:
        # First, let's check if the file has headers or not
        with open(csv_path, 'r') as f:
            first_line = f.readline().strip()
            print(f"First line of CSV: {first_line}")

        # Try to detect if first line contains headers
        has_header = False
        first_values = first_line.split(',')

        # Check if first line looks like headers (contains non-numeric values in expected positions)
        if len(first_values) > 3:
            try:
                # Try to convert the 4th column (class_id position) to int
                int(first_values[3])
                has_header = False
            except ValueError:
                has_header = True
        else:
            # If we can't determine, assume it has headers
            has_header = True

        print(f"Detected header: {has_header}")

        # Read CSV file with or without header
        if has_header:
            df = pd.read_csv(csv_path)
        else:
            # Read without header and assign column names
            df = pd.read_csv(csv_path, header=None)
            # Assign standard column names based on your custom format
            if df.shape[1] == 8:
                df.columns = ['video_name', 'timestamp', 'x1', 'y1', 'x2', 'y2', 'action_label', 'person_id']
            elif df.shape[1] >= 8:
                df.columns = ['video_name', 'timestamp', 'x1', 'y1', 'x2', 'y2', 'action_label', 'person_id'] + [
                    f'col_{i}' for i in range(8, df.shape[1])]
            elif df.shape[1] >= 4:
                df.columns = ['video_name', 'timestamp', 'x1', 'y1'] + [f'col_{i}' for i in range(4, df.shape[1])]
            else:
                print(f"Error: CSV has only {df.shape[1]} columns, expected at least 4")
                return False

        print(f"Original CSV shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")

        # Show first few rows for debugging
        print("First 5 rows of data:")
        print(df.head(5).to_string())
        print("\nColumn data types:")
        print(df.dtypes)

        # If this might not be the standard AVA format, let's analyze the structure
        print(f"\nAnalyzing CSV structure:")
        print(f"Number of columns: {df.shape[1]}")
        print(f"Number of rows: {df.shape[0]}")

        # Show some sample values from each column
        print("\nSample values from each column:")
        for i, col in enumerate(df.columns):
            sample_vals = df[col].dropna().head(3).tolist()
            print(f"Column {i} ({col}): {sample_vals}")

        # Ask user to manually specify class column if detection fails
        print(f"\nPlease check the above data and verify:")
        print(f"1. Which column contains the class IDs?")
        print(f"2. Do the class ID values match your label_map.txt?")
        print(f"3. Is this the expected CSV format for your dataset?")

        # Detect the class ID column (common names in AVA datasets)
        class_col_candidates = ['action_label', 'class_id', 'label_id', 'action_id', 'class', 'label']
        class_col = None

        for col in class_col_candidates:
            if col in df.columns:
                class_col = col
                break

        if class_col is None:
            # If no standard column name found, assume it's in a specific position
            # For your format, action_label is typically the 7th column (index 6)
            if df.shape[1] >= 7:
                class_col = df.columns[6]
                print(f"Assuming class column is: {class_col}")
            elif df.shape[1] >= 4:
                class_col = df.columns[3]
                print(f"Assuming class column is: {class_col}")
            else:
                print("Error: Could not identify class ID column")
                return False

        print(f"Using class column: {class_col}")

        # Check original class IDs
        original_classes = df[class_col].unique()
        original_classes = original_classes[~pd.isna(original_classes)]  # Remove NaN values

        # Convert to integers if they're stored as floats but are actually integers
        if len(original_classes) > 0 and all(isinstance(x, (float, np.floating)) for x in original_classes):
            if all(x == int(x) for x in original_classes):  # Check if they're whole numbers
                original_classes = [int(x) for x in original_classes]
                print("Converted float class IDs to integers")

        print(f"Found {len(original_classes)} unique classes in CSV")
        if len(original_classes) > 0:
            print(f"Original class range: {min(original_classes)} - {max(original_classes)}")
            print(f"Sample classes: {sorted(original_classes)[:10]}")
            print(f"Class data types: {[type(x) for x in original_classes[:5]]}")

        # Also show what's in the label map for comparison
        print(f"Label map classes: {sorted(list(original_to_new.keys()))[:10]}...")

        # Check if all classes have mappings
        unmapped_classes = set(original_classes) - set(original_to_new.keys())
        mapped_classes = set(original_classes) & set(original_to_new.keys())

        print(f"Classes with mappings: {len(mapped_classes)}")
        print(f"Classes without mappings: {len(unmapped_classes)}")

        if unmapped_classes:
            print(f"Warning: Found unmapped classes: {sorted(list(unmapped_classes))}")
            print("These rows will be removed from the output file")

        if len(mapped_classes) == 0:
            print("ERROR: No classes found that match the label mapping!")
            print("This would result in an empty CSV file.")
            print("Please check if your class IDs in the CSV match those in label_map.txt")
            return False

        # Remap class IDs
        df_remapped = df.copy()

        # First, filter out rows with unmapped classes before mapping
        if unmapped_classes:
            mask = df_remapped[class_col].isin(mapped_classes)
            df_remapped = df_remapped[mask]
            print(f"Filtered to {len(df_remapped)} rows with mappable classes")

        # Now remap the class IDs
        df_remapped[class_col] = df_remapped[class_col].map(original_to_new)

        # Double-check for any remaining NaN values (shouldn't happen after filtering)
        nan_count = df_remapped[class_col].isna().sum()
        if nan_count > 0:
            print(f"Warning: Found {nan_count} NaN values after mapping, removing them")
            df_remapped = df_remapped.dropna(subset=[class_col])

        # Convert class IDs to integers
        df_remapped[class_col] = df_remapped[class_col].astype(int)

        # Verify we still have data
        if len(df_remapped) == 0:
            print("ERROR: No data remaining after remapping!")
            return False

        # Save remapped CSV without header row
        df_remapped.to_csv(output_path, index=False, header=False)

        print(f"Remapped CSV shape: {df_remapped.shape}")
        print(f"New class range: {df_remapped[class_col].min()} - {df_remapped[class_col].max()}")
        print(f"Saved remapped CSV to: {output_path} (without header row)")

        return True

    except FileNotFoundError:
        print(f"Warning: CSV file not found: {csv_path}")
        return False
    except Exception as e:
        print(f"Error processing CSV file {csv_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_backup(file_path):
    """Create a backup of the original file with timestamp."""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")


def main():
    parser = argparse.ArgumentParser(description='Remap AVA dataset class IDs to sequential numbers')
    parser.add_argument('--input_dir', default='.',
                        help='Directory containing label_map.txt, ava_train_v2.2.csv, and ava_val_v2.2.csv (default: current directory)')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup copies of original files')

    args = parser.parse_args()

    input_dir = args.input_dir
    create_backups = args.backup

    print("=" * 60)
    print("AVA Dataset Label Remapping Script")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Create backups: {create_backups}")
    print()

    # File paths
    label_map_path = os.path.join(input_dir, 'label_map.txt')
    train_csv_path = os.path.join(input_dir, 'ava_train_v2.2.csv')
    val_csv_path = os.path.join(input_dir, 'ava_val_v2.2.csv')

    # Create mappings from label_map.txt
    original_to_new, new_to_label = create_label_mapping(label_map_path)

    # Create backups if requested
    if create_backups:
        print("\nCreating backups...")
        create_backup(label_map_path)
        create_backup(train_csv_path)
        create_backup(val_csv_path)

    # Create new label_map.txt
    print("\n" + "=" * 40)
    create_new_label_map(new_to_label, label_map_path)

    # Remap ava_train_v2.2.csv
    print("\n" + "=" * 40)
    if os.path.exists(train_csv_path):
        remap_csv_file(train_csv_path, original_to_new, train_csv_path)
    else:
        print(f"Warning: ava_train_v2.2.csv not found at {train_csv_path}")

    # Remap ava_val_v2.2.csv
    print("\n" + "=" * 40)
    if os.path.exists(val_csv_path):
        remap_csv_file(val_csv_path, original_to_new, val_csv_path)
    else:
        print(f"Warning: ava_val_v2.2.csv not found at {val_csv_path}")

    print("\n" + "=" * 60)
    print("Label remapping completed successfully!")
    print("=" * 60)

    # Print summary of mapping
    print("\nMapping Summary:")
    print("-" * 30)
    sample_mappings = list(original_to_new.items())[:10]  # Show first 10 mappings
    for orig, new in sample_mappings:
        print(f"{orig} -> {new} ({new_to_label[new]})")

    if len(original_to_new) > 10:
        print(f"... and {len(original_to_new) - 10} more mappings")


if __name__ == "__main__":
    main()