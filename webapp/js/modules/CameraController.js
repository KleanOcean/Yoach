export class CameraController {
  constructor(camera, controls) {
    this.camera = camera;
    this.controls = controls;
    this.speed = 0.1;
    this.bounds = {
      minY: -2, maxY: 2,
      minX: -2, maxX: 2
    };

    this.initControls();
  }

  initControls() {
    document.addEventListener('keydown', (e) => this.handleKeyInput(e));
  }

  handleKeyInput(event) {
    const key = event.key.toLowerCase();
    if (!['i','k','j','l'].includes(key)) return;

    const moveStep = this.speed;
    const newPos = {...this.camera.position};

    switch(key) {
      case 'i': newPos.y += moveStep; break;
      case 'k': newPos.y -= moveStep; break;
      case 'j': newPos.x -= moveStep; break;
      case 'l': newPos.x += moveStep; break;
    }

    this.camera.position.set(
      Math.max(Math.min(newPos.x, this.bounds.maxX), this.bounds.minX),
      Math.max(Math.min(newPos.y, this.bounds.maxY), this.bounds.minY),
      newPos.z
    );

    this.camera.lookAt(this.controls.target);
    this.controls.update();
  }
} 