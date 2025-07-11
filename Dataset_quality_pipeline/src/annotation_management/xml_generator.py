import pickle
import json
import os
import cv2
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from pathlib import Path
import sys
import traceback


def get_image_dimensions(base_path, video_name):
    print(f"Looking for images in {base_path} for video {video_name}")
    for subdir in range(1, 4):
        search_path = os.path.join(base_path, str(subdir))
        print(f"  Checking directory: {search_path}")
        if os.path.exists(search_path):
            files = os.listdir(search_path)
            print(f"    Found {len(files)} files")
            for file in files:
                if file.endswith('.jpg') and video_name in file:
                    print(f"    Found matching image: {file}")
                    img_path = os.path.join(search_path, file)
                    img = cv2.imread(img_path)
                    if img is not None:
                        print(f"    Image dimensions: {img.shape[0]}x{img.shape[1]}")
                        return img.shape[0], img.shape[1]
        else:
            print(f"    Directory does not exist: {search_path}")
    print(f"  No images found for {video_name}, using default dimensions")
    return 720, 1280


def count_images_for_video(base_path, video_name):

    count = 0
    print(f"Counting images for video {video_name}")
    for subdir in range(1, 4):
        search_path = os.path.join(base_path, str(subdir))
        if os.path.exists(search_path):
            files = os.listdir(search_path)
            for file in files:
                if file.endswith('.jpg') and video_name in file:
                    count += 1
    print(f"  Total images found: {count}")
    return count


def compute_iou(box1, box2):

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def create_tracks_from_detections(video_info, iou_threshold=0.5, max_gap=2, min_track_length=3, start_track_id=1):

    tracks = []
    current_track_id = start_track_id
    sorted_frames = sorted(video_info.keys(), key=lambda x: int(x.split(',')[1]))

    for frame_key in sorted_frames:
        frame_num = int(frame_key.split(',')[1]) - 1
        detections = video_info[frame_key]

        unmatched_detections = list(range(len(detections)))
        for track in tracks:
            if len(track['boxes']) == 0:
                continue
            last_frame = track['boxes'][-1]['frame']
            last_box = track['boxes'][-1]['bbox']
            if frame_num - last_frame > max_gap:
                continue
            best_iou = 0
            best_detection_idx = -1

            for i, detection_idx in enumerate(unmatched_detections):
                detection = detections[detection_idx]
                iou = compute_iou(last_box, detection)

                if iou > best_iou and iou > iou_threshold:
                    best_iou = iou
                    best_detection_idx = detection_idx
            if best_detection_idx != -1:
                track['boxes'].append({
                    'frame': frame_num,
                    'bbox': detections[best_detection_idx]
                })
                unmatched_detections.remove(best_detection_idx)
        for detection_idx in unmatched_detections:
            tracks.append({
                'id': current_track_id,
                'boxes': [{
                    'frame': frame_num,
                    'bbox': detections[detection_idx]
                }]
            })
            current_track_id += 1
    filtered_tracks = [track for track in tracks if len(track['boxes']) >= min_track_length]

    return filtered_tracks, current_track_id


def create_cvat_xml(video_name, video_info, base_path):

    num_images = count_images_for_video(base_path, video_name)
    img_H, img_W = get_image_dimensions(base_path, video_name)

    if num_images == 0:
        print(f"No images found for {video_name}")
        return None
    root = ET.Element("annotations")
    version = ET.SubElement(root, "version")
    version.text = "1.1"
    meta = ET.SubElement(root, "meta")
    task = ET.SubElement(meta, "task")

    task_id = ET.SubElement(task, "id")
    task_id.text = "1"
    task_name = ET.SubElement(task, "name")
    task_name.text = f"{video_name}_task"
    task_size = ET.SubElement(task, "size")
    task_size.text = str(num_images)
    labels = ET.SubElement(task, "labels")
    label = ET.SubElement(labels, "label")
    label_name = ET.SubElement(label, "name")
    label_name.text = "person"
    label_color = ET.SubElement(label, "color")
    label_color.text = "#ff0000"
    attributes = ET.SubElement(label, "attributes")
    attribute_defs = [
        ("walking_behavior", ["unknown", "normal_walk", "fast_walk", "slow_walk", "standing_still", "jogging"]),
        ("phone_usage", ["unknown", "no_phone", "talking_phone", "texting", "taking_photo"]),
        ("social_interaction", ["unknown", "alone", "talking_companion", "group_walking", "greeting_someone"]),
        ("carrying_items", ["unknown", "empty_hands", "shopping_bags", "backpack", "briefcase_bag"]),
        ("street_behavior", ["unknown", "sidewalk_walking", "crossing_street", "waiting_signal", "looking_around"]),
        ("posture_gesture", ["unknown", "upright_normal", "looking_down", "looking_up", "hands_in_pockets"]),
        ("clothing_style", ["unknown", "business_attire", "casual_wear", "tourist_style", "sports_wear"]),
        ("time_context", ["unknown", "rush_hour", "leisure_time", "shopping_time", "lunch_break"])
    ]

    for attr_name, attr_values in attribute_defs:
        attribute = ET.SubElement(attributes, "attribute")
        attr_name_elem = ET.SubElement(attribute, "name")
        attr_name_elem.text = attr_name
        attr_input_type = ET.SubElement(attribute, "input_type")
        attr_input_type.text = "select"
        attr_values_elem = ET.SubElement(attribute, "values")
        attr_values_elem.text = "\n".join(attr_values)
    tracks, _ = create_tracks_from_detections(video_info)

    print(f"Created {len(tracks)} tracks for {video_name}")
    for track in tracks:
        track_elem = ET.SubElement(root, "track")
        track_elem.set("id", str(track['id']))
        track_elem.set("label", "person")
        for box_data in track['boxes']:
            frame_num = box_data['frame']
            bbox = box_data['bbox']
            x1, y1, x2, y2 = bbox[0] * img_W, bbox[1] * img_H, bbox[2] * img_W, bbox[3] * img_H
            box = ET.SubElement(track_elem, "box")
            box.set("frame", str(frame_num))
            box.set("xtl", f"{x1:.2f}")
            box.set("ytl", f"{y1:.2f}")
            box.set("xbr", f"{x2:.2f}")
            box.set("ybr", f"{y2:.2f}")
            box.set("outside", "0")
            box.set("occluded", "0")
            box.set("keyframe", "1")
            for attr_name, attr_values in attribute_defs:
                attribute = ET.SubElement(box, "attribute")
                attribute.set("name", attr_name)
                attribute.text = attr_values[0]

    return root


