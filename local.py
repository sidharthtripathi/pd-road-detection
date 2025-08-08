from ultralytics import YOLO
import cv2
import os
from pathlib import Path

class SimpleRoadDefectDetector:
    def __init__(self, model_path: str = 'yolo-pd.pt'):
        self.model = YOLO(model_path)
        
        # class mappings
        self.defect_classes = {
            0: 'Longitudinal Crack', 
            1: 'Transverse Crack', 
            2: 'Alligator Crack', 
            3: 'Potholes'
        }
        
        # Colors for visualization
        self.colors = {
            'Longitudinal Crack': (0, 255, 0),
            'Transverse Crack': (255, 0, 0),
            'Alligator Crack': (0, 0, 255),
            'Potholes': (255, 0, 255)
        }
    
    def draw_detections(self, image, results):
        annotated_image = image.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    bbox = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    defect_type = self.defect_classes.get(class_id, "Unknown")
                    color = self.colors.get(defect_type, (255, 255, 255))
                    
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # Draw box
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label
                    label = f"{defect_type} {confidence:.2f}"
                    cv2.putText(annotated_image, label, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated_image
    
    def process_image(self, image_path: str, output_path: str = None):
        print(f"Processing image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return None
        
        # Run detection
        results = self.model(image, verbose=False)
        
        # Check if any detections
        has_detections = False
        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                has_detections = True
                break
        
        if has_detections:
            print(f"✓ Defects detected in {image_path}")
            annotated_image = self.draw_detections(image, results)
            
            # Save if output path provided
            if output_path:
                cv2.imwrite(output_path, annotated_image)
                print(f"Saved to: {output_path}")
            
            return annotated_image
        else:
            print(f"✗ No defects found in {image_path}")
            return None
    
    def process_video(self, video_path: str, output_dir: str = None):
        print(f"Processing video: {video_path}")
        
        # Create output directory
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        frames_with_detections = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            results = self.model(frame, verbose=False)
            
            # Check for detections
            has_detections = False
            for result in results:
                if result.boxes is not None and len(result.boxes) > 0:
                    has_detections = True
                    break
            
            if has_detections:
                print(f"✓ Defects found in frame {frame_count}")
                annotated_frame = self.draw_detections(frame, results)
                
                # Save frame if output directory provided
                if output_dir:
                    output_path = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
                    cv2.imwrite(output_path, annotated_frame)
                
                frames_with_detections += 1
                yield {
                    'frame_number': frame_count,
                    'frame': annotated_frame,
                    'saved_path': output_path if output_dir else None
                }
            
            frame_count += 1
        
        cap.release()
        print(f"Video processing complete: {frames_with_detections}/{frame_count} frames had defects")
    
    def process_stream(self, source=0, save_dir: str = None):
        print(f"Starting stream from source: {source}")
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(source)
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                
                # Run detection
                results = self.model(frame, verbose=False)
                
                # Check for detections
                has_detections = False
                for result in results:
                    if result.boxes is not None and len(result.boxes) > 0:
                        has_detections = True
                        break
                
                if has_detections:
                    print(f"✓ Stream defects detected at frame {frame_count}")
                    annotated_frame = self.draw_detections(frame, results)
                    
                    # Save frame if directory provided
                    saved_path = None
                    if save_dir:
                        saved_path = os.path.join(save_dir, f"stream_frame_{frame_count:06d}.jpg")
                        cv2.imwrite(saved_path, annotated_frame)
                    
                    yield {
                        'frame_number': frame_count,
                        'frame': annotated_frame,
                        'saved_path': saved_path
                    }
                
                frame_count += 1
                
        except KeyboardInterrupt:
            print("Stream stopped by user")
        finally:
            cap.release()
            print(f"Stream ended. Total frames processed: {frame_count}")


# Initialize detector
rdd = SimpleRoadDefectDetector()

# rdd.process_image("./assets/pothole.webp","output.webp")

video_path = "./assets/demo.mp4"

for frame_data in rdd.process_video(video_path, "./video"):
    print(f"  Frame {frame_data['frame_number']}: Saved to {frame_data['saved_path']}")