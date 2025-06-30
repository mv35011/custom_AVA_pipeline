#!/usr/bin/env python3
"""
Quality Validation Module for Existing Pipeline
Adds validation capabilities to your working codebase
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

class DatasetValidator:
    """Lightweight validator for your existing pipeline"""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
    
    def validate_proposals(self) -> Dict:
        """Validate proposal files"""
        results = {
            "proposal_files": {},
            "coordinate_ranges": {},
            "detection_counts": {}
        }
        
        proposal_files = ['dense_proposals_train.pkl', 'dense_proposals_val.pkl']
        proposals_dir = self.dataset_path / 'annotations'
        
        for file_name in proposal_files:
            file_path = proposals_dir / file_name
            if file_path.exists():
                try:
                    import pickle
                    with open(file_path, 'rb') as f:
                        proposals = pickle.load(f)
                    
                    results["proposal_files"][file_name] = {
                        "exists": True,
                        "entries": len(proposals),
                        "size_mb": file_path.stat().st_size / (1024*1024)
                    }
                    
                    # Validate coordinates
                    coord_issues = 0
                    total_detections = 0
                    for key, detections in proposals.items():
                        total_detections += len(detections)
                        for detection in detections:
                            if len(detection) >= 4:
                                x1, y1, x2, y2 = detection[:4]
                                if not (0 <= x1 <= 1 and 0 <= y1 <= 1 and 0 <= x2 <= 1 and 0 <= y2 <= 1):
                                    coord_issues += 1
                    
                    results["coordinate_ranges"][file_name] = {
                        "total_detections": total_detections,
                        "coordinate_issues": coord_issues
                    }
                    
                except Exception as e:
                    results["proposal_files"][file_name] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                results["proposal_files"][file_name] = {"exists": False}
        
        return results
    
    def validate_annotations(self) -> Dict:
        """Validate annotation CSV files"""
        results = {
            "csv_files": {},
            "action_distribution": {},
            "format_issues": []
        }
        
        csv_files = ['train.csv', 'val.csv']
        annotations_dir = self.dataset_path / 'annotations'
        
        for file_name in csv_files:
            file_path = annotations_dir / file_name
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    results["csv_files"][file_name] = {
                        "exists": True,
                        "rows": len(df),
                        "columns": len(df.columns)
                    }
                    
                    # Check action distribution
                    if len(df.columns) >= 7:
                        action_counts = df.iloc[:, 6].value_counts()
                        results["action_distribution"][file_name] = action_counts.to_dict()
                    
                    # Check format issues
                    if len(df.columns) < 7:
                        results["format_issues"].append(f"{file_name}: Insufficient columns")
                    
                except Exception as e:
                    results["csv_files"][file_name] = {
                        "exists": True,
                        "error": str(e)
                    }
            else:
                results["csv_files"][file_name] = {"exists": False}
        
        return results
    
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        report = {
            "proposals": self.validate_proposals(),
            "annotations": self.validate_annotations(),
            "summary": {}
        }
        
        # Generate summary
        proposal_status = all(
            info.get("exists", False) and "error" not in info 
            for info in report["proposals"]["proposal_files"].values()
        )
        
        annotation_status = all(
            info.get("exists", False) and "error" not in info 
            for info in report["annotations"]["csv_files"].values()
        )
        
        report["summary"] = {
            "proposals_valid": proposal_status,
            "annotations_valid": annotation_status,
            "overall_valid": proposal_status and annotation_status
        }
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset Quality Validator")
    parser.add_argument('--dataset_path', type=str, required=True, help='Path to dataset directory')
    parser.add_argument('--output', type=str, default='validation_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    validator = DatasetValidator(args.dataset_path)
    report = validator.generate_report()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("Dataset Validation Report")
    print("=" * 40)
    print(f"Proposals Valid: {report['summary']['proposals_valid']}")
    print(f"Annotations Valid: {report['summary']['annotations_valid']}")
    print(f"Overall Valid: {report['summary']['overall_valid']}")
    print(f"\nDetailed report saved to: {args.output}")

if __name__ == "__main__":
    main() 