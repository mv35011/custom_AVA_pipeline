import json
import os
import csv
import cv2
import sys

dicts = []


def get_image_path_and_dimensions(root_dir, video_name, frame_id):
    """Find image file and get its dimensions"""
    possible_paths = [
        os.path.join(root_dir, f"{video_name}_{str(frame_id * 30 + 1).zfill(6)}.jpg"),
        os.path.join(root_dir, video_name, f"{video_name}_{str(frame_id * 30 + 1).zfill(6)}.jpg"),
        os.path.join(root_dir, "choose_frames_all", f"{video_name}_{str(frame_id * 30 + 1).zfill(6)}.jpg"),
    ]

    for img_path in possible_paths:
        if os.path.exists(img_path):
            try:
                img_temp = cv2.imread(img_path)
                if img_temp is not None:
                    sp = img_temp.shape
                    return img_path, sp[0], sp[1]  # height, width
            except Exception as e:
                print(f"Error reading image {img_path}: {e}")
                continue
    print(f"Warning: Could not find image for {video_name} frame {frame_id}, using default dimensions")
    return None, 720, 1280


def calculate_cumulative_action_mapping(attributes):
    """Calculate cumulative action ID mapping like the original repo"""
    attribute_nums = [0]  # Start with 0
    cumulative_count = 0

    # Sort attributes by key to ensure consistent ordering
    sorted_attrs = sorted(attributes.items(), key=lambda x: int(x[0]))

    for attr_id, attr_info in sorted_attrs:
        if 'options' in attr_info:
            num_options = len(attr_info['options'])
            cumulative_count += num_options
            attribute_nums.append(cumulative_count)
            print(f"  Attribute {attr_id}: {num_options} options, cumulative total: {cumulative_count}")

    return attribute_nums


def process_json_file(json_path):
    """Process a single VIA JSON file"""
    print(f"Processing: {json_path}")

    try:
        with open(json_path, encoding='utf-8') as f:
            line = f.readline()
            via_json = json.loads(line)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return

    attributes = via_json.get('attribute', {})
    print(f"Found {len(attributes)} attributes")

    # Calculate cumulative action ID mapping
    attribute_nums = calculate_cumulative_action_mapping(attributes)
    print(f"Attribute cumulative mapping: {attribute_nums}")

    files = {}
    for file_key in via_json.get('file', {}):
        fid = via_json['file'][file_key]['fid']
        fname = via_json['file'][file_key]['fname']
        files[fid] = fname

    metadata_count = 0
    root_dir = os.path.dirname(json_path)

    for metadata_key in via_json.get('metadata', {}):
        imagen_x = via_json['metadata'][metadata_key]
        xy = imagen_x['xy'][1:]  # Skip the first element (shape type)
        vid = imagen_x['vid']
        fname = files.get(vid, '')

        if not fname:
            print(f"Warning: No filename found for vid {vid}")
            continue

        video_name = fname.split('_')[0]
        try:
            frame_id = int((int(fname.split('_')[1].split('.')[0]) - 1) / 30)
        except (IndexError, ValueError) as e:
            print(f"Error parsing frame ID from {fname}: {e}")
            continue

        img_path, img_H, img_W = get_image_path_and_dimensions(root_dir, video_name, frame_id)

        for attribute_id in imagen_x.get('av', {}):
            avs = imagen_x['av'][attribute_id]
            if avs == '':
                continue
            av_arr = avs.split(',')

            for av in av_arr:
                av = av.strip()
                if av == '':
                    continue

                x1 = xy[0] / img_W
                y1 = xy[1] / img_H
                x2 = (xy[0] + xy[2]) / img_W
                y2 = (xy[1] + xy[3]) / img_H

                # Clamp coordinates to [0,1]
                x1 = max(0, min(1, x1))
                y1 = max(0, min(1, y1))
                x2 = max(0, min(1, x2))
                y2 = max(0, min(1, y2))

                # Calculate action ID using cumulative mapping (like original repo)
                # actionId = attributeNums[int(action)-1] + int(av) + 1
                attr_index = int(attribute_id) - 1  # Convert to 0-based index
                if attr_index < len(attribute_nums) - 1:
                    action_id = attribute_nums[attr_index] + int(av) + 1
                else:
                    action_id = int(av) + 1  # Fallback

                csv_row = [video_name, frame_id, x1, y1, x2, y2, action_id]
                dicts.append(csv_row)

                print(
                    f"  Added: {video_name} frame {frame_id}, attribute {attribute_id}, option {av} -> action_id {action_id}")

        metadata_count += 1

    print(f"Processed {metadata_count} annotations from {json_path}")


def main():
    if len(sys.argv) > 1:
        search_directory = sys.argv[1]
    else:
        search_directory = "./choose_frames_middle"

    print(f"Searching for VIA JSON files in: {search_directory}")
    print("=" * 60)

    if not os.path.exists(search_directory):
        print(f"Error: Directory {search_directory} does not exist!")
        sys.exit(1)

    json_files_found = 0

    for root, dirs, files in os.walk(search_directory, topdown=False):
        for file in files:
            # Only accept files ending with _finish.json (like 1_finish.json, 2_finish.json, etc.)
            if file.endswith("_finish.json"):
                json_path = os.path.join(root, file)
                process_json_file(json_path)
                json_files_found += 1

    print("=" * 60)
    print(f"SUMMARY:")
    print(f"JSON files processed: {json_files_found}")
    print(f"Total CSV rows generated: {len(dicts)}")

    if len(dicts) == 0:
        print("Warning: No annotations found! Check your JSON files and file paths.")
        print("Make sure your files end with '_finish.json' (like '1_finish.json', '2_finish.json', etc.)")
        return

    output_file = './train_without_personID.csv'

    try:
        with open(output_file, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['video_name', 'frame_id', 'x1', 'y1', 'x2', 'y2', 'action_id'])
            writer.writerows(dicts)

        print(f"Successfully saved {len(dicts)} rows to {output_file}")

        print("\nSample CSV rows:")
        for i, row in enumerate(dicts[:5]):
            print(f"  {row}")
        if len(dicts) > 5:
            print(f"  ... and {len(dicts) - 5} more rows")

        # Show action ID distribution
        action_counts = {}
        for row in dicts:
            action_id = row[6]
            action_counts[action_id] = action_counts.get(action_id, 0) + 1

        print(f"\nAction ID distribution:")
        for action_id in sorted(action_counts.keys()):
            print(f"  Action {action_id}: {action_counts[action_id]} annotations")

        total_unique_actions = len(action_counts)
        max_action_id = max(action_counts.keys()) if action_counts else 0
        print(f"\nTotal unique action IDs: {total_unique_actions}")
        print(f"Highest action ID: {max_action_id}")

    except Exception as e:
        print(f"Error writing CSV file: {e}")


if __name__ == "__main__":
    main()