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
pip install -r requirements.txt
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

Extract frames from your input video (e.g., `1.mp4`) and create 30-second segments:

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
python json_extract.py
```

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
python yolov5_to_deepsort.py --source "../Dataset/frames"
```

### Step 11: Dataset Fusion and Finalization

```bash
cd ../Dataset
python train_temp.py
```

**What it does:**
- Fuses person ID and non-person ID datasets
- Creates final training dataset structure

### Step 12: Create Annotation Files

Navigate to annotations directory and create required files:

```bash
cd annotations
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

Create `action_list.pbtxt` with your action definitions.
```
item {
  name: "normal_walk"
  id: 0
}
item {
  name: "fast_walk"
  id: 1
}
item {
  name: "slow_walk"
  id: 2
}
item {
  name: "standing_still"
  id: 3
}
item {
  name: "jogging"
  id: 4
}
item {
  name: "window_shopping"
  id: 5
}
item {
  name: "no_phone"
  id: 6
}
item {
  name: "talking_phone"
  id: 7
}
item {
  name: "texting"
  id: 8
}
item {
  name: "taking_photo"
  id: 9
}
item {
  name: "listening_music"
  id: 10
}
item {
  name: "alone"
  id: 11
}
item {
  name: "talking_companion"
  id: 12
}
item {
  name: "group_walking"
  id: 13
}
item {
  name: "greeting_someone"
  id: 14
}
item {
  name: "asking_directions"
  id: 15
}
item {
  name: "avoiding_crowd"
  id: 16
}
item {
  name: "empty_hands"
  id: 17
}
item {
  name: "shopping_bags"
  id: 18
}
item {
  name: "backpack"
  id: 19
}
item {
  name: "briefcase_bag"
  id: 20
}
item {
  name: "umbrella"
  id: 21
}
item {
  name: "food_drink"
  id: 22
}
item {
  name: "multiple_items"
  id: 23
}
item {
  name: "sidewalk_walking"
  id: 24
}
item {
  name: "crossing_street"
  id: 25
}
item {
  name: "waiting_signal"
  id: 26
}
item {
  name: "looking_around"
  id: 27
}
item {
  name: "checking_map"
  id: 28
}
item {
  name: "entering_building"
  id: 29
}
item {
  name: "exiting_building"
  id: 30
}
item {
  name: "upright_normal"
  id: 31
}
item {
  name: "looking_down"
  id: 32
}
item {
  name: "looking_up"
  id: 33
}
item {
  name: "hands_in_pockets"
  id: 34
}
item {
  name: "arms_crossed"
  id: 35
}
item {
  name: "pointing_gesture"
  id: 36
}
item {
  name: "bowing_gesture"
  id: 37
}
item {
  name: "business_attire"
  id: 38
}
item {
  name: "casual_wear"
  id: 39
}
item {
  name: "tourist_style"
  id: 40
}
item {
  name: "school_uniform"
  id: 41
}
item {
  name: "sports_wear"
  id: 42
}
item {
  name: "traditional_wear"
  id: 43
}
item {
  name: "rush_hour"
  id: 44
}
item {
  name: "leisure_time"
  id: 45
}
item {
  name: "shopping_time"
  id: 46
}
item {
  name: "tourist_hours"
  id: 47
}
item {
  name: "lunch_break"
  id: 48
}
item {
  name: "evening_stroll"
  id: 49
}


```
Create empty `train_excluded_timestamps.csv`.

### Step 13: Copy Files for Training/Validation

```bash
# Copy dense proposals
cp "../yolovDeepsort/mywork/dense_proposals_train.pkl" "./dense_proposals_train.pkl"
cp "./dense_proposals_train.pkl" "./dense_proposals_val.pkl"

# Copy CSV files
cp "./train.csv" "./val.csv"
cp "./train_excluded_timestamps.csv" "./val_excluded_timestamps.csv"

# Copy frames to rawframes
cp -r "./frames/*" "./rawframes/"
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

