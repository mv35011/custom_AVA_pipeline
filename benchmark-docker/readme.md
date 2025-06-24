# AVA Dataset Benchmarking with MMAction2


- Docker installed and running
- NVIDIA Docker runtime (nvidia-docker) - you'll need this for GPU support
- An NVIDIA GPU with CUDA drivers
- Your custom AVA dataset (we'll validate this later)
- MMAction2 checkpoint files(I have added the files)
- Config files for your model

## Dataset Structure


```
benchmark-docker/data/ava/
├── annotations/
│   ├── ava_train_v2.2.csv
│   ├── ava_val_v2.1.csv
│   ├── label_map.txt
│   └── (any other annotation files you have)
├── rawframes/
│   ├── video_id_1/
│   │   ├── img_00001.jpg
│   │   ├── img_00002.jpg
│   │   └── (more frames...)
│   ├── video_id_2/
│   │   └── (frames for video 2...)
│   └── (more video folders...)
├── proposals/
│   ├── ava_dense_proposals_train.FAIR.recall_93.9.pkl
│   ├── ava_dense_proposals_val.FAIR.recall_93.9.pkl
│   └── (other proposal files if needed)
```

download slowonly_omnisource_pretrained_r101_8x8x1_20e_ava_rgb_20201217-16378594.pth
from https://drive.google.com/file/d/1VvNmpWhcZrV6jXJXb_Vm8LlkYdDt4g83/view?usp=sharing
and place it inside the benchmark-docker

### 1. Fix Your CSV Files

Your CSV files should NOT have headers. If they do, you'll get weird errors later. Check the first line:

```bash
head -1 /path/to/your/ava_train_v2.2.csv
```

If you see something like `video_name,timestamp,x1,y1,x2,y2,action_label,person_id`, that's a header and needs to go:

```bash
# Remove the header line
sed -i '1d' /path/to/your/ava_train_v2.2.csv
sed -i '1d' /path/to/your/ava_val_v2.1.csv
```

The format should be exactly 8 columns:
```
video_001,00:01:30.5,0.1,0.2,0.8,0.9,12,1
```

### 2. Check Your Action Labels

AVA uses action labels from 0 to 49 (that's 50 classes total). Double-check yours:

```bash
# See what labels you actually have
cut -d',' -f7 /path/to/your/ava_train_v2.2.csv | sort -n | uniq
```

If you see anything outside 0-49, you'll need to remap your labels.

### 3. Validate Bounding Boxes

Your coordinates should be normalized (between 0 and 1), and x1 should be less than x2, y1 less than y2. I learned this the hard way when my model kept crashing with weird coordinate errors.

### 4. Label Map File

Create a `label_map.txt` with exactly 50 lines - one class name per line. Here's the standard AVA classes if you need them:

```
0 walking_behavior:normal_walk
1 walking_behavior:fast_walk
2 walking_behavior:slow_walk
3 walking_behavior:standing_still
4 walking_behavior:jogging
5 walking_behavior:window_shopping
6 phone_usage:no_phone
7 phone_usage:talking_phone
8 phone_usage:texting
9 phone_usage:taking_photo
10 phone_usage:listening_music
11 social_interaction:alone
12 social_interaction:talking_companion
13 social_interaction:group_walking
14 social_interaction:greeting_someone
15 social_interaction:asking_directions
16 social_interaction:avoiding_crowd
17 carrying_items:empty_hands
18 carrying_items:shopping_bags
19 carrying_items:backpack
20 carrying_items:briefcase_bag
21 carrying_items:umbrella
22 carrying_items:food_drink
23 carrying_items:multiple_items
24 street_behavior:sidewalk_walking
25 street_behavior:crossing_street
26 street_behavior:waiting_signal
27 street_behavior:looking_around
28 street_behavior:checking_map
29 street_behavior:entering_building
30 street_behavior:exiting_building
31 posture_gesture:upright_normal
32 posture_gesture:looking_down
33 posture_gesture:looking_up
34 posture_gesture:hands_in_pockets
35 posture_gesture:arms_crossed
36 posture_gesture:pointing_gesture
37 posture_gesture:bowing_gesture
38 clothing_style:business_attire
39 clothing_style:casual_wear
40 clothing_style:tourist_style
41 clothing_style:school_uniform
42 clothing_style:sports_wear
43 clothing_style:traditional_wear
44 time_context:rush_hour
45 time_context:leisure_time
46 time_context:shopping_time
47 time_context:tourist_hours
48 time_context:lunch_break
49 time_context:evening_stroll

```

## Getting Started

### Step 1: Build the Docker Image

Navigate to your project folder and build the image:

```bash
cd benchmark-docker
docker build -t mmaction2-env .
```

### Step 2: Run Docker with GPU Support

**Windows (PowerShell):**
```powershell
docker run -it --rm --gpus all `
  -v "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\benchmark-docker\downloaded_configs:/mmaction2/configs/detection/slowonly" `
  -v "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\benchmark-docker:/mmaction2/checkpoints" `
  -v "C:\Users\mv350\Downloads\Documents\Pycharm_projects\AVA_benchmarks\benchmark-docker\data\ava:/mmaction2/data/ava" `
  mmaction2-env
```

**Linux/Mac:**
```bash
docker run -it --rm --gpus all \
  -v "/path/to/your/downloaded_configs:/mmaction2/configs/detection/slowonly" \
  -v "/path/to/your/benchmark-docker:/mmaction2/checkpoints" \
  -v "/path/to/your/benchmark-docker/data/ava:/mmaction2/data/ava" \
  mmaction2-env
```

*Note: Replace those Windows paths with your actual paths. The `--gpus all` part is crucial for GPU access.*

### Step 3: Verify Everything Mounted Correctly

Once you're inside the container, check that your files are there:

```bash
ls /mmaction2/configs/detection/slowonly
ls /mmaction2/checkpoints
ls /mmaction2/data/ava/annotations
ls /mmaction2/data/ava/rawframes
```

### Step 4: Check GPU Access

Make sure your GPU is visible:
```bash
nvidia-smi
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

If CUDA isn't available, something's wrong with your Docker GPU setup.

### Step 5: Activate the Environment

```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate mmaction
cd /mmaction2
```

## Configuration Setup

### Install a Text Editor (you'll need this)

```bash
apt update && apt install nano -y
```

### Edit Your Config File

```bash
nano /mmaction2/configs/detection/slowonly/slowonly_r101_ava.py
```

Add this at the very top:
```python
custom_imports = dict(
    imports=['mmdet.models']
)
```

Then update these paths to match your setup:
```python
data_root = '/mmaction2/data/ava/rawframes/'
ann_file = '/mmaction2/data/ava/annotations/ava_val_v2.1.csv'
proposal_file = '/mmaction2/data/ava/proposals/ava_dense_proposals_val.FAIR.recall_93.9.pkl'
label_file = '/mmaction2/data/ava/annotations/label_map.txt'
```

Save with `Ctrl+O`, press Enter, then exit with `Ctrl+X`.

## Install Dependencies

You'll need MMDetection:

```bash
cd /mmaction2
git clone https://github.com/open-mmlab/mmdetection.git
cd mmdetection
pip install -e .
```

And one more thing:
```bash
pip install yapf==0.32.0
```

## Quick Dataset Validation Script

This is a generated script to catch common issues. Run it before training:

```bash
cat > validate_dataset.py << 'EOF'
import os
import pandas as pd
import pickle

def check_dataset():
    print("🔍 Checking your AVA dataset...")
    
    data_root = '/mmaction2/data/ava'
    issues = []
    
    # Check if main directories exist
    for dirname in ['annotations', 'rawframes', 'proposals']:
        if not os.path.exists(f"{data_root}/{dirname}"):
            issues.append(f"Missing {dirname} directory")
    
    # Check annotation files
    for filename in ['ava_train_v2.2.csv', 'ava_val_v2.1.csv']:
        filepath = f"{data_root}/annotations/{filename}"
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, header=None)
            print(f"✅ {filename}: {len(df)} rows")
            
            if len(df.columns) != 8:
                issues.append(f"{filename} has {len(df.columns)} columns, expected 8")
            
            # Check action labels
            labels = df.iloc[:, 6]
            if labels.min() < 0 or labels.max() > 49:
                issues.append(f"{filename} has labels outside 0-49 range: {labels.min()}-{labels.max()}")
        else:
            issues.append(f"Missing {filename}")
    
    # Check label map
    label_map_path = f"{data_root}/annotations/label_map.txt"
    if os.path.exists(label_map_path):
        with open(label_map_path) as f:
            lines = f.readlines()
            if len(lines) != 50:
                issues.append(f"label_map.txt has {len(lines)} lines, expected 50")
            else:
                print("✅ label_map.txt looks good")
    else:
        issues.append("Missing label_map.txt")
    
    # Check proposal files
    for filename in ['ava_dense_proposals_train.FAIR.recall_93.9.pkl', 'ava_dense_proposals_val.FAIR.recall_93.9.pkl']:
        filepath = f"{data_root}/proposals/{filename}"
        if not os.path.exists(filepath):
            issues.append(f"Missing {filename}")
    
    if issues:
        print("\n❌ Found issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nFix these before running the benchmark!")
    else:
        print("\n🎉 Dataset validation passed! You're good to go.")

if __name__ == "__main__":
    check_dataset()
EOF

python validate_dataset.py
```

## Run the Benchmark

If validation passed, you can run the test:

```bash
cd /mmaction2
python tools/test.py \
  /mmaction2/configs/detection/slowonly/slowonly_r101_ava.py \
  /mmaction2/checkpoints/slowonly_omnisource_pretrained_r101_8x8x1_20e_ava_rgb_20201217-16378594.pth
```

For training, use `tools/train.py` instead.

## Common Issues & Solutions

**GPU not detected**
- Make sure nvidia-docker is installed: `sudo apt-get install nvidia-docker2`
- Restart Docker: `sudo systemctl restart docker`
- Check if `nvidia-smi` works in the container

**"CUDA out of memory" errors**
- Reduce batch size in your config file
- Close other GPU processes
- Use gradient accumulation if available

**File permission errors**
- Docker might not have access to your directories
- Try running Docker as admin/sudo (not recommended for production)
- Check if your antivirus is blocking file access

**Config file errors**
- Double-check all paths match your actual file structure
- Make sure you added the `custom_imports` at the top
- Verify your checkpoint file matches the config

**CSV parsing errors**
- Remove headers from CSV files
- Check for extra commas or malformed lines
- Validate that all videos in CSV have corresponding frame folders

## Quick Checklist

Before running anything:

- [ ] CSV files have no headers
- [ ] Action labels are 0-49
- [ ] All bounding boxes have x1<x2 and y1<y2
- [ ] label_map.txt has exactly 50 lines
- [ ] Both proposal pickle files exist and load properly
- [ ] Frame directories exist for all videos in your CSV
- [ ] GPU is accessible in Docker
- [ ] Config file paths match your setup

## Final Notes

This setup assumes you're using SlowOnly R101. If you're using a different model, adjust the config file paths accordingly.

The validation script should catch most issues, but if you run into problems, the error messages are usually pretty helpful. Don't skip the dataset validation step - it'll save you a lot of debugging time later!

Good luck with your benchmarking! 🚀