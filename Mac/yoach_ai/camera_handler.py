import cv2
import platform
import time
import os
import numpy as np

class CameraHandler:
    def __init__(self, camera_id=0):
        """Initialize camera with proper settings"""
        self.camera_id = camera_id
        self.cap = None
        self.frame_count = 0
        self.initialize_camera()

    def initialize_camera(self):
        """Initialize camera with platform-specific settings"""
        if platform.system() == 'Darwin':  # macOS
            self._setup_mac_camera()
        else:
            self._setup_default_camera()

    def _setup_mac_camera(self):
        """Setup camera specifically for Mac"""
        os.environ['OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS'] = '0'
        
        for idx in [self.camera_id, 0, 2]:
            cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
            if self._configure_camera(cap):
                self.cap = cap
                print(f"Successfully opened camera {idx}")
                return
        
        # Fallback to default
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not initialize any camera")

    def _setup_default_camera(self):
        """Setup camera for non-Mac platforms"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("Could not initialize camera")

    def _configure_camera(self, cap):
        """Configure camera settings"""
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test frames
            for _ in range(5):
                ret, frame = cap.read()
                if ret and frame is not None and not np.all(frame == 0):
                    return True
                time.sleep(0.1)
        return False

    def read_frame(self):
        """Read a frame from camera"""
        if self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
        return ret, frame

    def get_fps(self):
        """Get camera FPS"""
        return int(self.cap.get(cv2.CAP_PROP_FPS))

    def reset(self):
        """Reset camera connection"""
        print("Resetting camera...")
        self.release()
        self.initialize_camera()

    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def cleanup(self):
        """Cleanup resources"""
        self.release() 