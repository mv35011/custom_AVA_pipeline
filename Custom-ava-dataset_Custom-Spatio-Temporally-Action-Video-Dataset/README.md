# Custom AVA Dataset Pipeline
#follows this repo [Project README](https://github.com/Whiffe/Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset/blob/main/README.md)



## Prerequisites

- **FFmpeg**: Required for video processing
- **Python 3.10**: With pip package manager

## Installation

### 1. Install System Dependencies

```bash
# Install FFmpeg (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Windows)
# Download from https://ffmpeg.org/download.html
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset
```

### 3. Install Python Dependencies

```bash
cd yolovDeepsort

pip install opencv-python-headless==4.11.0.86

# Uninstall existing PyTorch (if any)
pip uninstall torch torchvision torchaudio

# Install PyTorch with CUDA support
pip install torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install numpy==1.26.4
```

### 4. Download Pre-trained Models

The YOLOv5 model and fonts are already included in the repository. If needed, you can download them manually:

```bash
# YOLOv5 model (optional - already included)
wget https://github.com/ultralytics/yolov5/releases/download/v6.1/yolov5s.pt -O ./yolov5/yolov5s.pt

# Arial font for annotations (optional - already included)  
mkdir -p /root/.config/Ultralytics/
wget https://ultralytics.com/assets/Arial.ttf -O /root/.config/Ultralytics/Arial.ttf
```

## Pipeline Workflow

### Step 1: Video Processing and Frame Extraction

crop the videos to 11 sec clips and extracts the frames (331 frames):

```bash
cd Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset/mywork
python video_processing.py
```

**What it does:**
- Creates 3 segments of 30-second clips from input video
- Extracts frames and saves them to `frames/` directory
- Names subdirectories as 1, 2, 3, etc.

### Step 2: Frame Selection for Processing

Select specific frames based on timing requirements:

```bash
# Select frames for all processing
python choose_frames_all.py <total_seconds> <start_second>

# Example: Process 10 seconds starting from second 0
cd ../Dataset
python choose_frames_all.py 10 0
```

**What it does:**
- Calculates frame numbers based on 30 FPS (frames 1, 31, 61, 91, ...)
- Copies selected frames to `choose_frames_all/` directory
- Maintains subfolder structure

### Step 3: Frame Selection for Middle Processing

```bash
python choose_frames.py 10 0
```

**What it does:**
- Similar to above but saves to `choose_frames/` directory
- Renames files to `<foldername>_<frameno>.jpg` format

### Step 4: Person Detection with YOLOv5

Run person detection on the selected frames:

```bash
cd ../yolovDeepsort
python ./yolov5/detect.py --source ../Dataset/choose_frames_all/ --save-txt --save-conf
```

**What it does:**
- Detects persons in images using YOLOv5
- Saves bounding box coordinates and confidence scores
- Outputs detection results to `runs/detect/exp/`

### Step 5: Generate Dense Proposals

Create dense proposals for training:

```bash
cd mywork
python dense_proposals_train.py ../yolov5/runs/detect/exp/labels ./dense_proposals_train.pkl show
```

**What it does:**
- Processes YOLO detection files
- Filters for "person" class only
- Aggregates detections into AVA-style format
- Saves results as `.pkl` file

### Step 6: Prepare Frames for Annotation

```bash
cd ../../Dataset
python choose_frames_middle.py
```

**What it does:**
- Creates `choose_frames_middle/` directory structure
- Copies relevant frames for annotation
- Handles frame number parsing and file organization

### Step 7: Convert to VIA3 Format

Prepare annotations for VIA3 (VGG Image Annotator):

```bash
cd ../yolovDeepsort/mywork/
python dense_proposals_train_to_via.py ./dense_proposals_train.pkl ../../Dataset/choose_frames_middle/
python chang_via_json.py 
```

**What it does:**
- Converts bounding box data to VIA3 JSON format
- Includes metadata for proper annotation setup
- Generates proposal files for each video segment

### Step 8: Manual Annotation (VIA3)

1. Open VIA3 in your web browser
2. Use the "+" symbol to add all images from subdirectories (1/, 2/, 3/)
3. Import the generated `_s.json` proposal files (e.g., `3_proposal.json`)
4. Manually annotate actions and save the results
5. Rename saved files to `1_finish.json`, `2_finish.json`, etc.

### Step 9: Extract Final Annotations

```bash
cd ../../Dataset
python json_extract_cumulative.py
```

---

## 🔁 General Pattern

