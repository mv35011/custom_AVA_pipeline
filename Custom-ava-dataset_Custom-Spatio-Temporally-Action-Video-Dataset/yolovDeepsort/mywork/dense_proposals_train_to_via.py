from via3_tool import Via3Json
import pickle
import csv
from collections import defaultdict
import os
import cv2
import sys


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


def process_video_annotations(video_name, video_info, json_path, attributes_dict):
    """Process annotations for a single video"""
    print(f"Processing video: {video_name}")

    # Create output directory
    output_dir = os.path.join(json_path, video_name)
    os.makedirs(output_dir, exist_ok=True)
    temp_json_path = os.path.join(output_dir, f"{video_name}_proposal.json")

    # Define search paths for images
    search_paths = [
        os.path.join(json_path, 'choose_frames_all'),
        os.path.join(json_path, video_name),
        os.path.join(json_path, '1'),  # subdirectory 1
        os.path.join(json_path, '2'),  # subdirectory 2
        os.path.join(json_path, '3'),  # subdirectory 3
    ]

    # Get image count and dimensions
    num_images = count_images_for_video(search_paths, video_name)
    img_H, img_W = get_image_dimensions(search_paths, video_name)

    print(f"Found {num_images} images for video {video_name}")
    print(f"Image dimensions: {img_W}x{img_H}")

    if num_images == 0:
        print(f"Warning: No images found for video {video_name}, skipping...")
        return False

    # Initialize VIA3 JSON
    try:
        via3 = Via3Json(temp_json_path, mode='dump')
        vid_list = list(map(str, range(1, num_images + 1)))
        via3.dumpPrejects(vid_list)
        via3.dumpConfigs()
        via3.dumpAttributes(attributes_dict)
    except Exception as e:
        print(f"Error initializing VIA3 for video {video_name}: {e}")
        return False

    # Process each frame
    files_dict = {}
    metadatas_dict = {}

    # Sort video_info by frame number to ensure proper ordering
    sorted_frames = sorted(video_info.keys(), key=lambda x: int(x.split(',')[1]))

    current_image_id = 0

    for frame_key in sorted_frames:
        frame_num = int(frame_key.split(',')[1])
        current_image_id += 1

        # Handle missing frames (frames without annotations)
        while current_image_id < frame_num:
            # Add empty annotation for missing frame
            files_dict[str(current_image_id)] = dict(
                fname=f"{video_name}_{str(current_image_id * 30 + 1).zfill(6)}.jpg",
                type=2
            )
            current_image_id += 1

        # Process current frame
        frame_filename = f"{video_name}_{str(frame_num * 30 + 1).zfill(6)}.jpg"
        files_dict[str(current_image_id)] = dict(fname=frame_filename, type=2)

        # Process detections in this frame
        detections = video_info[frame_key]
        for detection_id, bbox in enumerate(detections, 1):
            # Convert normalized coordinates to pixel coordinates
            x1 = img_W * bbox[0]
            y1 = img_H * bbox[1]
            x2 = img_W * bbox[2]
            y2 = img_H * bbox[3]

            width = x2 - x1
            height = y2 - y1

            # Create metadata for this detection
            metadata_dict = dict(
                vid=str(current_image_id),
                xy=[2, float(x1), float(y1), float(width), float(height)],
                av={'1': '0'}  # Default attribute value
            )

            metadatas_dict[f'image{current_image_id}_{detection_id}'] = metadata_dict

    # Add remaining frames if they exist but have no annotations
    while current_image_id < num_images:
        current_image_id += 1
        files_dict[str(current_image_id)] = dict(
            fname=f"{video_name}_{str(current_image_id * 30 + 1).zfill(6)}.jpg",
            type=2
        )

    # Save all data
    try:
        via3.dumpFiles(files_dict)
        via3.dumpMetedatas(metadatas_dict)

        # Create views
        views_dict = {}
        for i, vid in enumerate(vid_list, 1):
            views_dict[vid] = defaultdict(list)
            views_dict[vid]['fid_list'].append(str(i))

        via3.dumpViews(views_dict)
        via3.dempJsonSave()

        print(f"Successfully saved annotations for video {video_name}")
        return True

    except Exception as e:
        print(f"Error saving annotations for video {video_name}: {e}")
        return False


