import cv2
import mediapipe as mp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class PoseVisualizer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize matplotlib with specific size and DPI
        plt.ioff()
        self.fig = plt.figure(figsize=(4, 4), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Initialize MediaPipe
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=2,
            static_image_mode=False
        )

        self.right_hand_trajectory = []  # Store 3D trajectory points
        self.max_trajectory_points = 50  # Maximum number of points to show
        self.hand_above_shoulder = False  # Add status variable
        self.previous_hand_status = False  # Add this to track status change
        self.left_hand_raised = False  # Add left hand tracking
        self.upward_frames_count = 0  # Add counter for upward pointing frames
        self.colors = {
            'left_arm': '#FF0000',
            'right_arm': '#00FF00',
            'left_leg': '#FFA500',
            'right_leg': '#00FFA5',
            'torso': '#0000FF',
            'right_index': '#FFFF99',  # Light yellow for right index
            'status_active': (0, 255, 0),    # Green when active
            'status_inactive': (0, 165, 255)  # Orange when inactive
        }

    def process_frame(self, frame):
        """Process a frame and return pose results"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.pose.process(frame_rgb)

    def draw_2d_pose(self, frame, results):
        """Draw 2D pose on frame"""
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
        return frame

    def visualize_3d_pose(self, results):
        """Create 3D visualization of pose"""
        if not results.pose_world_landmarks:
            return None

        # Get 3D landmarks
        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in results.pose_world_landmarks.landmark])
        
        # Update hand positions status
        right_hand = landmarks[20]  # Right index
        right_shoulder = landmarks[12]
        right_hip = landmarks[24]
        
        # Check if hand is lower than hip
        hand_below_hip = right_hand[1] > right_hip[1]
        
        # Check if hand is pointing upward (Y coordinate decreasing)
        if len(self.right_hand_trajectory) >= 2:
            last_point = self.right_hand_trajectory[-1]
            current_point = right_hand.copy()
            current_point[1] = -current_point[1]  # Flip Y
            current_point *= 100  # Scale
            
            # Check if movement is upward
            if current_point[1] < last_point[1]:
                self.upward_frames_count += 1
            else:
                self.upward_frames_count = 0
            
            # Clear trajectory if hand is below hip and has been pointing upward
            if hand_below_hip and self.upward_frames_count >= 3:
                self.right_hand_trajectory = []
                self.upward_frames_count = 0
        
        # Center the pose horizontally (X and Z) using hip points
        center = np.mean(landmarks[[23, 24]], axis=0)  # Center using hip points
        landmarks[:, 0] = landmarks[:, 0] - center[0]  # Center X
        landmarks[:, 2] = landmarks[:, 2] - center[2]  # Center Z
        
        # Move feet to ground (Y=0)
        min_y = np.min(landmarks[:, 1])
        landmarks[:, 1] = landmarks[:, 1] - min_y
        
        # Store right hand position
        right_hand_pos = landmarks[16].copy()
        right_hand_pos[1] = -right_hand_pos[1]  # Flip Y
        right_hand_pos *= 100  # Scale
        self.right_hand_trajectory.append(right_hand_pos)
        self.right_hand_trajectory = self.right_hand_trajectory[-self.max_trajectory_points:]
        
        # Update previous status
        self.previous_hand_status = not hand_below_hip
        
        # Transform for visualization
        landmarks[:, 1] = -landmarks[:, 1]  # Flip Y
        landmarks *= 100  # Scale

        # Clear and setup plot
        self.ax.cla()
        self._setup_3d_plot(landmarks)
        
        # Draw trajectory in 3D
        self._draw_3d_trajectory()
        
        # Convert to image with proper size handling
        self.fig.canvas.draw()
        
        # Get the size of the figure in pixels
        w, h = self.fig.canvas.get_width_height()
        
        # Get the renderer's buffer
        buf = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8)
        
        try:
            # Reshape with explicit size check
            expected_size = h * w * 3
            if len(buf) != expected_size:
                print(f"Buffer size mismatch: got {len(buf)}, expected {expected_size}")
                return np.zeros((h, w, 3), dtype=np.uint8)
            
            # Reshape the buffer
            buf = buf.reshape(h, w, 3)
            return buf
            
        except ValueError as e:
            print(f"Reshape error: {e}")
            print(f"Buffer size: {len(buf)}, Target shape: ({h}, {w}, 3)")
            # Return a blank image of the expected size
            return np.zeros((h, w, 3), dtype=np.uint8)

    def _setup_3d_plot(self, landmarks):
        """Setup the 3D plot with landmarks"""
        # Plot points
        self.ax.scatter(landmarks[:, 0], landmarks[:, 2], landmarks[:, 1], c='red', marker='o', s=20)
        
        # Draw connections with colors
        self._draw_colored_connections(landmarks)
        
        # Set properties
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Z')
        self.ax.set_zlabel('Y')
        
        # Set view limits symmetrically around origin
        self.ax.set_xlim([-100, 100])
        self.ax.set_ylim([-100, 100])
        self.ax.set_zlim([-150, 50])  # Moved down by 200 units (from [50, 250] to [-150, 50])
        
        # Set camera angle
        self.ax.view_init(elev=10., azim=-70)  # Adjusted elevation for better view
        
        # Make background transparent
        self.ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        self.ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        self.ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        self.ax.grid(True)
        
        # Equal aspect ratio
        self.ax.set_box_aspect([1, 1, 1])
        
        # Tight layout
        self.fig.tight_layout()

    def _draw_colored_connections(self, landmarks):
        """Draw colored connections between landmarks"""
        for connection in self.mp_pose.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            color = self._get_connection_color(start_idx, end_idx, self.colors)
            
            # Special color for right index finger
            if start_idx == 20 or end_idx == 20:  # Right index landmark
                color = self.colors['right_index']
            
            x = [landmarks[start_idx, 0], landmarks[end_idx, 0]]
            y = [landmarks[start_idx, 2], landmarks[end_idx, 2]]
            z = [landmarks[start_idx, 1], landmarks[end_idx, 1]]
            
            self.ax.plot(x, y, z, color=color, linewidth=2)

    def _get_connection_color(self, start_idx, end_idx, colors):
        """Get color for a connection based on body part"""
        if start_idx in [11, 13, 15] or end_idx in [11, 13, 15]:
            return colors['left_arm']
        elif start_idx in [12, 14, 16] or end_idx in [12, 14, 16]:
            return colors['right_arm']
        elif start_idx in [23, 25, 27] or end_idx in [23, 25, 27]:
            return colors['left_leg']
        elif start_idx in [24, 26, 28] or end_idx in [24, 26, 28]:
            return colors['right_leg']
        return colors['torso']

    def _draw_3d_trajectory(self):
        """Draw the 3D trajectory of the right hand"""
        if len(self.right_hand_trajectory) > 1:
            trajectory = np.array(self.right_hand_trajectory)
            
            # Trajectory points are already transformed
            x = trajectory[:, 0]
            y = trajectory[:, 2]  # Use Z as Y for visualization
            z = trajectory[:, 1]  # Use Y as Z for visualization
            
            # Create color gradient from blue to red
            colors = plt.cm.jet(np.linspace(0, 1, len(x)))
            
            # Plot trajectory with lines only
            for i in range(1, len(x)):
                # Draw line segment only
                self.ax.plot(x[i-1:i+1], y[i-1:i+1], z[i-1:i+1], 
                            color=colors[i], linewidth=3)

    def clear_trajectory(self):
        """Clear the stored trajectory"""
        self.right_hand_trajectory = []

    def cleanup(self):
        """Cleanup resources"""
        self.pose.close()
        plt.close(self.fig)

    def draw_status_indicator(self, frame):
        """Draw status indicator dot in top right corner"""
        radius = 15
        center = (frame.shape[1] - 30, 30)  # 30 pixels from top-right corner
        
        # Use status-specific colors
        color = self.colors['status_active'] if not self.hand_above_shoulder else self.colors['status_inactive']
        
        cv2.circle(frame, center, radius, color, -1)  # Filled circle
        
        # Add white border
        cv2.circle(frame, center, radius, (255, 255, 255), 2)
        
        return frame

    def get_hand_status(self):
        """Return current hand position status"""
        return not self.hand_above_shoulder

    def is_left_hand_raised(self):
        """Return True if left hand is above left shoulder"""
        return self.left_hand_raised 