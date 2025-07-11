#!/usr/bin/env python3
"""
CVAT Annotation Organizer

This script reorganizes CVAT exported XML annotation files based on
annotator assignments and task metadata.

Author: Generated for CVAT project organization
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
parent = Path(__file__).parent.parent

# =============================================================================
# CONFIGURATION - UPDATE THESE PATHS
# =============================================================================

# Path to the extracted CVAT export folder
CVAT_EXPORT_PATH = "/path/to/exported_project"

# Path to the assignment report JSON file
ASSIGNMENT_REPORT_PATH = "/path/to/assignment_report.json"

# Path where you want the organized output
OUTPUT_BASE_PATH = "/path/to/output"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_json_file(file_path: str) -> Dict:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        raise


def create_directory_if_not_exists(dir_path: str) -> None:
    """Create directory if it doesn't exist."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def build_task_mapping(assignment_data: Dict) -> Dict[int, Dict]:
    """
    Build a mapping from task_id to task information.

    Returns:
        Dict[task_id] = {
            'annotator': str,
            'task_type': str,
            'clip_ids': List[str],
            'task_name': str
        }
    """
    task_mapping = {}

    for task in assignment_data.get('tasks', []):
        task_id = task.get('task_id')
        if task_id is None:
            logger.warning(f"Task missing task_id: {task}")
            continue

        task_mapping[task_id] = {
            'annotator': task.get('annotator', 'unknown'),
            'task_type': task.get('task_type', 'unknown'),
            'clip_ids': task.get('clip_ids', []),
            'task_name': task.get('task_name', f'task_{task_id}')
        }

    return task_mapping


def build_job_to_task_mapping(meta_data: Dict) -> Dict[int, int]:
    """
    Build a mapping from job_id to task_id.

    Returns:
        Dict[job_id] = task_id
    """
    job_to_task = {}

    for job in meta_data.get('jobs', []):
        job_id = job.get('id')
        task_id = job.get('task_id')

        if job_id is None or task_id is None:
            logger.warning(f"Job missing id or task_id: {job}")
            continue

        job_to_task[job_id] = task_id

    return job_to_task


def get_clip_id_for_task(task_info: Dict, job_id: int) -> str:
    """
    Get the appropriate clip_id for a task.

    For now, we'll use the first clip_id if multiple exist.
    You might want to modify this logic based on your specific needs.
    """
    clip_ids = task_info.get('clip_ids', [])

    if not clip_ids:
        logger.warning(f"No clip_ids found for task, using job_id {job_id} as fallback")
        return str(job_id)

    if len(clip_ids) > 1:
        logger.info(f"Multiple clip_ids found for task: {clip_ids}, using first one")

    return clip_ids[0]


def copy_annotation_file(source_path: str, dest_path: str, move_files: bool = False) -> bool:
    """
    Copy or move annotation file from source to destination.

    Args:
        source_path: Source file path
        dest_path: Destination file path
        move_files: If True, move files instead of copying

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(source_path):
            logger.warning(f"Source file not found: {source_path}")
            return False

        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        create_directory_if_not_exists(dest_dir)

        # Copy or move the file
        if move_files:
            shutil.move(source_path, dest_path)
            logger.info(f"Moved: {source_path} -> {dest_path}")
        else:
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied: {source_path} -> {dest_path}")

        return True

    except Exception as e:
        logger.error(f"Error processing file {source_path}: {e}")
        return False


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def organize_cvat_annotations(
        cvat_export_path: str,
        assignment_report_path: str,
        output_base_path: str,
        move_files: bool = False
) -> None:
    """
    Main function to organize CVAT annotations.

    Args:
        cvat_export_path: Path to extracted CVAT export
        assignment_report_path: Path to assignment report JSON
        output_base_path: Path for organized output
        move_files: If True, move files instead of copying
    """
    logger.info("Starting CVAT annotation organization...")

    # Load data files
    logger.info("Loading configuration files...")

    meta_json_path = os.path.join(cvat_export_path, 'meta.json')
    meta_data = load_json_file(meta_json_path)
    assignment_data = load_json_file(assignment_report_path)

    # Build mappings
    logger.info("Building task and job mappings...")
    task_mapping = build_task_mapping(assignment_data)
    job_to_task = build_job_to_task_mapping(meta_data)

    logger.info(f"Found {len(task_mapping)} tasks and {len(job_to_task)} jobs")

    # Process each job
    processed_count = 0
    error_count = 0

    for job_id, task_id in job_to_task.items():
        logger.info(f"Processing job {job_id} (task {task_id})...")

        # Get task information
        task_info = task_mapping.get(task_id)
        if not task_info:
            logger.warning(f"No task information found for task_id {task_id}")
            error_count += 1
            continue

        # Get clip ID for this task
        clip_id = get_clip_id_for_task(task_info, job_id)

        # Build source and destination paths
        source_path = os.path.join(
            cvat_export_path,
            'jobs',
            str(job_id),
            'annotations.xml'
        )

        dest_path = os.path.join(
            output_base_path,
            task_info['annotator'],
            task_info['task_type'],
            f"{clip_id}.xml"
        )

        # Copy/move the file
        if copy_annotation_file(source_path, dest_path, move_files):
            processed_count += 1
        else:
            error_count += 1

    # Summary
    logger.info("=" * 50)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total jobs processed: {processed_count}")
    logger.info(f"Errors encountered: {error_count}")
    logger.info(f"Output directory: {output_base_path}")
    logger.info("Organization complete!")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point."""
    try:
        # Validate input paths
        if not os.path.exists(CVAT_EXPORT_PATH):
            raise FileNotFoundError(f"CVAT export path not found: {CVAT_EXPORT_PATH}")

        if not os.path.exists(ASSIGNMENT_REPORT_PATH):
            raise FileNotFoundError(f"Assignment report not found: {ASSIGNMENT_REPORT_PATH}")

        # Run the organization process
        organize_cvat_annotations(
            cvat_export_path=CVAT_EXPORT_PATH,
            assignment_report_path=ASSIGNMENT_REPORT_PATH,
            output_base_path=OUTPUT_BASE_PATH,
            move_files=False  # Set to True if you want to move instead of copy
        )

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise


if __name__ == "__main__":
    main()