import asyncio
import json
import cv2
import numpy as np
import websockets
import base64
from utils.pose_visualizer import PoseVisualizer
from utils.video_recorder import VideoRecorder
from utils.display_manager import DisplayManager
from mediapipe.python.solutions import pose as mp_pose
import time

class PoseAnalysisServer:
    def __init__(self):
        self.mp_pose = mp_pose
        self.visualizer = PoseVisualizer()
        self.recorder = VideoRecorder()
        self.display_manager = DisplayManager(window_width=1280, window_height=720)  # Adjusted for web display
        self.fps = 0
        self.fps_counter = 0
        self.fps_start_time = cv2.getTickCount()
        self.last_3d_update = time.time()
        self.cached_3d = None
        
        # Configure visualizer's pose detector with lighter settings
        self.visualizer.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )
        
    async def process_frame(self, frame_data):
        try:
            # Decode frame
            jpg_bytes = base64.b64decode(frame_data)
            frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return {'error': 'Failed to decode frame'}
            
            frame = cv2.resize(frame, (320, 240))
            
            # Process frame
            results = self.visualizer.process_frame(frame)
            
            # Create output
            combined_frame = self.display_manager.create_quadrant_layout(
                self.visualizer.draw_2d_pose(frame, results),
                self.cached_3d if self.cached_3d is not None else np.zeros((240,320,3), np.uint8),
                results
            )
            
            # Ensure valid image output
            if combined_frame.size == 0:
                return {'error': 'Empty frame generated'}
            
            _, buffer = cv2.imencode('.jpg', combined_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            return {
                'processed_frame': buffer.tobytes(),
                'has_pose': results.pose_landmarks is not None
            }
        except Exception as e:
            print(f"Processing error: {str(e)}")
            return {'error': str(e)}

    def get_lighting_info(self, frame):
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

async def handler(websocket, path):
    server = PoseAnalysisServer()
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if 'frame' in data:
                    result = await server.process_frame(data['frame'])
                    await websocket.send(json.dumps(result))
                elif 'command' in data:
                    # Handle commands (like view adjustments)
                    if data['command'] == 'adjust_view':
                        server.visualizer.adjust_elevation(data.get('value', 0))
                    elif data['command'] == 'rotate_view':
                        server.visualizer.azim = (server.visualizer.azim + data.get('value', 0)) % 360
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send(json.dumps({'error': str(e)}))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        server.visualizer.cleanup()

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    print("Running pose analysis server on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main()) 