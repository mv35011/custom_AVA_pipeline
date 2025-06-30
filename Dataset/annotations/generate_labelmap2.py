#!/usr/bin/env python3
"""
Generate label_map.txt for custom AVA-based dataset
Creates mapping from action_id to action_name based on attributes dictionary
"""

import os
import csv
from collections import defaultdict
attributes_dict = {
    '1': dict(
        aname='walking_behavior',
        type=2,
        options={
            '0': 'normal_walk',
            '1': 'fast_walk',
            '2': 'slow_walk',
            '3': 'standing_still',
            '4': 'jogging',
            '5': 'window_shopping'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '2': dict(
        aname='phone_usage',
        type=2,
        options={
            '0': 'no_phone',
            '1': 'talking_phone',
            '2': 'texting',
            '3': 'taking_photo',
            '4': 'listening_music'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '3': dict(
        aname='social_interaction',
        type=2,
        options={
            '0': 'alone',
            '1': 'talking_companion',
            '2': 'group_walking',
            '3': 'greeting_someone',
            '4': 'asking_directions',
            '5': 'avoiding_crowd'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '4': dict(
        aname='carrying_items',
        type=2,
        options={
            '0': 'empty_hands',
            '1': 'shopping_bags',
            '2': 'backpack',
            '3': 'briefcase_bag',
            '4': 'umbrella',
            '5': 'food_drink',
            '6': 'multiple_items'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '5': dict(
        aname='street_behavior',
        type=2,
        options={
            '0': 'sidewalk_walking',
            '1': 'crossing_street',
            '2': 'waiting_signal',
            '3': 'looking_around',
            '4': 'checking_map',
            '5': 'entering_building',
            '6': 'exiting_building'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '6': dict(
        aname='posture_gesture',
        type=2,
        options={
            '0': 'upright_normal',
            '1': 'looking_down',
            '2': 'looking_up',
            '3': 'hands_in_pockets',
            '4': 'arms_crossed',
            '5': 'pointing_gesture',
            '6': 'bowing_gesture'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '7': dict(
        aname='clothing_style',
        type=2,
        options={
            '0': 'business_attire',
            '1': 'casual_wear',
            '2': 'tourist_style',
            '3': 'school_uniform',
            '4': 'sports_wear',
            '5': 'traditional_wear'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    ),

    '8': dict(
        aname='time_context',
        type=2,
        options={
            '0': 'rush_hour',
            '1': 'leisure_time',
            '2': 'shopping_time',
            '3': 'tourist_hours',
            '4': 'lunch_break',
            '5': 'evening_stroll'
        },
        default_option_id="",
        anchor_id='FILE1_Z0_XY1'
    )
}


def calculate_cumulative_action_mapping(attributes):
    """Calculate cumulative action ID mapping like the original repo"""
    attribute_nums = [0]
    cumulative_count = 0
    sorted_attrs = sorted(attributes.items(), key=lambda x: int(x[0]))

    for attr_id, attr_info in sorted_attrs:
        if 'options' in attr_info:
            num_options = len(attr_info['options'])
            cumulative_count += num_options
            attribute_nums.append(cumulative_count)
            print(
                f"  Attribute {attr_id} ({attr_info['aname']}): {num_options} options, cumulative total: {cumulative_count}")

    return attribute_nums


def generate_action_id_mapping(attributes):
    """Generate mapping from action_id to action_name using cumulative logic"""
    print("Generating action ID mapping...")
    attribute_nums = calculate_cumulative_action_mapping(attributes)
    print(f"Attribute cumulative mapping: {attribute_nums}")

    action_mapping = {}
    sorted_attrs = sorted(attributes.items(), key=lambda x: int(x[0]))

    for attr_id, attr_info in sorted_attrs:
        attr_index = int(attr_id) - 1

        if 'options' in attr_info:
            print(f"\nProcessing attribute {attr_id} ({attr_info['aname']}):")
            sorted_options = sorted(attr_info['options'].items(), key=lambda x: int(x[0]))

            for option_id, option_name in sorted_options:
                if attr_index < len(attribute_nums) - 1:
                    action_id = attribute_nums[attr_index] + int(option_id) + 1
                else:
                    action_id = int(option_id) + 1

                action_mapping[action_id] = option_name
                print(f"  Option {option_id} ({option_name}) -> action_id {action_id}")

    return action_mapping


def get_action_ids_from_csv(csv_file_path):
    """Extract unique action IDs from CSV file to verify mapping"""
    action_ids = set()

    if not os.path.exists(csv_file_path):
        print(f"Warning: CSV file {csv_file_path} not found. Generating label map based on attributes only.")
        return action_ids

    try:
        with open(csv_file_path, 'r') as f:
            csv_reader = csv.reader(f)
            first_row = next(csv_reader, None)
            if first_row and first_row[0] == 'video_name':
                pass
            else:
                if first_row and len(first_row) >= 7:
                    try:
                        action_id = int(first_row[6])
                        action_ids.add(action_id)
                    except (ValueError, IndexError):
                        pass
            for row in csv_reader:
                if len(row) >= 7:
                    try:
                        action_id = int(row[6])
                        action_ids.add(action_id)
                    except (ValueError, IndexError):
                        continue

        print(f"Found {len(action_ids)} unique action IDs in CSV: {sorted(action_ids)}")

    except Exception as e:
        print(f"Error reading CSV file: {e}")

    return action_ids


def generate_label_map():
    """Generate label_map.txt file"""
    print("=" * 60)
    print("GENERATING LABEL MAP FOR CUSTOM AVA DATASET")
    print("=" * 60)
    action_mapping = generate_action_id_mapping(attributes_dict)
    csv_file_path = './train_without_personID.csv'
    csv_action_ids = get_action_ids_from_csv(csv_file_path)
    if csv_action_ids:
        mapped_ids = set(action_mapping.keys())
        csv_only = csv_action_ids - mapped_ids
        mapped_only = mapped_ids - csv_action_ids

        if csv_only:
            print(f"\nWarning: Action IDs found in CSV but not in mapping: {sorted(csv_only)}")
        if mapped_only:
            print(f"Info: Action IDs in mapping but not found in CSV: {sorted(mapped_only)}")

        common_ids = csv_action_ids & mapped_ids
        print(f"Verified {len(common_ids)} action IDs match between CSV and mapping")
    output_file = './label_map.txt'

    try:
        with open(output_file, 'w') as f:
            for action_id in sorted(action_mapping.keys()):
                action_name = action_mapping[action_id]
                f.write(f"{action_id}: {action_name}\n")

        print(f"\n✅ Successfully generated {output_file}")
        print(f"Total actions mapped: {len(action_mapping)}")
        print(f"\nGenerated label map:")
        for action_id in sorted(action_mapping.keys()):
            action_name = action_mapping[action_id]
            print(f"  {action_id}: {action_name}")
        print(f"\nStatistics:")
        print(f"- Total attributes: {len(attributes_dict)}")
        print(f"- Total action classes: {len(action_mapping)}")
        print(f"- Action ID range: {min(action_mapping.keys())} to {max(action_mapping.keys())}")
        print(f"\nAction distribution by category:")
        attribute_nums = calculate_cumulative_action_mapping(attributes_dict)
        sorted_attrs = sorted(attributes_dict.items(), key=lambda x: int(x[0]))

        for i, (attr_id, attr_info) in enumerate(sorted_attrs):
            start_id = attribute_nums[i] + 1
            end_id = attribute_nums[i + 1] if i + 1 < len(attribute_nums) else start_id + len(attr_info['options']) - 1
            print(f"  {attr_info['aname']}: action_ids {start_id}-{end_id} ({len(attr_info['options'])} actions)")

    except Exception as e:
        print(f"❌ Error writing label map file: {e}")


if __name__ == "__main__":
    generate_label_map()