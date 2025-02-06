import cv2
import time
import os
import platform
import numpy as np

class VideoRecorder:
    def __init__(self, output_dir="recordings", target_fps=30):
        self.is_recording = False
        self.output_video = None
        self.record_start_time = None
        self.output_dir = output_dir
        self.frames = []  # Store frames in memory
        self.frame_timestamps = []  # Store timestamps for each frame
        self.target_fps = target_fps
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def write_frame(self, frame, results):
        """Store frame and pose data if recording"""
        if self.is_recording:
            self.frames.append(frame.copy())
            self.frame_timestamps.append(time.time())

    def start_recording(self, frame_shape, fps):
        """Start recording video"""
        if not self.is_recording:
            self.frames = []
            self.frame_timestamps = []
            self.record_start_time = time.time()
            self.is_recording = True
            print("Started recording")

    def stop_recording(self):
        """Stop recording video and save video"""
        if self.is_recording:
            self.is_recording = False
            if self.frames:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.output_dir, f'ray2_output_{timestamp}.mp4')
                
                # Get frame dimensions from the first frame
                height, width = self.frames[0].shape[:2]
                
                # Calculate actual duration and required frames
                total_duration = self.frame_timestamps[-1] - self.frame_timestamps[0]
                total_frames_needed = int(total_duration * self.target_fps)
                print(f"Recording duration: {total_duration:.2f}s")
                
                # Create frame mapping to match original timing
                output_frames = []
                for i in range(total_frames_needed):
                    target_time = self.frame_timestamps[0] + (i / self.target_fps)
                    # Find the closest frame to the target time
                    frame_idx = min(range(len(self.frame_timestamps)), 
                                  key=lambda x: abs(self.frame_timestamps[x] - target_time))
                    output_frames.append(self.frames[frame_idx])
                
                # Try different codecs
                if platform.system() == 'Darwin':  # macOS
                    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
                else:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                
                try:
                    # Create video writer
                    out = cv2.VideoWriter(
                        output_path,
                        fourcc,
                        self.target_fps,
                        (width, height)
                    )
                    
                    # Write frames
                    for frame in output_frames:
                        out.write(frame)
                    
                    # Release video writer
                    out.release()
                    print(f"Successfully saved video to {output_path}")
                    print(f"Original frames: {len(self.frames)}, Output frames: {len(output_frames)}")
                    
                except Exception as e:
                    print(f"Failed to save video with first codec, trying alternative...")
                    try:
                        # Try alternative codec
                        alternative_path = os.path.join(self.output_dir, f'ray2_output_{timestamp}_alt.mp4')
                        out = cv2.VideoWriter(
                            alternative_path,
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            self.target_fps,
                            (width, height)
                        )
                        
                        for frame in output_frames:
                            out.write(frame)
                        
                        out.release()
                        print(f"Successfully saved video to {alternative_path}")
                        
                    except Exception as e2:
                        print(f"Failed to save video: {str(e2)}")
                        # Save frames as individual images as last resort
                        images_dir = os.path.join(self.output_dir, f'ray2_output_{timestamp}_frames')
                        os.makedirs(images_dir, exist_ok=True)
                        for i, frame in enumerate(output_frames):
                            cv2.imwrite(os.path.join(images_dir, f'frame_{i:04d}.jpg'), frame)
                        print(f"Saved individual frames to {images_dir}")
                
                # Clear frames and timestamps
                self.frames = []
                self.frame_timestamps = []
            print("Stopped recording")

    def add_recording_indicator(self, frame):
        """Add recording indicator to frame"""
        if self.is_recording:
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            elapsed_time = time.time() - self.record_start_time
            time_str = f"REC {int(elapsed_time)}s"
            cv2.putText(frame, time_str, (50, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame

    def cleanup(self):
        """Cleanup resources"""
        self.stop_recording() 