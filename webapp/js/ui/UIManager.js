export class UIManager {
  constructor() {
    this.elements = {
      video: document.querySelector('.input_video'),
      canvas: document.querySelector('.output_canvas'),
      webcamButton: document.getElementById('webcamButton'),
      status: {
        camera: document.getElementById('cameraStatus'),
        pose: document.getElementById('poseStatus')
      }
    };
    
    this._initEventListeners();
  }

  _initEventListeners() {
    this.elements.webcamButton.addEventListener('click', () => {
      this.toggleButtonState();
    });
  }

  toggleButtonState() {
    const isActive = this.elements.webcamButton.classList.toggle('active');
    this.elements.webcamButton.textContent = isActive ? 'DISABLE WEBCAM' : 'ENABLE WEBCAM';
    return isActive;
  }

  updateStatus(element, active) {
    element.classList.toggle('status-red', !active);
    element.classList.toggle('status-green', active);
  }

  showError(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-toast';
    errorElement.textContent = message;
    document.body.appendChild(errorElement);
    
    setTimeout(() => {
      errorElement.remove();
    }, APP_CONFIG.ui.statusIndicatorTimeout);
  }
} 