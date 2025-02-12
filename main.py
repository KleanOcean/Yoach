from pose_visualizer import PoseVisualizer
from video_recorder import VideoRecorder
from display_manager import DisplayManager
import cv2
import time
import numpy as np
import platform
import sys

def setup_camera(camera_id=0):
    """Initialize camera with platform-specific settings"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Try to use AVFOUNDATION backend specifically
        cap = cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)
        # Use IPhone camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise Exception("Could not open camera")
            
        # Set Mac-specific camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
    elif system == "Windows":
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            camera_id = 1
            cap = cv2.VideoCapture(camera_id)
            
    if not cap.isOpened():
        raise Exception("Could not open camera")
        
    return cap

def print_instructions():
    """Print usage instructions with platform-specific details"""
    system = platform.system()
    print("Camera initialized. Press:")
    print("'q' - quit")
    print("'r' - reset camera")
    print("'v' - start/stop recording")
    
    if system == "Darwin":  # macOS
        print("'I/K' or Up/Down arrows - tilt up/down")
        print("'J/L' or Left/Right arrows - rotate left/right")
        print("'U/N' - adjust height up/down")
    else:  # Windows
        print("'I/K' - tilt up/down")
        print("'J/L' - rotate left/right")
        print("'U/N' - adjust height up/down")

def process_frame(cap, visualizer):
    """Process a single frame"""
    ret, frame = cap.read()
    if not ret:
        return None
    
    # Preprocess frame
    height, width = frame.shape[:2]
    if width > 1280:  # Scale down large frames
        scale = 1280 / width
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
    
    # Enhance image
    frame = cv2.GaussianBlur(frame, (3, 3), 0)
    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)  # Contrast and brightness
    
    # Process with MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = visualizer.process_frame(frame_rgb)
    
    return frame, results

def get_lighting_info(frame):
    """Analyze lighting conditions"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    contrast = np.std(gray)
    
    status = "Lighting: "
    if brightness < 50:
        status += "Too Dark"
        color = (0, 0, 255)
    elif brightness > 200:
        status += "Too Bright"
        color = (0, 0, 255)
    else:
        status += "Good"
        color = (0, 255, 0)
        
    return {
        'status': status,
        'color': color,
        'contrast_warning': contrast < 20
    }

def handle_keys(key, visualizer, recorder, camera, frame=None):
    """Handle keyboard input"""
    if key == ord('q'):
        if recorder.is_recording:
            recorder.stop_recording()
        return True
    elif key == ord('r'):
        camera.release()
        camera = cv2.VideoCapture(0)
    elif key == ord('v'):
        if not recorder.is_recording and frame is not None:
            recorder.start_recording(frame.shape, camera.get(cv2.CAP_PROP_FPS))
        else:
            recorder.stop_recording()
    elif key == ord('i'):
        visualizer.adjust_elevation(5)
    elif key == ord('k'):
        visualizer.adjust_elevation(-5)
    elif key == ord('u'):
        visualizer.adjust_z_offset(visualizer.z_step)
    elif key == ord('n'):
        visualizer.adjust_z_offset(-visualizer.z_step)
    elif key == ord('j'):
        visualizer.azim = (visualizer.azim + 5) % 360
    elif key == ord('l'):
        visualizer.azim = (visualizer.azim - 5) % 360
    return False

def cleanup(camera, visualizer, recorder, display):
    """Cleanup resources"""
    camera.release()
    visualizer.cleanup()
    recorder.cleanup()
    display.cleanup()

def main():
    try:
        # Initialize camera using the platform-specific setup
        camera = setup_camera()
        
        # Initialize components
        visualizer = PoseVisualizer()
        recorder = VideoRecorder()
        display = DisplayManager()
        
        print_instructions()
        
        # FPS calculation
        fps_start_time = time.time()
        fps_counter = 0
        fps = 0
        fps_update_interval = 0.5
        
        while True:
            # Process frame
            frame, results = process_frame(camera, visualizer)
            if frame is None:
                continue
            
            # Create visualizations
            frame_2d = frame.copy()
            if results.pose_landmarks:
                frame_2d = visualizer.draw_2d_pose(frame_2d, results)
            frame_3d = visualizer.visualize_3d_pose(results)
            
            # Create four-quadrant layout with pose detection
            recording_time = recorder.get_recording_time() if recorder.is_recording else None
            combined_frame = display.create_quadrant_layout(
                frame_2d, frame_3d, results, recording_time)
            
            # Calculate FPS
            fps_counter += 1
            if (time.time() - fps_start_time) > fps_update_interval:
                fps = fps_counter / (time.time() - fps_start_time)
                fps_counter = 0
                fps_start_time = time.time()
            
            # Add overlays
            lighting_info = get_lighting_info(frame)
            view_info = visualizer.current_view if hasattr(visualizer, 'current_view') else None
            display.add_overlays(combined_frame, fps, lighting_info, view_info)
            
            # Handle recording
            if recorder.is_recording:
                recorder.write_frame(combined_frame)
            
            # Show frame
            display.show_frame(combined_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if handle_keys(key, visualizer, recorder, camera, combined_frame):
                break
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup(camera, visualizer, recorder, display)

if __name__ == "__main__":
    main() 