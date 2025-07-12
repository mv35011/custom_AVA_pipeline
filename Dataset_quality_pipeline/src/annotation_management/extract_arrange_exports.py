#!/usr/bin/env python3
"""
CVAT Pipeline Processing Script

This script processes CVAT annotation exports by:
1. Copying all zip files from Docker container to local machine
2. Loading metadata from meta_data.json
3. Extracting zip files into organized folder structure
4. Renaming XML files with clip and job IDs
5. Generating a CSV report of processed files
"""

import os
import json
import zipfile
import csv
import subprocess
import shutil
from pathlib import Path
parent = Path(__file__).parent.parent.parent
DOCKER_CONTAINER_NAME = "cvat_server"
DOCKER_EXPORT_PATH = "/home/django/data/cache/export"
EXPORT_COPY_DIR = str(parent / "outputs" / "exported_zip")
EXTRACT_DEST_DIR = str(parent / "outputs" / "exported_xml")


def copy_files_from_docker(container_name, docker_path, local_path):
    """Copy all zip files from Docker container to local machine."""
    print(f"Copying zip files from Docker container...")
    print(f"  Container: {container_name}")
    print(f"  Docker path: {docker_path}")
    print(f"  Local path: {local_path}")
    os.makedirs(local_path, exist_ok=True)

    try:
        list_cmd = f"docker exec {container_name} ls -la {docker_path}"
        result = subprocess.run(list_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: Failed to list files in container: {result.stderr}")
            return False

        print(f"  Files in container export directory:")
        print(f"  {result.stdout}")
        ls_cmd = f"docker exec {container_name} find {docker_path} -name '*.zip' -type f"
        result = subprocess.run(ls_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: Failed to find zip files: {result.stderr}")
            return False

        zip_files = result.stdout.strip().split('\n')
        zip_files = [f for f in zip_files if f.strip()]

        if not zip_files:
            print(f"  WARNING: No zip files found in {docker_path}")
            return True

        print(f"  Found {len(zip_files)} zip files to copy")
        for zip_file in zip_files:
            filename = os.path.basename(zip_file)
            local_file_path = os.path.join(local_path, filename)

            copy_cmd = f"docker cp {container_name}:{zip_file} {local_file_path}"
            print(f"  Copying {filename}...")

            result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"    ERROR: Failed to copy {filename}: {result.stderr}")
            else:
                print(f"    ✓ Copied {filename}")

        return True

    except Exception as e:
        print(f"  ERROR: Exception during Docker copy: {str(e)}")
        return False


def load_metadata(extract_dest_dir):
    """Load metadata from meta_data.json file."""
    metadata_path = os.path.join(extract_dest_dir, "meta_data.json")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"meta_data.json not found at {metadata_path}")

    print(f"Loading metadata from: {metadata_path}")

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    print(f"Loaded {len(metadata)} records from metadata")
    return metadata


def find_matching_zip_file(export_copy_dir, zip_filename):
    """Find the actual zip file that matches the metadata entry."""
    exact_path = os.path.join(export_copy_dir, zip_filename)
    if os.path.exists(exact_path):
        return exact_path
    base_name = os.path.splitext(zip_filename)[0]

    for filename in os.listdir(export_copy_dir):
        if filename.endswith('.zip'):
            if base_name in filename or any(part in filename for part in base_name.split('_')):
                print(f"    Found potential match: {filename} for {zip_filename}")
                return os.path.join(export_copy_dir, filename)

    return None


