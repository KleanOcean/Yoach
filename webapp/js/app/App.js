import { MediaPipeManager } from '../modules/MediaPipeManager.js';
import { ThreeJSViewer } from '../modules/ThreeJSViewer.js';
import { UIManager } from '../ui/UIManager.js';
import { APP_CONFIG } from './config.js';

export class App {
  constructor() {
    this.ui = new UIManager();
    this.modules = {
      pose: this.initPoseDetection(),
      threeD: this.init3DVisualization()
    };
    
    this.registerEventListeners();
    this.initErrorHandling();
  }

  initPoseDetection() {
    return new MediaPipeManager({
      videoElement: this.ui.getVideoElement(),
      canvasElement: this.ui.getCanvasElement(),
      config: APP_CONFIG.mediaPipe
    });
  }

  init3DVisualization() {
    return new ThreeJSViewer({
      canvasId: '3dCanvas',
      config: APP_CONFIG.threeJS
    });
  }

  registerEventListeners() {
    this.ui.on('webcamToggle', async (enabled) => {
      try {
        const success = await this.modules.pose.toggleWebcam();
        this.ui.updateCameraStatus(success);
        if (success) this.modules.threeD.enable();
      } catch (error) {
        this.ui.showError('Camera failed to start');
      }
    });
  }

  initErrorHandling() {
    window.addEventListener('error', (event) => {
      this.ui.showError(event.message);
    });
  }
} 