import cv2
import numpy as np
import platform

class DisplayManager:
    def __init__(self, window_width=2880, window_height=1620):
        self.window_width = window_width
        self.window_height = window_height
        # Adjust base font scale based on platform
        if platform.system() == "Darwin":  # macOS
            self.base_font_scale = (window_height / 500.0 * 0.75) * 0.5  # Half size for Mac
        else:
            self.base_font_scale = window_height / 500.0 * 0.75
        self.base_thickness = max(1, int(self.base_font_scale * 2))

    def create_quadrant_layout(self, frame_2d, frame_3d, pose_results=None, recording_time=None):
        # Create a black canvas for the full window
        full_frame = np.zeros((self.window_height, self.window_width, 3), dtype=np.uint8)
        
        # Calculate quadrant dimensions
        quad_width = self.window_width // 2
        quad_height = self.window_height // 2
        
        # Q1: Video and keypoints (top-left)
        resized_2d = self._resize_with_aspect_ratio(frame_2d, quad_width, quad_height)
        pad_2d = self._add_padding(resized_2d, quad_width, quad_height)
        full_frame[0:quad_height, 0:quad_width] = pad_2d
        
        # Q2: Coach Chat (top-right) with white background
        q2 = np.full((quad_height, quad_width, 3), 255, dtype=np.uint8)  # White background
        self._add_centered_text(q2, "Coach Chat", 1.0, is_title=True, color=(0, 0, 0))
        full_frame[0:quad_height, quad_width:] = q2
        
        # Q3: 3D Visualizer (bottom-left)
        resized_3d = self._resize_with_aspect_ratio(frame_3d, quad_width, quad_height)
        pad_3d = self._add_padding(resized_3d, quad_width, quad_height)
        full_frame[quad_height:, 0:quad_width] = pad_3d
        
        # Q4: Sports Analysis (bottom-right) with white background
        q4 = np.full((quad_height, quad_width, 3), 255, dtype=np.uint8)  # White background
        self._add_centered_text(q4, "Sports Analysis", 1.0, is_title=True, color=(0, 0, 0))
        
        # Add pose detection text if landmarks are present
        if pose_results and pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            pose_texts = []
            
            # Check right hand
            if landmarks[16].y < landmarks[12].y:  # Right wrist above right shoulder
                pose_texts.append("Raising right hand")
                
            # Check left hand
            if landmarks[15].y < landmarks[11].y:  # Left wrist above left shoulder
                pose_texts.append("Raising left hand")
            
            # Calculate text properties for consistent positioning
            font_scale = self.base_font_scale
            thickness = self.base_thickness
            _, text_height = cv2.getTextSize("Test", cv2.FONT_HERSHEY_SIMPLEX, 
                                           font_scale, thickness)[0]
            
            # Add detected poses to Q4
            for i, text in enumerate(pose_texts):
                y_pos = 120 + (i + 1) * (text_height + 30)  # Start below title with spacing
                cv2.putText(q4, text, (30, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                           (0, 0, 0), thickness)
        
        full_frame[quad_height:, quad_width:] = q4
        
        # Add recording indicator if recording
        if recording_time is not None:
            rec_text = f"REC {int(recording_time)}s"
            cv2.putText(full_frame, rec_text,
                       (self.window_width - 200, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, self.base_font_scale,
                       (0, 0, 255), self.base_thickness)
            # Add red circle indicator
            cv2.circle(full_frame, 
                      (self.window_width - 220, 30),
                      10, (0, 0, 255), -1)
        
        return full_frame

    def _resize_with_aspect_ratio(self, frame, target_width, target_height):
        h, w = frame.shape[:2]
        aspect = w / h
        
        if aspect > target_width / target_height:  # Width limited
            new_width = target_width
            new_height = int(target_width / aspect)
        else:  # Height limited
            new_height = target_height
            new_width = int(target_height * aspect)
            
        return cv2.resize(frame, (new_width, new_height))

    def _add_padding(self, frame, target_width, target_height):
        h, w = frame.shape[:2]
        pad_top = (target_height - h) // 2
        pad_bottom = target_height - h - pad_top
        pad_left = (target_width - w) // 2
        pad_right = target_width - w - pad_left
        
        return cv2.copyMakeBorder(frame, pad_top, pad_bottom, pad_left, pad_right,
                                cv2.BORDER_CONSTANT, value=[0, 0, 0])

    def _add_centered_text(self, frame, text, scale_factor=1.0, is_title=False, color=(255, 255, 255)):
        # Adjust font sizes for Mac
        if platform.system() == "Darwin":  # macOS
            if is_title and (text == "Coach Chat" or text == "Sports Analysis"):
                # Make Coach Chat and Sports Analysis titles bigger on Mac
                font_scale = self.base_font_scale * scale_factor * 2.0  # Increased from 0.75
                thickness = max(2, int(self.base_thickness * scale_factor * 1.5))
            else:
                font_scale = self.base_font_scale * scale_factor * 1.0
                if is_title:
                    font_scale *= 0.7
                thickness = max(1, int(self.base_thickness * scale_factor * 0.75))
        else:
            font_scale = self.base_font_scale * scale_factor * 1.5
            if is_title:
                font_scale *= 0.7
            thickness = max(2, int(self.base_thickness * scale_factor * 1.5))
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Calculate position
        if is_title:
            x = (frame.shape[1] - text_width) // 2
            # Move Mac titles down a bit more for better visibility
            if platform.system() == "Darwin" and (text == "Coach Chat" or text == "Sports Analysis"):
                y = text_height + 80  # Increased from 60
            else:
                y = text_height + 60
        else:
            x = (frame.shape[1] - text_width) // 2
            y = (frame.shape[0] + text_height) // 2
        
        cv2.putText(frame, text, (x, y),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    def add_overlays(self, frame, fps, lighting_info, view_info):
        # Adjust text size based on platform
        if platform.system() == "Darwin":  # macOS
            # You can adjust these values to change text size
            fps_size = 2.5 # Size for FPS text
            control_size = 1.2  # Size for control instructions
            status_size = 2.0  # Size for lighting status
            
            # Base thickness for the text
            thickness = max(1, int(self.base_thickness * 1.0))
        else:
            # Windows sizes
            fps_size = 3.0
            control_size = 3.0
            status_size = 2.0
            thickness = max(3, int(self.base_thickness * 3))
        
        # FPS text position - (x, y) coordinates
        fps_x = 50  # Adjust this value to move left/right
        fps_y = 80  # Adjust this value to move up/down
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(frame, fps_text,
                   (fps_x, fps_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   self.base_font_scale * fps_size,
                   (0, 255, 0),
                   thickness + 1)
        
        # Lighting status position
        lighting_x = 50  # Adjust this value
        lighting_y = 140  # Adjust this value
        cv2.putText(frame, lighting_info['status'], 
                   (lighting_x, lighting_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   self.base_font_scale * status_size,
                   lighting_info['color'], 
                   thickness)
        
        if lighting_info['contrast_warning']:
            contrast_x = 80  # Adjust this value
            contrast_y = 350  # Adjust this value
            cv2.putText(frame, "Low Contrast", 
                       (contrast_x, contrast_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.base_font_scale * status_size,
                       (0, 0, 255), 
                       thickness)
        
        # Control instructions position
        if view_info:
            control_x = 80  # Adjust this value
            control_y = self.window_height - 100  # Adjust this value
            control_text = "Controls: I/K: Tilt | J/L: Rotate | U/N: Height"
            cv2.putText(frame, control_text,
                       (control_x, control_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.base_font_scale * control_size,
                       (0, 255, 0), 
                       thickness + 1)
            
            try:
                parts = view_info.split('|')
                tilt = int(''.join(filter(str.isdigit, parts[1])))
                rotate = int(''.join(filter(str.isdigit, parts[2])))
                height = float(parts[3].split(':')[1].strip())
                
                # View info text position
                view_x = control_x  # Adjust this value
                view_y = control_y + 10  # Adjust this value
                view_info_text = f"Tilt: {tilt} | Rotate: {rotate} | Height: {height:.1f}"
                cv2.putText(frame, view_info_text,
                           (view_x, view_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           self.base_font_scale * control_size,
                           (0, 255, 0), 
                           thickness + 1)
            except (IndexError, ValueError) as e:
                cv2.putText(frame, view_info,
                           (control_x, control_y + 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           self.base_font_scale * control_size,  # Adjust this multiplier
                           (0, 255, 0), 
                           thickness + 1)

    def show_frame(self, frame):
        """Display frame with platform-specific handling"""
        if frame is None:
            return
        
        # Ensure frame is properly sized for display
        height, width = frame.shape[:2]
        max_dimension = 1280
        
        if width > max_dimension:
            scale = max_dimension / width
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        
        # Create named window with proper flags for Mac
        cv2.namedWindow('Pose Detection', cv2.WINDOW_NORMAL)
        cv2.imshow('Pose Detection', frame)

    def cleanup(self):
        pass  # Just pass as we don't need to clean up windows anymore