| Filename         | Frame Number | Calculation             | `frame_id` |
|------------------|--------------|--------------------------|------------|
| `1_00001.jpg`    | 1            | (1 - 1) // 30            | 0          |
| `1_00031.jpg`    | 31           | (31 - 1) // 30           | 1          |
| `1_00061.jpg`    | 61           | (61 - 1) // 30           | 2          |
| `1_00301.jpg`    | 301          | (301 - 1) // 30          | 10         |

---

## 📄 Output Format

The script generates a CSV file `train_without_personID.csv` with the following columns:

| Column      | Description                                 |
|-------------|---------------------------------------------|
| video_name  | Name of the video (e.g., `1`)               |
| frame_id    | Index of the frame in the 1 FPS sampled set |
| x1, y1, x2, y2 | Normalized bounding box coordinates (0–1) |
| action_id   | Unique action class ID                     |

---

## 💡 Why This Calculation?

- To **align with real-time annotations**, the dataset uses **1 FPS samples** for annotation simplicity.
- The original videos are likely **30 FPS**, so to compute the 1 FPS frame index, we map `frame_number` to `frame_id` using:

Cumulative Action ID Logic
The action IDs in the CSV files use a cumulative mapping system that converts your organized action categories into sequential IDs for training purposes.
How It Works:

Original Action Structure: Your actions are organized in categories with specific ID ranges:

Walking Behavior: 10-15 (6 actions)
Phone Usage: 20-24 (5 actions)
Social Interaction: 30-35 (6 actions)
Carrying Items: 40-46 (7 actions)
Street Behavior: 50-56 (7 actions)
Posture Gesture: 60-66 (7 actions)
Clothing Style: 70-75 (6 actions)
Time Context: 80-85 (6 actions)


Cumulative Mapping Process:
attribute_nums = [0, 6, 11, 17, 24, 31, 38, 44, 50]

For each action:
action_id = attribute_nums[category_index] + option_index + 1

Example Mapping:

normal_walk (category 1, option 0) → action_id = 0 + 0 + 1 = 1
fast_walk (category 1, option 1) → action_id = 0 + 1 + 1 = 2
no_phone (category 2, option 0) → action_id = 6 + 0 + 1 = 7
talking_phone (category 2, option 1) → action_id = 6 + 1 + 1 = 8


Result: Sequential action IDs (1, 2, 3, 4, 5, 6, 7, 8, 9, ...) that maintain category relationships while being compatible with standard ML frameworks.

Why Use Cumulative IDs?

Framework Compatibility: Most ML frameworks expect sequential class IDs starting from 0 or 1
Memory Efficiency: Avoids sparse arrays when using original IDs like 10, 20, 30, etc.
Category Preservation: Actions from the same category remain grouped together
Scalability: Easy to add new action categories without ID conflicts
**What it does:**
- Reads VIA3 `_finish.json` files
- Extracts bounding box coordinates and attributes
- Normalizes coordinates relative to image dimensions
- Maps action values to sequential integers
- Saves cleaned annotations to CSV format

### Step 10: Person Tracking with DeepSORT

```bash
cd ../yolovDeepsort/mywork
python dense_proposals_train_deepsort.py ../yolov5/runs/detect/exp/labels ./dense_proposals_train_deepsort.pkl show
```

Download DeepSORT model(Optional as I included it in Repo):
```bash
cd ../
wget https://drive.google.com/drive/folders/1xhG0kRH1EX5B9_Iz8gQJb7UNnn_riXi6 -O ./deep_sort_pytorch/deep_sort/deep/checkpoint/ckpt.t7
```

Run tracking:
```bash
cd mywork
python dense_proposals_train_deepsort.py ../yolov5/runs/detect/exp/labels ./dense_proposals_train_deepsort.pkl show
cd ../
python yolov5_to_deepsort.py --source "../Dataset/frames"
```

### Step 11: Dataset Fusion and Finalization

```bash
cd ../Dataset
python train_temp.py
python train_fixed.py
```

**What it does:**
- Fuses person ID and non-person ID datasets
- Creates final training dataset structure
- train.py removes the data with person ID -1 and saves it as train.csv at annotations
### Step 12: Create Annotation Files

Navigate to annotations directory and create required files:

```bash
cd annotations
```
```bash
New-Item included_timestamps.txt -ItemType File

New-Item action_list.pbtxt -ItemType File
```
Create `included_timestamps.txt`:
```
02
03
04
05
06
07
08
```
```bash
New-Item train_excluded_timestamps.csv -ItemType File
```