def main():
    print("Starting XML generation script...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")

    try:
        parent = Path(__file__).parent.parent.parent
        print(f"Parent directory: {parent}")

        pickle_file = str(parent / "data" / "Dataset" / "proposals" / "dense_proposals_train.pkl")
        base_path = str(parent / "data" / "Dataset" / "choose_frames_middle")
        output_dir = str(parent / "data" / "cvat_xmls")

        print(f"Pickle file path: {pickle_file}")
        print(f"Base path: {base_path}")
        print(f"Output directory: {output_dir}")
        if not os.path.exists(pickle_file):
            print(f"ERROR: Pickle file does not exist: {pickle_file}")
            return
        else:
            print(f"✓ Pickle file exists")

        if not os.path.exists(base_path):
            print(f"ERROR: Base path does not exist: {base_path}")
            return
        else:
            print(f"✓ Base path exists")
        iou_threshold = 0.5
        max_gap = 2
        min_track_length = 3

        os.makedirs(output_dir, exist_ok=True)
        print(f"✓ Output directory created: {output_dir}")
        print("Loading pickle file...")
        with open(pickle_file, 'rb') as f:
            info = pickle.load(f, encoding='iso-8859-1')
        print(f"✓ Pickle loaded successfully. Total entries: {len(info)}")
        keys = list(info.keys())[:5]
        print(f"Sample keys: {keys}")
        video_data = defaultdict(dict)
        for key, detections in info.items():
            video_name = key.split(',')[0]
            video_data[video_name][key] = detections

        print(f"Found {len(video_data)} unique videos")
        print(f"Video names: {list(video_data.keys())[:10]}")
        global_track_id = 1
        for video_name, video_info in video_data.items():
            print(f"\n=== Processing video: {video_name} ===")
            print(f"Video has {len(video_info)} frames")
            num_images = count_images_for_video(base_path, video_name)
            if num_images == 0:
                print(f"Warning: No images found for {video_name}, skipping...")
                continue
            tracks, next_track_id = create_tracks_from_detections(
                video_info,
                iou_threshold=iou_threshold,
                max_gap=max_gap,
                min_track_length=min_track_length,
                start_track_id=global_track_id
            )
            global_track_id = next_track_id

            if len(tracks) == 0:
                print(f"Warning: No valid tracks created for {video_name}, skipping...")
                continue

            xml_root = create_cvat_xml(video_name, video_info, base_path)
            if xml_root is not None:
                rough_string = ET.tostring(xml_root, 'unicode')
                reparsed = minidom.parseString(rough_string)
                pretty_xml = reparsed.toprettyxml(indent="  ")

                xml_path = os.path.join(output_dir, f"{video_name}_annotations.xml")
                with open(xml_path, 'w') as f:
                    f.write(pretty_xml)

                print(f"✓ Created XML for {video_name} with {len(tracks)} tracks")
                print(f"  Saved to: {xml_path}")
            else:
                print(f"Failed to create XML for {video_name}")

        print(f"\n=== Processing complete ===")
        print(f"Total track IDs used: {global_track_id - 1}")
        print(f"Check output directory: {output_dir}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    main()