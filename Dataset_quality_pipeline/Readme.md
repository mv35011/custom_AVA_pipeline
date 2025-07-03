# Annotation Quality Assurance Pipeline

A comprehensive quality control system for multi-annotator spatio-temporal video annotation projects.

## 🎯 What This Pipeline Does

This pipeline ensures high-quality annotations when multiple people are working on the same video dataset. It:
- Measures how well annotators agree with each other
- Identifies problematic annotations automatically
- Generates quality reports for research presentations
- Provides real-time monitoring of annotation quality

## 📁 Quick Start

### Prerequisites
- Python 3.8+
- Your existing video processing pipeline (we don't handle video processing)
- Annotation files in CSV format

### Installation
```bash
git clone <your-repo>
cd annotation_quality_pipeline
pip install -r requirements.txt
```

### Basic Setup
```bash
# 1. Set up the pipeline structure
python scripts/setup_pipeline.py

# 2. Create annotation assignments (who annotates what)
python scripts/create_assignments.py --num-annotators 7 --overlap-ratio 0.2

# 3. Run quality checks
python scripts/run_quality_check.py

# 4. Generate reports
python scripts/generate_reports.py
```

## 🔄 Workflow Overview

### Phase 1: Calibration (First Week)
```
Your Pipeline → Extracts frames/annotations → Golden Dataset (50 videos)
                                              ↓
All 7 annotators work on same 50 videos → Quality Pipeline analyzes agreement
                                              ↓
Generate calibration report → Update annotation guidelines
```

### Phase 2: Production with Overlap (Main Work)
```
Your Pipeline → Produces annotation assignments
                ↓
Quality Pipeline → Assigns 20% videos to 3 annotators (overlap)
                → Assigns 80% videos to 1 annotator (unique)
                ↓
Annotators work → Quality Pipeline monitors agreement
                ↓
Generate weekly quality reports
```

### Phase 3: Final Quality Check
```
All annotations complete → Quality Pipeline final analysis
                        ↓
Generate conference-ready quality report
```

## 📊 Input Format

Your annotation CSV files should look like this:
```csv
video_name,timestamp,x1,y1,x2,y2,action_label,person_id
video_001,1.0,0.911,0.592,0.931,0.667,1,0
video_001,1.0,0.911,0.592,0.931,0.667,7,0
video_001,2.0,0.525,0.608,0.552,0.739,1,1
```

Place them in:
```
data/annotations/raw_annotations/
├── annotator_1/
│   ├── batch_001.csv
│   └── batch_002.csv
├── annotator_2/
│   └── ...
```

## 🎯 Key Quality Metrics

### 1. **Spatial IoU (Intersection over Union)**
- Measures how well bounding boxes overlap
- **Good**: > 0.8 (80% overlap)
- **Excellent**: > 0.9 (90% overlap)

### 2. **Temporal IoU** 
- Measures agreement on action timing
- **Good**: > 0.75 (75% time overlap)
- **Excellent**: > 0.85 (85% time overlap)

### 3. **Fleiss' Kappa**
- Measures agreement on action labels
- **Good**: > 0.7 (70% better than chance)
- **Excellent**: > 0.8 (80% better than chance)

## 🚨 Quality Alerts

The pipeline automatically flags:
- **Low IoU samples**: Bounding boxes don't match well
- **Low Kappa samples**: Annotators disagree on action labels
- **Outlier annotators**: Someone consistently different from others
- **Problematic videos**: Certain videos cause lots of disagreement

## 📈 Monitoring Dashboard

Access real-time quality metrics:
```bash
python src/monitoring/dashboard.py
```

View in browser: `http://localhost:8050`

Dashboard shows:
- Live agreement scores per annotator
- Progress tracking
- Flagged samples requiring review
- Quality trends over time

## 📋 Daily Workflow for Annotators

### For Annotators:
1. Check assignment file: `data/assignments/annotator_X_assignments.csv`
2. Annotate assigned videos using CVAT
3. Export annotations to: `data/annotations/raw_annotations/annotator_X/`
4. Check quality dashboard for feedback

### For Quality Manager (You):
1. Run daily quality check: `python scripts/run_quality_check.py`
2. Review flagged samples in dashboard
3. Update annotation guidelines if needed
4. Generate weekly reports: `python scripts/generate_reports.py`

## 📊 Reports Generated

### Daily Reports
- Agreement scores per annotator
- Flagged samples needing review
- Progress updates

### Weekly Reports  
- Quality trends analysis
- Annotator performance comparison
- Guideline update recommendations

### Final Conference Report
- Overall dataset quality metrics
- Statistical significance tests
- Comparison with benchmark datasets

## 🛠️ Configuration

```yaml
quality_thresholds:
  spatial_iou: 0.8
  temporal_iou: 0.75
  fleiss_kappa: 0.7

overlap_settings:
  overlap_ratio: 0.2      # 20% of videos get multiple annotators
  annotators_per_overlap: 3

monitoring:
  dashboard_port: 8050
  alert_email: your-email@domain.com
```

## 🔧 Troubleshooting

### Common Issues:

**"Low agreement scores"**
- Check if annotation guidelines are clear
- Run calibration session with problematic annotators
- Review flagged samples manually

**"Missing annotation files"**
- Ensure annotators export to correct directories
- Check file naming conventions
- Verify CSV format matches expected schema

**"Dashboard not loading"**
- Check if port 8050 is available
- Ensure all dependencies installed
- Check logs in `logs/dashboard.log`

## 🎓 For Quality report

Generate final quality report:
```bash
python scripts/generate_reports.py --final-report --include-statistics
```

This creates a comprehensive report with:
- Inter-annotator agreement statistics
- Quality validation methodology
- Comparison with standard benchmarks
- Confidence intervals and significance tests


## 🔄 Integration with Your Existing Pipeline

This quality pipeline is designed to work **alongside** your existing video processing pipeline:



```
Your Pipeline:          Quality Pipeline:
Videos → Frames    →    Annotations → Quality Check
     ↓                           ↓
  Sampling           →    Agreement Analysis
     ↓                           ↓
 Annotation Setup   →    Reports & Monitoring
```

The quality pipeline only needs your annotation CSV files - it doesn't interfere with your video processing workflow!

### File structure 
```
annotation_quality_pipeline/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── config.yaml                 # Main configuration file
│   ├── annotation_guidelines.md    # Detailed annotation rules
│   └── quality_thresholds.yaml     # IoU, Kappa thresholds
│
├── data/
│   ├── raw_videos/                 # Original video files
│   │   ├── video_001.mp4
│   │   ├── video_002.mp4
│   │   └── ...
│   │
│   ├── extracted_frames/           # Extracted frames per video
│   │   ├── video_001/
│   │   │   ├── img_00001.jpg       # Frame 1
│   │   │   ├── img_00031.jpg       # Frame 31 (1 sec later @ 30fps)
│   │   │   ├── img_00061.jpg       # Frame 61 (2 sec later @ 30fps)
│   │   │   └── ...
│   │   ├── video_002/
│   │   │   ├── img_00001.jpg
│   │   │   └── ...
│   │   └── ...
│   │
│   ├── annotations/                # All annotation files
│   │   ├── raw_annotations/        # Direct from CVAT/VIA
│   │   │   ├── annotator_1/
│   │   │   │   ├── batch_001.csv
│   │   │   │   ├── batch_002.csv
│   │   │   │   └── ...
│   │   │   ├── annotator_2/
│   │   │   └── ...
│   │   │
│   │   ├── processed_annotations/  # Standardized format
│   │   │   ├── train.csv           # Final training annotations
│   │   │   ├── val.csv             # Validation annotations
│   │   │   ├── test.csv            # Test annotations
│   │   │   └── overlap_samples.csv # Overlap annotations for quality check
│   │   │
│   │   └── golden_dataset/         # Ground truth for calibration
│   │       ├── golden_train.csv
│   │       └── golden_annotations_v1.csv
│   │
│   ├── assignments/                # Who annotates what
│   │   ├── overlap_assignments.csv
│   │   ├── unique_assignments.csv
│   │   └── annotator_workload.csv
│   │
│   └── quality_reports/            # Quality analysis results
│       ├── daily_reports/
│       ├── weekly_reports/
│       └── final_quality_report.pdf
│
├── src/
│   ├── __init__.py
│   │
│   ├── data_preparation/           # OPTIONAL - Only if you need format conversion
│   │   ├── __init__.py
│   │   ├── format_converter.py     # Convert between frame_id and timestamps
│   │   └── dataset_splitter.py     # Split into overlap/unique assignments
│   │
│   ├── annotation_management/
│   │   ├── __init__.py
│   │   ├── assignment_generator.py # Generate annotation assignments
│   │   ├── cvat_integration.py     # CVAT API integration
│   │   ├── annotation_validator.py # Basic format validation
│   │   └── batch_processor.py      # Process annotation batches
│   │
│   ├── quality_control/
│   │   ├── __init__.py
│   │   ├── iou_calculator.py       # Calculate spatial IoU
│   │   ├── temporal_iou.py         # Calculate temporal IoU
│   │   ├── kappa_calculator.py     # Calculate Fleiss' Kappa
│   │   ├── agreement_analyzer.py   # Main quality analysis
│   │   ├── outlier_detector.py     # Detect problematic annotations
│   │   └── quality_reporter.py     # Generate quality reports
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── dashboard.py            # Real-time quality dashboard
│   │   ├── alert_system.py         # Quality threshold alerts
│   │   ├── progress_tracker.py     # Track annotation progress
│   │   └── performance_metrics.py  # Annotator performance tracking
│   │
│   ├── calibration/
│   │   ├── __init__.py
│   │   ├── golden_dataset_creator.py # Create calibration dataset
│   │   ├── calibration_analyzer.py   # Analyze calibration results
│   │   └── guideline_updater.py      # Update annotation guidelines
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py           # File I/O utilities
│       ├── visualization.py        # Plot quality metrics
│       ├── data_loader.py          # Load annotation data
│       └── logger.py               # Logging utilities
│
├── scripts/
│   ├── setup_pipeline.py           # Initial setup script
│   ├── create_assignments.py       # Generate annotation assignments
│   ├── run_quality_check.py        # Run quality analysis
│   ├── generate_reports.py         # Generate quality reports
│   └── export_final_dataset.py     # Export final dataset
│
├── tests/
│   ├── __init__.py
│   ├── test_quality_metrics.py     # Test quality calculations
│   ├── test_data_processing.py     # Test data processing
│   └── test_integration.py         # Integration tests
│
├── notebooks/
│   ├── data_exploration.ipynb      # Explore annotation data
│   ├── quality_analysis.ipynb      # Quality analysis experiments
│   └── visualization.ipynb         # Visualize quality metrics
│
├── docs/
│   ├── setup_guide.md              # Setup instructions
│   ├── annotation_workflow.md      # Annotation workflow
│   ├── quality_pipeline_guide.md   # Quality pipeline usage
│   └── api_documentation.md        # API documentation
│
└── outputs/
    ├── final_dataset/              # Final processed dataset
    │   ├── ava_format/             # AVA-compatible format
    │   │   ├── train.csv
    │   │   ├── val.csv
    │   │   └── test.csv
    │   └── custom_format/          # Your custom format
    │       ├── train.csv
    │       └── val.csv
    │
    ├── quality_reports/            # Generated quality reports
    └── visualizations/             # Quality metric plots
```