import cv2
import numpy as np
import time
import mediapipe as mp
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class PoseVisualizer:
    def __init__(self, smoothing_factor=0.5):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Simplified pose configuration - removed segmentation
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=0,  # Use the most accurate model
            smooth_landmarks=True,
            enable_segmentation=False  # Disable segmentation to avoid errors
        )
        
        self.previous_landmarks = None
        self.smoothing_factor = smoothing_factor
        self.trajectory = []
        
        # 3D visualization settings - make figure square
        plt.rcParams['figure.figsize'] = [8, 8]  # Square figure
        self.fig = plt.figure(figsize=(8, 8))    # Square figure
        self.ax = self.fig.add_subplot(111, projection='3d')
        plt.ion()
        
        # Define connections for 3D visualization
        self.pose_connections = self.mp_pose.POSE_CONNECTIONS
        
        # View control parameters
        self.elev = 5
        self.azim = 20
        self.z_offset = -1.9
        self.z_step = 0.1
        
        # For temporal smoothing
        self.landmark_history = []
        self.history_length = 5
        
    def smooth_landmarks(self, current_landmarks):
        if self.previous_landmarks is None:
            self.previous_landmarks = current_landmarks
            return current_landmarks
            
        for prev, curr in zip(self.previous_landmarks.landmark, current_landmarks.landmark):
            smoothed_x = prev.x * (1 - self.smoothing_factor) + curr.x * self.smoothing_factor
            smoothed_y = prev.y * (1 - self.smoothing_factor) + curr.y * self.smoothing_factor
            smoothed_z = prev.z * (1 - self.smoothing_factor) + curr.z * self.smoothing_factor
            curr.x, curr.y, curr.z = smoothed_x, smoothed_y, smoothed_z
            
        self.previous_landmarks = current_landmarks
        return current_landmarks

    def process_frame(self, frame):
        # Get ROI around previous detection if available
        if self.previous_landmarks is not None:
            x_coords = [l.x for l in self.previous_landmarks.landmark]
            y_coords = [l.y for l in self.previous_landmarks.landmark]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Add margin
            margin = 0.1
            roi_x1 = max(0, int((min_x - margin) * frame.shape[1]))
            roi_y1 = max(0, int((min_y - margin) * frame.shape[0]))
            roi_x2 = min(frame.shape[1], int((max_x + margin) * frame.shape[1]))
            roi_y2 = min(frame.shape[0], int((max_y + margin) * frame.shape[0]))
            
            # Process ROI
            roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            results = self.pose.process(roi)
            
            # Adjust coordinates back to full frame
            if results.pose_landmarks:
                for landmark in results.pose_landmarks.landmark:
                    landmark.x = (landmark.x * (roi_x2 - roi_x1) + roi_x1) / frame.shape[1]
                    landmark.y = (landmark.y * (roi_y2 - roi_y1) + roi_y1) / frame.shape[0]
        else:
            results = self.pose.process(frame)
            
        if results.pose_landmarks:
            results.pose_landmarks = self.smooth_landmarks(results.pose_landmarks)
        return results
        
    def draw_2d_pose(self, frame, results):
        if results.pose_landmarks:
            # Draw landmarks with confidence-based colors
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                confidence = landmark.visibility if hasattr(landmark, 'visibility') else 1.0
                color = (0, int(255 * confidence), 0)  # Green with confidence-based intensity
                
                pos = (int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0]))
                cv2.circle(frame, pos, 5, color, -1)
                
            # Draw connections with confidence-based thickness
            for connection in self.mp_pose.POSE_CONNECTIONS:
                start_idx = connection[0]
                end_idx = connection[1]
                
                start = results.pose_landmarks.landmark[start_idx]
                end = results.pose_landmarks.landmark[end_idx]
                
                confidence = min(start.visibility, end.visibility) if hasattr(start, 'visibility') else 1.0
                thickness = int(3 * confidence)
                
                if thickness > 0:
                    start_pos = (int(start.x * frame.shape[1]), int(start.y * frame.shape[0]))
                    end_pos = (int(end.x * frame.shape[1]), int(end.y * frame.shape[0]))
                    cv2.line(frame, start_pos, end_pos, (0, 255, 0), thickness)
                    
        return frame
        
    def visualize_3d_pose(self, results):
        # Remove the initial check so we always draw the grid
        self.ax.clear()
        
        # Force aspect ratio to be equal (1:1:1)
        self.ax.set_box_aspect([1, 1, 1])
        
        # Set white background
        self.ax.set_facecolor('white')
        self.fig.patch.set_facecolor('white')
        
        # Set up grid with equal spacing
        self.ax.grid(True, linestyle='-', linewidth=1.0, color='gray', alpha=0.7)
        
        # Set equal axis limits for perfect cube
        max_range = 2.0
        mid_x = 0
        mid_y = 0
        mid_z = -0.75
        
        self.ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        self.ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        self.ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
        
        # Set equal spacing for grid lines
        self.ax.set_xticks(np.linspace(mid_x - max_range/2, mid_x + max_range/2, 9))
        self.ax.set_yticks(np.linspace(mid_y - max_range/2, mid_y + max_range/2, 9))
        self.ax.set_zticks(np.linspace(mid_z - max_range/2, mid_z + max_range/2, 9))
        
        # Labels and styling
        self.ax.set_xlabel('X', fontsize=8, labelpad=8)
        self.ax.set_ylabel('Y', fontsize=8, labelpad=8)
        self.ax.set_zlabel('Z', fontsize=8, labelpad=8)
        
        # Make tick labels smaller
        self.ax.tick_params(axis='both', which='major', labelsize=7, length=4, width=1)
        
        # Equal grid spacing on all faces
        self.ax.xaxis._axinfo["grid"]['color'] = (0.5, 0.5, 0.5, 0.7)
        self.ax.yaxis._axinfo["grid"]['color'] = (0.5, 0.5, 0.5, 0.7)
        self.ax.zaxis._axinfo["grid"]['color'] = (0.5, 0.5, 0.5, 0.7)
        self.ax.xaxis._axinfo["grid"]['linewidth'] = 1.0
        self.ax.yaxis._axinfo["grid"]['linewidth'] = 1.0
        self.ax.zaxis._axinfo["grid"]['linewidth'] = 1.0
        
        # Draw pose only if landmarks are detected
        if results.pose_world_landmarks:
            x = [-landmark.z for landmark in results.pose_world_landmarks.landmark]
            y = [landmark.x for landmark in results.pose_world_landmarks.landmark]
            z = [-landmark.y for landmark in results.pose_world_landmarks.landmark]
            
            # Normalize z coordinates with adjustable offset
            min_z = min(z)
            z = [((z_coord - min_z) * (-1.0 / min_z)) + self.z_offset for z_coord in z]
            
            # Draw main connections
            for connection in self.pose_connections:
                start_idx = connection[0]
                end_idx = connection[1]
                self.ax.plot([x[start_idx], x[end_idx]],
                            [y[start_idx], y[end_idx]],
                            [z[start_idx], z[end_idx]], 'b-', linewidth=2)
            
            # Plot landmarks
            self.ax.scatter(x, y, z, c='y', s=50)
        
        # Update view angle with controls help
        self.ax.view_init(elev=self.elev, azim=self.azim)
        controls_text = "I/K: Tilt | J/L: Rotate | U/N: Height"
        self.current_view = f"{controls_text}\nTilt: {int(self.elev)} | Rotate: {int(self.azim)} | Height: {self.z_offset:.1f}"
        
        # Convert plot to image
        self.fig.canvas.draw()
        img = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(self.fig.canvas.get_width_height()[::-1] + (3,))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        return img
        
    def adjust_z_offset(self, step):
        """Adjust the z-axis offset"""
        self.z_offset += step
        print(f"Z offset: {self.z_offset:.1f}")
        
    def adjust_elevation(self, step):
        """Adjust the viewing elevation"""
        self.elev = max(min(self.elev + step, 90), -90)
        print(f"Tilt angle: {self.elev}")

    def cleanup(self):
        self.pose.close()
        plt.close(self.fig)

    def temporal_smoothing(self, landmarks):
        """Apply temporal smoothing over multiple frames"""
        self.landmark_history.append(landmarks)
        if len(self.landmark_history) > self.history_length:
            self.landmark_history.pop(0)
            
        smoothed_landmarks = []
        for i in range(33):  # MediaPipe has 33 landmarks
            x = sum(frame[i].x for frame in self.landmark_history) / len(self.landmark_history)
            y = sum(frame[i].y for frame in self.landmark_history) / len(self.landmark_history)
            z = sum(frame[i].z for frame in self.landmark_history) / len(self.landmark_history)
            # Create a simple landmark object instead of using PoseLandmark
            landmark = type('Landmark', (), {'x': x, 'y': y, 'z': z})()
            smoothed_landmarks.append(landmark)
            
        return smoothed_landmarks

