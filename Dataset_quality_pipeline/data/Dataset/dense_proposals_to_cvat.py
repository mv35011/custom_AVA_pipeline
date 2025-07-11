import pickle
import json
import os
import cv2
import sys
from collections import defaultdict
import xml.etree.ElementTree as ET
from xml.dom import minidom


def get_image_dimensions(search_paths, video_name):
    """Get image dimensions from the first found image"""
    for search_path in search_paths:
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                if "ipynb_checkpoints" in root:
                    continue
                for file in files:
                    if '.jpg' in file and video_name in file:
                        temp_img_path = os.path.join(root, file)
                        try:
                            img = cv2.imread(temp_img_path)
                            if img is not None:
                                return img.shape[0], img.shape[1]  # height, width
                        except Exception as e:
                            print(f"Error reading image {temp_img_path}: {e}")
                            continue
    return 720, 1280  # Default dimensions


def count_images_for_video(search_paths, video_name):
    """Count total images for a specific video"""
    total_count = 0
    for search_path in search_paths:
        if os.path.exists(search_path):
            for root, dirs, files in os.walk(search_path):
                if "ipynb_checkpoints" in root:
                    continue
                for file in files:
                    if '.jpg' in file and video_name in file:
                        total_count += 1
    return total_count


def create_cvat_task_json(video_name, video_info, json_path, num_images, img_H, img_W):
    """Create simplified CVAT task configuration JSON for single person annotation"""

    # Define the same attributes as in your VIA script
    labels = [
        {
            "id": 1,
            "name": "person",
            "color": "#ff0000",
            "attributes": [
                {
                    "id": 1,
                    "name": "walking_behavior",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "normal_walk",
                    "values": [
                        "normal_walk",
                        "fast_walk",
                        "slow_walk",
                        "standing_still",
                        "jogging",
                        "window_shopping"
                    ]
                },
                {
                    "id": 2,
                    "name": "phone_usage",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "no_phone",
                    "values": [
                        "no_phone",
                        "talking_phone",
                        "texting",
                        "taking_photo",
                        "listening_music"
                    ]
                },
                {
                    "id": 3,
                    "name": "social_interaction",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "alone",
                    "values": [
                        "alone",
                        "talking_companion",
                        "group_walking",
                        "greeting_someone",
                        "asking_directions",
                        "avoiding_crowd"
                    ]
                },
                {
                    "id": 4,
                    "name": "carrying_items",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "empty_hands",
                    "values": [
                        "empty_hands",
                        "shopping_bags",
                        "backpack",
                        "briefcase_bag",
                        "umbrella",
                        "food_drink",
                        "multiple_items"
                    ]
                },
                {
                    "id": 5,
                    "name": "street_behavior",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "sidewalk_walking",
                    "values": [
                        "sidewalk_walking",
                        "crossing_street",
                        "waiting_signal",
                        "looking_around",
                        "checking_map",
                        "entering_building",
                        "exiting_building"
                    ]
                },
                {
                    "id": 6,
                    "name": "posture_gesture",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "upright_normal",
                    "values": [
                        "upright_normal",
                        "looking_down",
                        "looking_up",
                        "hands_in_pockets",
                        "arms_crossed",
                        "pointing_gesture",
                        "bowing_gesture"
                    ]
                },
                {
                    "id": 7,
                    "name": "clothing_style",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "casual_wear",
                    "values": [
                        "business_attire",
                        "casual_wear",
                        "tourist_style",
                        "school_uniform",
                        "sports_wear",
                        "traditional_wear"
                    ]
                },
                {
                    "id": 8,
                    "name": "time_context",
                    "mutable": True,
                    "input_type": "select",
                    "default_value": "leisure_time",
                    "values": [
                        "rush_hour",
                        "leisure_time",
                        "shopping_time",
                        "tourist_hours",
                        "lunch_break",
                        "evening_stroll"
                    ]
                }
            ]
        }
    ]

    # Simplified task configuration for single person testing
    task_config = {
        "name": f"{video_name}_annotation_task",
        "labels": labels,
        "mode": "annotation",
        "overlap": 0,
        "segment_size": num_images,
        "image_quality": 70,
        "start_frame": 0,
        "stop_frame": num_images - 1
    }

    return task_config


