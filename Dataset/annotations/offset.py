import pandas as pd
import os


def convert_csv_to_zero_based(csv_file):
    """
    Convert action_label column in CSV file from 1-based to 0-based indexing
    CSV files have no headers, so we use column index to access second-to-last column
    """
    print(f"Processing {csv_file}...")

    # Read the CSV file without headers
    df = pd.read_csv(csv_file, header=None)

    # Create backup
    backup_file = csv_file.replace('.csv', '_backup.csv')
    df.to_csv(backup_file, index=False, header=False)
    print(f"Backup created: {backup_file}")

    # Convert second-to-last column (action_label) from 1-based to 0-based
    # Second-to-last column is at index -2
    df.iloc[:, -2] = df.iloc[:, -2] - 1

    # Save the modified CSV without headers
    df.to_csv(csv_file, index=False, header=False)
    print(f"Updated {csv_file} with 0-based indexing")

    return df


def convert_label_map_to_zero_based(label_map_file):
    """
    Convert label_map.txt from 1-based to 0-based indexing
    """
    print(f"Processing {label_map_file}...")

    # Create backup
    backup_file = label_map_file.replace('.txt', '_backup.txt')

    # Read the original file
    with open(label_map_file, 'r') as f:
        lines = f.readlines()

    # Create backup
    with open(backup_file, 'w') as f:
        f.writelines(lines)
    print(f"Backup created: {backup_file}")

    # Convert to 0-based indexing
    updated_lines = []
    for line in lines:
        line = line.strip()
        if line and ':' in line:
            # Split by colon and convert the first part (ID) to 0-based
            parts = line.split(':', 1)
            old_id = int(parts[0])
            new_id = old_id - 1
            new_line = f"{new_id}:{parts[1]}\n"
            updated_lines.append(new_line)
        else:
            updated_lines.append(line + '\n')

    # Write the updated file
    with open(label_map_file, 'w') as f:
        f.writelines(updated_lines)

    print(f"Updated {label_map_file} with 0-based indexing")


def main():
    """
    Main function to convert all files to 0-based indexing
    """
    print("Converting files to 0-based indexing for mmaction2...")
    print("=" * 50)

    # List of CSV files to process
    csv_files = ['train.csv', 'val.csv']

    # Process CSV files
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            df = convert_csv_to_zero_based(csv_file)
            print(f"Sample data from {csv_file} after conversion:")
            print(df.head())
            print()
        else:
            print(f"Warning: {csv_file} not found!")

    # Process label map file
    label_map_file = 'label_map.txt'
    if os.path.exists(label_map_file):
        convert_label_map_to_zero_based(label_map_file)

        # Display updated label map
        print("\nUpdated label map:")
        with open(label_map_file, 'r') as f:
            print(f.read())
    else:
        print(f"Warning: {label_map_file} not found!")

    print("=" * 50)
    print("Conversion completed! All files have been updated to 0-based indexing.")
    print("Backup files have been created with '_backup' suffix.")


if __name__ == "__main__":
    main()