import csv

train_temp_path = './train_temp.csv'
train_temp = []
with open(train_temp_path) as csvfile:
    csv_reader = csv.reader(csvfile)
    for row in csv_reader:
        train_temp.append(row)
print("Sorting data by video and frame for temporal consistency...")
header = None
data_rows = []

for row in train_temp:
    if row[0] == 'video_name':
        header = row
    else:
        data_rows.append(row)
data_rows.sort(key=lambda x: (x[0], int(x[1])))
train_temp = [header] + data_rows if header else data_rows
print(f"Sorted {len(data_rows)} data rows")


def update_train_temp(videoName, index, maxId):
    """Update person IDs for unassigned (-1) entries"""
    if index >= len(train_temp):
        return
    train_temp[index][-1] = str(maxId + 1)
    try:
        x1 = float(train_temp[index][2])
        y1 = float(train_temp[index][3])
        x2 = float(train_temp[index][4])
        y2 = float(train_temp[index][5])
        current_frame = int(train_temp[index][1])
    except (ValueError, IndexError):
        print(f"Warning: Invalid coordinates or frame at index {index}")
        return
    for offset in range(1, 11):
        next_index = index + offset
        if next_index >= len(train_temp):
            break
        if train_temp[next_index][0] != videoName:
            break
        if str(train_temp[next_index][-1]) != '-1':
            break

        try:
            next_frame = int(train_temp[next_index][1])
            if abs(next_frame - current_frame) > 10:
                break

            xT1 = float(train_temp[next_index][2])
            yT1 = float(train_temp[next_index][3])
            xT2 = float(train_temp[next_index][4])
            yT2 = float(train_temp[next_index][5])

            if (abs(x1 - xT1) < 0.005 and abs(y1 - yT1) < 0.005 and
                    abs(x2 - xT2) < 0.005 and abs(y2 - yT2) < 0.005):
                train_temp[next_index][-1] = str(maxId + 1)
            else:
                break

        except (ValueError, IndexError):
            print(f"Warning: Invalid coordinates or frame at index {next_index}")
            break


maxId = -1
videoName = ''
processed_count = 0

for index in range(len(train_temp)):
    if index == 0 and train_temp[index][0] == 'video_name':
        continue

    data = train_temp[index]
    if videoName != data[0]:
        videoName = data[0]
        maxId = -1
        print(f"Processing video: {videoName}")

    try:
        current_id = int(data[-1]) if str(data[-1]) != '-1' else -1
        if current_id > maxId:
            maxId = current_id
    except ValueError:
        print(f"Warning: Invalid person_id '{data[-1]}' at index {index}")
        continue

    if str(data[-1]) == '-1':
        update_train_temp(videoName, index, maxId)
        maxId = maxId + 1
        processed_count += 1

        if processed_count % 100 == 0:
            print(f"Processed {processed_count} unassigned entries...")

print("Writing results to ./annotations/train.csv...")
with open('./annotations/train.csv', "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(train_temp)

print(f"Processing complete! Updated {processed_count} entries.")
print(f"Results saved to: ./annotations/train.csv")