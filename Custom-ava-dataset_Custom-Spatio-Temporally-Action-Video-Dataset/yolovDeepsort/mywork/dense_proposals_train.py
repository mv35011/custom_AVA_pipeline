import sys
import os
import json
import pickle
from collections import defaultdict


def parse_yolo_detection_file(file_path):
    """Parse a single YOLO detection file and return detections"""
    detections = []

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 6:
                print(f"Warning: Invalid format in {file_path}: {line}")
                continue

            try:
                class_id = int(parts[0])
                # Only process person detections (class 0 in YOLO)
                if class_id != 0:
                    continue

                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                confidence = float(parts[5])

                # Convert from YOLO format (center, width, height) to AVA format (x1, y1, x2, y2)
                # Keep in normalized coordinates [0,1]
                x1 = x_center - width / 2
                y1 = y_center - height / 2
                x2 = x_center + width / 2
                y2 = y_center + height / 2

                # Ensure coordinates are within [0,1] bounds
                x1 = max(0, min(1, x1))
                y1 = max(0, min(1, y1))
                x2 = max(0, min(1, x2))
                y2 = max(0, min(1, y2))

                detections.append([x1, y1, x2, y2, confidence])

            except (ValueError, IndexError) as e:
                print(f"Error parsing detection in {file_path}: {line} - {e}")
                continue

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return detections


def process_label_directory(label_path):
    """Process all label files in the directory"""
    results_dict = {}
    all_files = []

    # Collect all .txt files
    for root, dirs, files in os.walk(label_path):
        for file in files:
            if file.endswith('.txt'):
                all_files.append(os.path.join(root, file))

    print(f"Found {len(all_files)} label files")

    if len(all_files) == 0:
        print("ERROR: No .txt files found in the label directory!")
        return {}

    # Group files by video name
    video_files = defaultdict(list)

    for file_path in all_files:
        file_name = os.path.basename(file_path)

        try:
            # Parse filename: expected format like "1_000001.txt" or "video1_frame001.txt"
            parts = file_name.replace('.txt', '').split('_')

            if len(parts) >= 2:
                video_name = parts[0]
                frame_str = parts[1]

                # Extract frame number
                frame_num = int(''.join(filter(str.isdigit, frame_str)))

                video_files[video_name].append({
                    'path': file_path,
                    'frame': frame_num,
                    'filename': file_name
                })
            else:
                print(f"Warning: Unexpected filename format: {file_name}")

        except (ValueError, IndexError) as e:
            print(f"Error parsing filename {file_name}: {e}")
            continue

    print(f"Found files for {len(video_files)} videos")

    # Process each video
    for video_name, files_info in video_files.items():
        print(f"Processing video: {video_name}")

        # Sort files by frame number
        files_info.sort(key=lambda x: x['frame'])

        total_frames = len(files_info)
        print(f"  Total frames: {total_frames}")

        if total_frames == 0:
            continue

        # Calculate seconds (assuming 30 fps)
        max_frame = max(f['frame'] for f in files_info)
        total_seconds = max_frame // 30 + 1

        print(f"  Estimated total seconds: {total_seconds}")

        # Process each frame, but skip first 2 and last 2 seconds only if we have enough data
        skip_start_seconds = 2 if total_seconds > 6 else 0
        skip_end_seconds = 2 if total_seconds > 6 else 0

        processed_count = 0

        for file_info in files_info:
            frame_num = file_info['frame']
            file_path = file_info['path']

            # Calculate which second this frame belongs to
            second = frame_num // 30

            # Skip frames if they're in the excluded time range
            if second < skip_start_seconds or second >= (total_seconds - skip_end_seconds):
                continue

            # Parse detections from this file
            detections = parse_yolo_detection_file(file_path)

            if detections:  # Only add if we have detections
                # Create key in AVA format: "video_name,second"
                key = f"{video_name},{str(second).zfill(4)}"

                # If this second already has detections, merge them
                if key in results_dict:
                    results_dict[key].extend(detections)
                else:
                    results_dict[key] = detections

                processed_count += 1

        print(f"  Processed {processed_count} frames with detections")

    return results_dict


def main():
    if len(sys.argv) < 3:
        print("Usage: python dense_proposals_train.py <label_path> <output_pkl_path> [show]")
        print("Example: python dense_proposals_train.py ../yolov5/runs/detect/exp/labels ./dense_proposals_train.pkl")
        sys.exit(1)

    label_path = sys.argv[1]
    output_pkl_path = sys.argv[2]
    show_pkl = len(sys.argv) > 3 and sys.argv[3].lower() == "show"

    print(f"Label path: {label_path}")
    print(f"Output path: {output_pkl_path}")

    # Check if label path exists
    if not os.path.exists(label_path):
        print(f"ERROR: Label path {label_path} does not exist!")
        sys.exit(1)

    # Process all label files
    results_dict = process_label_directory(label_path)

    if not results_dict:
        print("ERROR: No detections found! Check your label files and format.")
        print("\nDEBUG INFO:")
        print("- Make sure your YOLO detection files are in .txt format")
        print("- Make sure files are named like: videoname_framenumber.txt")
        print("- Make sure the files contain person detections (class 0)")
        print("- Check if files have the correct YOLO format: class x_center y_center width height confidence")
        return

    print(f"\nSUCCESS: Found detections for {len(results_dict)} time segments")

    # Show some sample data
    sample_keys = list(results_dict.keys())[:3]
    for key in sample_keys:
        detections = results_dict[key]
        print(f"Sample - {key}: {len(detections)} detections")

    # Save to pickle file
    try:
        os.makedirs(os.path.dirname(output_pkl_path), exist_ok=True)
        with open(output_pkl_path, "wb") as pkl_file:
            pickle.dump(results_dict, pkl_file)
        print(f"\nSuccessfully saved {len(results_dict)} entries to {output_pkl_path}")

        # Verify the saved file
        file_size = os.path.getsize(output_pkl_path)
        print(f"Output file size: {file_size} bytes")

    except Exception as e:
        print(f"ERROR saving pickle file: {e}")
        return

    # Display contents if requested
    if show_pkl:
        print(f"\nDISPLAYING CONTENTS:")
        print("=" * 50)
        for i, (key, detections) in enumerate(results_dict.items()):
            print(f"{key}: {len(detections)} detections")
            for j, detection in enumerate(detections[:2]):  # Show first 2 detections
                print(f"  Detection {j + 1}: {detection}")
            if len(detections) > 2:
                print(f"  ... and {len(detections) - 2} more")

            if i >= 10:  # Limit output
                print(f"... and {len(results_dict) - 11} more entries")
                break


if __name__ == "__main__":
    main()