import csv
import os


def debug_csv_files():
    # File paths
    train_personID_path = './train_personID.csv'
    train_without_personID_path = './train_without_personID.csv'

    print("=== DEBUGGING CSV FILES ===\n")

    # Debug train_personID.csv
    print("1. train_personID.csv:")
    if os.path.exists(train_personID_path):
        with open(train_personID_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            rows = list(csv_reader)

            print(f"   Total rows: {len(rows)}")
            print(f"   First row: {rows[0] if rows else 'Empty'}")
            print(f"   Second row: {rows[1] if len(rows) > 1 else 'No second row'}")
            print(f"   Third row: {rows[2] if len(rows) > 2 else 'No third row'}")
            print(f"   Last row: {rows[-1] if rows else 'Empty'}")

    else:
        print("   ❌ File not found")

    print()

    # Debug train_without_personID.csv
    print("2. train_without_personID.csv:")
    if os.path.exists(train_without_personID_path):
        with open(train_without_personID_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            rows = list(csv_reader)

            print(f"   Total rows: {len(rows)}")
            print(f"   First row: {rows[0] if rows else 'Empty'}")
            print(f"   Second row: {rows[1] if len(rows) > 1 else 'No second row'}")
            print(f"   Third row: {rows[2] if len(rows) > 2 else 'No third row'}")
            print(f"   Last row: {rows[-1] if rows else 'Empty'}")

    else:
        print("   ❌ File not found")

    print()

    # Check for overlapping video names and frame indices
    print("3. Checking for potential matches:")

    personID_data = []
    without_personID_data = []

    # Load personID data (skip header)
    with open(train_personID_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        rows = list(csv_reader)
        personID_data = rows[1:] if len(rows) > 1 else []  # Skip header

    # Load without_personID data (skip header)
    with open(train_without_personID_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        rows = list(csv_reader)
        without_personID_data = rows[1:] if len(rows) > 1 else []  # Skip header

    print(f"   PersonID data rows (after header): {len(personID_data)}")
    print(f"   Without PersonID data rows (after header): {len(without_personID_data)}")

    # Check video names
    if personID_data and without_personID_data:
        personID_videos = set(row[0] for row in personID_data if len(row) > 0)
        without_personID_videos = set(row[0] for row in without_personID_data if len(row) > 0)

        print(f"   Unique videos in personID: {len(personID_videos)}")
        print(f"   Sample personID videos: {list(personID_videos)[:3]}")
        print(f"   Unique videos in without_personID: {len(without_personID_videos)}")
        print(f"   Sample without_personID videos: {list(without_personID_videos)[:3]}")

        common_videos = personID_videos.intersection(without_personID_videos)
        print(f"   Common videos: {len(common_videos)}")
        if common_videos:
            print(f"   Sample common videos: {list(common_videos)[:3]}")

        # Check frame indices for a common video
        if common_videos:
            sample_video = list(common_videos)[0]
            personID_frames = set(row[1] for row in personID_data if row[0] == sample_video)
            without_personID_frames = set(row[1] for row in without_personID_data if row[0] == sample_video)

            print(f"\n   Sample video '{sample_video}':")
            print(f"     PersonID frames: {sorted(list(personID_frames))[:10]}")
            print(f"     Without PersonID frames: {sorted(list(without_personID_frames))[:10]}")

            common_frames = personID_frames.intersection(without_personID_frames)
            print(
                f"     Common frames: {len(common_frames)} out of {len(personID_frames)} vs {len(without_personID_frames)}")

            if common_frames:
                print(f"     Sample common frames: {sorted(list(common_frames))[:5]}")

                # Show sample coordinates for matching
                sample_frame = list(common_frames)[0]
                personID_coords = [(row[2], row[3], row[4], row[5]) for row in personID_data
                                   if row[0] == sample_video and row[1] == sample_frame]
                without_personID_coords = [(row[2], row[3], row[4], row[5]) for row in without_personID_data
                                           if row[0] == sample_video and row[1] == sample_frame]

                print(f"     Frame {sample_frame} coordinates:")
                print(f"       PersonID: {personID_coords[:3]}")
                print(f"       Without PersonID: {without_personID_coords[:3]}")
            else:
                print("     ❌ NO COMMON FRAMES FOUND - This is the problem!")
        else:
            print("   ❌ NO COMMON VIDEOS FOUND")


if __name__ == "__main__":
    debug_csv_files()