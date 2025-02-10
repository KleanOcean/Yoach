from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
import sys
import cv2
import numpy as np

# Import your existing components
from pose_visualizer import PoseVisualizer
from video_recorder import VideoRecorder
from display_manager import DisplayManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sports Analysis System")
        self.setup_ui()
        self.setup_components()
        self.setup_timer()
        # Enable key press events
        self.setFocusPolicy(Qt.StrongFocus)

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Changed to HBoxLayout for side-by-side

        # Create left side container for display and controls
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        # Create display area
        display_widget = QWidget()
        display_layout = QHBoxLayout(display_widget)

        # Create frame display with 50% larger size
        self.frame_label = QLabel()
        self.frame_label.setMinimumSize(2160, 1215)  # 1440*1.5, 810*1.5
        self.frame_label.setAlignment(Qt.AlignCenter)
        display_layout.addWidget(self.frame_label)

        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        # Add buttons with larger size
        self.record_button = QPushButton("Record (V)")
        self.reset_button = QPushButton("Reset Camera (R)")
        self.quit_button = QPushButton("Quit (Q)")
        
        # Make buttons much larger
        button_height = 100
        for button in [self.record_button, self.reset_button, self.quit_button]:
            button.setMinimumHeight(button_height)
            button.setMinimumWidth(250)
            button.setFont(QFont('Arial', 40, QFont.Bold))
        
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addWidget(self.quit_button)

        # Add display and controls to left container
        left_layout.addWidget(display_widget)
        left_layout.addWidget(control_panel)

        # Create right side settings panel
        right_panel = QWidget()
        right_panel.setFixedWidth(600)  # Increased from 400 to 600
        right_layout = QVBoxLayout(right_panel)
        
        # Add settings title
        settings_title = QLabel("Chat Settings")
        settings_title.setFont(QFont('Arial', 48, QFont.Bold))  # Increased from 36 to 48
        settings_title.setAlignment(Qt.AlignCenter)
        settings_title.setStyleSheet("color: white; padding: 30px;")  # Increased padding
        right_layout.addWidget(settings_title)

        # Add some example settings (you can modify these)
        settings_options = [
            "Language Selection",
            "Voice Control",
            "Chat History",
            "Response Speed",
            "AI Model Settings"
        ]

        for option in settings_options:
            button = QPushButton(option)
            button.setFont(QFont('Arial', 32))  # Increased from 24 to 32
            button.setMinimumHeight(100)  # Increased from 80 to 100
            right_layout.addWidget(button)

        # Add stretch to push everything to the top
        right_layout.addStretch()

        # Add both sides to main layout
        main_layout.addWidget(left_container)
        main_layout.addWidget(right_panel)

        # Connect buttons
        self.record_button.clicked.connect(self.toggle_recording)
        self.reset_button.clicked.connect(self.reset_camera)
        self.quit_button.clicked.connect(self.close)

        # Set window properties
        self.setMinimumSize(2900, 1350)  # Increased from 2700 to 2900 to accommodate wider right panel
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 25px;
                min-width: 250px;
                border-radius: 12px;
                font-size: 40px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QLabel {
                background-color: black;
                border: 3px solid #4a4a4a;
            }
            QWidget#right_panel {
                background-color: #333333;
                border-left: 2px solid #4a4a4a;
            }
            QPushButton#settings_button {
                background-color: #333333;
                border: 2px solid #4a4a4a;
                border-radius: 8px;
                padding: 15px;
                font-size: 24px;
            }
        """)

    def setup_components(self):
        # Initialize your existing components
        self.camera = cv2.VideoCapture(0)
        self.visualizer = PoseVisualizer()
        self.recorder = VideoRecorder()
        self.display_manager = DisplayManager()
        
        # FPS calculation
        self.fps_start_time = cv2.getTickCount()
        self.fps_counter = 0
        self.fps = 0

    def setup_timer(self):
        # Create timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms = ~33fps

    def update_frame(self):
        # Process frame (similar to your main loop)
        ret, frame = self.camera.read()
        if not ret:
            return

        # Process frame using your existing code
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.visualizer.process_frame(frame_rgb)

        # Create visualizations
        frame_2d = frame.copy()  # Keep BGR format for 2D view
        if results.pose_landmarks:
            frame_2d = self.visualizer.draw_2d_pose(frame_2d, results)
        frame_3d = self.visualizer.visualize_3d_pose(results)

        # Get recording time if recording
        recording_time = self.recorder.get_recording_time() if self.recorder.is_recording else None

        # Create layout using display manager
        combined_frame = self.display_manager.create_quadrant_layout(
            frame_2d, frame_3d, results, recording_time)

        # Convert BGR to RGB for Qt display
        combined_frame_rgb = cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB)

        # Calculate FPS
        self.fps_counter += 1
        if self.fps_counter % 30 == 0:
            current_time = cv2.getTickCount()
            self.fps = 30 / ((current_time - self.fps_start_time) / cv2.getTickFrequency())
            self.fps_start_time = current_time

        # Add overlays
        lighting_info = self.get_lighting_info(frame)
        view_info = self.visualizer.current_view if hasattr(self.visualizer, 'current_view') else None
        self.display_manager.add_overlays(combined_frame, self.fps, lighting_info, view_info)

        # Handle recording
        if self.recorder.is_recording:
            self.recorder.write_frame(combined_frame)

        # Convert frame to Qt format and display
        h, w, ch = combined_frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(combined_frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.frame_label.setPixmap(scaled_pixmap)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.recorder.start_recording(
                (self.display_manager.window_height, self.display_manager.window_width),
                self.camera.get(cv2.CAP_PROP_FPS)
            )
            self.record_button.setText("Stop Recording")
        else:
            self.recorder.stop_recording()
            self.record_button.setText("Record (V)")

    def reset_camera(self):
        self.camera.release()
        self.camera = cv2.VideoCapture(0)

    def get_lighting_info(self, frame):
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

    def closeEvent(self, event):
        # Cleanup when closing
        self.timer.stop()
        self.camera.release()
        self.visualizer.cleanup()
        self.recorder.cleanup()
        self.display_manager.cleanup()
        event.accept()

    def keyPressEvent(self, event):
        # Handle 3D view controls
        if event.key() == Qt.Key_I:  # Tilt up
            self.visualizer.adjust_elevation(5)
        elif event.key() == Qt.Key_K:  # Tilt down
            self.visualizer.adjust_elevation(-5)
        elif event.key() == Qt.Key_J:  # Rotate left
            self.visualizer.azim = (self.visualizer.azim + 5) % 360
        elif event.key() == Qt.Key_L:  # Rotate right
            self.visualizer.azim = (self.visualizer.azim - 5) % 360
        elif event.key() == Qt.Key_U:  # Height up
            self.visualizer.adjust_z_offset(self.visualizer.z_step)
        elif event.key() == Qt.Key_N:  # Height down
            self.visualizer.adjust_z_offset(-self.visualizer.z_step)
        # Handle other controls
        elif event.key() == Qt.Key_V:  # Toggle recording
            self.toggle_recording()
        elif event.key() == Qt.Key_R:  # Reset camera
            self.reset_camera()
        elif event.key() == Qt.Key_Q:  # Quit
            self.close()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()