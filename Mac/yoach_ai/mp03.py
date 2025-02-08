import cv2
import numpy as np
import time
from yoach_ai.pose_visualizer import PoseVisualizer
from yoach_ai.video_recorder import VideoRecorder
from yoach_ai.camera_handler import CameraHandler  # Use your existing camera handler

class PoseVisualizer:
    def __init__(self, smoothing_factor=0.5):
        self.previous_landmarks = None
        self.smoothing_factor = smoothing_factor
        
    def smooth_landmarks(self, current_landmarks):
        if self.previous_landmarks is None:
            self.previous_landmarks = current_landmarks
            return current_landmarks
            
        smoothed = []
        for prev, curr in zip(self.previous_landmarks, current_landmarks):
            smoothed_x = prev.x * (1 - self.smoothing_factor) + curr.x * self.smoothing_factor
            smoothed_y = prev.y * (1 - self.smoothing_factor) + curr.y * self.smoothing_factor
            smoothed_z = prev.z * (1 - self.smoothing_factor) + curr.z * self.smoothing_factor
            smoothed.append(PoseLandmark(x=smoothed_x, y=smoothed_y, z=smoothed_z))
            
        self.previous_landmarks = smoothed
        return smoothed
        
    def process_frame(self, frame):
        results = super().process_frame(frame)
        if results.pose_landmarks:
            results.pose_landmarks.landmark = self.smooth_landmarks(results.pose_landmarks.landmark)
        return results

def main():
    try:
        # Initialize components
        camera = CameraHandler(camera_id=1)
        visualizer = PoseVisualizer(
            min_detection_confidence=0.7,  # Default is 0.5
            min_tracking_confidence=0.7,   # Default is 0.5
            model_complexity=2             # Use the most accurate model (0, 1, or 2)
        )
        recorder = VideoRecorder()
        
        # Add FPS calculation variables
        fps_start_time = time.time()
        fps_counter = 0
        fps = 0
        fps_update_interval = 0.5  # Update FPS every 0.5 seconds
        
        print("Camera initialized. Press:")
        print("'q' - quit")
        print("'r' - reset camera")
        print("'v' - start/stop recording")
        print("'c' - clear trajectory")
        print("Raise left hand above shoulder to stop recording and exit")
        
        frame_count = 0
        while True:
            # Get frame
            ret, frame = camera.read_frame()
            if not ret:
                print(f"Failed to grab frame {frame_count}")
                camera.reset()
                continue
            
            # Add preprocessing steps
            # 1. Resize frame to optimal size (not too small, not too large)
            height, width = frame.shape[:2]
            if width > 1280:  # Limit max width while maintaining aspect ratio
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
                
            # 2. Apply subtle smoothing to reduce noise
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            
            # 3. Adjust brightness and contrast if needed
            alpha = 1.2  # Contrast control (1.0-3.0)
            beta = 10    # Brightness control (0-100)
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
            
            # Calculate FPS
            fps_counter += 1
            if (time.time() - fps_start_time) > fps_update_interval:
                fps = fps_counter / (time.time() - fps_start_time)
                fps_counter = 0
                fps_start_time = time.time()
            
            # Process frame with improved image
            results = visualizer.process_frame(frame)
            
            # Check for left hand raise to stop
            if results.pose_world_landmarks and visualizer.is_left_hand_raised():
                print("Left hand raised - stopping recording and exiting...")
                if recorder.is_recording:
                    recorder.stop_recording()
                break
            
            # Create visualizations
            frame_2d = frame.copy()
            if results.pose_landmarks:
                frame_2d = visualizer.draw_2d_pose(frame_2d, results)
                frame_3d = visualizer.visualize_3d_pose(results)
                if frame_3d is not None:
                    target_height = frame_2d.shape[0]
                    target_width = int(target_height * frame_3d.shape[1] / frame_3d.shape[0])
                    frame_3d = cv2.resize(frame_3d, (target_width, target_height))
                    
                    # Draw status indicators
                    frame_2d = visualizer.draw_status_indicator(frame_2d)
                    frame_3d = visualizer.draw_status_indicator(frame_3d)
                else:
                    frame_3d = np.zeros((frame_2d.shape[0], frame_2d.shape[0], 3), dtype=np.uint8)
            else:
                frame_3d = np.zeros((frame_2d.shape[0], frame_2d.shape[0], 3), dtype=np.uint8)
            
            # Combine frames
            combined_frame = np.hstack([frame_2d, frame_3d])
            
            # Add FPS text to combined frame
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(combined_frame, fps_text, (10, combined_frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add lighting quality check
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Draw lighting status
            lighting_status = "Lighting: "
            if brightness < 50:
                lighting_status += "Too Dark"
                color = (0, 0, 255)  # Red
            elif brightness > 200:
                lighting_status += "Too Bright"
                color = (0, 0, 255)  # Red
            else:
                lighting_status += "Good"
                color = (0, 255, 0)  # Green
                
            cv2.putText(combined_frame, lighting_status, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Add contrast warning
            if contrast < 20:
                cv2.putText(combined_frame, "Low Contrast", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Handle recording
            if recorder.is_recording:
                recorder.write_frame(combined_frame, results)
            
            combined_frame = recorder.add_recording_indicator(combined_frame)
            
            # Display frame
            cv2.imshow('MediaPipe Pose (2D and 3D)', combined_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                camera.reset()
            elif key == ord('v'):
                if not recorder.is_recording:
                    visualizer.clear_trajectory()  # Clear trajectory when starting new recording
                    recorder.start_recording(combined_frame.shape, camera.get_fps())
                else:
                    recorder.stop_recording()
            elif key == ord('c'):
                visualizer.clear_trajectory()  # Clear trajectory manually
            
            frame_count += 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        camera.cleanup()
        visualizer.cleanup()
        recorder.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()