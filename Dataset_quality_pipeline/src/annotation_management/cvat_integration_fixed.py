#!/usr/bin/env python3
"""
Fixed CVAT Integration Script for AVA Dataset Pipeline
This script fixes the authentication and connection issues with CVAT.
"""

import requests
import json
import os
import time
import zipfile
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVATClient:
    def __init__(self, host="http://localhost:8080", username=None, password=None):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        
        # Set common headers (avoid Accept header as CVAT API can be picky)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        })
        
        if username and password:
            self.login()
    
    def test_connection(self):
        """Test if CVAT is accessible"""
        try:
            logger.info(f"Testing connection to: {self.host}")
            # First try basic connection
            response = self.session.get(f"{self.host}", timeout=10)
            if response.status_code != 200:
                logger.error(f"CVAT server not accessible: {response.status_code}")
                return False
            
            # Then try API endpoint
            response = self.session.get(f"{self.host}/api/server/about", timeout=10)
            
            if response.status_code == 200:
                logger.info("✓ CVAT server is accessible")
                try:
                    server_info = response.json()
                    logger.info(f"Server info: {server_info}")
                except:
                    logger.warning("Server responded but couldn't parse JSON")
                return True
            else:
                logger.error(f"CVAT server error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: Cannot connect to {self.host}")
            logger.error("Make sure CVAT is running with: docker compose up -d")
            return False
        except requests.exceptions.Timeout:
            logger.error("Timeout error: CVAT server is not responding")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
    
    def login(self):
        """Login to CVAT with improved authentication"""
        try:
            logger.info(f"Attempting login for user: {self.username}")
            
            # First, try the simple API login
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            response = self.session.post(
                f"{self.host}/api/auth/login",
                json=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✓ Login successful")
                self.authenticated = True
                return True
            
            # If that fails, try form-based login
            logger.info("Trying form-based login...")
            
            # Get login page to get CSRF token
            response = self.session.get(f"{self.host}/auth/login")
            
            # Extract CSRF token from cookies
            csrf_token = None
            for cookie in self.session.cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if csrf_token:
                self.session.headers.update({'X-CSRFToken': csrf_token})
                logger.info("✓ CSRF token obtained")
            
            # Try form login
            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(
                f"{self.host}/auth/login",
                data=login_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                allow_redirects=False
            )
            
            if response.status_code in [200, 302]:
                logger.info("✓ Form-based login successful")
                self.authenticated = True
                return True
            
            logger.error(f"Login failed with status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make authenticated request to CVAT API"""
        if not self.authenticated:
            logger.warning("Not authenticated, attempting login...")
            if not self.login():
                raise Exception("Authentication failed")
        
        url = f"{self.host}/api{endpoint}"
        
        # Add CSRF token if available
        if 'csrftoken' in [cookie.name for cookie in self.session.cookies]:
            csrf_token = next(cookie.value for cookie in self.session.cookies if cookie.name == 'csrftoken')
            if method.upper() != 'GET':
                kwargs.setdefault('headers', {})
                kwargs['headers']['X-CSRFToken'] = csrf_token
        
        response = self.session.request(method, url, **kwargs)
        
        # Handle 403 errors (potentially CSRF issues)
        if response.status_code == 403:
            logger.warning("403 error, trying to refresh authentication...")
            if self.login():
                response = self.session.request(method, url, **kwargs)
        
        return response
    
    def create_project(self, name, labels):
        """Create a new project"""
        try:
            project_data = {
                'name': name,
                'labels': labels
            }
            
            response = self._make_request('POST', '/projects', json=project_data)
            
            if response.status_code == 201:
                project_id = response.json()['id']
                logger.info(f"✓ Project created: {name} (ID: {project_id})")
                return project_id
            else:
                logger.error(f"Failed to create project: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Create project error: {str(e)}")
            return None
    
    def create_task(self, name, project_id, zip_files, overlap=0):
        """Create a new task with zip files"""
        try:
            logger.info(f"Creating task '{name}' with {len(zip_files)} zip files")
            
            # Validate zip files
            valid_zip_files = []
            for zip_path in zip_files:
                if self._validate_zip_file(zip_path):
                    valid_zip_files.append(zip_path)
            
            if not valid_zip_files:
                logger.error("No valid zip files provided")
                return None
            
            # Create task with data
            task_spec = {
                "name": name,
                "project_id": project_id,
                "overlap": overlap
            }
            
            files = {}
            file_handles = []
            
            try:
                # Add task specification
                files['task_spec'] = (None, json.dumps(task_spec))
                
                # Add zip files
                for i, zip_path in enumerate(valid_zip_files):
                    file_handle = open(zip_path, 'rb')
                    file_handles.append(file_handle)
                    files[f'client_files[{i}]'] = (
                        os.path.basename(zip_path),
                        file_handle,
                        'application/zip'
                    )
                
                # Make request without JSON content-type for multipart
                headers = {}
                if 'csrftoken' in [cookie.name for cookie in self.session.cookies]:
                    csrf_token = next(cookie.value for cookie in self.session.cookies if cookie.name == 'csrftoken')
                    headers['X-CSRFToken'] = csrf_token
                
                response = self.session.post(
                    f"{self.host}/api/tasks",
                    files=files,
                    headers=headers,
                    timeout=300
                )
                
            finally:
                for file_handle in file_handles:
                    file_handle.close()
            
            if response.status_code == 201:
                task_data = response.json()
                task_id = task_data['id']
                logger.info(f"✓ Task created: {name} (ID: {task_id})")
                
                # Wait for task to be ready
                if self._wait_for_task_ready(task_id):
                    job_ids = self._get_job_ids(task_id)
                    return {
                        'task_id': task_id,
                        'job_ids': job_ids,
                        'project_id': project_id
                    }
                else:
                    logger.warning(f"Task {task_id} created but may not be ready")
                    return {'task_id': task_id, 'job_ids': [], 'project_id': project_id}
            else:
                logger.error(f"Failed to create task: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Create task error: {str(e)}")
            return None
    
    def _validate_zip_file(self, zip_path):
        """Validate zip file contains images"""
        try:
            if not os.path.exists(zip_path):
                logger.error(f"Zip file not found: {zip_path}")
                return False
            
            if not zipfile.is_zipfile(zip_path):
                logger.error(f"Invalid zip file: {zip_path}")
                return False
            
            valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                image_files = [f for f in zip_ref.namelist() 
                             if any(f.lower().endswith(ext) for ext in valid_extensions)
                             and not f.startswith('.')]
                
                if len(image_files) > 0:
                    logger.info(f"✓ Zip file {zip_path} contains {len(image_files)} images")
                    return True
                else:
                    logger.error(f"Zip file {zip_path} contains no valid images")
                    return False
                    
        except Exception as e:
            logger.error(f"Error validating zip file {zip_path}: {str(e)}")
            return False
    
    def _wait_for_task_ready(self, task_id, timeout=60):
        """Wait for task to be ready"""
        logger.info(f"Waiting for task {task_id} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self._make_request('GET', f'/tasks/{task_id}')
                if response.status_code == 200:
                    task_info = response.json()
                    status = task_info.get('status', 'unknown')
                    
                    if status in ['annotation', 'validation', 'completed']:
                        logger.info(f"✓ Task {task_id} is ready (status: {status})")
                        return True
                    elif status == 'failed':
                        logger.error(f"✗ Task {task_id} failed")
                        return False
                    
                    logger.info(f"Task status: {status}")
                    time.sleep(2)
                else:
                    logger.warning(f"Error checking task status: {response.status_code}")
                    time.sleep(2)
                    
            except Exception as e:
                logger.warning(f"Error checking task status: {str(e)}")
                time.sleep(2)
        
        logger.warning(f"Timeout waiting for task {task_id}")
        return False
    
    def _get_job_ids(self, task_id):
        """Get job IDs for a task"""
        try:
            response = self._make_request('GET', f'/jobs?task_id={task_id}')
            if response.status_code == 200:
                jobs = response.json()
                if isinstance(jobs, dict) and 'results' in jobs:
                    return [job['id'] for job in jobs['results']]
                elif isinstance(jobs, list):
                    return [job['id'] for job in jobs]
            return []
        except Exception as e:
            logger.error(f"Error getting job IDs: {str(e)}")
            return []
    
    def import_annotations(self, task_id, xml_file_path):
        """Import annotations from XML file"""
        try:
            logger.info(f"Importing annotations from {xml_file_path} to task {task_id}")
            
            if not os.path.exists(xml_file_path):
                logger.error(f"XML file not found: {xml_file_path}")
                return False
            
            with open(xml_file_path, 'rb') as f:
                files = {'annotation_file': f}
                data = {'format': 'CVAT for images 1.1'}
                
                # Add CSRF token
                headers = {}
                if 'csrftoken' in [cookie.name for cookie in self.session.cookies]:
                    csrf_token = next(cookie.value for cookie in self.session.cookies if cookie.name == 'csrftoken')
                    headers['X-CSRFToken'] = csrf_token
                
                response = self.session.post(
                    f"{self.host}/api/tasks/{task_id}/annotations",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info("✓ Annotations imported successfully")
                    return True
                else:
                    logger.error(f"Failed to import annotations: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error importing annotations: {str(e)}")
            return False
    
    def assign_user_to_task(self, task_id, username):
        """Assign user to task"""
        try:
            logger.info(f"Assigning user {username} to task {task_id}")
            
            # Get user ID
            response = self._make_request('GET', '/users')
            if response.status_code != 200:
                logger.error(f"Failed to get users: {response.status_code}")
                return False
            
            users = response.json()
            if isinstance(users, dict) and 'results' in users:
                users = users['results']
            
            user_id = None
            for user in users:
                if user['username'] == username:
                    user_id = user['id']
                    break
            
            if not user_id:
                logger.error(f"User not found: {username}")
                return False
            
            # Assign user to task
            assignment_data = {'assignee': user_id}
            response = self._make_request('PATCH', f'/tasks/{task_id}', json=assignment_data)
            
            if response.status_code == 200:
                logger.info(f"✓ User {username} assigned to task {task_id}")
                return True
            else:
                logger.error(f"Failed to assign user: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error assigning user: {str(e)}")
            return False

def get_default_labels():
    """Get default labels for AVA dataset"""
    return [
        {
            'name': 'person',
            'color': '#ff0000',
            'attributes': [
                {
                    'name': 'walking_behavior',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'normal_walk',
                    'values': ['normal_walk', 'fast_walk', 'slow_walk', 'standing_still', 'jogging', 'window_shopping']
                },
                {
                    'name': 'phone_usage',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'no_phone',
                    'values': ['no_phone', 'talking_phone', 'texting', 'taking_photo', 'listening_music']
                },
                {
                    'name': 'social_interaction',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'alone',
                    'values': ['alone', 'talking_companion', 'group_walking', 'greeting_someone', 'asking_directions', 'avoiding_crowd']
                },
                {
                    'name': 'carrying_items',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'empty_hands',
                    'values': ['empty_hands', 'shopping_bags', 'backpack', 'briefcase_bag', 'umbrella', 'food_drink', 'multiple_items']
                },
                {
                    'name': 'street_behavior',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'sidewalk_walking',
                    'values': ['sidewalk_walking', 'crossing_street', 'waiting_signal', 'looking_around', 'checking_map', 'entering_building', 'exiting_building']
                },
                {
                    'name': 'posture_gesture',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'upright_normal',
                    'values': ['upright_normal', 'looking_down', 'looking_up', 'hands_in_pockets', 'arms_crossed', 'pointing_gesture', 'bowing_gesture']
                },
                {
                    'name': 'clothing_style',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'casual_wear',
                    'values': ['business_attire', 'casual_wear', 'tourist_style', 'school_uniform', 'sports_wear', 'traditional_wear']
                },
                {
                    'name': 'time_context',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'leisure_time',
                    'values': ['rush_hour', 'leisure_time', 'shopping_time', 'tourist_hours', 'lunch_break', 'evening_stroll']
                }
            ]
        }
    ]

if __name__ == "__main__":
    # Test the CVAT client
    logger.info("Testing CVAT client...")
    
    client = CVATClient()
    if client.test_connection():
        logger.info("✓ CVAT connection successful")
        
        # Test with authentication
        auth_client = CVATClient(username="mv350", password="Amazon123")
        if auth_client.authenticated:
            logger.info("✓ Authentication successful")
        else:
            logger.error("✗ Authentication failed")
    else:
        logger.error("✗ CVAT connection failed")
        logger.error("Please run: python setup_cvat.py")