def create_cvat_annotations_xml(video_name, video_info, json_path, num_images, img_H, img_W):
    """Create CVAT annotations XML with pre-annotations from dense proposals"""

    # Create root element
    root = ET.Element("annotations")

    # Add version
    version = ET.SubElement(root, "version")
    version.text = "1.1"

    # Add meta information
    meta = ET.SubElement(root, "meta")

    task = ET.SubElement(meta, "task")

    # Task details
    task_id = ET.SubElement(task, "id")
    task_id.text = "1"

    task_name = ET.SubElement(task, "name")
    task_name.text = f"{video_name}_annotation_task"

    task_size = ET.SubElement(task, "size")
    task_size.text = str(num_images)

    task_mode = ET.SubElement(task, "mode")
    task_mode.text = "annotation"

    task_overlap = ET.SubElement(task, "overlap")
    task_overlap.text = "0"

    task_bugtracker = ET.SubElement(task, "bugtracker")
    task_bugtracker.text = ""

    task_created = ET.SubElement(task, "created")
    task_created.text = "2024-01-01 00:00:00.000000+00:00"

    task_updated = ET.SubElement(task, "updated")
    task_updated.text = "2024-01-01 00:00:00.000000+00:00"

    task_subset = ET.SubElement(task, "subset")
    task_subset.text = ""

    task_start_frame = ET.SubElement(task, "start_frame")
    task_start_frame.text = "0"

    task_stop_frame = ET.SubElement(task, "stop_frame")
    task_stop_frame.text = str(num_images - 1)

    task_frame_filter = ET.SubElement(task, "frame_filter")
    task_frame_filter.text = ""

    # Owner
    owner = ET.SubElement(task, "owner")
    owner_username = ET.SubElement(owner, "username")
    owner_username.text = "admin"
    owner_email = ET.SubElement(owner, "email")
    owner_email.text = "admin@example.com"

    # Labels
    labels = ET.SubElement(task, "labels")

    # Add person label with attributes
    label = ET.SubElement(labels, "label")
    label_name = ET.SubElement(label, "name")
    label_name.text = "person"
    label_color = ET.SubElement(label, "color")
    label_color.text = "#ff0000"

    # Add attributes
    attributes = ET.SubElement(label, "attributes")

    attribute_definitions = [
        ("walking_behavior", ["normal_walk", "fast_walk", "slow_walk", "standing_still", "jogging", "window_shopping"]),
        ("phone_usage", ["no_phone", "talking_phone", "texting", "taking_photo", "listening_music"]),
        ("social_interaction",
         ["alone", "talking_companion", "group_walking", "greeting_someone", "asking_directions", "avoiding_crowd"]),
        ("carrying_items",
         ["empty_hands", "shopping_bags", "backpack", "briefcase_bag", "umbrella", "food_drink", "multiple_items"]),
        ("street_behavior", ["sidewalk_walking", "crossing_street", "waiting_signal", "looking_around", "checking_map",
                             "entering_building", "exiting_building"]),
        ("posture_gesture",
         ["upright_normal", "looking_down", "looking_up", "hands_in_pockets", "arms_crossed", "pointing_gesture",
          "bowing_gesture"]),
        ("clothing_style",
         ["business_attire", "casual_wear", "tourist_style", "school_uniform", "sports_wear", "traditional_wear"]),
        ("time_context",
         ["rush_hour", "leisure_time", "shopping_time", "tourist_hours", "lunch_break", "evening_stroll"])
    ]

    for attr_name, attr_values in attribute_definitions:
        attribute = ET.SubElement(attributes, "attribute")
        attr_name_elem = ET.SubElement(attribute, "name")
        attr_name_elem.text = attr_name
        attr_mutable = ET.SubElement(attribute, "mutable")
        attr_mutable.text = "True"
        attr_input_type = ET.SubElement(attribute, "input_type")
        attr_input_type.text = "select"
        attr_default = ET.SubElement(attribute, "default_value")
        attr_default.text = attr_values[0]  # First value as default
        attr_values_elem = ET.SubElement(attribute, "values")
        attr_values_elem.text = "\n".join(attr_values)

    # Add segments
    segments = ET.SubElement(task, "segments")
    segment = ET.SubElement(segments, "segment")
    seg_id = ET.SubElement(segment, "id")
    seg_id.text = "1"
    seg_start = ET.SubElement(segment, "start")
    seg_start.text = "0"
    seg_stop = ET.SubElement(segment, "stop")
    seg_stop.text = str(num_images - 1)

    # Add dumped data
    dumped = ET.SubElement(task, "dumped")
    dumped.text = "2024-01-01 00:00:00.000000+00:00"

    # Sort video_info by frame number
    sorted_frames = sorted(video_info.keys(), key=lambda x: int(x.split(',')[1]))

    # Process annotations
    annotation_id = 1

    for frame_key in sorted_frames:
        frame_num = int(frame_key.split(',')[1])
        detections = video_info[frame_key]

        for detection_id, bbox in enumerate(detections, 1):
            # Convert normalized coordinates to pixel coordinates
            x1 = img_W * bbox[0]
            y1 = img_H * bbox[1]
            x2 = img_W * bbox[2]
            y2 = img_H * bbox[3]

            width = x2 - x1
            height = y2 - y1

            # Create annotation
            annotation = ET.SubElement(root, "track")
            annotation.set("id", str(annotation_id))
            annotation.set("label", "person")
            annotation.set("source", "manual")

            # Create box for this frame
            box = ET.SubElement(annotation, "box")
            box.set("frame", str(frame_num - 1))  # CVAT uses 0-based indexing
            box.set("outside", "0")
            box.set("occluded", "0")
            box.set("keyframe", "1")
            box.set("xtl", f"{x1:.2f}")
            box.set("ytl", f"{y1:.2f}")
            box.set("xbr", f"{x2:.2f}")
            box.set("ybr", f"{y2:.2f}")
            box.set("z_order", "0")

            # Add default attribute values
            for attr_name, attr_values in attribute_definitions:
                attribute = ET.SubElement(box, "attribute")
                attribute.set("name", attr_name)
                attribute.text = attr_values[0]  # Default to first value

            annotation_id += 1

    return root


