#!/usr/bin/env python3
"""
Meta Data Generator Script

This script generates a meta_data.json file by combining information from:
1. Assignment config JSON (clip assignments and overlap information)
2. Latest task report JSON (task/job/clip mappings)

The output contains mappings of project_id, task_id, job_id, clip_id,
annotator, task_type, and original zip file names.
"""

import json
import os
import glob
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
parent = Path(__file__).parent.parent.parent
ASSIGNMENT_CONFIG_PATH = str(parent / "config" / "assignment_config.json" )
TASK_REPORT_PATH = str(parent / "src" / "annotation_management"/ "multi_annotator_task_report_YYYYMMDD_HHMMSS.json" )
METADATA_JSON_PATH = str(parent / "outputs" / "exported_xml"/ "meta_data.json")


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e}")


def find_latest_task_report(base_path: str) -> str:
    """
    Find the latest task report file based on the naming pattern.

    Args:
        base_path: Base directory path to search for task report files

    Returns:
        Path to the latest task report file

    Raises:
        FileNotFoundError: If no task report files are found
    """
    directory = os.path.dirname(base_path)
    if not directory:
        directory = "."
    pattern = os.path.join(directory, "multi_annotator_task_report_*.json")
    task_report_files = glob.glob(pattern)

    if not task_report_files:
        raise FileNotFoundError(f"No task report files found matching pattern: {pattern}")
    latest_file = sorted(task_report_files)[-1]
    return latest_file


def extract_clip_id_from_zip_name(zip_file: str) -> str:
    """
    Extract clip ID from zip file name.

    Args:
        zip_file: Name of the zip file (e.g., "2.zip")

    Returns:
        Clip ID as string (e.g., "2")
    """
    return os.path.splitext(zip_file)[0]


def determine_task_type(annotator: str, clip_assignments: Dict[str, Any]) -> str:
    """
    Determine if a task is primary or overlap based on assignment config.
    This function is now redundant since task_type is already in the task report,
    but kept for backward compatibility.

    Args:
        annotator: The annotator name
        clip_assignments: Assignment configuration data

    Returns:
        Task type: "primary" or "overlap"
    """
    assignments = clip_assignments.get("assignments", [])

    for assignment in assignments:
        assigned_to = assignment.get("assigned_to")
        overlap_with = assignment.get("overlap_with", "")
        if annotator in overlap_with:
            return "overlap"
        elif annotator == assigned_to:
            return "primary"

    return "primary"


def generate_metadata_records(assignment_config: Dict[str, Any],
                              task_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate metadata records by combining assignment config and task report data.

    Args:
        assignment_config: Assignment configuration data
        task_report: Task report data

    Returns:
        List of metadata records
    """
    metadata_records = []
    project_id = task_report.get("project_id")
    tasks = task_report.get("tasks", [])

    for task in tasks:
        task_id = task.get("task_id")
        job_ids = task.get("job_ids", [])
        annotator = task.get("annotator")
        task_type = task.get("task_type")
        clip_ids = task.get("clip_ids", [])
        zip_files = task.get("zip_files", [])
        for i, clip_id in enumerate(clip_ids):
            zip_file = zip_files[i] if i < len(zip_files) else f"{clip_id}.zip"
            for job_id in job_ids:
                record = {
                    "project_id": project_id,
                    "task_id": task_id,
                    "job_id": job_id,
                    "clip_id": clip_id,
                    "annotator": annotator,
                    "task_type": task_type,
                    "zip_file": zip_file
                }

                metadata_records.append(record)

    return metadata_records


def write_metadata_json(metadata_records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write metadata records to JSON file.

    Args:
        metadata_records: List of metadata records
        output_path: Path to output JSON file
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(metadata_records, file, indent=2, ensure_ascii=False)

        print(f"Successfully wrote {len(metadata_records)} metadata records to {output_path}")

    except Exception as e:
        raise Exception(f"Error writing metadata file: {e}")


def validate_metadata_records(metadata_records: List[Dict[str, Any]]) -> None:
    """
    Validate that all metadata records have required fields.

    Args:
        metadata_records: List of metadata records to validate

    Raises:
        ValueError: If any record is missing required fields
    """
    required_fields = ["project_id", "task_id", "job_id", "clip_id", "annotator", "task_type", "zip_file"]

    for i, record in enumerate(metadata_records):
        missing_fields = [field for field in required_fields if field not in record or record[field] is None]
        if missing_fields:
            raise ValueError(f"Record {i} is missing required fields: {missing_fields}")


def main():
    """
    Main function to orchestrate the metadata generation process.
    """
    try:
        print("Starting metadata generation process...")
        print(f"Loading assignment config from: {ASSIGNMENT_CONFIG_PATH}")
        assignment_config = load_json_file(ASSIGNMENT_CONFIG_PATH)
        print(f"Finding latest task report near: {TASK_REPORT_PATH}")
        latest_task_report_path = find_latest_task_report(TASK_REPORT_PATH)
        print(f"Loading task report from: {latest_task_report_path}")
        task_report = load_json_file(latest_task_report_path)
        print("Generating metadata records...")
        metadata_records = generate_metadata_records(assignment_config, task_report)
        print("Validating metadata records...")
        validate_metadata_records(metadata_records)
        print(f"Writing metadata to: {METADATA_JSON_PATH}")
        write_metadata_json(metadata_records, METADATA_JSON_PATH)

        print("Metadata generation completed successfully!")
        print(f"Generated {len(metadata_records)} metadata records")
        if metadata_records:
            print("\nSample metadata records:")
            for i, record in enumerate(metadata_records[:3]):
                print(f"  Record {i + 1}: {record}")
            if len(metadata_records) > 3:
                print(f"  ... and {len(metadata_records) - 3} more records")

    except Exception as e:
        print(f"Error during metadata generation: {e}")
        raise


if __name__ == "__main__":
    main()