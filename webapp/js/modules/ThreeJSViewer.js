import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export class ThreeJSViewer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = null;
    this.controls = null;
    this.keypoints = new THREE.Group();
    this.connections = new THREE.Group();
    this.customConnections = [
      [0,1], [1,2], [2,3], [3,7],
      [0,4], [4,5], [5,6], [6,8],
      [9,10],
      [11,12], [11,13], [12,14],
      [13,15], [14,16],
      [23,24], [23,25], [24,26],
      [25,27], [26,28]
    ];

    this.init();
  }

  init() {
    try {
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true
      });
      
      this.camera.position.set(0, 0, 2);
      this.scene.add(this.keypoints, this.connections);
      
      this.setupLights();
      this.setupControls();
      this.setupRenderer();

    } catch (e) {
      console.error('[3D] Initialization failed:', e);
      this.renderer = null;
    }
  }

  setupLights() {
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(2, 2, 5);
    this.scene.add(ambientLight, directionalLight);
  }

  setupControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableZoom = false;
    this.controls.enableKeys = false;
    this.controls.screenSpacePanning = true;
  }

  setupRenderer() {
    this.renderer.setClearColor(0xf0f0f0);
    this.renderer.setSize(480, 270);
    this.renderer.setPixelRatio(1);
  }

  updatePose(landmarks) {
    if (!landmarks || !Array.isArray(landmarks)) {
      console.log('[3D] No landmarks detected - clearing scene');
      this.clearScene();
      this.render();
      return;
    }

    this.clearScene();
    
    try {
      landmarks.forEach((landmark, i) => {
        const sphere = this.createSphere(landmark);
        this.keypoints.add(sphere);
      });

      this.createConnections();
    } catch (e) {
      console.error('[3D] Error updating pose:', e);
      this.clearScene();
    }
    
    this.render();
  }

  createSphere(landmark) {
    const geometry = new THREE.SphereGeometry(0.04);
    const material = new THREE.MeshPhongMaterial({ color: 0xFF0000 });
    const sphere = new THREE.Mesh(geometry, material);
    
    sphere.position.set(
      (landmark.x - 0.5) * 2,
      (-landmark.y + 0.5) * 2,
      (landmark.z || 0) * 2
    );
    
    return sphere;
  }

  createConnections() {
    const material = new THREE.MeshPhongMaterial({
      color: 0x00FF00,
      transparent: true,
      opacity: 0.9
    });

    this.customConnections.forEach(([startIdx, endIdx]) => {
      const start = this.keypoints.children[startIdx];
      const end = this.keypoints.children[endIdx];
      if (!start || !end) return;

      const connection = this.createConnection(start, end, material);
      this.connections.add(connection);
    });
  }

  createConnection(start, end, material) {
    const direction = new THREE.Vector3()
      .subVectors(end.position, start.position)
      .normalize();

    const distance = start.position.distanceTo(end.position);
    const geometry = new THREE.CylinderGeometry(0.02, 0.02, distance, 8);
    const cylinder = new THREE.Mesh(geometry, material);

    cylinder.position.lerpVectors(start.position, end.position, 0.5);
    cylinder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);

    return cylinder;
  }

  clearScene() {
    while(this.keypoints.children.length > 0) this.keypoints.remove(this.keypoints.children[0]);
    while(this.connections.children.length > 0) this.connections.remove(this.connections.children[0]);
  }

  render() {
    if (this.renderer) {
      this.renderer.render(this.scene, this.camera);
    }
  }
} 