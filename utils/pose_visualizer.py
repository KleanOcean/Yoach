import cv2
import numpy as np
import matplotlib.pyplot as plt
import mediapipe as mp
from mpl_toolkits.mplot3d import Axes3D
import platform

class PoseVisualizer:
    def __init__(self, smoothing_factor=0.5):
        self._init_mediapipe()
        self._init_3d_visualization()
        self._init_smoothing(smoothing_factor)
        self._init_view_controls()

    def _init_mediapipe(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=0,
            smooth_landmarks=True,
            enable_segmentation=False
        )
        self.pose_connections = self.mp_pose.POSE_CONNECTIONS

    def _init_3d_visualization(self):
        # Use Agg backend for Mac compatibility
        import matplotlib
        matplotlib.use('Agg')
        
        plt.rcParams['figure.figsize'] = [8, 8]
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        # Remove plt.ion() as we're using Agg backend
        self.fig.tight_layout()

    def _init_smoothing(self, smoothing_factor):
        self.previous_landmarks = None
        self.smoothing_factor = smoothing_factor
        self.landmark_history = []
        self.history_length = 5

    def _init_view_controls(self):
        self.elev = 5
        self.azim = 20
        self.z_offset = 0.0
        self.z_step = 0.1

    def process_frame(self, frame):
        """Process frame with ROI tracking and automatic reset"""
        results = None
        
        # Try processing with previous ROI
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
            if roi.size > 0:  # Check if ROI is valid
                results = self.pose.process(roi)
                
                # Adjust coordinates back to full frame if detection successful
                if results and results.pose_landmarks:
                    for landmark in results.pose_landmarks.landmark:
                        landmark.x = (landmark.x * (roi_x2 - roi_x1) + roi_x1) / frame.shape[1]
                        landmark.y = (landmark.y * (roi_y2 - roi_y1) + roi_y1) / frame.shape[0]
        
        # If ROI processing failed or no previous landmarks, process full frame
        if results is None or not results.pose_landmarks:
            results = self.pose.process(frame)
            # Reset previous landmarks if no detection
            if not results.pose_landmarks:
                self.previous_landmarks = None
        
        # Update landmarks with smoothing if detection successful
        if results.pose_landmarks:
            results.pose_landmarks = self.smooth_landmarks(results.pose_landmarks)
            self.previous_landmarks = results.pose_landmarks
        
        return results

    def draw_2d_pose(self, frame, results):
        if results.pose_landmarks:
            # Draw landmarks with thicker lines for visibility
            for connection in self.pose_connections:
                start_idx = connection[0]
                end_idx = connection[1]
                start = results.pose_landmarks.landmark[start_idx]
                end = results.pose_landmarks.landmark[end_idx]
                
                # Convert normalized coordinates to image dimensions
                h, w = frame.shape[:2]
                start_pos = (int(start.x * w), int(start.y * h))
                end_pos = (int(end.x * w), int(end.y * h))
                
                # Draw thicker lines
                cv2.line(frame, start_pos, end_pos, (0, 255, 0), 3)
                
            # Draw landmarks as circles
            for landmark in results.pose_landmarks.landmark:
                pos = (int(landmark.x * w), int(landmark.y * h))
                cv2.circle(frame, pos, 5, (0, 0, 255), -1)
        
        return frame

    def visualize_3d_pose(self, results):
        self._setup_3d_plot()
        if results.pose_world_landmarks:
            print("Found world landmarks, drawing 3D pose...")  # Debug log
            view_params = {
                'elevation': self.elev,
                'azimuth': self.azim,
                'z_offset': self.z_offset
            }
            self._draw_pose(results.pose_world_landmarks, view_params)
        else:
            print("No world landmarks found")  # Debug log
        self._update_view()
        return self._convert_plot_to_image()

    def _setup_3d_plot(self):
        self.ax.clear()
        self.ax.set_box_aspect([1, 1, 1])
        self._set_background()
        self._setup_grid()
        self._setup_axes()

    def _set_background(self):
        self.ax.set_facecolor('white')
        self.fig.patch.set_facecolor('white')

    def _setup_grid(self):
        """Setup grid with fixed center point"""
        self.ax.grid(True, linestyle='-', linewidth=1.0, color='gray', alpha=0.7)
        max_range = 2.0
        
        # Set center point at (0,0,0)
        self.ax.set_xlim(-max_range/2, max_range/2)
        self.ax.set_ylim(-max_range/2, max_range/2)
        self.ax.set_zlim(-max_range/2, max_range/2)
        
        # Set equal spacing for grid lines
        self.ax.set_xticks(np.linspace(-max_range/2, max_range/2, 9))
        self.ax.set_yticks(np.linspace(-max_range/2, max_range/2, 9))
        self.ax.set_zticks(np.linspace(-max_range/2, max_range/2, 9))

    def _setup_axes(self):
        self.ax.set_xlabel('X', fontsize=8, labelpad=8)
        self.ax.set_ylabel('Y', fontsize=8, labelpad=8)
        self.ax.set_zlabel('Z', fontsize=8, labelpad=8)
        self.ax.tick_params(axis='both', which='major', labelsize=7, length=4, width=1)

    def _draw_pose(self, landmarks, view_params):
        """Draw 3D pose with landmarks"""
        print("Drawing 3D pose...")  # Debug log
        
        # Extract coordinates
        x = [-landmark.z for landmark in landmarks.landmark]
        y = [landmark.x for landmark in landmarks.landmark]
        z = [-landmark.y for landmark in landmarks.landmark]
        
        # Normalize pose size
        left_shoulder_idx = self.mp_pose.PoseLandmark.LEFT_SHOULDER.value
        right_shoulder_idx = self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value
        
        # Calculate shoulder width in 3D space
        shoulder_width = np.sqrt(
            (x[right_shoulder_idx] - x[left_shoulder_idx])**2 +
            (y[right_shoulder_idx] - y[left_shoulder_idx])**2 +
            (z[right_shoulder_idx] - z[left_shoulder_idx])**2
        )
        
        # Define target shoulder width (normalized scale)
        target_width = 0.5
        scale_factor = target_width / shoulder_width if shoulder_width > 0 else 1.0
        
        # Calculate centroid for centering
        centroid_x = np.mean(x)
        centroid_y = np.mean(y)
        centroid_z = np.mean(z)
        
        # Center and scale the pose
        x = [(coord - centroid_x) * scale_factor for coord in x]
        y = [(coord - centroid_y) * scale_factor for coord in y]
        z = [(coord - centroid_z) * scale_factor for coord in z]
        
        # Update view
        self.ax.view_init(elev=view_params['elevation'], azim=view_params['azimuth'])
        
        # Clear previous frame
        self.ax.clear()
        self._setup_grid()
        self._setup_axes()
        
        # Draw connections
        for connection in self.pose_connections:
            start_idx = connection[0]
            end_idx = connection[1]
            self.ax.plot([x[start_idx], x[end_idx]],
                        [y[start_idx], y[end_idx]],
                        [z[start_idx], z[end_idx]], 'b-', linewidth=2)
        
        # Plot landmarks
        self.ax.scatter(x, y, z, c='r', s=50)
        
        # Set view limits
        max_range = 1.0
        self.ax.set_xlim([-max_range, max_range])
        self.ax.set_ylim([-max_range, max_range])
        self.ax.set_zlim([-max_range, max_range])
        
        print("3D pose drawing completed")  # Debug log

    def _update_view(self):
        self.ax.view_init(elev=self.elev, azim=self.azim)
        controls_text = "I/K: Tilt | J/L: Rotate | U/N: Height"
        height_text = f"Height: {self.z_offset:+.1f}"
        self.current_view = f"{controls_text}\nTilt: {int(self.elev)} | Rotate: {int(self.azim)} | {height_text}"

    def _convert_plot_to_image(self):
        self.fig.canvas.draw()
        
        # Get the correct dimensions from the figure
        width, height = self.fig.canvas.get_width_height()
        buffer = self.fig.canvas.buffer_rgba()
        
        # Convert to numpy array with correct shape
        img = np.asarray(buffer)
        # Convert RGBA to RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        
        return img

    def smooth_landmarks(self, current_landmarks):
        """Apply temporal smoothing to landmarks"""
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
            # Create a simple landmark object
            landmark = type('Landmark', (), {'x': x, 'y': y, 'z': z})()
            smoothed_landmarks.append(landmark)
        
        return smoothed_landmarks

    def adjust_elevation(self, step):
        """Adjust the viewing elevation"""
        self.elev = max(min(self.elev + step, 90), -90)
        print(f"Tilt angle: {self.elev}")

    def adjust_z_offset(self, step):
        """Adjust the z-axis offset"""
        self.z_offset += step
        print(f"Z offset: {self.z_offset:.1f}")

    def cleanup(self):
        """Cleanup resources"""
        self.pose.close()
        plt.close(self.fig)

    # ... (rest of the methods) 