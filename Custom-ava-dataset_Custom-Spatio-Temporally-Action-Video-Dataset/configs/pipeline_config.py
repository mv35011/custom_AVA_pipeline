#!/usr/bin/env python3
"""
Configuration Management for Existing Pipeline
Simple configuration system for your working codebase
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class PipelineConfig:
    """Simple configuration manager for your pipeline"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_default_config()
        if config_path and os.path.exists(config_path):
            self._load_user_config(config_path)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "video_processing": {
                "frame_rate": 30,
                "segment_duration": 30,
                "skip_start_seconds": 2,
                "skip_end_seconds": 2
            },
            "detection": {
                "confidence_threshold": 0.5,
                "model": "yolov5s.pt"
            },
            "proposals": {
                "output_format": "pkl",
                "coordinate_normalization": True
            },
            "annotation": {
                "via3_template": True,
                "action_categories": {
                    "walking_behavior": ["normal_walk", "fast_walk", "slow_walk"],
                    "phone_usage": ["no_phone", "talking_phone", "texting"],
                    "social_interaction": ["alone", "talking_companion", "group_walking"]
                }
            }
        }
    
    def _load_user_config(self, config_path: str):
        """Load user configuration and merge with defaults"""
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        # Deep merge configuration
        self._merge_config(self.config, user_config)
    
    def _merge_config(self, base: Dict, update: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default=None) -> Any:
        """Get configuration value by dot-separated path"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def save(self, output_path: str):
        """Save current configuration to file"""
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def print_summary(self):
        """Print configuration summary"""
        print("Pipeline Configuration Summary")
        print("=" * 40)
        print(f"Frame Rate: {self.get('video_processing.frame_rate')}")
        print(f"Segment Duration: {self.get('video_processing.segment_duration')}s")
        print(f"Detection Confidence: {self.get('detection.confidence_threshold')}")
        print(f"Action Categories: {len(self.get('annotation.action_categories', {}))}")

# Global configuration instance
config = PipelineConfig()

def get_config() -> PipelineConfig:
    """Get global configuration instance"""
    return config 