def process_video_annotations(video_name, video_info, json_path):
    """Process annotations for a single video and create CVAT format files"""
    print(f"Processing video: {video_name}")

    # Create output directory
    output_dir = os.path.join(json_path, video_name)
    os.makedirs(output_dir, exist_ok=True)

    # Define search paths for images
    search_paths = [
        os.path.join(json_path, 'choose_frames_all'),
        os.path.join(json_path, video_name),
        os.path.join(json_path, '1'),
        os.path.join(json_path, '2'),
        os.path.join(json_path, '3'),
    ]

    # Get image count and dimensions
    num_images = count_images_for_video(search_paths, video_name)
    img_H, img_W = get_image_dimensions(search_paths, video_name)

    print(f"Found {num_images} images for video {video_name}")
    print(f"Image dimensions: {img_W}x{img_H}")

    if num_images == 0:
        print(f"Warning: No images found for video {video_name}, skipping...")
        return False

    try:
        # Create CVAT task configuration
        task_config = create_cvat_task_json(video_name, video_info, json_path, num_images, img_H, img_W)

        # Save task configuration
        task_config_path = os.path.join(output_dir, f"{video_name}_task_config.json")
        with open(task_config_path, 'w') as f:
            json.dump(task_config, f, indent=2)

        # Create CVAT annotations XML
        annotations_root = create_cvat_annotations_xml(video_name, video_info, json_path, num_images, img_H, img_W)

        # Pretty print XML
        rough_string = ET.tostring(annotations_root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Save annotations XML
        annotations_xml_path = os.path.join(output_dir, f"{video_name}_annotations.xml")
        with open(annotations_xml_path, 'w') as f:
            f.write(pretty_xml)

        # Create image list file for CVAT
        image_list_path = os.path.join(output_dir, f"{video_name}_image_list.txt")
        with open(image_list_path, 'w') as f:
            for i in range(1, num_images + 1):
                filename = f"{video_name}_{str(i * 30 + 1).zfill(6)}.jpg"
                f.write(f"{filename}\n")

        print(f"Successfully created CVAT files for video {video_name}")
        print(f"  - Task config: {task_config_path}")
        print(f"  - Annotations: {annotations_xml_path}")
        print(f"  - Image list: {image_list_path}")

        return True

    except Exception as e:
        print(f"Error creating CVAT files for video {video_name}: {e}")
        return False


def main():
    # Parse command line arguments
    if len(sys.argv) != 3:
        print("Usage: python dense_proposals_to_cvat.py <pickle_file> <json_output_path>")
        sys.exit(1)

    pickle_file_path = sys.argv[1]
    json_path = sys.argv[2]

    # Load pickle file
    try:
        with open(pickle_file_path, 'rb') as f:
            info = pickle.load(f, encoding='iso-8859-1')
        print(f"Loaded {len(info)} entries from pickle file")
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        sys.exit(1)

    # Group data by video
    video_data = defaultdict(dict)
    for key, detections in info.items():
        video_name = key.split(',')[0]
        video_data[video_name][key] = detections

    print(f"Found {len(video_data)} videos to process")

    # Process each video
    successful_videos = 0
    for video_name, video_info in video_data.items():
        if process_video_annotations(video_name, video_info, json_path):
            successful_videos += 1

    print(f"Successfully processed {successful_videos}/{len(video_data)} videos")

    # Print instructions
    print("\n" + "=" * 50)
    print("CVAT SETUP INSTRUCTIONS FOR SINGLE PERSON TESTING:")
    print("=" * 50)
    print("1. For each video, you'll find these files:")
    print("   - {video_name}_task_config.json: Task configuration")
    print("   - {video_name}_annotations.xml: Pre-annotations from dense proposals")
    print("   - {video_name}_image_list.txt: List of image files")
    print("\n2. To test in CVAT:")
    print("   - Create a new task manually in CVAT web interface")
    print("   - Upload the images for the video")
    print("   - Import the pre-annotations using the XML file")
    print("   - Start annotating to refine the dense proposals")
    print("\n3. After annotation, export results from CVAT in XML format")
    print("   - Use CVAT's export functionality to get annotated XML")
    print("   - This XML will contain all refined bounding boxes and attributes")


if __name__ == "__main__":
    main()