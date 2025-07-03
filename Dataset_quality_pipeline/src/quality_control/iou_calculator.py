import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IoUCalculator:
    def __init__(self, min_iou_threshold: float = 0.5):
        self.min_iou_threshold = min_iou_threshold

    def calculate_spatial_iou(self, box1: List[float], box2: List[float]) -> float:
        try:
            x1_1, y1_1, x2_1, y2_1 = box1
            x1_2, y1_2, x2_2, y2_2 = box2

            if not self._is_valid_box(box1) or not self._is_valid_box(box2):
                logger.warning(f"Invalid bounding box: {box1} or {box2}")
                return 0.0
            x1_inter = max(x1_1, x1_2)
            y1_inter = max(y1_1, y1_2)
            x2_inter = min(x2_1, x2_2)
            y2_inter = min(y2_1, y2_2)

            if x1_inter >= x2_inter or y1_inter >= y2_inter:
                return 0.0

            intersection_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
            box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
            box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
            union_area = box1_area + box2_area - intersection_area

            if union_area == 0:
                return 0.0
            iou = intersection_area / union_area
            return max(0.0, min(1.0, iou))

        except Exception as e:
            logger.error(f"Error calculating spatial IoU: {e}")
            return 0.0

    def calculate_temporal_iou(self, time1: List[float], time2: List[float]) -> float:
        try:
            start1, end1 = time1
            start2, end2 = time2
            if start1 >= end1 or start2 >= end2:
                logger.warning(f"Invalid temporal interval: {time1} or {time2}")
                return 0.0
            intersection_start = max(start1, start2)
            intersection_end = min(end1, end2)

            if intersection_start >= intersection_end:
                return 0.0

            intersection_duration = intersection_end - intersection_start
            duration1 = end1 - start1
            duration2 = end2 - start2
            union_duration = duration1 + duration2 - intersection_duration

            if union_duration == 0:
                return 0.0
            tiou = intersection_duration / union_duration
            return max(0.0, min(1.0, tiou))

        except Exception as e:
            logger.error(f"Error calculating temporal IoU: {e}")
            return 0.0

    def calculate_batch_spatial_iou(self, boxes1: List[List[float]],
                                    boxes2: List[List[float]]) -> List[float]:
        if len(boxes1) != len(boxes2):
            logger.warning(f"Mismatched box counts: {len(boxes1)} vs {len(boxes2)}")
            return []
        iou_scores = []
        for box1, box2 in zip(boxes1, boxes2):
            iou = self.calculate_spatial_iou(box1, box2)
            iou_scores.append(iou)

        return iou_scores

    def calculate_annotation_agreement(self, annotations1: pd.DataFrame,
                                       annotations2: pd.DataFrame,
                                       video_name: str = None) -> Dict[str, float]:
        try:
            if video_name:
                annotations1 = annotations1[annotations1['video_name'] == video_name]
                annotations2 = annotations2[annotations2['video_name'] == video_name]
            matches = []
            for _, row1 in annotations1.iterrows():
                mask = (
                        (annotations2['video_name'] == row1['video_name']) &
                        (annotations2['timestamp'] == row1['timestamp']) &
                        (annotations2['person_id'] == row1['person_id'])
                )
                matching_rows = annotations2[mask]
                if len(matching_rows) > 0:
                    row2 = matching_rows.iloc[0]  # Take first match

                    # Calculate spatial IoU
                    box1 = [row1['x1'], row1['y1'], row1['x2'], row1['y2']]
                    box2 = [row2['x1'], row2['y1'], row2['x2'], row2['y2']]
                    spatial_iou = self.calculate_spatial_iou(box1, box2)

                    # Check if action labels match
                    label_match = row1['action_label'] == row2['action_label']

                    matches.append({
                        'video_name': row1['video_name'],
                        'timestamp': row1['timestamp'],
                        'person_id': row1['person_id'],
                        'spatial_iou': spatial_iou,
                        'label_match': label_match,
                        'box1': box1,
                        'box2': box2
                    })
            if not matches:
                logger.warning("No matching annotations found")
                return {
                    'mean_spatial_iou': 0.0,
                    'median_spatial_iou': 0.0,
                    'label_accuracy': 0.0,
                    'total_matches': 0,
                    'high_iou_matches': 0
                }
            iou_scores = [match['spatial_iou'] for match in matches]
            label_matches = [match['label_match'] for match in matches]

            results = {
                'mean_spatial_iou': np.mean(iou_scores),
                'median_spatial_iou': np.median(iou_scores),
                'std_spatial_iou': np.std(iou_scores),
                'label_accuracy': np.mean(label_matches),
                'total_matches': len(matches),
                'high_iou_matches': sum(1 for iou in iou_scores if iou >= self.min_iou_threshold),
                'low_iou_samples': [match for match in matches if match['spatial_iou'] < self.min_iou_threshold]
            }

            logger.info(f"Agreement analysis complete: {results['total_matches']} matches found")
            return results
        except Exception as e:
            logger.error(f"Error calculating annotation agreement: {e}")
            return {}

    def calculate_multi_annotator_iou(self, annotation_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        annotator_names = list(annotation_dict.keys())
        pairwise_results = {}

        for i, annotator1 in enumerate(annotator_names):
            for j, annotator2 in enumerate(annotator_names):
                if i < j:  # Avoid duplicate pairs
                    pair_key = f"{annotator1}_vs_{annotator2}"

                    agreement = self.calculate_annotation_agreement(
                        annotation_dict[annotator1],
                        annotation_dict[annotator2]
                    )

                    pairwise_results[pair_key] = agreement

        return pairwise_results

    def _is_valid_box(self, box: List[float]) -> bool:
        if len(box) != 4:
            return False
        x1, y1, x2, y2 = box
        if not all(isinstance(coord, (int, float)) for coord in box):
            return False
        if x1 >= x2 or y1 >= y2:
            return False
        if not all(0 <= coord <= 1 for coord in box):
            logger.warning(f"Bounding box coordinates outside [0,1]: {box}")
        return True

    def get_problematic_samples(self, annotation_dict: Dict[str, pd.DataFrame],
                                min_iou: float = 0.5) -> List[Dict]:
        problematic_samples = []
        pairwise_results = self.calculate_multi_annotator_iou(annotation_dict)

        for pair_key, results in pairwise_results.items():
            if 'low_iou_samples' in results:
                for sample in results['low_iou_samples']:
                    sample['annotator_pair'] = pair_key
                    sample['needs_review'] = True
                    problematic_samples.append(sample)

        return problematic_samples

def test_iou_calculator():
    """Test the IoU calculator with sample data"""
    calc = IoUCalculator()

    # Test spatial IoU
    print("=== Testing Spatial IoU ===")
    box1 = [0.1, 0.2, 0.5, 0.8]  # x1, y1, x2, y2
    box2 = [0.2, 0.3, 0.6, 0.9]  # Overlapping box
    box3 = [0.7, 0.1, 0.9, 0.3]  # Non-overlapping box

    iou1 = calc.calculate_spatial_iou(box1, box2)
    iou2 = calc.calculate_spatial_iou(box1, box3)

    print(f"IoU between overlapping boxes: {iou1:.3f}")
    print(f"IoU between non-overlapping boxes: {iou2:.3f}")

    # Test temporal IoU
    print("\n=== Testing Temporal IoU ===")
    time1 = [1.0, 5.0]  # 1 to 5 seconds
    time2 = [3.0, 7.0]  # 3 to 7 seconds (overlapping)
    time3 = [6.0, 8.0]  # 6 to 8 seconds (non-overlapping)

    tiou1 = calc.calculate_temporal_iou(time1, time2)
    tiou2 = calc.calculate_temporal_iou(time1, time3)

    print(f"Temporal IoU between overlapping intervals: {tiou1:.3f}")
    print(f"Temporal IoU between non-overlapping intervals: {tiou2:.3f}")

    # Test with sample annotation data
    print("\n=== Testing Annotation Agreement ===")
    # Create sample annotations
    annotations1 = pd.DataFrame({
        'video_name': ['video_001', 'video_001', 'video_002'],
        'timestamp': [1.0, 2.0, 1.0],
        'x1': [0.1, 0.2, 0.3],
        'y1': [0.2, 0.3, 0.4],
        'x2': [0.5, 0.6, 0.7],
        'y2': [0.8, 0.9, 0.8],
        'action_label': [1, 7, 12],
        'person_id': [0, 1, 0]
    })

    annotations2 = pd.DataFrame({
        'video_name': ['video_001', 'video_001', 'video_002'],
        'timestamp': [1.0, 2.0, 1.0],
        'x1': [0.15, 0.25, 0.35],  # Slightly different boxes
        'y1': [0.25, 0.35, 0.45],
        'x2': [0.55, 0.65, 0.75],
        'y2': [0.85, 0.95, 0.85],
        'action_label': [1, 7, 15],  # Different action for last sample
        'person_id': [0, 1, 0]
    })

    agreement = calc.calculate_annotation_agreement(annotations1, annotations2)

    print(f"Mean spatial IoU: {agreement['mean_spatial_iou']:.3f}")
    print(f"Label accuracy: {agreement['label_accuracy']:.3f}")
    print(f"Total matches: {agreement['total_matches']}")
    print(f"High IoU matches: {agreement['high_iou_matches']}")

if __name__ == "__main__":
    test_iou_calculator()