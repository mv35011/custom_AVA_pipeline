import json
import os
import sys
import shutil
from datetime import datetime


def backup_file(file_path):
    try:
        backup_path = file_path.replace('.json', '_backup.json')
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"Warning: Could not create backup for {file_path}: {e}")
        return None


def process_via_json_file(json_path, create_backup=True):
    """Process a single VIA JSON file to modify attributes"""

    print(f"Processing: {json_path}")
    backup_path = None
    if create_backup:
        backup_path = backup_file(json_path)
        if backup_path:
            print(f"  Created backup: {backup_path}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            via_json = json.load(f)

        if 'metadata' not in via_json:
            print(f"  Warning: No 'metadata' field found in {json_path}")
            return False

        # FIXED: Dynamically detect all attributes instead of hardcoding 1,2,3
        attributes_config = {}
        if 'attribute' in via_json:
            for attr_id, attr_info in via_json['attribute'].items():
                if 'options' in attr_info:
                    default_option = list(attr_info['options'].keys())[0] if attr_info['options'] else ''
                    attributes_config[attr_id] = default_option
                else:
                    attributes_config[attr_id] = ''
        else:
            # Fallback: create attributes 1-8 to match dense_proposals_train_to_via.py
            for i in range(1, 9):
                attributes_config[str(i)] = ''

        print(f"  Using attributes: {attributes_config}")

        modified_count = 0
        for metadata_key in via_json['metadata']:
            if 'av' in via_json['metadata'][metadata_key]:
                via_json['metadata'][metadata_key]['av'] = attributes_config.copy()
                modified_count += 1

        print(f"  Modified {modified_count} metadata entries")

        base_name = os.path.basename(json_path)
        dir_name = os.path.dirname(json_path)

        if base_name.endswith('_proposal.json'):
            new_name = base_name.replace('_proposal.json', '_proposal_s.json')
        else:
            name_parts = base_name.split('.')
            new_name = f"{name_parts[0]}_s.{name_parts[1]}"

        new_path = os.path.join(dir_name, new_name)

        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(via_json, f, indent=2, ensure_ascii=False)

        print(f"  Saved modified file: {new_path}")
        return True

    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON in {json_path}: {e}")
        return False
    except Exception as e:
        print(f"  Error processing {json_path}: {e}")
        return False


def find_and_process_via_files(root_directory, create_backup=True):
    """Find all VIA JSON files and process them"""

    print(f"Searching for VIA JSON files in: {root_directory}")
    print("=" * 60)

    if not os.path.exists(root_directory):
        print(f"Error: Directory {root_directory} does not exist!")
        return

    processed_files = []
    failed_files = []

    for root, dirs, files in os.walk(root_directory):
        if any(skip_dir in root for skip_dir in ['.backup', '__pycache__', '.git']):
            continue

        for file in files:
            if file.endswith('_proposal.json'):
                json_path = os.path.join(root, file)

                if process_via_json_file(json_path, create_backup):
                    processed_files.append(json_path)
                else:
                    failed_files.append(json_path)

    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY:")
    print(f"Successfully processed: {len(processed_files)} files")
    print(f"Failed to process: {len(failed_files)} files")

    if processed_files:
        print("\nSuccessfully processed files:")
        for file_path in processed_files:
            print(f"  ✓ {file_path}")

    if failed_files:
        print("\nFailed files:")
        for file_path in failed_files:
            print(f"  ✗ {file_path}")

    return len(processed_files), len(failed_files)


def main():
    """Main function with command line argument handling"""
    default_directory = "./choose_frames_middle"

    if len(sys.argv) > 1:
        root_directory = sys.argv[1]
    else:
        root_directory = default_directory

    create_backup = True
    if len(sys.argv) > 2 and sys.argv[2].lower() == 'no-backup':
        create_backup = False

    print("VIA JSON Attribute Modifier")
    print("=" * 60)
    print(f"Root directory: {root_directory}")
    print(f"Create backups: {create_backup}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success_count, fail_count = find_and_process_via_files(root_directory, create_backup)

    if fail_count > 0:
        print(f"\nWarning: {fail_count} files failed to process")
        sys.exit(1)
    elif success_count == 0:
        print("\nNo VIA JSON files found to process")
        print("Make sure you have run the previous step (dense_proposals_train_to_via.py)")
        sys.exit(1)
    else:
        print(f"\nAll {success_count} files processed successfully!")
        print("\nNOTE: After annotation, rename '_proposal_s.json' files to '_finish.json'")
        print("      or use the following command in your directory:")
        print(
            "      find . -name '*_proposal_s.json' -exec bash -c 'mv \"$1\" \"${1/_proposal_s.json/_finish.json}\"' _ {} \\;")
        sys.exit(0)


if __name__ == "__main__":
    main()