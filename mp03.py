import cv2
import numpy as np
import time
from yoach_ai.pose_visualizer import PoseVisualizer
from yoach_ai.video_recorder import VideoRecorder
from yoach_ai.camera_handler import CameraHandler  # Use your existing camera handler

def main():
    try:
        # Initialize components
        camera = CameraHandler(camera_id=1)
        visualizer = PoseVisualizer()
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
            
            # Calculate FPS
            fps_counter += 1
            if (time.time() - fps_start_time) > fps_update_interval:
                fps = fps_counter / (time.time() - fps_start_time)
                fps_counter = 0
                fps_start_time = time.time()
            
            # Process frame
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