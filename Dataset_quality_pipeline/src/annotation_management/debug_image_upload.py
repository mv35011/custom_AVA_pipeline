#!/usr/bin/env python3
"""
Manual debug checks for CVAT image upload issues
"""

import os
import requests
from PIL import Image
import mimetypes
from pathlib import Path


def check_image_structure(base_path, video_name):
    """Check the actual image file structure"""
    print(f"=== CHECKING IMAGE STRUCTURE FOR VIDEO: {video_name} ===")
    print(f"Base path: {base_path}")

    if not os.path.exists(base_path):
        print(f"❌ Base path does not exist: {base_path}")
        return []

    # Check subdirectories
    for subdir in range(1, 4):
        subdir_path = os.path.join(base_path, str(subdir))
        print(f"\nChecking subdirectory: {subdir_path}")

        if not os.path.exists(subdir_path):
            print(f"  ❌ Subdirectory does not exist")
            continue

        # List all files in this subdirectory
        all_files = os.listdir(subdir_path)
        print(f"  Total files in subdirectory: {len(all_files)}")

        # Find files matching our video name pattern
        video_files = [f for f in all_files if video_name in f and f.endswith('.jpg')]
        print(f"  Video {video_name} files: {len(video_files)}")

        # Show first few files
        for i, filename in enumerate(sorted(video_files)[:5]):
            filepath = os.path.join(subdir_path, filename)
            file_size = os.path.getsize(filepath)
            print(f"    {i + 1}. {filename} ({file_size} bytes)")

    # Now get all images using your existing method
    image_files = get_video_images_debug(base_path, video_name)
    return image_files


def get_video_images_debug(base_path, video_name):
    """Debug version of get_video_images with detailed logging"""
    print(f"\n=== GET_VIDEO_IMAGES DEBUG ===")
    print(f"Searching for video: {video_name}")
    print(f"In base path: {base_path}")

    image_files = []

    for subdir in range(1, 4):
        search_path = os.path.join(base_path, str(subdir))
        print(f"\nSearching in: {search_path}")

        if not os.path.exists(search_path):
            print(f"  ❌ Directory does not exist")
            continue

        try:
            files = sorted(os.listdir(search_path))
            print(f"  Found {len(files)} total files")

            matching_files = []
            for file in files:
                if '.jpg' in file and video_name in file:
                    matching_files.append(file)
                    full_path = os.path.join(search_path, file)
                    image_files.append(full_path)

            print(f"  Matching files: {len(matching_files)}")
            if matching_files:
                print(f"  First few: {matching_files[:3]}")
                print(f"  Last few: {matching_files[-3:]}")

        except Exception as e:
            print(f"  ❌ Error reading directory: {e}")

    print(f"\nTotal images found: {len(image_files)}")
    return image_files


def validate_images(image_files):
    """Validate that images are proper JPEG files"""
    print(f"\n=== VALIDATING {len(image_files)} IMAGES ===")

    valid_images = []
    invalid_images = []

    for i, img_path in enumerate(image_files):
        print(f"\nValidating {i + 1}/{len(image_files)}: {os.path.basename(img_path)}")

        # Check if file exists
        if not os.path.exists(img_path):
            print(f"  ❌ File does not exist")
            invalid_images.append((img_path, "File not found"))
            continue

        # Check file size
        file_size = os.path.getsize(img_path)
        if file_size == 0:
            print(f"  ❌ File is empty")
            invalid_images.append((img_path, "Empty file"))
            continue

        print(f"  ✓ File size: {file_size} bytes")

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(img_path)
        print(f"  ✓ MIME type: {mime_type}")

        # Try to open with PIL
        try:
            with Image.open(img_path) as img:
                print(f"  ✓ Image format: {img.format}")
                print(f"  ✓ Image size: {img.size}")
                print(f"  ✓ Image mode: {img.mode}")

                # Check if it's the expected size
                if img.size == (640, 360):
                    print(f"  ✓ Size matches expected (640x360)")
                else:
                    print(f"  ⚠ Size doesn't match expected (640x360)")

                valid_images.append(img_path)

        except Exception as e:
            print(f"  ❌ Cannot open as image: {e}")
            invalid_images.append((img_path, f"Invalid image: {e}"))

    print(f"\n=== VALIDATION SUMMARY ===")
    print(f"Valid images: {len(valid_images)}")
    print(f"Invalid images: {len(invalid_images)}")

    if invalid_images:
        print("\nInvalid images:")
        for img_path, reason in invalid_images:
            print(f"  - {os.path.basename(img_path)}: {reason}")

    return valid_images