class VideoRecorder:
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        
    def start_recording(self, frame_size, fps):
        if not self.is_recording:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"pose_recording_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, fps, 
                                              (frame_size[1], frame_size[0]))
            self.is_recording = True
            
    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
                
    def write_frame(self, frame, results):
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
            
    def cleanup(self):
        self.stop_recording()

def main():
    # Try camera 0 first on Windows, then fall back to 1 if needed
    camera_id = 0
    cap = None
    
    try:
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            camera_id = 1
            cap = cv2.VideoCapture(camera_id)
            
        if not cap.isOpened():
            raise Exception("Could not open camera")
            
        visualizer = PoseVisualizer()
        recorder = VideoRecorder()
        
        # FPS calculation
        fps_start_time = time.time()
        fps_counter = 0
        fps = 0
        fps_update_interval = 0.5
        
        print("Camera initialized. Press:")
        print("'q' - quit")
        print("'r' - reset camera")
        print("'v' - start/stop recording")
        print("'c' - clear trajectory")
        
        # Create fixed window (non-resizable)
        window_name = 'MediaPipe Pose (2D and 3D)'
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        
        # Set fixed window size (16:9) - 50% larger
        window_width = 2880  # 1920 * 1.5
        window_height = 1620  # 1080 * 1.5
        
        # Adjust font sizes and thicknesses for text (half the current size)
        base_font_scale = window_height / 500.0 * 0.75  # Reduced from 1.5 to 0.75 (half of 1.5)
        base_thickness = max(1, int(base_font_scale * 2))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                continue
                
            # Preprocess frame
            height, width = frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
                
            # Enhance image
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            alpha = 1.2  # Contrast
            beta = 10    # Brightness
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = visualizer.process_frame(frame_rgb)
            
            # Create visualizations
            frame_2d = frame.copy()
            if results.pose_landmarks:
                frame_2d = visualizer.draw_2d_pose(frame_2d, results)
                frame_3d = visualizer.visualize_3d_pose(results)
            else:
                # Still show 3D grid even when no pose is detected
                frame_3d = visualizer.visualize_3d_pose(results)  # Will show grid without pose
                
            if frame_3d is not None:
                # Make left side square with black padding
                pose2d_width = window_width // 2
                pose2d_height = pose2d_width  # Make it square
                
                # Calculate scaling to fit video in square while maintaining aspect ratio
                src_ratio = frame_2d.shape[1] / frame_2d.shape[0]
                if src_ratio > 1:  # Width > Height
                    new_width = pose2d_width
                    new_height = int(pose2d_width / src_ratio)
                    pad_top = (pose2d_height - new_height) // 2
                    pad_bottom = pose2d_height - new_height - pad_top
                    pad_left = 0
                    pad_right = 0
                else:  # Height > Width
                    new_height = pose2d_height
                    new_width = int(pose2d_height * src_ratio)
                    pad_left = (pose2d_width - new_width) // 2
                    pad_right = pose2d_width - new_width - pad_left
                    pad_top = 0
                    pad_bottom = 0
                
                # Resize frame_2d maintaining aspect ratio
                frame_2d = cv2.resize(frame_2d, (new_width, new_height))
                
                # Add black padding to make it square
                frame_2d = cv2.copyMakeBorder(frame_2d, pad_top, pad_bottom, pad_left, pad_right,
                                            cv2.BORDER_CONSTANT, value=[0, 0, 0])
                
                # Resize 3D view to match height
                pose3d_width = window_width // 2
                pose3d_height = pose2d_height
                frame_3d = cv2.resize(frame_3d, (pose3d_width, pose3d_height))
            
            # Combine frames
            combined_frame = np.hstack([frame_2d, frame_3d])
            
            # Add FPS and lighting indicators
            fps_counter += 1
            if (time.time() - fps_start_time) > fps_update_interval:
                fps = fps_counter / (time.time() - fps_start_time)
                fps_counter = 0
                fps_start_time = time.time()
                
            # Add text with size relative to larger window
            font_scale = base_font_scale
            thickness = base_thickness
            
            # Add FPS text with smaller size
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(combined_frame, fps_text,
                       (30, combined_frame.shape[0] - 25),  # Adjusted positions
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            # Add lighting quality indicators
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Lighting status
            lighting_status = "Lighting: "
            if brightness < 50:
                lighting_status += "Too Dark"
                color = (0, 0, 255)
            elif brightness > 200:
                lighting_status += "Too Bright"
                color = (0, 0, 255)
            else:
                lighting_status += "Good"
                color = (0, 255, 0)
                
            cv2.putText(combined_frame, lighting_status, (30, 70),  # Adjusted from 135 to 70
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            
            if contrast < 20:
                cv2.putText(combined_frame, "Low Contrast", (30, 135),  # Adjusted from 270 to 135
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
            
            # Adjust view text spacing
            if hasattr(visualizer, 'current_view'):
                view_lines = visualizer.current_view.split('\n')
                for i, line in enumerate(view_lines):
                    text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                    text_x = combined_frame.shape[1] - text_size[0] - 20
                    text_y = combined_frame.shape[0] - 20 - (len(view_lines) - 1 - i) * int(25 * font_scale)  # Reduced spacing
                    cv2.putText(combined_frame, line,
                               (text_x, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            # Handle recording
            if recorder.is_recording:
                recorder.write_frame(combined_frame, results)
            
            # Display frame in resizable window
            cv2.imshow(window_name, combined_frame)
            
            # Handle key presses with new controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                cap.release()
                cap = cv2.VideoCapture(camera_id)
            elif key == ord('v'):
                if not recorder.is_recording:
                    recorder.start_recording(combined_frame.shape, cap.get(cv2.CAP_PROP_FPS))
                else:
                    recorder.stop_recording()
            elif key == ord('i'):  # Tilt up
                visualizer.adjust_elevation(5)
            elif key == ord('k'):  # Tilt down
                visualizer.adjust_elevation(-5)
            elif key == ord('u'):  # Press U to move pose up (was 7)
                visualizer.adjust_z_offset(visualizer.z_step)
            elif key == ord('n'):  # Press N to move pose down (was 1)
                visualizer.adjust_z_offset(-visualizer.z_step)
            elif key == ord('j'):  # Rotate left
                visualizer.azim = (visualizer.azim + 5) % 360
            elif key == ord('l'):  # Rotate right
                visualizer.azim = (visualizer.azim - 5) % 360
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if cap is not None:
            cap.release()
        visualizer.cleanup()
        recorder.cleanup()
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Extra wait for Windows
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()