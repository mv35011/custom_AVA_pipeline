
## Quality Validation

### Install the dependencies
```bash
pip install -r requirements.txt
```
#### Now there might be some numpy and pytorch gpu issues so run these(Dont run the installation from other readme if this is run)
```bash
pip install opencv-python-headless==4.11.0.86

# Uninstall existing PyTorch (if any)
pip uninstall torch torchvision torchaudio

# Install PyTorch with CUDA support
pip install torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install numpy==1.26.4
```

### Run Quality Check
```bash
python mywork/quality_check.py --dataset_path dataset --visualize
```

### Check Report
The quality checker validates:
- File structure integrity
- Frame quality and consistency
- Annotation quality and format
- Action class distribution
- Temporal consistency
- Bounding box quality
- Person tracking consistency

### Common Issues and Solutions

#### 1. Imbalanced Action Classes
**Issue**: Some action classes have very few annotations
**Solution**: 
- Collect more data for underrepresented classes
- Use data augmentation techniques
- Consider class weighting in training

#### 2. Invalid Bounding Boxes
**Issue**: Bounding boxes with invalid coordinates
**Solution**:
- Review annotation guidelines
- Use coordinate validation in annotation tools
- Implement automatic coordinate clamping

#### 3. Temporal Gaps
**Issue**: Large gaps in frame sequences
**Solution**:
- Check video processing pipeline
- Ensure consistent frame extraction
- Validate temporal annotations

## Customization

### Adding New Action Categories
1. Edit `configs/dataset_config.json`
2. Add new category to `action_categories`
3. Define action names for the category
4. Re-run annotation template generation

### Modifying Processing Parameters
- `frame_rate`: Change frame extraction rate
- `segment_duration`: Modify video segment length
- `person_detection_confidence`: Adjust detection threshold
- `skip_start_seconds`/`skip_end_seconds`: Modify temporal trimming

### Custom Annotation Tools
The pipeline supports VIA3 by default, but can be extended for:
- CVAT integration
- Labelbox integration
- Custom annotation interfaces

## Troubleshooting

### Common Errors

#### FFmpeg Not Found
```bash
# Install FFmpeg
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

#### CUDA/GPU Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CPU-only version if needed
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### Memory Issues
- Reduce batch size in detection
- Process videos in smaller segments
- Use lower resolution frames

### Performance Optimization

#### For Large Datasets
- Use multi-GPU processing
- Implement parallel video processing
- Use SSD storage for faster I/O

#### For Real-time Processing
- Reduce frame rate
- Use smaller detection models
- Implement streaming processing

## Integration with Training

### MMAction2 Integration
```bash
# Copy dataset to MMAction2 format
cp -r dataset/* /path/to/mmaction2/data/ava/

# Update config files
# Modify num_classes in model config
# Update data paths in dataset config
```

### Custom Training
```python
# Load dataset
from mmaction.datasets import AVADataset
dataset = AVADataset(
    ann_file='annotations/train.csv',
    pipeline=train_pipeline,
    data_prefix='rawframes/'
)
```

## Next Steps

1. **Benchmark Testing**: Test the pipeline with existing models
2. **Custom Dataset Creation**: Create your own action recognition dataset
3. **Model Training**: Train custom models on your dataset
4. **UI Tool Development**: Integrate CVAT with quality checks
5. **Deployment**: Deploy the complete pipeline for production use

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review quality check reports
3. Validate configuration files
4. Check log files for detailed error messages