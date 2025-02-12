import asyncio
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from ming3 import PoseAnalysisServer  # Import the PoseAnalysisServer class
import json
import random
import uvloop
import cv2
import numpy as np

# HTTP Server for static files
def run_http_server():
    class CORSRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory="static", **kwargs)
            
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    httpd = HTTPServer(('localhost', 8001), CORSRequestHandler)
    print("Serving HTTP on http://localhost:8001")
    httpd.serve_forever()

# WebSocket handler
async def websocket_handler(websocket):
    server = PoseAnalysisServer()
    print("New client connected")
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Directly process binary JPEG
                frame = cv2.imdecode(np.frombuffer(message, np.uint8), cv2.IMREAD_COLOR)
                result = await server.process_frame(frame)
                print(f"Processed frame, has_pose: {result['has_pose']}")
                await websocket.send(json.dumps(result))
            elif message == "ping":
                await websocket.send("pong")
                continue
            elif random.random() < 0.3:  # Drop 30% of frames when busy
                continue
            elif 'command' in message:
                print(f"Received command: {message['command']}")
                if message['command'] == 'adjust_view':
                    server.visualizer.adjust_elevation(message.get('value', 0))
                elif message['command'] == 'rotate_view':
                    server.visualizer.azim = (server.visualizer.azim + message.get('value', 0)) % 360
            else:
                print(f"Unknown message format: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        server.visualizer.cleanup()

# WebSocket Server
async def websocket_server():
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Run forever

async def main():
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()

    # Run WebSocket server
    await websocket_server()

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main()) 