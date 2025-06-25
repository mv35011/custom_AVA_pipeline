import csv
import os
import sys
from collections import defaultdict


def generate_label_map_from_csv(csv_file_path):
    """Generate label_map.txt from CSV file by reading unique action_labels"""
    print(f"Reading CSV file: {csv_file_path}")

    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file {csv_file_path} not found!")
        return False

    action_labels = set()

    try:
        with open(csv_file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            first_row = next(reader, None)
            if first_row and first_row[0] == 'video_name':
                print("Header detected and skipped")
            else:
                if first_row and len(first_row) >= 7:
                    try:
                        action_label = int(first_row[6])
                        action_labels.add(action_label)
                    except (ValueError, IndexError):
                        print(f"Warning: Could not parse action_label from first row: {first_row}")
            for row_num, row in enumerate(reader, start=2):
                if len(row) >= 7:
                    try:
                        action_label = int(row[6])
                        action_labels.add(action_label)
                    except ValueError:
                        print(f"Warning: Invalid action_label in row {row_num}: {row[6]}")
                else:
                    print(f"Warning: Row {row_num} has insufficient columns: {row}")

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

    if not action_labels:
        print("Error: No valid action_labels found in CSV file!")
        return False
    sorted_action_labels = sorted(action_labels)
    print(f"Found {len(sorted_action_labels)} unique action labels: {sorted_action_labels}")
    csv_dir = os.path.dirname(csv_file_path)
    label_map_path = os.path.join(csv_dir, 'label_map.txt')
    action_mapping = {
        1: "normal_walk",
        7: "multiple_items",
        12: "slow_walk",
        18: "talking_phone",
        25: "listening_music",
        32: "group_walking",
        39: "empty_hands",
        45: "food_drink",
    }

    try:
        with open(label_map_path, 'w') as f:
            for action_label in sorted_action_labels:
                if action_label in action_mapping:
                    action_name = action_mapping[action_label]
                else:
                    action_name = f"action_{action_label}"
                f.write(f"{action_label}: {action_name}\n")

        print(f"Successfully generated label_map.txt at: {label_map_path}")
        print("\nGenerated label mapping:")
        with open(label_map_path, 'r') as f:
            for line in f:
                print(f"  {line.strip()}")

        return True

    except Exception as e:
        print(f"Error writing label_map.txt: {e}")
        return False


def remove_header_from_csv(csv_file_path):
    """Remove header from CSV file by removing the first line"""
    print(f"Processing: {csv_file_path}")

    if not os.path.exists(csv_file_path):
        print(f"Warning: File {csv_file_path} not found, skipping...")
        return False

    try:
        with open(csv_file_path, 'r', newline='') as f:
            lines = f.readlines()

        if not lines:
            print(f"Warning: {csv_file_path} is empty")
            return False
        first_line = lines[0].strip()
        if 'video_name' in first_line or 'action_label' in first_line:
            print(f"  Header detected: {first_line}")
            lines_without_header = lines[1:]
            with open(csv_file_path, 'w', newline='') as f:
                f.writelines(lines_without_header)

            print(f"  Successfully removed header from {csv_file_path}")
            print(f"  Rows remaining: {len(lines_without_header)}")
            return True
        else:
            print(f"  No header detected in {csv_file_path}, skipping...")
            return False

    except Exception as e:
        print(f"Error processing {csv_file_path}: {e}")
        return False


def analyze_csv_structure(csv_file_path):
    """Analyze the CSV structure to understand the data better"""
    print(f"\nAnalyzing CSV structure: {csv_file_path}")

    if not os.path.exists(csv_file_path):
        return

    try:
        with open(csv_file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = []
            for i, row in enumerate(reader):
                rows.append(row)
                if i >= 10:
                    break

            if not rows:
                print("  CSV is empty")
                return

            print(f"  CSV has {len(rows[0])} columns")
            print(f"  First row: {rows[0]}")
            if 'video_name' in rows[0][0] or 'action_label' in str(rows[0]):
                print("  First row appears to be a header")
                data_rows = rows[1:]
            else:
                print("  First row appears to be data")
                data_rows = rows

            if data_rows:
                print(f"  Sample data rows:")
                for i, row in enumerate(data_rows[:3]):
                    print(f"    Row {i + 1}: {row}")
                action_labels = set()
                for row in data_rows:
                    if len(row) >= 7:
                        try:
                            action_labels.add(int(row[6]))
                        except ValueError:
                            pass

                print(f"  Unique action_labels found: {sorted(action_labels)}")

    except Exception as e:
        print(f"  Error analyzing CSV: {e}")


def main():
    current_dir = os.getcwd()

    print("=" * 60)
    print("LABEL MAP GENERATOR AND CSV HEADER REMOVER")
    print("=" * 60)
    csv_files_to_analyze = ['train_without_personID.csv', 'train.csv', 'val.csv']

    for csv_file in csv_files_to_analyze:
        csv_path = os.path.join(current_dir, csv_file)
        if os.path.exists(csv_path):
            analyze_csv_structure(csv_path)

    print("\n" + "=" * 60)
    print("Step 1: Generating label_map.txt")
    csv_candidates = ['train_without_personID.csv', 'train.csv', 'val.csv']

    for csv_file in csv_candidates:
        csv_path = os.path.join(current_dir, csv_file)
        if os.path.exists(csv_path):
            print(f"Using {csv_file} to generate label_map.txt")
            generate_label_map_from_csv(csv_path)
            break
    else:
        print("No suitable CSV files found to generate label_map.txt")

    print("\n" + "=" * 60)
    print("Step 2: Removing headers from train.csv and val.csv")

    csv_files_to_clean = ['train.csv', 'val.csv']

    for csv_file in csv_files_to_clean:
        csv_path = os.path.join(current_dir, csv_file)
        remove_header_from_csv(csv_path)

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)

    print("\nIMPORTANT NOTE:")
    print("The label_map.txt generated uses generic action names (action_1, action_7, etc.)")
    print("You'll need to manually map these IDs to your actual action names from your action_list.pbtxt")
    print("Based on your action IDs, you should update the action_mapping dictionary in this script")
    print("with the correct mappings from your cumulative ID calculation.")


if __name__ == "__main__":
    main()