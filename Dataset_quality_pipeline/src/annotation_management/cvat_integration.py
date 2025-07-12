import requests
import json
import os
from pathlib import Path
import time
import zipfile


class CVATClient:
    def __init__(self, host="http://localhost:8080", username=None, password=None):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self.authenticated = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/vnd.cvat+json',
            'Referer': f'{self.host}/',
        })

        if username and password:
            self.login()

    def test_connection(self):
        """Test if CVAT is accessible"""
        try:
            print(f"Testing connection to: {self.host}")
            response = self.session.get(f"{self.host}/", timeout=10)
            print(f"Main page status: {response.status_code}")
            headers = {'Accept': 'application/vnd.cvat+json'}
            response = self.session.get(f"{self.host}/api/server/about", headers=headers, timeout=10)
            print(f"API endpoint status: {response.status_code}")

            if response.status_code == 200:
                print("✓ CVAT server is accessible")
                try:
                    server_info = response.json()
                    print(f"Server info: {server_info}")
                except:
                    print("Server responded but couldn't parse JSON")
                return True
            else:
                print(f"CVAT server error: {response.status_code}")
                print(f"Response text: {response.text}")
                return False

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: Cannot connect to {self.host}")
            print(f"Error details: {str(e)}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"Timeout error: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False

    def get_csrf_token(self):
        """Get CSRF token for authentication - improved method"""
        try:
            print("Getting CSRF token...")
            response = self.session.get(f"{self.host}/auth/login")
            if 'csrftoken' in response.cookies:
                self.csrf_token = response.cookies['csrftoken']
                print(f"✓ CSRF token obtained from cookies: {self.csrf_token[:10]}...")
                return True
            if 'csrftoken' in response.text or 'csrf' in response.text.lower():
                import re
                csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
                if not csrf_match:
                    csrf_match = re.search(r'csrftoken["\']?\s*:\s*["\']([^"\']+)["\']', response.text)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    print(f"✓ CSRF token extracted from HTML: {self.csrf_token[:10]}...")
                    return True
            headers = {'Accept': 'application/vnd.cvat+json'}
            response = self.session.get(f"{self.host}/api/auth/login", headers=headers)

            if 'csrftoken' in response.cookies:
                self.csrf_token = response.cookies['csrftoken']
                print(f"✓ CSRF token obtained from API: {self.csrf_token[:10]}...")
                return True

            print("⚠ Could not obtain CSRF token")
            return False

        except Exception as e:
            print(f"CSRF token error: {str(e)}")
            return False

    def login(self):
        """Login with improved CSRF handling"""
        try:
            print(f"Attempting login for user: {self.username}")
            if not self.get_csrf_token():
                print("Warning: Proceeding without CSRF token...")
            headers = {
                'Accept': 'application/vnd.cvat+json',
                'Content-Type': 'application/json',
                'Referer': f'{self.host}/auth/login',
            }

            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
                self.session.headers.update({'X-CSRFToken': self.csrf_token})
            login_data = {
                'username': self.username,
                'password': self.password
            }
            response = self.session.post(
                f"{self.host}/api/auth/login",
                json=login_data,
                headers=headers
            )

            print(f"Login response status: {response.status_code}")

            if response.status_code == 200:
                print("✓ Login successful")
                self.authenticated = True
                if 'csrftoken' in response.cookies:
                    self.csrf_token = response.cookies['csrftoken']
                    self.session.headers.update({'X-CSRFToken': self.csrf_token})

                return True

            elif response.status_code == 403:
                print("⚠ CSRF verification failed, trying alternative methods...")
                return self.login_alternative()

            else:
                print(f"Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return self.login_alternative()

        except Exception as e:
            print(f"Login error: {str(e)}")
            return False

    def login_alternative(self):
        """Alternative login methods"""
        try:
            print("Trying alternative login methods...")
            if not self.csrf_token:
                self.get_csrf_token()

            headers = {
                'Accept': 'application/vnd.cvat+json',
                'Referer': f'{self.host}/auth/login',
            }

            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token

            login_data = {
                'username': self.username,
                'password': self.password
            }

            if self.csrf_token:
                login_data['csrfmiddlewaretoken'] = self.csrf_token

            response = self.session.post(
                f"{self.host}/api/auth/login",
                data=login_data,
                headers=headers
            )

            print(f"Alternative login response status: {response.status_code}")

            if response.status_code == 200:
                print("✓ Alternative login successful")
                self.authenticated = True
                return True
            print("Trying web-based login...")
            response = self.session.get(f"{self.host}/auth/login")
            if 'csrftoken' in response.cookies:
                self.csrf_token = response.cookies['csrftoken']
            login_data = {
                'username': self.username,
                'password': self.password,
                'csrfmiddlewaretoken': self.csrf_token
            }

            headers = {
                'Referer': f'{self.host}/auth/login',
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = self.session.post(
                f"{self.host}/auth/login",
                data=login_data,
                headers=headers,
                allow_redirects=False
            )

            print(f"Web login response status: {response.status_code}")

            if response.status_code in [200, 302]:
                print("✓ Web login successful")
                self.authenticated = True
                if 'csrftoken' in response.cookies:
                    self.csrf_token = response.cookies['csrftoken']
                    self.session.headers.update({'X-CSRFToken': self.csrf_token})

                return True

            print(f"All login methods failed")
            return False

        except Exception as e:
            print(f"Alternative login error: {str(e)}")
            return False

    def _make_authenticated_request(self, method, url, **kwargs):
        """Make an authenticated request with proper CSRF handling"""
        if not self.authenticated:
            print("Not authenticated, attempting login...")
            if not self.login():
                raise Exception("Authentication failed")
        if method.upper() != 'GET' and not self.csrf_token:
            self.get_csrf_token()
        headers = kwargs.get('headers', {})
        headers.update({
            'Accept': 'application/vnd.cvat+json',
            'Referer': f'{self.host}/',
        })

        if self.csrf_token and method.upper() != 'GET':
            headers['X-CSRFToken'] = self.csrf_token

        kwargs['headers'] = headers
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 403 and 'CSRF' in response.text:
            print("CSRF verification failed, refreshing token...")
            self.get_csrf_token()
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
                kwargs['headers'] = headers
                response = self.session.request(method, url, **kwargs)

        return response

    def create_project(self, name, labels):
        """Create a new project"""
        try:
            project_data = {
                'name': name,
                'labels': labels
            }

            headers = {'Content-Type': 'application/json'}
            response = self._make_authenticated_request(
                'POST',
                f"{self.host}/api/projects",
                json=project_data,
                headers=headers
            )

            if response.status_code == 201:
                project_id = response.json()['id']
                print(f"✓ Project created: {name} (ID: {project_id})")
                return project_id
            else:
                print(f"Failed to create project: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"Create project error: {str(e)}")
            return None

    def get_task_job_ids(self, task_id):
        """Get all job IDs for a task"""
        try:
            response = self._make_authenticated_request('GET', f"{self.host}/api/jobs?task_id={task_id}")
            if response.status_code == 200:
                jobs = response.json()['results']
                return [job['id'] for job in jobs]
            return []
        except Exception as e:
            print(f"Error getting job IDs for task {task_id}: {str(e)}")
            return []

    def create_task(self, name, project_id, zip_files, overlap=0):
        """Create a new task and upload zip files in a single request."""
        try:
            print(f"Creating task '{name}' and uploading {len(zip_files)} zip file(s)...")
            valid_zip_files = []
            for zip_path in zip_files:
                if not os.path.exists(zip_path):
                    print(f"Error: Zip file not found: {zip_path}")
                    continue
                if not zipfile.is_zipfile(zip_path):
                    print(f"Error: Invalid zip file: {zip_path}")
                    continue
                if not self._validate_zip_contents(zip_path):
                    print(f"Error: Zip file contains no valid images: {zip_path}")
                    continue
                valid_zip_files.append(zip_path)

            if not valid_zip_files:
                print("Error: No valid zip files provided to create the task.")
                return None
            task_spec = {
                "name": name,
                "project_id": project_id,
                "overlap": overlap
            }
            files = {}
            file_handles = []

            try:
                files['json_data'] = (None, json.dumps(task_spec), 'application/json')
                files['image_quality'] = (None, '95')
                files['use_zip_chunks'] = (None, 'true')
                files['use_cache'] = (None, 'true')
                files['sorting_method'] = (None, 'lexicographical')
                for i, zip_path in enumerate(valid_zip_files):
                    file_handle = open(zip_path, 'rb')
                    file_handles.append(file_handle)
                    files[f'client_files[{i}]'] = (
                        os.path.basename(zip_path),
                        file_handle,
                        'application/zip'
                    )

                print(f"Sending request with {len(valid_zip_files)} zip file(s)...")
                response = self._make_authenticated_request(
                    'POST',
                    f"{self.host}/api/tasks",
                    files=files
                )

            finally:
                for file_handle in file_handles:
                    try:
                        file_handle.close()
                    except:
                        pass
            if response.status_code == 201:
                task_data = response.json()
                task_id = task_data['id']
                print(f"✓ Task '{name}' (ID: {task_id}) created successfully")
                if self.wait_for_task_completion(task_id):
                    print(f"✓ Task {task_id} data processing completed")
                    job_ids = self.get_task_job_ids(task_id)
                    return {'task_id': task_id, 'job_ids': job_ids}
                else:
                    print(f"⚠ Task {task_id} was created but data processing may have failed")
                    job_ids = self.get_task_job_ids(task_id)
                    return {'task_id': task_id, 'job_ids': job_ids}

            elif response.status_code == 400:
                print(f"✗ Bad request creating task: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                return None

            elif response.status_code == 403:
                print(f"✗ Permission denied creating task: {response.status_code}")
                print("Check if user has permission to create tasks in this project")
                return None

            else:
                print(f"✗ Failed to create task: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"Create task error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def get_task_jobs(self, task_id):
        """Get job IDs for a specific task"""
        try:
            response = self.session.get(f"{self.host}/api/tasks/{task_id}/jobs")
            if response.status_code == 200:
                jobs = response.json()
                return [job['id'] for job in jobs.get('results', [])]
            else:

                return []
        except Exception as e:

            return []

    def create_task_alternative(self, name, project_id, zip_files, overlap=0):
        """Alternative method: Create task first, then upload data separately - returns task_id, job_ids, and project_id"""
        try:
            print(f"Creating task '{name}' (alternative method)...")
            task_data = {
                'name': name,
                'project_id': project_id,
                'overlap': overlap
            }

            headers = {'Content-Type': 'application/json'}
            response = self._make_authenticated_request(
                'POST',
                f"{self.host}/api/tasks",
                json=task_data,
                headers=headers
            )

            if response.status_code != 201:
                print(f"Failed to create task: {response.status_code}")
                print(f"Response: {response.text}")
                return None

            task_id = response.json()['id']
            print(f"✓ Empty task created: {name} (ID: {task_id})")

            if self.upload_zip_files_improved(task_id, zip_files):
                # --- START: MODIFIED LOGIC ---
                print(f"✓ Data processing complete. Waiting for job creation...")
                job_ids = []
                # Retry for 15 seconds to give CVAT time to create the jobs
                for _ in range(15):
                    job_ids = self.get_task_job_ids(task_id)
                    if job_ids:
                        print(f"✓ Found jobs for task {task_id}.")
                        break  # Exit the loop once jobs are found
                    time.sleep(1) # Wait 1 second before retrying

                if not job_ids:
                    print(f"⚠ Warning: Could not retrieve job IDs for task {task_id} after waiting.")

                print(f"✓ Task creation process finished. Job IDs: {job_ids}")
                return {
                    'task_id': task_id,
                    'job_ids': job_ids,
                    'project_id': project_id
                }
                # --- END: MODIFIED LOGIC ---
            else:
                print(f"Failed to upload data to task {task_id}")
                return None

        except Exception as e:
            print(f"Create task alternative error: {str(e)}")
            return None

    def upload_zip_files_improved(self, task_id, zip_files):
        """Improved zip file upload with better error handling."""
        try:
            print(f"Uploading {len(zip_files)} zip file(s) to task {task_id}")
            valid_zip_files = []
            for zip_path in zip_files:
                if not os.path.exists(zip_path):
                    print(f"Warning: Zip file not found: {zip_path}")
                    continue
                if not zipfile.is_zipfile(zip_path):
                    print(f"Warning: Invalid zip file: {zip_path}")
                    continue
                if self._validate_zip_contents(zip_path):
                    valid_zip_files.append(zip_path)
                else:
                    print(f"Warning: Zip file contains no valid images: {zip_path}")

            if not valid_zip_files:
                print("No valid zip files to upload")
                return False
            files = {}
            file_handles = []

            try:
                files['image_quality'] = (None, '95')
                files['use_zip_chunks'] = (None, 'true')
                files['use_cache'] = (None, 'true')
                files['sorting_method'] = (None, 'lexicographical')
                for i, zip_path in enumerate(valid_zip_files):
                    file_handle = open(zip_path, 'rb')
                    file_handles.append(file_handle)
                    files[f'client_files[{i}]'] = (
                        os.path.basename(zip_path),
                        file_handle,
                        'application/zip'
                    )

                print(f"Uploading {len(valid_zip_files)} zip file(s)...")

                response = self._make_authenticated_request(
                    'POST',
                    f"{self.host}/api/tasks/{task_id}/data",
                    files=files
                )

            finally:
                for file_handle in file_handles:
                    try:
                        file_handle.close()
                    except:
                        pass

            if response.status_code in [200, 201, 202]:
                print(f"✓ Successfully uploaded zip files to task {task_id}")
                return self.wait_for_task_completion(task_id)
            else:
                print(f"Failed to upload zip files: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"Upload zip files error: {str(e)}")
            return False
    def _validate_zip_contents(self, zip_path):
        """Enhanced validation that zip file contains valid image files."""
        try:
            valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                image_files = []
                for file_name in file_list:
                    if file_name.endswith('/'):
                        continue
                    if os.path.basename(file_name).startswith('.'):
                        continue
                    if any(file_name.lower().endswith(ext) for ext in valid_extensions):
                        image_files.append(file_name)

                if len(image_files) > 0:
                    print(f"✓ Zip file {zip_path} contains {len(image_files)} valid images")
                    return True
                else:
                    print(f"✗ Zip file {zip_path} contains no valid images")
                    return False

        except Exception as e:
            print(f"Error validating zip contents for {zip_path}: {str(e)}")
            return False

    def upload_zip_files(self, task_id, zip_files):
        """Upload zip files to a task"""
        try:
            print(f"Uploading {len(zip_files)} zip files to task {task_id}")
            valid_zip_files = []
            for zip_path in zip_files:
                if not os.path.exists(zip_path):
                    print(f"Warning: Zip file not found: {zip_path}")
                    continue

                if not zipfile.is_zipfile(zip_path):
                    print(f"Warning: Invalid zip file: {zip_path}")
                    continue
                if self._validate_zip_contents(zip_path):
                    valid_zip_files.append(zip_path)
                else:
                    print(f"Warning: Zip file contains no valid images: {zip_path}")

            if not valid_zip_files:
                print("No valid zip files to upload")
                return False
            for zip_path in valid_zip_files:
                print(f"Uploading: {zip_path}")

                with open(zip_path, 'rb') as zip_file:
                    files = {'client_files': (os.path.basename(zip_path), zip_file, 'application/zip')}

                    data = {
                        'image_quality': 95,
                        'use_zip_chunks': True,
                        'use_cache': True,
                        'sorting_method': 'lexicographical'
                    }

                    response = self._make_authenticated_request(
                        'POST',
                        f"{self.host}/api/tasks/{task_id}/data",
                        files=files,
                        data=data
                    )

                    if response.status_code not in [200, 201, 202]:
                        print(f"Failed to upload {zip_path}: {response.status_code} - {response.text}")
                        return False
                    else:
                        print(f"✓ Successfully uploaded: {zip_path}")
            return self.wait_for_task_completion(task_id)

        except Exception as e:
            print(f"Upload zip files error: {str(e)}")
            return False

    def _validate_zip_contents(self, zip_path):
        """Validate that zip file contains valid image files"""
        try:
            valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                for file_name in file_list:
                    if any(file_name.lower().endswith(ext) for ext in valid_extensions):
                        return True

            return False

        except Exception as e:
            print(f"Error validating zip contents for {zip_path}: {str(e)}")
            return False

    def upload_images(self, task_id, image_files):
        """Legacy method - converts image files to zip and uploads

        This method is kept for backward compatibility but will create
        a temporary zip file from the provided images.
        """
        try:
            print(f"Converting {len(image_files)} images to zip format for upload...")
            temp_zip_path = f"temp_task_{task_id}.zip"

            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_path in image_files:
                    if os.path.exists(img_path):
                        zipf.write(img_path, os.path.basename(img_path))
                    else:
                        print(f"Warning: Image file not found: {img_path}")
            result = self.upload_zip_files(task_id, [temp_zip_path])
            try:
                os.remove(temp_zip_path)
            except:
                pass

            return result

        except Exception as e:
            print(f"Legacy upload images error: {str(e)}")
            return False

    def wait_for_task_completion(self, task_id, max_wait=60):
        """Wait for task to complete processing"""
        try:
            print(f"Waiting for task {task_id} to complete processing...")

            for i in range(max_wait):
                response = self._make_authenticated_request('GET', f"{self.host}/api/tasks/{task_id}")

                if response.status_code == 200:
                    task_info = response.json()
                    status = task_info.get('status', 'unknown')

                    print(f"Task status: {status}")

                    if status == 'completed':
                        print(f"✓ Task {task_id} completed successfully")
                        return True
                    elif status == 'failed':
                        print(f"✗ Task {task_id} failed")
                        return False
                    elif status in ['annotation', 'validation']:
                        print(f"✓ Task {task_id} ready for annotation")
                        return True
                    time.sleep(1)
                else:
                    print(f"Error checking task status: {response.status_code}")
                    break

            print(f"Timeout waiting for task {task_id}")
            return False

        except Exception as e:
            print(f"Wait for completion error: {str(e)}")
            return False

    def import_annotations(self, task_id, xml_file_path, timeout=300):
        """Import annotations from XML file using the new requests API pattern"""
        try:
            print(f"Importing annotations from {xml_file_path} to task {task_id}")
            if not os.path.exists(xml_file_path):
                print(f"XML file not found: {xml_file_path}")
                return False
            with open(xml_file_path, 'rb') as f:
                files = {'annotation_file': f}
                data = {'format': 'CVAT for video 1.1'}

                response = self._make_authenticated_request(
                    'POST',
                    f"{self.host}/api/tasks/{task_id}/annotations",
                    files=files,
                    data=data
                )

                if response.status_code not in [200, 201, 202]:
                    print(f"Failed to initiate annotation import: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                response_data = response.json()
                rq_id = response_data.get('rq_id')

                if not rq_id:
                    print("No rq_id found in response - this might be an older CVAT version")
                    return response.status_code in [200, 201]

                print(f"Import initiated successfully. Request ID: {rq_id}")
            import_start_time = time.time()
            while True:
                try:
                    status_response = self._make_authenticated_request(
                        'GET',
                        f"{self.host}/api/requests/{rq_id}"
                    )

                    if status_response.status_code != 200:
                        print(f"Failed to check import status: {status_response.status_code}")
                        print(f"Response: {status_response.text}")
                        return False

                    status_data = status_response.json()
                    status = status_data.get('status', 'unknown')

                    print(f"Import status: {status}")

                    if status == 'finished':
                        print("✓ Annotation import completed successfully")
                        return True
                    elif status == 'failed':
                        error_message = status_data.get('exc_info', 'Unknown error')
                        print(f"✗ Annotation import failed: {error_message}")
                        return False
                    elif status in ['queued', 'started']:
                        elapsed_time = time.time() - import_start_time
                        if elapsed_time > timeout:
                            print(f"✗ Import timeout after {timeout} seconds")
                            return False

                        print(f"Import in progress... ({elapsed_time:.1f}s elapsed)")
                        time.sleep(5)
                    else:
                        print(f"Unknown status: {status}")
                        time.sleep(5)

                except Exception as e:
                    print(f"Error checking import status: {str(e)}")
                    time.sleep(5)
                    elapsed_time = time.time() - import_start_time
                    if elapsed_time > timeout:
                        print(f"✗ Import timeout after {timeout} seconds")
                        return False

        except Exception as e:
            print(f"Error importing annotations: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def assign_user_to_task(self, task_id, username):
        """Assign a user to a task - Fixed version"""
        try:
            response = self._make_authenticated_request('GET', f"{self.host}/api/users")
            if response.status_code != 200:
                print(f"Failed to get users: {response.status_code}")
                return False

            users = response.json()['results']
            user_id = None
            for user in users:
                if user['username'] == username:
                    user_id = user['id']
                    break

            if not user_id:
                print(f"User not found: {username}")
                return False
            response = self._make_authenticated_request('GET', f"{self.host}/api/tasks/{task_id}")
            if response.status_code != 200:
                print(f"Failed to get task info: {response.status_code}")
                return False

            task_info = response.json()
            print(f"Current task info: {task_info}")
            assignment_methods = [
                {'assignee_id': user_id},
                {'assignee': user_id},
                {'owner_id': user_id},
                {'owner': user_id},
            ]

            for assignment_data in assignment_methods:
                print(f"Trying assignment with data: {assignment_data}")

                headers = {'Content-Type': 'application/json'}
                response = self._make_authenticated_request(
                    'PATCH',
                    f"{self.host}/api/tasks/{task_id}",
                    json=assignment_data,
                    headers=headers
                )

                if response.status_code == 200:
                    print(f"✓ User {username} assigned to task {task_id}")
                    return True
                else:
                    print(f"Assignment attempt failed: {response.status_code}")
                    print(f"Response: {response.text}")
            print("Trying job-based assignment...")
            response = self._make_authenticated_request('GET', f"{self.host}/api/jobs?task_id={task_id}")
            if response.status_code == 200:
                jobs = response.json()['results']

                for job in jobs:
                    job_id = job['id']
                    job_assignment_data = {
                        'assignee': user_id
                    }

                    headers = {'Content-Type': 'application/json'}
                    response = self._make_authenticated_request(
                        'PATCH',
                        f"{self.host}/api/jobs/{job_id}",
                        json=job_assignment_data,
                        headers=headers
                    )

                    if response.status_code == 200:
                        print(f"✓ User {username} assigned to job {job_id} of task {task_id}")
                        return True
                    else:
                        print(f"Job assignment failed: {response.status_code}")
                        print(f"Response: {response.text}")
            print("Trying project membership assignment...")
            project_id = task_info.get('project_id') or task_info.get('project')
            if project_id:
                project_assignment_data = {
                    'user_id': user_id,
                    'role': 'annotator'
                }

                response = self._make_authenticated_request(
                    'POST',
                    f"{self.host}/api/projects/{project_id}/members",
                    json=project_assignment_data,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code in [200, 201]:
                    print(f"✓ User {username} added to project {project_id}")
                    return True
                else:
                    print(f"Project membership failed: {response.status_code}")
                    print(f"Response: {response.text}")

            print(f"All assignment methods failed for user {username}")
            return False

        except Exception as e:
            print(f"Assign user error: {str(e)}")
            return False

    def create_zip_from_directory(self, directory_path, output_zip_path):
        """Helper method to create a zip file from a directory of images"""
        try:
            if not os.path.exists(directory_path):
                print(f"Directory not found: {directory_path}")
                return False

            valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}

            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                image_count = 0
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in valid_extensions):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, directory_path)
                            zipf.write(file_path, arcname)
                            image_count += 1

            if image_count > 0:
                print(f"✓ Created zip file with {image_count} images: {output_zip_path}")
                return True
            else:
                print(f"No valid images found in directory: {directory_path}")
                return False

        except Exception as e:
            print(f"Error creating zip from directory: {str(e)}")
            return False


def get_default_labels():
    """Get default labels for person annotation"""
    return [
        {
            'name': 'person',
            'color': '#ff0000',
            'attributes': [
                {
                    'name': 'walking_behavior',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'normal_walk', 'fast_walk', 'slow_walk', 'standing_still', 'jogging']
                },
                {
                    'name': 'phone_usage',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'no_phone', 'talking_phone', 'texting', 'taking_photo']
                },
                {
                    'name': 'social_interaction',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'alone', 'talking_companion', 'group_walking', 'greeting_someone']
                },
                {
                    'name': 'carrying_items',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'empty_hands', 'shopping_bags', 'backpack', 'briefcase_bag']
                },
                {
                    'name': 'street_behavior',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'sidewalk_walking', 'crossing_street', 'waiting_signal', 'looking_around']
                },
                {
                    'name': 'posture_gesture',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'upright_normal', 'looking_down', 'looking_up', 'hands_in_pockets']
                },
                {
                    'name': 'clothing_style',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'business_attire', 'casual_wear', 'tourist_style', 'sports_wear']
                },
                {
                    'name': 'time_context',
                    'mutable': True,
                    'input_type': 'select',
                    'default_value': 'unknown',
                    'values': ['unknown', 'rush_hour', 'leisure_time', 'shopping_time', 'lunch_break']
                }
            ]
        }
    ]
