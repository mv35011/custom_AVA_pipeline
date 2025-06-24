import sys
import os
import json
import pickle


def process_yolo_labels(label_path, output_pkl_path, show_pkl=False):

    print(f"Processing YOLO labels from: {label_path}")
    print(f"Output pickle file: {output_pkl_path}")
    print("=" * 60)

    if not os.path.exists(label_path):
        print(f"Error: Label path {label_path} does not exist!")
        return False

    results_dict = {}
    all_detections = []
    processed_files = 0

    # Walk through the label directory
    for root, dirs, files in os.walk(label_path):
        if root == label_path:
            # Filter only .txt files
            txt_files = [f for f in files if f.endswith('.txt')]

            if not txt_files:
                print("No .txt files found in the label directory!")
                return False

            print(f"Found {len(txt_files)} label files")

            # Sort files
            txt_files.sort(
                key=lambda x: (x.split("_")[0], int(x.split("_")[1].split('.')[0]) if len(x.split("_")) > 1 else 0))

            for filename in txt_files:
                try:
                    # Parse filename to get video name and frame info
                    name_parts = filename.split("_")
                    if len(name_parts) < 2:
                        print(f"Warning: Skipping file with unexpected format: {filename}")
                        continue

                    temp_file_name = name_parts[0]
                    temp_frame_number = name_parts[1].split('.')[0]
                    temp_frame_number = int(temp_frame_number)

                    # Calculate second ID (assuming 30 FPS)
                    temp_video_second = int((temp_frame_number - 1) / 30)
                    temp_video_ID = str(temp_video_second).zfill(4)

                    # Create key: 'video_name,second_id' (e.g., '1,0002')
                    key = f"{temp_file_name},{temp_video_ID}"

                    # Read YOLO detection file
                    label_file_path = os.path.join(root, filename)
                    detections = []

                    with open(label_file_path, 'r') as txt_file:
                        lines = txt_file.readlines()

                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue

                            parts = line.split(' ')
                            if len(parts) < 5:
                                continue

                            class_id = parts[0]

                            # Only process person detections (class 0)
                            if class_id == '0':
                                try:
                                    # YOLO format: class_id x_center y_center width height [confidence]
                                    x_center = float(parts[1])
                                    y_center = float(parts[2])
                                    width = float(parts[3])
                                    height = float(parts[4])
                                    confidence = float(parts[5]) if len(parts) > 5 else 1.0

                                    # Convert from YOLO format (xywh) to xyxy format
                                    x1 = x_center - width / 2  # top left x
                                    y1 = y_center - height / 2  # top left y
                                    x2 = x_center + width / 2  # bottom right x
                                    y2 = y_center + height / 2  # bottom right y

                                    # Store detection: [x1, y1, x2, y2, confidence]
                                    detection = [x1, y1, x2, y2, confidence]
                                    detections.append(detection)
                                    all_detections.append(detection)

                                except (ValueError, IndexError) as e:
                                    print(f"Warning: Error parsing line in {filename}: {line} - {e}")
                                    continue

                    # Store detections for this key
                    if detections:
                        results_dict[key] = detections
                        print(f"Processed {filename}: {len(detections)} person detections")

                    processed_files += 1

                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    continue

    print("=" * 60)
    print(f"SUMMARY:")
    print(f"Processed files: {processed_files}")
    print(f"Total unique keys: {len(results_dict)}")
    print(f"Total person detections: {len(all_detections)}")

    if not results_dict:
        print("Warning: No person detections found!")
        return False

    # Save as pickle file
    try:
        with open(output_pkl_path, "wb") as pkl_file:
            pickle.dump(results_dict, pkl_file)
        print(f"Successfully saved dense proposals to: {output_pkl_path}")
    except Exception as e:
        print(f"Error saving pickle file: {e}")
        return False

    # Display pickle content if requested
    if show_pkl:
        print("\n" + "=" * 60)
        print("PICKLE CONTENT:")
        print("=" * 60)
        for key, detections in results_dict.items():
            print(f"Key: {key}")
            print(f"  Detections ({len(detections)}):")
            for i, detection in enumerate(detections):
                print(f"    {i + 1}: [x1={detection[0]:.4f}, y1={detection[1]:.4f}, "
                      f"x2={detection[2]:.4f}, y2={detection[3]:.4f}, conf={detection[4]:.4f}]")
            print()

            # Limit output for readability
            if len(results_dict) > 10:
                remaining = len(results_dict) - 10
                print(f"... and {remaining} more keys (use smaller dataset or remove 'show' to see all)")
                break

    return True


def main():
    """Main function with command line argument handling"""

    if len(sys.argv) < 3:
        print("Usage: python dense_proposals_train_deepsort.py <label_path> <output_pkl_path> [show]")
        print()
        print("Arguments:")
        print("  label_path     : Path to YOLO detection labels directory")
        print("  output_pkl_path: Path to save the dense proposals pickle file")
        print("  show          : Optional - add 'show' to display pickle content")
        print()
        print("Example:")
        print(
            "  python dense_proposals_train_deepsort.py ../yolov5/runs/detect/exp/labels ./dense_proposals_train_deepsort.pkl show")
        sys.exit(1)

    # Parse command line arguments
    label_path = sys.argv[1]
    output_pkl_path = sys.argv[2]
    show_pkl = len(sys.argv) > 3 and sys.argv[3].lower() == 'show'

    print("Dense Proposals Train DeepSort")
    print("=" * 60)
    print(f"Label path: {label_path}")
    print(f"Output pickle: {output_pkl_path}")
    print(f"Show content: {show_pkl}")
    print()

    # Process the labels
    success = process_yolo_labels(label_path, output_pkl_path, show_pkl)

    if success:
        print("\nProcessing completed successfully!")
        sys.exit(0)
    else:
        print("\nProcessing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()