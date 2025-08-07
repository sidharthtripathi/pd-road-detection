from ultralytics import YOLO
import json
import cv2
from datetime import datetime
from typing import List, Dict
import numpy as np

class RoadDefectDetector:
    def __init__(self, model_path: str = 'yolo-pd.pt'):

        self.model = YOLO(model_path)
        
        # class mappings
        self.defect_classes = {0: 'Longitudinal Crack', 1: 'Transverse Crack', 2: 'Alligator Crack', 3: 'Potholes'}
        
        # Severity levels based on size/area
        self.severity_thresholds = {
            "low": 1000,    
            "medium": 5000, 
            "high": 15000   
        }
    
    def calculate_severity(self, bbox: List[float]) -> str:
        x1, y1, x2, y2 = bbox
        area = (x2 - x1) * (y2 - y1)
        
        if area < self.severity_thresholds["low"]:
            return "low"
        elif area < self.severity_thresholds["medium"]:
            return "medium"
        elif area < self.severity_thresholds["high"]:
            return "high"
        else:
            return "critical"
    
    def process_image(self, image_path: str, metadata: Dict = None) -> Dict:
        results = self.model(image_path,verbose=False)
        
        detection_data = {
            "source": image_path,
            "type": "image",
            "metadata": metadata or {},
            "detections": [],
            "summary": {
                "total_defects": 0,
                "defect_counts": {},
                "severity_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0}
            }
        }
        
        # Process detections
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    # Extract detection info
                    bbox = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Get defect type
                    defect_type = self.defect_classes.get(class_id, f"unknown_class_{class_id}")
                    
                    # Calculate severity
                    severity = self.calculate_severity(bbox)
                    
                    # Create detection object
                    detection = {
                        "defect_type": defect_type,
                        "confidence": round(confidence, 3),
                        "bounding_box": {
                            "x1": round(bbox[0], 2),
                            "y1": round(bbox[1], 2), 
                            "x2": round(bbox[2], 2),
                            "y2": round(bbox[3], 2),
                            "width": round(bbox[2] - bbox[0], 2),
                            "height": round(bbox[3] - bbox[1], 2),
                            "area": round((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 2)
                        },
                        "severity": severity,
                    }
                    
                    detection_data["detections"].append(detection)
                    
                    # Update summary
                    detection_data["summary"]["total_defects"] += 1
                    detection_data["summary"]["defect_counts"][defect_type] = detection_data["summary"]["defect_counts"].get(defect_type, 0) + 1
                    detection_data["summary"]["severity_distribution"][severity] += 1
        
        return detection_data
    
    def process_video(self, video_path: str, metadata: Dict = None) -> List[Dict]:

        results = self.model.predict(source=video_path,stream=True,verbose=False)
        video_data = {
            "timestamp": datetime.now().isoformat(),
            "source": video_path,
            "type": "video",
            "frames_results" : []
        }
        frame_idx = 1
        
        for result in results:
            
                frame_data = {
                    "detections": [],
                    "summary": {
                        "total_defects": 0,
                        "defect_counts": {},
                        "severity_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    }
                }
                
                # Process detections for this frame
                if result.boxes is not None:
                    for box in result.boxes:
                        bbox = box.xyxy[0].cpu().numpy().tolist()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        defect_type = self.defect_classes.get(class_id, f"unknown_class_{class_id}")
                        severity = self.calculate_severity(bbox)
                        
                        detection = {
                            "defect_type": defect_type,
                            "confidence": round(confidence, 3),
                            "bounding_box": {
                                "x1": round(bbox[0], 2),
                                "y1": round(bbox[1], 2),
                                "x2": round(bbox[2], 2),
                                "y2": round(bbox[3], 2),
                                "width": round(bbox[2] - bbox[0], 2),
                                "height": round(bbox[3] - bbox[1], 2),
                                "area": round((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 2)
                            },
                            "severity": severity,
                        }
                        
                        frame_data["detections"].append(detection)
                        
                        # Update summary
                        frame_data["summary"]["total_defects"] += 1
                        frame_data["summary"]["defect_counts"][defect_type] = frame_data["summary"]["defect_counts"].get(defect_type, 0) + 1
                        frame_data["summary"]["severity_distribution"][severity] += 1
                
                video_data["frames_results"].append(frame_data)
                frame_idx+=1
        
        return video_data
    
    def process_realtime_stream(self, source=0, metadata: Dict = None):
        """Process real-time camera feed and yield JSON data"""
        cap = cv2.VideoCapture(source)
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Run detection on frame
                results = self.model(frame)
                
                frame_data = {
                    "timestamp": datetime.now().isoformat(),
                    "source": f"camera_{source}",
                    "type": "realtime",
                    "frame_number": frame_count,
                    "metadata": metadata or {},
                    "detections": [],
                    "summary": {
                        "total_defects": 0,
                        "defect_counts": {},
                        "severity_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    }
                }
                
                # Process detections
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            bbox = box.xyxy[0].cpu().numpy().tolist()
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            
                            defect_type = self.defect_classes.get(class_id, f"unknown_class_{class_id}")
                            severity = self.calculate_severity(bbox)
                            
                            detection = {
                                "defect_type": defect_type,
                                "confidence": round(confidence, 3),
                                "bounding_box": {
                                    "x1": round(bbox[0], 2),
                                    "y1": round(bbox[1], 2),
                                    "x2": round(bbox[2], 2),
                                    "y2": round(bbox[3], 2)
                                },
                                "severity": severity
                            }
                            
                            frame_data["detections"].append(detection)
                            frame_data["summary"]["total_defects"] += 1
                            frame_data["summary"]["defect_counts"][defect_type] = \
                                frame_data["summary"]["defect_counts"].get(defect_type, 0) + 1
                            frame_data["summary"]["severity_distribution"][severity] += 1
                
                yield frame_data
                frame_count += 1
                
        finally:
            cap.release()