if __name__ == "__main__":
    print("Starting CVAT client test with zip file support...")
    client = CVATClient(host="http://localhost:8080")
    if client.test_connection():
        print("✓ CVAT connection successful")
        print("\nTesting authentication...")
        client_auth = CVATClient(host="http://localhost:8080", username="mv350", password="Amazon123")

        if client_auth.authenticated:
            print("✓ Authentication successful")
            print("\nTesting project creation...")
            labels = get_default_labels()
            project_id = client_auth.create_project("Test Project with Zip", labels)

            if project_id:
                print(f"✓ Project created successfully with ID: {project_id}")
                print("\nExample usage with zip files:")
                print("1. Create zip files from directories:")
                print("   client.create_zip_from_directory('path/to/images/1/', '1.zip')")
                print("   client.create_zip_from_directory('path/to/images/2/', '2.zip')")
                print("2. Create task with zip files:")
                print("   task_id = client.create_task('Task Name', project_id, ['1.zip', '2.zip'])")

            else:
                print("✗ Project creation failed")
        else:
            print("✗ Authentication failed")

    else:
        print("✗ CVAT connection failed")
        print("\nTroubleshooting steps:")
        print("1. Make sure CVAT is running: docker-compose up -d")
        print("2. Check if port 8080 is accessible: curl http://localhost:8080")
        print("3. Verify CVAT is properly initialized")
        print("4. Check docker logs: docker-compose logs cvat")
        print("5. If using custom hostname, add to CSRF_TRUSTED_ORIGINS in settings")