Create `action_list.pbtxt` with your action definitions.
we have flexibility here we can add and change the configs for benchmark later
```
# Walking Behavior Actions (1x series)
item {
  name: "normal_walk"
  id: 10
}
item {
  name: "fast_walk"
  id: 11
}
item {
  name: "slow_walk"
  id: 12
}
item {
  name: "standing_still"
  id: 13
}
item {
  name: "jogging"
  id: 14
}
item {
  name: "window_shopping"
  id: 15
}

# Phone Usage Actions (2x series)
item {
  name: "no_phone"
  id: 20
}
item {
  name: "talking_phone"
  id: 21
}
item {
  name: "texting"
  id: 22
}
item {
  name: "taking_photo"
  id: 23
}
item {
  name: "listening_music"
  id: 24
}

# Social Interaction Actions (3x series)
item {
  name: "alone"
  id: 30
}
item {
  name: "talking_companion"
  id: 31
}
item {
  name: "group_walking"
  id: 32
}
item {
  name: "greeting_someone"
  id: 33
}
item {
  name: "asking_directions"
  id: 34
}
item {
  name: "avoiding_crowd"
  id: 35
}

# Carrying Items Actions (4x series)
item {
  name: "empty_hands"
  id: 40
}
item {
  name: "shopping_bags"
  id: 41
}
item {
  name: "backpack"
  id: 42
}
item {
  name: "briefcase_bag"
  id: 43
}
item {
  name: "umbrella"
  id: 44
}
item {
  name: "food_drink"
  id: 45
}
item {
  name: "multiple_items"
  id: 46
}

# Street Behavior Actions (5x series)
item {
  name: "sidewalk_walking"
  id: 50
}
item {
  name: "crossing_street"
  id: 51
}
item {
  name: "waiting_signal"
  id: 52
}
item {
  name: "looking_around"
  id: 53
}
item {
  name: "checking_map"
  id: 54
}
item {
  name: "entering_building"
  id: 55
}
item {
  name: "exiting_building"
  id: 56
}

# Posture Gesture Actions (6x series)
item {
  name: "upright_normal"
  id: 60
}
item {
  name: "looking_down"
  id: 61
}
item {
  name: "looking_up"
  id: 62
}
item {
  name: "hands_in_pockets"
  id: 63
}
item {
  name: "arms_crossed"
  id: 64
}
item {
  name: "pointing_gesture"
  id: 65
}
item {
  name: "bowing_gesture"
  id: 66
}

# Clothing Style Actions (7x series)
item {
  name: "business_attire"
  id: 70
}
item {
  name: "casual_wear"
  id: 71
}
item {
  name: "tourist_style"
  id: 72
}
item {
  name: "school_uniform"
  id: 73
}
item {
  name: "sports_wear"
  id: 74
}
item {
  name: "traditional_wear"
  id: 75
}

# Time Context Actions (8x series)
item {
  name: "rush_hour"
  id: 80
}
item {
  name: "leisure_time"
  id: 81
}
item {
  name: "shopping_time"
  id: 82
}
item {
  name: "tourist_hours"
  id: 83
}
item {
  name: "lunch_break"
  id: 84
}
item {
  name: "evening_stroll"
  id: 85
}


```
Create empty `train_excluded_timestamps.csv`.

### Step 13: Copy Files for Training/Validation

```bash
# Copy the necessary files in the annotations change the path for your system

(Windows)


Copy-Item "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\yolovDeepsort\mywork\dense_proposals_train.pkl" `
-Destination "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\"

Copy-Item "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\dense_proposals_train.pkl" `
-Destination "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\dense_proposals_val.pkl"

Copy-Item "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\train.csv" `
-Destination "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\val.csv"

Copy-Item "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\train_excluded_timestamps.csv" `
-Destination "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\annotations\val_excluded_timestamps.csv"

Copy-Item "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\frames\*" `
-Destination "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\Custom-ava-dataset_Custom-Spatio-Temporally-Action-Video-Dataset\Dataset\rawframes" `
-Recurse
```

### Step 14: Final Processing

```bash
cd ../../yolovDeepsort/mywork/
python change_raw_frames.py
python change_dense_proposals_train.py
python change_dense_proposals_val.py
```

## Output Structure

After completion, your dataset will have the following structure:

```
Dataset/
├── annotations/
│   ├── train.csv
│   ├── val.csv
│   ├── dense_proposals_train.pkl
│   ├── dense_proposals_val.pkl
│   ├── action_list.pbtxt
│   ├── included_timestamps.txt
│   └── *_excluded_timestamps.csv
├── rawframes/
│   ├── 1/
│   ├── 2/
│   └── 3/
└── frames/
    ├── 1/
    ├── 2/
    └── 3/