def create_folder_structure(extract_dest_dir, clip_id, annotator, task_type, job_id):
    """Create the required folder structure and return the path."""
    folder_path = os.path.join(
        extract_dest_dir,
        f"clip_{clip_id}",
        annotator,
        task_type,
        f"job_{job_id}"
    )
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def extract_and_rename_files(zip_path, destination_folder, clip_id, job_id):
    """Extract zip file and rename XML files according to requirements."""
    xml_files = []

    print(f"  Extracting {os.path.basename(zip_path)} to {destination_folder}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            zip_ref.extractall(destination_folder)
            for file_name in file_list:
                if file_name.lower().endswith('.xml'):
                    original_path = os.path.join(destination_folder, file_name)
                    base_name = os.path.basename(file_name)
                    new_name = f"clip{clip_id}_job{job_id}_{base_name}"
                    new_path = os.path.join(destination_folder, new_name)
                    if os.path.exists(original_path):
                        os.rename(original_path, new_path)
                        xml_files.append(new_name)
                        print(f"    Renamed {base_name} → {new_name}")

        return xml_files

    except Exception as e:
        print(f"    ERROR: Failed to extract {zip_path}: {str(e)}")
        return []


def process_annotations(export_copy_dir, extract_dest_dir):
    """Main processing function."""
    metadata = load_metadata(extract_dest_dir)
    csv_data = []
    available_files = [f for f in os.listdir(export_copy_dir) if f.endswith('.zip')]
    print(f"Available zip files in {export_copy_dir}: {available_files}")
    for i, record in enumerate(metadata, 1):
        print(f"\nProcessing record {i}/{len(metadata)}")
        clip_id = record['clip_id']
        annotator = record['annotator']
        task_type = record['task_type']
        job_id = record['job_id']
        zip_file = record['zip_file']

        print(f"  Record: clip_{clip_id}, {annotator}, {task_type}, job_{job_id}")
        print(f"  Looking for zip file: {zip_file}")
        zip_path = find_matching_zip_file(export_copy_dir, zip_file)

        if not zip_path:
            print(f"  WARNING: No matching zip file found for {zip_file}")
            continue

        print(f"  Using zip file: {os.path.basename(zip_path)}")
        destination_folder = create_folder_structure(
            extract_dest_dir, clip_id, annotator, task_type, job_id
        )
        xml_files = extract_and_rename_files(zip_path, destination_folder, clip_id, job_id)
        for xml_file in xml_files:
            relative_path = os.path.relpath(
                os.path.join(destination_folder, xml_file),
                extract_dest_dir
            )

            csv_data.append({
                'clip_id': clip_id,
                'annotator': annotator,
                'task_type': task_type,
                'job_id': job_id,
                'xml_file_path': relative_path
            })

        print(f"  ✓ Processed {len(xml_files)} XML files")

    return csv_data


def generate_csv_report(csv_data, extract_dest_dir):
    """Generate CSV report with processing results."""
    csv_path = os.path.join(extract_dest_dir, "processing_report.csv")

    print(f"\nGenerating CSV report: {csv_path}")

    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['clip_id', 'annotator', 'task_type', 'job_id', 'xml_file_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)

    print(f"✓ CSV report generated with {len(csv_data)} entries")


def main():
    """Main execution function."""
    print("CVAT Pipeline Processing Script")
    print("=" * 50)
    if not os.path.exists(EXTRACT_DEST_DIR):
        print(f"ERROR: Extract destination directory not found: {EXTRACT_DEST_DIR}")
        return

    print(f"Docker container: {DOCKER_CONTAINER_NAME}")
    print(f"Docker export path: {DOCKER_EXPORT_PATH}")
    print(f"Export copy directory: {EXPORT_COPY_DIR}")
    print(f"Extract destination directory: {EXTRACT_DEST_DIR}")

    try:
        print(f"\nStep 1: Copying files from Docker container")
        print("-" * 30)
        success = copy_files_from_docker(DOCKER_CONTAINER_NAME, DOCKER_EXPORT_PATH, EXPORT_COPY_DIR)

        if not success:
            print("❌ Failed to copy files from Docker container")
            return
        print(f"\nStep 2: Processing annotations")
        print("-" * 30)
        csv_data = process_annotations(EXPORT_COPY_DIR, EXTRACT_DEST_DIR)
        print(f"\nStep 3: Generating report")
        print("-" * 30)
        generate_csv_report(csv_data, EXTRACT_DEST_DIR)

        print("\n" + "=" * 50)
        print("✓ Processing completed successfully!")
        print(f"  - Copied zip files to: {EXPORT_COPY_DIR}")
        print(f"  - Extracted and organized files in: {EXTRACT_DEST_DIR}")
        print(f"  - Generated CSV report: {os.path.join(EXTRACT_DEST_DIR, 'processing_report.csv')}")

    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        raise


if __name__ == "__main__":
    main()