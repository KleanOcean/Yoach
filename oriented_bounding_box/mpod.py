import cv2
import mediapipe as mp
import time
import numpy as np

# Initialize MediaPipe Objectron
mp_objectron = mp.solutions.objectron
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize Camera
cap = cv2.VideoCapture(0)

# Configure Objectron
# Try different models: Shoe, Chair, Cup, Camera
with mp_objectron.Objectron(
    static_image_mode=False,
    max_num_objects=5,  # Increased from 2
    min_detection_confidence=0.3,  # Lowered from 0.5 for better detection
    min_tracking_confidence=0.5,  # Lowered from 0.8
    model_name="Cup") as objectron:

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to read camera frame")
            continue

        start = time.time()

        # Convert image and process
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = objectron.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Draw detections
        if results.detected_objects:
            for detected_object in results.detected_objects:
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    image,
                    detected_object.landmarks_2d,
                    mp_objectron.BOX_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
                
                # Draw axes
                mp_drawing.draw_axis(image, detected_object.rotation, detected_object.translation)
                
                # Get and draw center point
                landmarks = np.array([[lm.x, lm.y] for lm in detected_object.landmarks_2d.landmark])
                center = np.mean(landmarks, axis=0)
                center = tuple(map(int, center * [image.shape[1], image.shape[0]]))
                cv2.circle(image, center, 5, (0, 255, 0), -1)

        # Calculate and display FPS
        end = time.time()
        total_time = end - start
        fps = 1 / total_time
        cv2.putText(image, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

        # Add instructions
        cv2.putText(image, "Hold cup vertically in front of camera", (20, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(image, "Press 'q' to quit", (20, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Show image
        cv2.imshow('MediaPipe Objectron', image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()


