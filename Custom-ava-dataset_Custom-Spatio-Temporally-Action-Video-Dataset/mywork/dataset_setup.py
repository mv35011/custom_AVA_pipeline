#!/usr/bin/env python3
"""
Enhanced Dataset Setup Pipeline for Custom Action Recognition
This script provides a complete pipeline for preparing custom action recognition datasets
similar to AVA (Atomic Visual Actions) format.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetSetupPipeline:
    """Complete pipeline for setting up custom action recognition datasets"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.base_dir = Path(self.config.get('base_dir', '.'))
        self.setup_directories()
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from JSON file or use defaults"""
        default_config = {
            'base_dir': '.',
            'input_video_dir': 'input_videos',
            'output_dir': 'dataset',
            'frame_rate': 30,
            'segment_duration': 30,  # seconds
            'skip_start_seconds': 2,
            'skip_end_seconds': 2,
            'person_detection_confidence': 0.5,
            'action_categories': {
                'walking_behavior': ['normal_walk', 'fast_walk', 'slow_walk', 'standing_still', 'jogging'],
                'phone_usage': ['no_phone', 'talking_phone', 'texting', 'taking_photo', 'listening_music'],
                'social_interaction': ['alone', 'talking_companion', 'group_walking', 'greeting_someone'],
                'carrying_items': ['empty_hands', 'shopping_bags', 'backpack', 'briefcase_bag', 'umbrella'],
                'street_behavior': ['sidewalk_walking', 'crossing_street', 'waiting_signal', 'looking_around'],
                'posture_gesture': ['upright_normal', 'looking_down', 'looking_up', 'hands_in_pockets'],
                'clothing_style': ['business_attire', 'casual_wear', 'tourist_style', 'sports_wear'],
                'time_context': ['rush_hour', 'leisure_time', 'shopping_time', 'evening_stroll']
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def setup_directories(self):
        """Create necessary directory structure"""
        dirs = [
            self.base_dir / self.config['output_dir'],
            self.base_dir / self.config['output_dir'] / 'frames',
            self.base_dir / self.config['output_dir'] / 'rawframes',
            self.base_dir / self.config['output_dir'] / 'annotations',
            self.base_dir / self.config['output_dir'] / 'proposals',
            self.base_dir / self.config['output_dir'] / 'intermediate',
            self.base_dir / self.config['output_dir'] / 'intermediate' / 'detections',
            self.base_dir / self.config['output_dir'] / 'intermediate' / 'via_annotations',
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    def process_videos(self):
        """Step 1: Process input videos into segments and extract frames"""
        logger.info("Step 1: Processing videos and extracting frames...")
        
        input_dir = self.base_dir / self.config['input_video_dir']
        if not input_dir.exists():
            logger.error(f"Input video directory not found: {input_dir}")
            return False
            
        video_files = list(input_dir.glob("*.mp4")) + list(input_dir.glob("*.avi")) + list(input_dir.glob("*.mov"))
        
        if not video_files:
            logger.error(f"No video files found in {input_dir}")
            return False
            
        for video_file in video_files:
            self._process_single_video(video_file)
            
        return True
    
    def _process_single_video(self, video_path: Path):
        """Process a single video file"""
        logger.info(f"Processing video: {video_path.name}")
        
        # Get video duration
        duration = self._get_video_duration(video_path)
        if duration is None:
            logger.error(f"Could not get duration for {video_path}")
            return
            
        # Create segments
        segment_duration = self.config['segment_duration']
        num_segments = max(1, int(duration // segment_duration))
        
        for segment_id in range(num_segments):
            start_time = segment_id * segment_duration
            end_time = min((segment_id + 1) * segment_duration, duration)
            
            # Skip if segment is too short
            if end_time - start_time < 5:
                continue
                
            self._extract_video_segment(video_path, segment_id, start_time, end_time)
            self._extract_frames_from_segment(segment_id)
    
    def _get_video_duration(self, video_path: Path) -> Optional[float]:
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Error getting video duration: {e}")
            return None
    
    def _extract_video_segment(self, video_path: Path, segment_id: int, start_time: float, end_time: float):
        """Extract a segment from the video"""
        output_path = self.base_dir / self.config['output_dir'] / 'intermediate' / f'{segment_id}.mp4'
        
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c', 'copy',
            '-y', str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted segment {segment_id}: {start_time:.1f}s - {end_time:.1f}s")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting segment {segment_id}: {e}")
    
    def _extract_frames_from_segment(self, segment_id: int):
        """Extract frames from a video segment"""
        segment_path = self.base_dir / self.config['output_dir'] / 'intermediate' / f'{segment_id}.mp4'
        frames_dir = self.base_dir / self.config['output_dir'] / 'frames' / str(segment_id)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        frame_rate = self.config['frame_rate']
        output_pattern = str(frames_dir / f'{segment_id}_%06d.jpg')
        
        cmd = [
            'ffmpeg', '-i', str(segment_path),
            '-r', str(frame_rate),
            '-q:v', '1',
            '-y', output_pattern
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted frames for segment {segment_id}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting frames for segment {segment_id}: {e}")
    
    def run_person_detection(self):
        """Step 2: Run person detection on extracted frames"""
        logger.info("Step 2: Running person detection...")
        
        frames_dir = self.base_dir / self.config['output_dir'] / 'frames'
        detections_dir = self.base_dir / self.config['output_dir'] / 'intermediate' / 'detections'
        
        # Run YOLOv5 detection
        cmd = [
            'python', 'yolov5/detect.py',
            '--source', str(frames_dir),
            '--weights', 'yolov5s.pt',
            '--conf', str(self.config['person_detection_confidence']),
            '--save-txt',
            '--save-conf',
            '--project', str(detections_dir),
            '--name', 'yolo_detections'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info("Person detection completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error in person detection: {e}")
            return False
    
    def generate_proposals(self):
        """Step 3: Generate dense proposals from detections"""
        logger.info("Step 3: Generating dense proposals...")
        
        detections_dir = self.base_dir / self.config['output_dir'] / 'intermediate' / 'detections' / 'yolo_detections' / 'labels'
        proposals_dir = self.base_dir / self.config['output_dir'] / 'proposals'
        
        # Import and use the existing proposal generation logic
        from dense_proposals_train import process_label_directory
        
        results = process_label_directory(str(detections_dir))
        
        # Save proposals
        train_proposals_path = proposals_dir / 'dense_proposals_train.pkl'
        val_proposals_path = proposals_dir / 'dense_proposals_val.pkl'
        
        import pickle
        with open(train_proposals_path, 'wb') as f:
            pickle.dump(results, f)
        with open(val_proposals_path, 'wb') as f:
            pickle.dump(results, f)
            
        logger.info(f"Generated proposals: {len(results)} entries")
        return True
    
    def create_annotation_templates(self):
        """Step 4: Create annotation templates for VIA3"""
        logger.info("Step 4: Creating annotation templates...")
        
        via_dir = self.base_dir / self.config['output_dir'] / 'intermediate' / 'via_annotations'
        
        # Create action categories mapping
        action_mapping = {}
        action_id = 0
        
        for category, actions in self.config['action_categories'].items():
            for action in actions:
                action_mapping[action] = action_id
                action_id += 1
        
        # Save action mapping
        mapping_path = self.base_dir / self.config['output_dir'] / 'annotations' / 'action_mapping.json'
        with open(mapping_path, 'w') as f:
            json.dump(action_mapping, f, indent=2)
        
        # Create VIA3 templates for each segment
        frames_dir = self.base_dir / self.config['output_dir'] / 'frames'
        proposals_path = self.base_dir / self.config['output_dir'] / 'proposals' / 'dense_proposals_train.pkl'
        
        # Import and use existing VIA3 conversion logic
        from dense_proposals_train_to_via import process_video_annotations
        
        import pickle
        with open(proposals_path, 'rb') as f:
            proposals = pickle.load(f)
        
        for video_name in proposals.keys():
            video_info = {k: v for k, v in proposals.items() if k.startswith(video_name)}
            process_video_annotations(video_name, video_info, str(via_dir), action_mapping)
        
        logger.info("Annotation templates created")
        return True
    
    def create_final_annotations(self):
        """Step 5: Create final annotation files"""
        logger.info("Step 5: Creating final annotation files...")
        
        via_dir = self.base_dir / self.config['output_dir'] / 'intermediate' / 'via_annotations'
        annotations_dir = self.base_dir / self.config['output_dir'] / 'annotations'
        
        # Import and use existing annotation extraction logic
        from json_extract_cumulative import process_json_file
        
        # Process all VIA3 JSON files
        json_files = list(via_dir.glob("*_finish.json"))
        
        for json_file in json_files:
            process_json_file(str(json_file))
        
        # Create final CSV files
        self._create_final_csv_files()
        
        # Create action list file
        self._create_action_list_file()
        
        logger.info("Final annotations created")
        return True
    
    def _create_final_csv_files(self):
        """Create final train/val CSV files"""
        # This would use the existing logic from train.py and train_temp.py
        pass
    
    def _create_action_list_file(self):
        """Create action_list.pbtxt file"""
        action_list_path = self.base_dir / self.config['output_dir'] / 'annotations' / 'action_list.pbtxt'
        
        with open(action_list_path, 'w') as f:
            action_id = 0
            for category, actions in self.config['action_categories'].items():
                f.write(f"# {category.replace('_', ' ').title()}\n")
                for action in actions:
                    f.write(f"item {{\n")
                    f.write(f"  name: \"{action}\"\n")
                    f.write(f"  id: {action_id}\n")
                    f.write(f"}}\n")
                    action_id += 1
    
    def run_complete_pipeline(self):
        """Run the complete dataset preparation pipeline"""
        logger.info("Starting complete dataset preparation pipeline...")
        
        steps = [
            ("Video Processing", self.process_videos),
            ("Person Detection", self.run_person_detection),
            ("Proposal Generation", self.generate_proposals),
            ("Annotation Templates", self.create_annotation_templates),
            ("Final Annotations", self.create_final_annotations)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Running step: {step_name}")
            if not step_func():
                logger.error(f"Pipeline failed at step: {step_name}")
                return False
        
        logger.info("Dataset preparation pipeline completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Custom Action Recognition Dataset Setup Pipeline")
    parser.add_argument('--config', type=str, help='Path to configuration JSON file')
    parser.add_argument('--step', type=str, choices=['all', 'videos', 'detection', 'proposals', 'templates', 'annotations'],
                       default='all', help='Which step to run')
    
    args = parser.parse_args()
    
    pipeline = DatasetSetupPipeline(args.config)
    
    if args.step == 'all':
        pipeline.run_complete_pipeline()
    elif args.step == 'videos':
        pipeline.process_videos()
    elif args.step == 'detection':
        pipeline.run_person_detection()
    elif args.step == 'proposals':
        pipeline.generate_proposals()
    elif args.step == 'templates':
        pipeline.create_annotation_templates()
    elif args.step == 'annotations':
        pipeline.create_final_annotations()

if __name__ == "__main__":
    main()