def test_single_image_upload(cvat_client, task_id, image_path):
    """Test uploading a single image to debug the upload process"""
    print(f"\n=== TESTING SINGLE IMAGE UPLOAD ===")
    print(f"Task ID: {task_id}")
    print(f"Image: {image_path}")

    if not os.path.exists(image_path):
        print("❌ Image file does not exist")
        return False

    try:
        # Prepare single file upload
        with open(image_path, 'rb') as f:
            files = [('client_files', (os.path.basename(image_path), f, 'image/jpeg'))]

            data = {
                'image_quality': 95,
                'use_zip_chunks': False,
                'use_cache': True,
                'copy_data': False
            }

            print(f"Upload data: {data}")
            print(f"File info: {os.path.basename(image_path)}, size: {os.path.getsize(image_path)}")

            response = cvat_client._make_authenticated_request(
                'POST',
                f"{cvat_client.host}/api/tasks/{task_id}/data",
                files=files,
                data=data
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")

            return response.status_code in [200, 201, 202]

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False


def check_cvat_task_manually(cvat_client, task_id):
    """Check task status manually via API"""
    print(f"\n=== CHECKING TASK {task_id} STATUS ===")

    try:
        response = cvat_client._make_authenticated_request(
            'GET',
            f"{cvat_client.host}/api/tasks/{task_id}"
        )

        if response.status_code == 200:
            task_data = response.json()
            print(f"Task name: {task_data.get('name')}")
            print(f"Task status: {task_data.get('status')}")
            print(f"Task mode: {task_data.get('mode')}")

            data_info = task_data.get('data', {})
            print(f"Data size: {data_info.get('size', 0)} frames")
            print(f"Data start frame: {data_info.get('start_frame', 0)}")
            print(f"Data stop frame: {data_info.get('stop_frame', 0)}")
            print(f"Image quality: {data_info.get('image_quality', 'N/A')}")

            # Check if task has jobs
            jobs = task_data.get('jobs', [])
            print(f"Number of jobs: {len(jobs)}")

            if data_info.get('size', 0) == 0:
                print("❌ Task has no media data - this is the problem!")
                return False
            else:
                print("✓ Task has media data")
                return True
        else:
            print(f"❌ Failed to get task info: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error checking task: {e}")
        return False


def main_debug():
    """Main debug function"""
    print("CVAT IMAGE UPLOAD DEBUG TOOL")
    print("=" * 50)

    # Configuration
    base_path = r"C:\Users\mv350\Downloads\Documents\Pycharm_projects\Dataset_Quality_control\data\Dataset\choose_frames_middle"
    video_name = "1"  # Test with video "1"

    # Step 1: Check image structure
    image_files = check_image_structure(base_path, video_name)

    if not image_files:
        print("❌ No images found. Cannot continue.")
        return

    # Step 2: Validate images
    valid_images = validate_images(image_files[:10])  # Test first 10 images

    if not valid_images:
        print("❌ No valid images found. Cannot continue.")
        return

    print(f"\n✓ Found {len(valid_images)} valid images")

    # Step 3: Test CVAT connection and create a test task
    from cvat_integration import CVATClient

    client = CVATClient(host="http://localhost:8080", username="mv350", password="Amazon123")

    if not client.test_connection():
        print("❌ Cannot connect to CVAT")
        return

    # For manual testing, you can create a simple test task
    print("\n=== MANUAL TEST RECOMMENDATIONS ===")
    print("1. Try uploading just 1-2 images first")
    print("2. Check the file naming pattern matches CVAT expectations")
    print("3. Verify the subdirectory structure")
    print("4. Test with a simple task creation via CVAT web interface")

    print(f"\nFirst few valid images to test with:")
    for i, img_path in enumerate(valid_images[:5]):
        print(f"  {i + 1}. {img_path}")


if __name__ == "__main__":
    main_debug()