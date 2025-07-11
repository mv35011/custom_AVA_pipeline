#!/usr/bin/env python3
"""
Multi-Annotator AVA Dataset Task Creator with Overlap Support
Creates tasks for multiple annotators with configurable overlap based on JSON assignment file.
Supports 20% overlap for quality control and consensus building.
"""

import os
import json
import logging
from pathlib import Path
from cvat_integration import CVATClient, get_default_labels
import time
from datetime import datetime
from typing import List, Dict, Optional, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiAnnotatorTaskCreator:
    def __init__(self, cvat_client, assignment_config_path):
        self.client = cvat_client
        self.assignment_config_path = assignment_config_path
        self.project_id = None
        self.assignments = {}
        self.annotators = set()
        self.overlap_assignments = {}

    def load_assignment_config(self):
        """Load assignment configuration from JSON file"""
        try:
            with open(self.assignment_config_path, 'r') as f:
                config = json.load(f)
            if 'assignments' not in config:
                raise ValueError("Assignment config must have 'assignments' key")

            self.assignments = config['assignments']
            for assignment in self.assignments:
                clip_id = str(assignment['clip_id'])
                assigned_to = assignment['assigned_to']
                overlap_with = assignment.get('overlap_with', [])

                if isinstance(assigned_to, str):
                    assigned_to = [assigned_to]
                if isinstance(overlap_with, str) and overlap_with:
                    overlap_with = [overlap_with]
                elif not overlap_with:
                    overlap_with = []

                self.annotators.update(assigned_to)
                self.annotators.update(overlap_with)

                if overlap_with:
                    self.overlap_assignments[clip_id] = {
                        'primary': assigned_to,
                        'overlap': overlap_with
                    }

            logger.info(f"Loaded assignments for {len(self.assignments)} clips")
            logger.info(f"Found annotators: {', '.join(sorted(self.annotators))}")
            logger.info(f"Overlap assignments: {len(self.overlap_assignments)} clips")
            return True

        except Exception as e:
            logger.error(f"Error loading assignment config: {str(e)}")
            return False

    def create_project(self, project_name=None):
        """Create a new CVAT project with default labels"""
        if not project_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"AVA_MultiAnnotator_{timestamp}"

        try:
            labels = get_default_labels()
            self.project_id = self.client.create_project(project_name, labels)

            if self.project_id:
                logger.info(f"✓ Project '{project_name}' created successfully with ID: {self.project_id}")
                return True
            else:
                logger.error(f"✗ Failed to create project '{project_name}'")
                return False

        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return False

    def get_annotator_assignments(self, annotator):
        """Get all clip assignments for a specific annotator"""
        primary_clips = []
        overlap_clips = []

        for assignment in self.assignments:
            clip_id = str(assignment['clip_id'])
            assigned_to = assignment['assigned_to']
            overlap_with = assignment.get('overlap_with', [])

            if isinstance(assigned_to, str):
                assigned_to = [assigned_to]
            if isinstance(overlap_with, str) and overlap_with:
                overlap_with = [overlap_with]
            elif not overlap_with:
                overlap_with = []

            if annotator in assigned_to:
                primary_clips.append(clip_id)
            if annotator in overlap_with:
                overlap_clips.append(clip_id)

        return primary_clips, overlap_clips

    def create_task_for_annotator_clips(self, annotator, clip_ids, task_type, zip_dir, xml_dir=None):
        """Create a single task for specific clips assigned to an annotator"""
        if not self.project_id:
            logger.error("No project created. Cannot create task.")
            return None

        if not clip_ids:
            logger.warning(f"No clips assigned to {annotator} for {task_type}")
            return None

        clip_range = f"{min(map(int, clip_ids))}-{max(map(int, clip_ids))}"
        task_name = f"AVA_{annotator}_{task_type}_clips_{clip_range}"
        zip_files = []
        xml_files = []

        # Collect valid zip files
        for clip_id in clip_ids:
            zip_file_path = os.path.join(zip_dir, f"{clip_id}.zip")

            if not os.path.exists(zip_file_path):
                logger.warning(f"Zip file not found: {zip_file_path}")
                continue

            if not self.validate_zip_file(zip_file_path):
                logger.warning(f"Invalid zip file: {zip_file_path}")
                continue

            zip_files.append(zip_file_path)

            # Find corresponding XML file if xml_dir is provided
            if xml_dir:
                xml_file_path = self.find_xml_file(xml_dir, clip_id)
                if xml_file_path:
                    xml_files.append(xml_file_path)

        if not zip_files:
            logger.error(f"No valid zip files found for {annotator} {task_type} clips")
            return None

        try:
            logger.info(f"Creating task: {task_name} with {len(zip_files)} zip files")

            # Use the updated create_task_alternative method
            task_result = self.client.create_task_alternative(
                name=task_name,
                project_id=self.project_id,
                zip_files=zip_files,
                overlap=0
            )

            if not task_result:
                logger.error(f"Failed to create task {task_name}")
                return None

            # Extract the returned metadata
            task_id = task_result['task_id']
            job_ids = task_result['job_ids']
            project_id = task_result['project_id']

            logger.info(f"✓ Task '{task_name}' created successfully with ID: {task_id}")
            logger.info(f"✓ Job IDs: {job_ids}")

            # Wait for server to process files
            wait_time = 5 + len(zip_files)
            logger.info(f"Waiting {wait_time} seconds for server to process {len(zip_files)} zip files...")
            time.sleep(wait_time)

            # Import XML annotations if available
            imported_annotations = 0
            if xml_files:
                for xml_file in xml_files:
                    logger.info(f"Importing annotations from {os.path.basename(xml_file)}")
                    if self.client.import_annotations(task_id, xml_file):
                        imported_annotations += 1
                        logger.info(f"✓ Annotations imported from {os.path.basename(xml_file)}")
                    else:
                        logger.warning(f"⚠ Failed to import annotations from {os.path.basename(xml_file)}")

            # Assign user to task
            logger.info(f"Assigning user {annotator} to task {task_id}")
            if self.client.assign_user_to_task(task_id, annotator):
                logger.info(f"✓ User {annotator} assigned to task {task_id}")
            else:
                logger.warning(f"⚠ Failed to assign user {annotator} to task {task_id}")

            total_size = sum(self.get_zip_file_size(zf) for zf in zip_files)

            return {
                'project_id': project_id,  # Use the project_id from task_result
                'task_id': task_id,
                'job_ids': job_ids,  # Include job_ids in the return
                'task_name': task_name,
                'annotator': annotator,
                'task_type': task_type,
                'clip_ids': clip_ids,
                'zip_files': [os.path.basename(zf) for zf in zip_files],
                'total_size_mb': round(total_size, 2),
                'xml_files_imported': imported_annotations,
                'xml_files_found': len(xml_files)
            }

        except Exception as e:
            logger.error(f"Error creating task for {annotator} {task_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def create_all_annotator_tasks(self, zip_dir, xml_dir=None):
        """Create tasks for all annotators based on assignment configuration"""
        if not self.project_id:
            logger.error("No project created. Cannot create tasks.")
            return []

        if not self.assignments:
            logger.error("No assignments loaded. Cannot create tasks.")
            return []

        created_tasks = []

        for annotator in sorted(self.annotators):
            logger.info(f"Processing tasks for annotator: {annotator}")
            primary_clips, overlap_clips = self.get_annotator_assignments(annotator)

            logger.info(f"  Primary clips: {len(primary_clips)} clips")
            logger.info(f"  Overlap clips: {len(overlap_clips)} clips")

            if primary_clips:
                primary_task = self.create_task_for_annotator_clips(
                    annotator, primary_clips, "primary", zip_dir, xml_dir
                )
                if primary_task:
                    created_tasks.append(primary_task)

            if overlap_clips:
                overlap_task = self.create_task_for_annotator_clips(
                    annotator, overlap_clips, "overlap", zip_dir, xml_dir
                )
                if overlap_task:
                    created_tasks.append(overlap_task)

        return created_tasks

    def validate_zip_file(self, zip_file_path):
        """Validate that zip file exists and is readable"""
        if not os.path.exists(zip_file_path):
            return False

        if not os.path.isfile(zip_file_path):
            return False

        if not zip_file_path.lower().endswith('.zip'):
            return False

        if not self.client._validate_zip_contents(zip_file_path):
            return False

        try:
            with open(zip_file_path, 'rb') as f:
                pass
            return True
        except Exception:
            return False

    def get_zip_file_size(self, zip_file_path):
        """Get the size of the zip file in MB"""
        try:
            size_bytes = os.path.getsize(zip_file_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        except Exception:
            return 0

    def find_xml_file(self, xml_dir, clip_id):
        """Find XML file for a specific clip ID"""
        xml_patterns = [
            f"subdir_{clip_id}_annotations.xml",
            f"{clip_id}_annotations.xml",
            f"annotations_{clip_id}.xml",
            f"subdir_{clip_id}.xml",
            f"clip_{clip_id}.xml"
        ]

        for pattern in xml_patterns:
            xml_path = os.path.join(xml_dir, pattern)
            if os.path.exists(xml_path):
                return xml_path
        return None

    def save_task_report(self, tasks):
        """Save comprehensive task creation report"""
        if not tasks:
            logger.warning("No tasks to save in report")
            return

        annotator_tasks = {}
        for task in tasks:
            annotator = task['annotator']
            if annotator not in annotator_tasks:
                annotator_tasks[annotator] = {'primary': [], 'overlap': []}
            annotator_tasks[annotator][task['task_type']].append(task)

        overlap_analysis = {}
        for clip_id, overlap_info in self.overlap_assignments.items():
            overlap_analysis[clip_id] = {
                'primary_annotators': overlap_info['primary'],
                'overlap_annotators': overlap_info['overlap'],
                'total_annotators': len(overlap_info['primary']) + len(overlap_info['overlap'])
            }

        report = {
            'project_id': self.project_id,
            'creation_timestamp': datetime.now().isoformat(),
            'assignment_config_path': self.assignment_config_path,
            'annotators': sorted(list(self.annotators)),
            'tasks': tasks,
            'annotator_tasks': annotator_tasks,
            'overlap_analysis': overlap_analysis,
            'summary': {
                'total_tasks': len(tasks),
                'total_annotators': len(self.annotators),
                'total_clips': len(self.assignments),
                'overlap_clips': len(self.overlap_assignments),
                'total_size_mb': sum(task['total_size_mb'] for task in tasks),
                'xml_files_imported': sum(task['xml_files_imported'] for task in tasks),
                'tasks_by_type': {
                    'primary': len([t for t in tasks if t['task_type'] == 'primary']),
                    'overlap': len([t for t in tasks if t['task_type'] == 'overlap'])
                }
            }
        }

        report_file = f'multi_annotator_task_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Task report saved to {report_file}")
            self.print_summary(report)

        except Exception as e:
            logger.error(f"Error saving task report: {str(e)}")

    def print_summary(self, report):
        """Print detailed summary of created tasks"""
        print("\n" + "=" * 80)
        print("MULTI-ANNOTATOR TASK CREATION SUMMARY")
        print("=" * 80)
        print(f"Project ID: {report['project_id']}")
        print(f"Total Annotators: {report['summary']['total_annotators']}")
        print(f"Total Tasks: {report['summary']['total_tasks']}")
        print(f"  - Primary Tasks: {report['summary']['tasks_by_type']['primary']}")
        print(f"  - Overlap Tasks: {report['summary']['tasks_by_type']['overlap']}")
        print(f"Total Clips: {report['summary']['total_clips']}")
        print(f"Overlap Clips: {report['summary']['overlap_clips']}")
        print(f"Total Size: {report['summary']['total_size_mb']:.2f} MB")
        print(f"XML Files Imported: {report['summary']['xml_files_imported']}")

        print("\nAnnotator Breakdown:")
        for annotator, tasks in report['annotator_tasks'].items():
            primary_count = len(tasks['primary'])
            overlap_count = len(tasks['overlap'])
            total_clips = sum(len(t['clip_ids']) for t in tasks['primary'] + tasks['overlap'])
            total_size = sum(t['total_size_mb'] for t in tasks['primary'] + tasks['overlap'])

            print(f"  {annotator}:")
            print(f"    - Primary: {primary_count} tasks")
            print(f"    - Overlap: {overlap_count} tasks")
            print(f"    - Total clips: {total_clips}")
            print(f"    - Total size: {total_size:.2f} MB")

        print("\nOverlap Analysis:")
        if report['overlap_analysis']:
            for clip_id, overlap_info in report['overlap_analysis'].items():
                print(f"  Clip {clip_id}: {overlap_info['total_annotators']} annotators")
                print(f"    Primary: {', '.join(overlap_info['primary_annotators'])}")
                print(f"    Overlap: {', '.join(overlap_info['overlap_annotators'])}")
        else:
            print("  No overlap assignments found")

        print("\nTasks Created:")
        for task in report['tasks']:
            print(f"  - {task['task_name']} (ID: {task['task_id']})")
            print(
                f"    └─ {task['annotator']} | {task['task_type']} | {len(task['clip_ids'])} clips | {task['total_size_mb']}MB")

        print("=" * 80)

    def create_sample_assignment_config(self, output_path, num_clips=10):
        """Create a sample assignment configuration file"""
        sample_config = {
            "description": "Sample assignment configuration for multi-annotator tasks",
            "created": datetime.now().isoformat(),
            "overlap_percentage": 20,
            "assignments": []
        }

        annotators = ["annotator_1", "annotator_2", "annotator_3"]

        for clip_id in range(1, num_clips + 1):
            primary_annotator = annotators[(clip_id - 1) % len(annotators)]
            overlap_annotator = None

            if clip_id % 5 == 0:
                overlap_annotator = annotators[(clip_id % len(annotators))]
                if overlap_annotator == primary_annotator:
                    overlap_annotator = annotators[(clip_id + 1) % len(annotators)]

            assignment = {
                "clip_id": clip_id,
                "assigned_to": primary_annotator,
                "overlap_with": overlap_annotator if overlap_annotator else ""
            }

            sample_config["assignments"].append(assignment)

        try:
            with open(output_path, 'w') as f:
                json.dump(sample_config, f, indent=2)
            logger.info(f"Sample assignment config created at: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating sample config: {str(e)}")
            return False

    def validate_assignment_config(self):
        """Validate the assignment configuration"""
        if not self.assignments:
            logger.error("No assignments loaded")
            return False

        issues = []
        clip_ids = set()

        for assignment in self.assignments:
            clip_id = assignment.get('clip_id')
            assigned_to = assignment.get('assigned_to')

            if not clip_id:
                issues.append("Missing clip_id in assignment")
                continue

            if not assigned_to:
                issues.append(f"Missing assigned_to for clip {clip_id}")
                continue

            if clip_id in clip_ids:
                issues.append(f"Duplicate clip_id: {clip_id}")
            else:
                clip_ids.add(clip_id)

        if issues:
            logger.error("Assignment config validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False

        logger.info("Assignment config validation passed")
        return True


def main():
    """Main function with multi-annotator support"""
    CVAT_HOST = "http://localhost:8080"
    CVAT_USERNAME = "mv350"
    CVAT_PASSWORD = "Amazon123"

    parent = Path(__file__).parent.parent.parent
    zip_dir = str(parent / "data" / "Dataset" / "zip_choose_frames_middle")
    xml_dir = str(parent / "data" / "cvat_xmls")
    assignment_config_path = str(parent / "config" / "assignment_config.json")

    print(f"Zip directory: {zip_dir}")
    print(f"XML directory: {xml_dir}")
    print(f"Assignment config: {assignment_config_path}")

    # Create sample config if it doesn't exist
    if not os.path.exists(assignment_config_path):
        os.makedirs(os.path.dirname(assignment_config_path), exist_ok=True)
        print("Creating sample assignment configuration...")
        temp_creator = MultiAnnotatorTaskCreator(None, assignment_config_path)
        if temp_creator.create_sample_assignment_config(assignment_config_path, 10):
            print(f"Sample config created at: {assignment_config_path}")
            print("Please edit this file to match your requirements before running again.")
            return

    # Validate directories
    if not os.path.exists(zip_dir):
        logger.error(f"Zip directory does not exist: {zip_dir}")
        return

    if xml_dir and not os.path.exists(xml_dir):
        logger.warning(f"XML directory does not exist: {xml_dir}")
        xml_dir = None

    # Initialize CVAT client
    logger.info("Initializing CVAT client...")
    try:
        client = CVATClient(host=CVAT_HOST, username=CVAT_USERNAME, password=CVAT_PASSWORD)

        if not client.test_connection():
            logger.error("Cannot connect to CVAT server. Please check if it's running.")
            return

        if not client.authenticated:
            logger.error("Authentication failed. Please check credentials.")
            return

        logger.info("✓ Connected to CVAT server successfully")

    except Exception as e:
        logger.error(f"Error initializing CVAT client: {str(e)}")
        return

    # Create tasks
    task_creator = MultiAnnotatorTaskCreator(client, assignment_config_path)

    try:
        if not task_creator.load_assignment_config():
            logger.error("Failed to load assignment configuration. Exiting.")
            return

        if not task_creator.validate_assignment_config():
            logger.error("Assignment configuration validation failed. Exiting.")
            return

        if not task_creator.create_project():
            logger.error("Failed to create project. Exiting.")
            return

        created_tasks = task_creator.create_all_annotator_tasks(zip_dir, xml_dir)
        task_creator.save_task_report(created_tasks)

        if created_tasks:
            logger.info(
                f"✓ Successfully created {len(created_tasks)} tasks for {len(task_creator.annotators)} annotators")
        else:
            logger.error("✗ No tasks were created successfully")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()