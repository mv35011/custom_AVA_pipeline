import csv
import os
train_personID_path = './train_personID.csv'
train_without_personID_path = './train_without_personID.csv'
output_path = './train_temp.csv'
if not os.path.exists(train_personID_path):
    print(f"Error: {train_personID_path} not found")
    exit(1)

if not os.path.exists(train_without_personID_path):
    print(f"Error: {train_without_personID_path} not found")
    exit(1)

train_personID = []
train_without_personID = []
print("Reading train_personID.csv...")
with open(train_personID_path, 'r', newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    header = next(csv_reader, None)  # Skip header if exists
    for row in csv_reader:
        if len(row) >= 7:  # Ensure row has enough columns
            train_personID.append(row)
print("Reading train_without_personID.csv...")
with open(train_without_personID_path, 'r', newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    header = next(csv_reader, None)  # Skip header if exists
    for row in csv_reader:
        if len(row) >= 7:  # Ensure row has enough columns
            train_without_personID.append(row)

print(f"Loaded {len(train_personID)} rows from train_personID.csv")
print(f"Loaded {len(train_without_personID)} rows from train_without_personID.csv")

dicts = []
matched_count = 0
unmatched_count = 0

print("Matching bounding boxes...")
for i, data in enumerate(train_without_personID):
    if i % 100 == 0:
        print(f"Processing {i}/{len(train_without_personID)}")

    isFind = False
    for temp_data in train_personID:
        try:
            if data[0] == temp_data[0]:
                data_frame = int(data[1])  # Convert from string to int
                temp_data_frame = int(temp_data[1])  # Convert from string (with leading zeros) to int
                if data_frame == temp_data_frame:
                    if (abs(float(data[2]) - float(temp_data[2])) < 0.005 and
                            abs(float(data[3]) - float(temp_data[3])) < 0.005 and
                            abs(float(data[4]) - float(temp_data[4])) < 0.005 and
                            abs(float(data[5]) - float(temp_data[5])) < 0.005):
                        dict_entry = [data[0], data[1], data[2], data[3], data[4], data[5], data[6],
                                      int(temp_data[6]) - 1]
                        dicts.append(dict_entry)
                        isFind = True
                        matched_count += 1
                        break
        except (ValueError, IndexError) as e:
            print(f"Warning: Error processing row {i}: {e}")
            continue

    if not isFind:
        dict_entry = [data[0], data[1], data[2], data[3], data[4], data[5], data[6], -1]
        dicts.append(dict_entry)
        unmatched_count += 1

print(f"Matching complete!")
print(f"Matched: {matched_count}")
print(f"Unmatched: {unmatched_count}")
print(f"Total: {len(dicts)}")
print(f"Writing results to {output_path}...")
with open(output_path, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['video_name', 'frame_idx', 'x1', 'y1', 'x2', 'y2', 'action_label', 'person_id'])
    writer.writerows(dicts)

print(f"Results saved to: {output_path}")
print("Processing complete!")