def main():
    # Parse command line arguments
    if len(sys.argv) != 3:
        print("Usage: python dense_proposals_train_to_via.py <pickle_file> <json_output_path>")
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

    # Define attributes dictionary
    attributes_dict = {
        '1': dict(
            aname='walking_behavior',
            type=2,
            options={
                '0': 'normal_walk',  # Regular walking pace
                '1': 'fast_walk',  # Hurried/rushing
                '2': 'slow_walk',  # Leisurely stroll
                '3': 'standing_still',  # Stopped/waiting
                '4': 'jogging',  # Light running
                '5': 'window_shopping'  # Stopping to look at stores
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '2': dict(
            aname='phone_usage',
            type=2,
            options={
                '0': 'no_phone',  # Not using phone
                '1': 'talking_phone',  # Phone call
                '2': 'texting',  # Looking down at phone
                '3': 'taking_photo',  # Camera/photo mode
                '4': 'listening_music'  # Earphones/headphones visible
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '3': dict(
            aname='social_interaction',
            type=2,
            options={
                '0': 'alone',  # Walking alone
                '1': 'talking_companion',  # Conversing with others
                '2': 'group_walking',  # Walking in group silently
                '3': 'greeting_someone',  # Bowing or greeting gesture
                '4': 'asking_directions',  # Interacting with strangers
                '5': 'avoiding_crowd'  # Navigating around people
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '4': dict(
            aname='carrying_items',
            type=2,
            options={
                '0': 'empty_hands',  # No visible items
                '1': 'shopping_bags',  # Carrying shopping bags
                '2': 'backpack',  # Wearing backpack
                '3': 'briefcase_bag',  # Business bag/briefcase
                '4': 'umbrella',  # Holding umbrella
                '5': 'food_drink',  # Eating/drinking while walking
                '6': 'multiple_items'  # Carrying several things
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '5': dict(
            aname='street_behavior',
            type=2,
            options={
                '0': 'sidewalk_walking',  # Normal sidewalk use
                '1': 'crossing_street',  # At crosswalk/intersection
                '2': 'waiting_signal',  # Waiting at traffic light
                '3': 'looking_around',  # Tourist-like behavior
                '4': 'checking_map',  # Looking at map/GPS
                '5': 'entering_building',  # Going into shop/station
                '6': 'exiting_building'  # Coming out of building
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '6': dict(
            aname='posture_gesture',
            type=2,
            options={
                '0': 'upright_normal',  # Normal walking posture
                '1': 'looking_down',  # Head down (phone/shy)
                '2': 'looking_up',  # Looking at signs/buildings
                '3': 'hands_in_pockets',  # Relaxed casual posture
                '4': 'arms_crossed',  # Defensive/cold posture
                '5': 'pointing_gesture',  # Pointing at something
                '6': 'bowing_gesture'  # Traditional Japanese bow
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '7': dict(
            aname='clothing_style',
            type=2,
            options={
                '0': 'business_attire',  # Suit/formal wear
                '1': 'casual_wear',  # Everyday clothes
                '2': 'tourist_style',  # Casual with camera/map
                '3': 'school_uniform',  # Student uniform
                '4': 'sports_wear',  # Athletic clothing
                '5': 'traditional_wear'  # Kimono or traditional clothes
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        ),

        '8': dict(
            aname='time_context',
            type=2,
            options={
                '0': 'rush_hour',  # Busy commuting behavior
                '1': 'leisure_time',  # Relaxed weekend walking
                '2': 'shopping_time',  # Shopping district behavior
                '3': 'tourist_hours',  # Sightseeing behavior
                '4': 'lunch_break',  # Midday office worker behavior
                '5': 'evening_stroll'  # After-work relaxed walking
            },
            default_option_id="",
            anchor_id='FILE1_Z0_XY1'
        )
    }

    # Group data by video
    video_data = defaultdict(dict)
    for key, detections in info.items():
        video_name = key.split(',')[0]
        video_data[video_name][key] = detections

    print(f"Found {len(video_data)} videos to process")

    # Process each video
    successful_videos = 0
    for video_name, video_info in video_data.items():
        if process_video_annotations(video_name, video_info, json_path, attributes_dict):
            successful_videos += 1

    print(f"Successfully processed {successful_videos}/{len(video_data)} videos")


if __name__ == "__main__":
    main()