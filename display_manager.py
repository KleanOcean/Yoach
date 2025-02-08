import cv2
import numpy as np

class DisplayManager:
    def __init__(self, window_width=2880, window_height=1620):
        self.window_name = 'Yoach Sports Analysis'
        self.window_width = window_width
        self.window_height = window_height
        self.base_font_scale = window_height / 500.0 * 0.75
        self.base_thickness = max(1, int(self.base_font_scale * 2))
        self._init_window()

    def _init_window(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

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
        self._add_centered_text(q2, "Coach Chat", 1.5, is_title=True, color=(0, 0, 0))
        full_frame[0:quad_height, quad_width:] = q2
        
        # Q3: 3D Visualizer (bottom-left)
        resized_3d = self._resize_with_aspect_ratio(frame_3d, quad_width, quad_height)
        pad_3d = self._add_padding(resized_3d, quad_width, quad_height)
        full_frame[quad_height:, 0:quad_width] = pad_3d
        
        # Q4: Sports Analysis (bottom-right) with white background
        q4 = np.full((quad_height, quad_width, 3), 255, dtype=np.uint8)  # White background
        self._add_centered_text(q4, "Sports Analysis", 1.5, is_title=True, color=(0, 0, 0))
        
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
        """Add text to frame, either centered or as a title"""
        font_scale = self.base_font_scale * scale_factor
        if is_title:
            font_scale *= 0.8  # Make title smaller
        thickness = max(1, int(self.base_thickness * scale_factor))
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Calculate position
        if is_title:
            # Position at top with padding
            x = (frame.shape[1] - text_width) // 2
            y = text_height + 40  # Add padding from top
        else:
            # Center position
            x = (frame.shape[1] - text_width) // 2
            y = (frame.shape[0] + text_height) // 2
        
        cv2.putText(frame, text, (x, y),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    def add_overlays(self, frame, fps, lighting_info, view_info):
        font_scale = self.base_font_scale
        thickness = self.base_thickness
        
        # Add FPS (Q1)
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(frame, fps_text,
                   (30, self.window_height//2 - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
        
        # Add lighting status (Q1)
        cv2.putText(frame, lighting_info['status'], 
                   (30, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, lighting_info['color'], thickness)
        
        if lighting_info['contrast_warning']:
            cv2.putText(frame, "Low Contrast", 
                       (30, 135),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
        
        # Add view controls and info (Q3)
        if view_info:
            lines = view_info.split('\n')
            for i, line in enumerate(lines):
                text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                text_x = self.window_width//2 - text_size[0] - 20
                text_y = self.window_height - 20 - (len(lines) - 1 - i) * int(25 * font_scale)
                cv2.putText(frame, line,
                           (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)

    def show_frame(self, frame):
        cv2.imshow(self.window_name, frame)

    def cleanup(self):
        cv2.destroyAllWindows()
        cv2.waitKey(1)