from ultralytics import YOLO
import cv2
import numpy as np
import requests

# Download and load image
def load_image_from_url(url):
    response = requests.get(url)
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

# Load model with correct format
model = YOLO("yolo11n-obb.pt")  # Use yolov8n-obb.pt for OBB detection

# Load image
image_url = "https://ultralytics.com/images/boats.jpg"
image = load_image_from_url(image_url)

# Run prediction
results = model(image)

# Visualize results
for r in results:
    # Create a copy of the image for visualization
    im_vis = image.copy()
    
    # Access OBB results directly
    if hasattr(r, 'obb') and r.obb is not None:
        obb = r.obb
        
        # Get box data in corner point format
        boxes = obb.xywhr.cpu().numpy()  # Get boxes in xywhr format
        conf = obb.conf.cpu().numpy()
        cls = obb.cls.cpu().numpy()
        
        # Draw each detection
        for i, box in enumerate(boxes):
            # Get center, width, height, and rotation
            x, y, w, h, angle = box
            
            # Convert angle from radians to degrees
            angle_deg = angle * 180 / np.pi
            
            # Create rotated rectangle
            rect = ((x, y), (w, h), angle_deg)
            points = cv2.boxPoints(rect).astype(np.int32)
            
            # Get class info
            confidence = conf[i]
            class_id = int(cls[i])
            class_name = r.names[class_id]
            
            # Draw oriented box
            cv2.polylines(im_vis, [points], True, (0, 255, 255), 2)
            
            # Fill with semi-transparent color
            overlay = im_vis.copy()
            cv2.fillPoly(overlay, [points], (0, 255, 255))
            cv2.addWeighted(overlay, 0.2, im_vis, 0.8, 0, im_vis)
            
            # Add text with class name, confidence and angle
            text = f"{class_name} {confidence:.2f} {angle_deg:.1f}°"
            cv2.putText(im_vis, text, 
                      (points[0][0], points[0][1] - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Draw orientation arrow
            center = (int(x), int(y))
            end_point = (
                int(x + 50 * np.cos(angle)),
                int(y + 50 * np.sin(angle))
            )
            cv2.arrowedLine(im_vis, center, end_point, (0, 0, 255), 2)
            
            print(f"Detected {class_name} with confidence {confidence:.2f} at angle {angle_deg:.1f}°")

    # Show results
    cv2.imshow("OBB Detections", im_vis)
    cv2.waitKey(0)
    
    # Save results
    cv2.imwrite("obb_detections.jpg", im_vis)

cv2.destroyAllWindows()