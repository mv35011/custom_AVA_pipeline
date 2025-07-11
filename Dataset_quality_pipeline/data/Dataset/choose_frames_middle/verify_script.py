import json
import os
import sys


def verify_via_json(json_path):
    """Verify what values are stored in VIA JSON files"""
    print(f"Verifying: {json_path}")

    try:
        with open(json_path, encoding='utf-8') as f:
            line = f.readline()
            via_json = json.loads(line)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return

    # Check attributes structure
    attributes = via_json.get('attribute', {})
    print(f"\n=== ATTRIBUTES STRUCTURE ===")
    for attr_id, attr_info in attributes.items():
        print(f"Attribute {attr_id}:")
        if 'options' in attr_info:
            for opt_key, opt_value in attr_info['options'].items():
                print(f"  Option key: '{opt_key}' -> value: '{opt_value}'")
        print()

    # Check what av values are actually stored
    print(f"=== ANNOTATION VALUES (AV) ===")
    av_values_found = {}

    for metadata_key in via_json.get('metadata', {}):
        imagen_x = via_json['metadata'][metadata_key]

        for attribute_id in imagen_x.get('av', {}):
            avs = imagen_x['av'][attribute_id]
            if avs == '':
                continue

            av_arr = avs.split(',')

            if attribute_id not in av_values_found:
                av_values_found[attribute_id] = set()

            for av in av_arr:
                av = av.strip()
                if av != '':
                    av_values_found[attribute_id].add(av)

    # Display found av values
    for attr_id in sorted(av_values_found.keys()):
        print(f"Attribute {attr_id} - Found av values: {sorted(av_values_found[attr_id])}")

        # Check if these match the expected option keys
        if attr_id in attributes and 'options' in attributes[attr_id]:
            expected_keys = set(attributes[attr_id]['options'].keys())
            found_values = av_values_found[attr_id]

            if found_values == expected_keys:
                print(f"  ✓ MATCH: av values match option keys")
            else:
                print(f"  ✗ MISMATCH:")
                print(f"    Expected option keys: {sorted(expected_keys)}")
                print(f"    Found av values: {sorted(found_values)}")
                print(f"    Missing: {sorted(expected_keys - found_values)}")
                print(f"    Extra: {sorted(found_values - expected_keys)}")
        print()


def main():
    if len(sys.argv) > 1:
        search_directory = sys.argv[1]
    else:
        search_directory = "./choose_frames_middle"

    print(f"Searching for VIA JSON files in: {search_directory}")

    if not os.path.exists(search_directory):
        print(f"Error: Directory {search_directory} does not exist!")
        sys.exit(1)

    json_files_found = 0

    for root, dirs, files in os.walk(search_directory, topdown=False):
        for file in files:
            if file.endswith("_finish.json"):
                json_path = os.path.join(root, file)
                verify_via_json(json_path)
                json_files_found += 1
                print("=" * 60)

    print(f"Total JSON files processed: {json_files_found}")


if __name__ == "__main__":
    main()