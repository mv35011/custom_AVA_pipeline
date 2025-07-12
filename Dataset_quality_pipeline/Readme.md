# CVAT AVA Dataset Pipeline

Pipeline for setting up CVAT with multiple annotators to create AVA-based datasets.

## Prerequisites

- Docker and Docker Compose
- Python 3.x
- Git

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Video Data
- Place your clip files (directories: `1/`, `2/`, `3/`) at `data/Dataset/choose_frames_middle/`
- Zip the frame directories:
```bash
cd src/data_preparation
python zip_middle_frames.py
cd ../../
```
This creates `1.zip`, `2.zip`, `3.zip` from subdirectories.

### 3. Setup CVAT
```bash
git clone https://github.com/opencv/cvat.git
cd cvat
docker compose up -d
```

### 4. Create Admin Account
```bash
docker compose exec cvat django-admin createsuperuser
```
Enter username, email, and password when prompted.

Test CVAT at localhost and login with admin credentials.

## Annotation Pipeline

### 1. Generate Annotations
- Place `dense_proposals.pkl` at `data/Dataset/proposals`
- Generate CVAT annotation files:
```bash
cd src/annotation_management
python xml_generator.py
```
This creates `1_annotations.xml`, `2_annotations.xml` in `data/cvat_xmls/`

### 2. Single Annotator Setup
```bash
python single_annotator_assignments.py
```
Creates individual tasks for each clip.

**Manual Upload**: In CVAT UI, click 3 lines (top left) → Upload annotation → Choose CVAT 1.1 → Select corresponding annotation file.

### 3. Multiple Annotators with Overlap
Configure assignments in `config/assignment_config.json`:
```json
{
  "assignments": [
    {
      "clip_id": 1,
      "assigned_to": "annotator1",
      "overlap_with": ""
    },
    {
      "clip_id": 2,
      "assigned_to": "annotator2",
      "overlap_with": "annotator1"
    },
    {
      "clip_id": 3,
      "assigned_to": "annotator3",
      "overlap_with": ""
    }
  ]
}
```

**Requirements**:
- Add users through CVAT admin page
- Username must match config file
- Clip ID must match clip name

Assignment report generated in `annotation_management/`

## Export Process

### Current Workaround (Export Path Bug)
CVAT local export path is corrupted. Use Docker copy:
```bash
docker cp cvat_server:/home/django/data/cache/export/job-53-annotations-instance1752217257.267743-cvat-for-images-11.zip .
```
Replace with actual export filename from cvat_server.

Extract and verify export XML.

### Next we will be generating meta_data.json which is mapping for project_id, job_id and task_id
```bash
cd src/annotation_management
python metadata_generator.py
```
This creates a meta data json at the specified path
keep it at the required extract export files location

Now we generate the required folder structure
by copying all the files from the docker directory , extracting them and renaming them acording to the meta data mapping

```bash
cd src/annotation_management
python extract_arrange_exports.py
```
this also creates a report csv for human readable file arrangement

next we will be extracting our no_personID_train.csv from the export json and then running quality checks

## Future Development

- Script to map project_id, task_id, job_id - DONE
- Automated directory structure for exports - DONE
- Generate `no_personID_train.csv` from processed exports
- Run quality checks using iou calculator for the overlapped clips
- create a dash board to parse and display all the results and reports
## Directory Structure
```
├── config/
│   └── assignment_config.json
├── data/
│   ├── Dataset/
│   │   ├── choose_frames_middle/
│   │   └── proposals/
│   └── cvat_xmls/
├── src/
│   ├── annotation_management/
│   └── data_preparation/
└── requirements.txt
```