export class UIManager {
  constructor() {
    this.statusElements = {
      camera: document.getElementById('cameraStatus'),
      pose: document.getElementById('poseStatus')
    };
  }

  updateStatus(element, active) {
    element.classList.toggle('status-red', !active);
    element.classList.toggle('status-green', active);
    element.textContent = `● ${element.id.replace('Status', '')}: ${active ? 'Active' : 'Inactive'}`;
  }

  setupWebcamButton(handler) {
    const button = document.getElementById('webcamButton');
    button.addEventListener('click', async () => {
      const isActive = await handler();
      button.classList.toggle('active', isActive);
      button.textContent = isActive ? 'DISABLE WEBCAM' : 'ENABLE WEBCAM';
    });
  }
} 