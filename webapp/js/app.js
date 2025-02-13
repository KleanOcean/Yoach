import { ThreeJSViewer } from './modules/ThreeJSViewer.js';
import { MediaPipeManager } from './modules/MediaPipeManager.js';
import { CameraController } from './modules/CameraController.js';
import { UIManager } from './managers/UIManager.js';

class App {
  constructor() {
    this.ui = new UIManager();
    this.threeViewer = new ThreeJSViewer('3dCanvas');
    this.mediaPipe = new MediaPipeManager(
      document.querySelector('.input_video'),
      document.querySelector('.output_canvas')
    );

    this.init();
  }

  async init() {
    this.setupCameraController();
    this.setupMediaPipe();
    this.setupUI();
  }

  setupCameraController() {
    if (this.threeViewer.camera && this.threeViewer.controls) {
      new CameraController(this.threeViewer.camera, this.threeViewer.controls);
    }
  }

  async setupMediaPipe() {
    const success = await this.mediaPipe.initialize();
    if (success) {
      this.mediaPipe.pose.onResults(results => {
        this.mediaPipe.drawResults(results);
        this.threeViewer.updatePose(results.poseLandmarks);
      });
    }
  }

  setupUI() {
    this.ui.setupWebcamButton(async () => {
      const isActive = await this.mediaPipe.toggleWebcam();
      this.ui.updateStatus(this.ui.statusElements.camera, isActive);
      return isActive;
    });
  }
}

// Initialize application
new App(); 