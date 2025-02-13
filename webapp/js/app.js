import { ThreeJSManager } from './modules/ThreeJSManager.js';
import { MediaPipeManager } from './modules/MediaPipeManager.js';
import { CameraController } from './modules/CameraController.js';
import { UIManager } from './ui/UIManager.js';

class App {
  constructor() {
    this.ui = new UIManager();
    this.threeManager = new ThreeJSManager('3dCanvas', {
      cameraPosition: { x: 0, y: 1.5, z: 3 },
      connectionColor: 0x00FF00
    });
    this.mediaPipe = new MediaPipeManager(
      this.ui.elements.video,
      this.ui.elements.canvas
    );

    this.init();
  }

  async init() {
    this.setupCameraController();
    this.setupMediaPipe();
    this.setupUI();
  }

  setupCameraController() {
    if (this.threeManager.camera && this.threeManager.controls) {
      new CameraController(this.threeManager.camera, this.threeManager.controls);
    }
  }

  async setupMediaPipe() {
    const success = await this.mediaPipe.initialize();
    if (success) {
      this.mediaPipe.pose.onResults(results => {
        this.mediaPipe.drawResults(results);
        this.threeManager.updatePose(results.poseLandmarks);
      });
    }
  }

  setupUI() {
    this.ui.elements.webcamButton.addEventListener('click', async () => {
      const isActive = await this.mediaPipe.toggleWebcam();
      this.ui.updateStatus(this.ui.elements.status.camera, isActive);
    });
  }
}

// Initialize application
new App(); 