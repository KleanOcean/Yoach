import cv2
import time
from datetime import datetime

class VideoRecorder:
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.start_time = None
        self.frame_count = 0
        
    def start_recording(self, frame_size, fps):
        if not self.is_recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pose_recording_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, fps, 
                                              (frame_size[1], frame_size[0]))
            self.is_recording = True
            self.start_time = time.time()
            self.frame_count = 0
            print(f"Started recording: {filename}")
            
    def stop_recording(self):
        if self.is_recording:
            duration = time.time() - self.start_time
            fps = self.frame_count / duration
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
                print(f"Recording stopped. Duration: {duration:.1f}s, Frames: {self.frame_count}, FPS: {fps:.1f}")
                
    def write_frame(self, frame):
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
            self.frame_count += 1
            
    def get_recording_time(self):
        if self.is_recording and self.start_time:
            return time.time() - self.start_time
        return 0

    def cleanup(self):
        self.stop_recording()

    # ... (rest of VideoRecorder class) 