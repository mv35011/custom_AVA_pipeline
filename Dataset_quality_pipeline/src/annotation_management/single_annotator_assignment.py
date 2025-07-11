#!/usr/bin/env python3
"""
Updated AVA Dataset Task Creator - Using Improved CVATClient
Creates a project and assigns tasks for each zip file (1.zip, 2.zip, 3.zip) to different tasks
for a single annotator with custom annotations XML.
Uses the improved cvat_integration.py with better error handling and authentication.
"""

import os
import json
import logging
from pathlib import Path
from cvat_integration import CVATClient, get_default_labels
import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImprovedAVATaskCreator:
    def __init__(self, cvat_client, annotator_username="mv350"):
        self.client = cvat_client
        self.annotator = annotator_username
        self.project_id = None

    def create_project(self, project_name="AVA_Dataset_Improved"):
        """Create a new CVAT project with default labels"""
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

    def validate_zip_file(self, zip_file_path):
        """Validate that zip file exists and is readable"""
        if not os.path.exists(zip_file_path):
            logger.error(f"Zip file does not exist: {zip_file_path}")
            return False

        if not os.path.isfile(zip_file_path):
            logger.error(f"Path is not a file: {zip_file_path}")
            return False

        if not zip_file_path.lower().endswith('.zip'):
            logger.error(f"File is not a zip file: {zip_file_path}")
            return False
        if not self.client._validate_zip_contents(zip_file_path):
            logger.error(f"Zip file contains no valid images: {zip_file_path}")
            return False

        try:
            with open(zip_file_path, 'rb') as f:
                pass
            return True
        except Exception as e:
            logger.error(f"Cannot read zip file {zip_file_path}: {str(e)}")
            return False

    def get_zip_file_size(self, zip_file_path):
        """Get the size of the zip file in MB"""
        try:
            size_bytes = os.path.getsize(zip_file_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        except Exception as e:
            logger.error(f"Error getting zip file size: {str(e)}")
            return 0

    def create_task_for_zip(self, zip_file_path, subdir_num, xml_file_path=None):
        """Create a task for a specific zip file using improved CVATClient"""
        if not self.project_id:
            logger.error("No project created. Cannot create task.")
            return None
        if not self.validate_zip_file(zip_file_path):
            return None
        zip_size = self.get_zip_file_size(zip_file_path)
        zip_filename = os.path.basename(zip_file_path)
        task_name = f"AVA_Subdir_{subdir_num}_{self.annotator}"

        try:
            logger.info(f"Creating task: {task_name} using {zip_filename} ({zip_size}MB)")
            task_id = self.client.create_task(
                name=task_name,
                project_id=self.project_id,
                zip_files=[zip_file_path],
                overlap=0
            )
            if not task_id:
                logger.info("Main task creation failed, trying alternative method...")
                task_id = self.client.create_task_alternative(
                    name=task_name,
                    project_id=self.project_id,
                    zip_files=[zip_file_path],
                    overlap=0
                )

            if not task_id:
                logger.error(f"Failed to create task {task_name} with both methods")
                return None

            logger.info(f"✓ Task '{task_name}' created successfully with ID: {task_id}")
            if xml_file_path and os.path.exists(xml_file_path):
                wait_time = 5
                logger.info(f"Waiting for {wait_time} seconds for server to process images...")
                time.sleep(wait_time)


                logger.info(f"Importing annotations from {xml_file_path}")
                if self.client.import_annotations(task_id, xml_file_path):
                    logger.info(f"✓ Annotations imported successfully for task {task_id}")
                else:
                    logger.warning(f"⚠ Failed to import annotations for task {task_id}")
            elif xml_file_path:
                logger.warning(f"XML file not found: {xml_file_path}")
            logger.info(f"Assigning user {self.annotator} to task {task_id}")
            if self.client.assign_user_to_task(task_id, self.annotator):
                logger.info(f"✓ User {self.annotator} assigned to task {task_id}")
            else:
                logger.warning(f"⚠ Failed to assign user {self.annotator} to task {task_id}")

            return {
                'task_id': task_id,
                'task_name': task_name,
                'subdirectory': subdir_num,
                'zip_file_path': zip_file_path,
                'zip_filename': zip_filename,
                'zip_size_mb': zip_size,
                'annotator': self.annotator,
                'xml_imported': xml_file_path and os.path.exists(xml_file_path),
                'xml_file_path': xml_file_path
            }

        except Exception as e:
            logger.error(f"Error creating task for zip file {zip_filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def create_all_tasks(self, zip_dir, xml_dir=None):
        """Create tasks for all zip files (1.zip, 2.zip, 3.zip) using improved methods"""
        if not self.project_id:
            logger.error("No project created. Cannot create tasks.")
            return []

        if not os.path.exists(zip_dir):
            logger.error(f"Zip directory does not exist: {zip_dir}")
            return []

        created_tasks = []
        for subdir_num in range(1, 4):
            logger.info(f"Processing zip file {subdir_num}.zip")
            zip_filename = f"{subdir_num}.zip"
            zip_file_path = os.path.join(zip_dir, zip_filename)
            if not os.path.exists(zip_file_path):
                logger.warning(f"Zip file not found: {zip_file_path}")
                continue
            xml_file_path = None
            if xml_dir:
                xml_patterns = [
                    f"subdir_{subdir_num}_annotations.xml",
                    f"{subdir_num}_annotations.xml",
                    f"annotations_{subdir_num}.xml",
                    f"subdir_{subdir_num}.xml"
                ]

                for pattern in xml_patterns:
                    potential_xml_path = os.path.join(xml_dir, pattern)
                    if os.path.exists(potential_xml_path):
                        xml_file_path = potential_xml_path
                        logger.info(f"Found XML file: {xml_file_path}")
                        break

                if not xml_file_path:
                    logger.warning(f"No XML file found for subdirectory {subdir_num} in {xml_dir}")
            task_info = self.create_task_for_zip(
                zip_file_path, subdir_num, xml_file_path
            )

            if task_info:
                created_tasks.append(task_info)
                logger.info(f"✓ Task created for {zip_filename}")
            else:
                logger.error(f"✗ Failed to create task for {zip_filename}")

        return created_tasks

    def create_zip_from_directory_if_needed(self, directory_path, zip_filename):
        """Helper method to create zip file from directory using improved client"""
        zip_path = os.path.join(os.path.dirname(directory_path), zip_filename)

        if os.path.exists(zip_path):
            logger.info(f"Zip file already exists: {zip_path}")
            return zip_path

        if self.client.create_zip_from_directory(directory_path, zip_path):
            logger.info(f"✓ Created zip file: {zip_path}")
            return zip_path
        else:
            logger.error(f"✗ Failed to create zip file: {zip_path}")
            return None

    def batch_create_tasks_from_directories(self, base_dir, xml_dir=None):
        """Create tasks from subdirectories, creating zip files as needed"""
        if not self.project_id:
            logger.error("No project created. Cannot create tasks.")
            return []

        if not os.path.exists(base_dir):
            logger.error(f"Base directory does not exist: {base_dir}")
            return []

        created_tasks = []
        for subdir_num in range(1, 4):
            subdir_path = os.path.join(base_dir, str(subdir_num))
            zip_filename = f"{subdir_num}.zip"
            zip_path = os.path.join(base_dir, zip_filename)

            logger.info(f"Processing subdirectory {subdir_num}")
            if not os.path.exists(zip_path):
                if os.path.exists(subdir_path):
                    logger.info(f"Creating zip file from directory: {subdir_path}")
                    zip_path = self.create_zip_from_directory_if_needed(subdir_path, zip_filename)
                    if not zip_path:
                        logger.error(f"Failed to create zip file for subdirectory {subdir_num}")
                        continue
                else:
                    logger.warning(f"Neither zip file nor directory exists for subdirectory {subdir_num}")
                    continue
            xml_file_path = None
            if xml_dir:
                xml_patterns = [
                    f"subdir_{subdir_num}_annotations.xml",
                    f"{subdir_num}_annotations.xml",
                    f"annotations_{subdir_num}.xml",
                    f"subdir_{subdir_num}.xml"
                ]

                for pattern in xml_patterns:
                    potential_xml_path = os.path.join(xml_dir, pattern)
                    if os.path.exists(potential_xml_path):
                        xml_file_path = potential_xml_path
                        logger.info(f"Found XML file: {xml_file_path}")
                        break
            task_info = self.create_task_for_zip(
                zip_path, subdir_num, xml_file_path
            )

            if task_info:
                created_tasks.append(task_info)
                logger.info(f"✓ Task created for subdirectory {subdir_num}")
            else:
                logger.error(f"✗ Failed to create task for subdirectory {subdir_num}")

        return created_tasks

    def save_task_report(self, tasks):
        """Save task creation report to JSON with improved formatting"""
        if not tasks:
            logger.warning("No tasks to save in report")
            return

        report = {
            'project_id': self.project_id,
            'annotator': self.annotator,
            'creation_timestamp': logger.handlers[0].formatter.formatTime(
                logging.LogRecord('', 0, '', 0, '', (), None)
            ) if logger.handlers else None,
            'tasks': tasks,
            'summary': {
                'total_tasks': len(tasks),
                'total_zip_size_mb': sum(task['zip_size_mb'] for task in tasks),
                'subdirectories_processed': [task['subdirectory'] for task in tasks],
                'zip_files_used': [task['zip_filename'] for task in tasks],
                'xml_files_imported': sum(1 for task in tasks if task['xml_imported'])
            }
        }

        report_file = 'ava_task_report_improved.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Task report saved to {report_file}")
            self.print_summary(report)

        except Exception as e:
            logger.error(f"Error saving task report: {str(e)}")

    def print_summary(self, report):
        """Print a detailed summary of created tasks"""
        print("\n" + "=" * 70)
        print("IMPROVED AVA TASK CREATION SUMMARY")
        print("=" * 70)
        print(f"Project ID: {report['project_id']}")
        print(f"Annotator: {report['annotator']}")
        print(f"Total Tasks: {report['summary']['total_tasks']}")
        print(f"Total Zip Size: {report['summary']['total_zip_size_mb']:.2f} MB")
        print(f"Subdirectories: {report['summary']['subdirectories_processed']}")
        print(f"Zip Files Used: {report['summary']['zip_files_used']}")
        print(f"XML Files Imported: {report['summary']['xml_files_imported']}")
        print("\nTasks Created:")
        for task in report['tasks']:
            xml_status = "✓" if task['xml_imported'] else "✗"
            print(f"  - {task['task_name']} (ID: {task['task_id']})")
            print(f"    └─ {task['zip_filename']} ({task['zip_size_mb']}MB) - XML: {xml_status}")
        print("=" * 70)

    def list_available_files(self, zip_dir, xml_dir=None):
        """List available zip and XML files for debugging"""
        print("\n" + "=" * 50)
        print("AVAILABLE FILES ANALYSIS")
        print("=" * 50)
        print(f"Zip directory: {zip_dir}")
        if os.path.exists(zip_dir):
            zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
            if zip_files:
                print("Available zip files:")
                for f in sorted(zip_files):
                    size = self.get_zip_file_size(os.path.join(zip_dir, f))
                    zip_path = os.path.join(zip_dir, f)
                    is_valid = self.client._validate_zip_contents(zip_path)
                    status = "✓" if is_valid else "✗"

                    print(f"  {status} {f} ({size}MB)")
            else:
                print("  No zip files found")
        else:
            print("  Directory does not exist")
        if xml_dir:
            print(f"\nXML directory: {xml_dir}")
            if os.path.exists(xml_dir):
                xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]
                if xml_files:
                    print("Available XML files:")
                    for f in sorted(xml_files):
                        xml_path = os.path.join(xml_dir, f)
                        size = round(os.path.getsize(xml_path) / 1024, 2)
                        print(f"  - {f} ({size}KB)")
                else:
                    print("  No XML files found")
            else:
                print("  Directory does not exist")
        print(f"\nSubdirectories in {zip_dir}:")
        if os.path.exists(zip_dir):
            subdirs = [d for d in os.listdir(zip_dir) if os.path.isdir(os.path.join(zip_dir, d))]
            if subdirs:
                for d in sorted(subdirs):
                    subdir_path = os.path.join(zip_dir, d)
                    image_count = len([f for f in os.listdir(subdir_path)
                                       if
                                       f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'))])
                    print(f"  - {d}/ ({image_count} images)")
            else:
                print("  No subdirectories found")

        print("=" * 50)


def main():
    """Main function with improved error handling and connection testing"""
    CVAT_HOST = "http://localhost:8080"
    CVAT_USERNAME = "mv350"
    CVAT_PASSWORD = "Amazon123"
    ANNOTATOR = "mv350"
    parent = Path(__file__).parent.parent.parent
    zip_dir = str(parent / "data" / "Dataset" / "zip_choose_frames_middle")
    xml_dir = str(parent / "data" / "cvat_xmls")

    print(f"Zip directory: {zip_dir}")
    print(f"XML directory: {xml_dir}")
    if not os.path.exists(zip_dir):
        logger.error(f"Zip directory does not exist: {zip_dir}")
        return

    if xml_dir and not os.path.exists(xml_dir):
        logger.warning(f"XML directory does not exist: {xml_dir}")
        xml_dir = None
    logger.info("Initializing improved CVAT client...")
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
    task_creator = ImprovedAVATaskCreator(client, ANNOTATOR)
    task_creator.list_available_files(zip_dir, xml_dir)

    try:
        if not task_creator.create_project():
            logger.error("Failed to create project. Exiting.")
            return
        zip_files_exist = all(os.path.exists(os.path.join(zip_dir, f"{i}.zip")) for i in range(1, 4))

        if zip_files_exist:
            logger.info("Using existing zip files...")
            created_tasks = task_creator.create_all_tasks(zip_dir, xml_dir)
        else:
            logger.info("Creating zip files from directories...")
            created_tasks = task_creator.batch_create_tasks_from_directories(zip_dir, xml_dir)
        task_creator.save_task_report(created_tasks)
        if created_tasks:
            logger.info(f"✓ Successfully created {len(created_tasks)} tasks using improved methods")
        else:
            logger.error("✗ No tasks were created successfully")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()