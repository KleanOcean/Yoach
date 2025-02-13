import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export class ThreeJSManager {
  constructor(canvasId, config = {}) {
    this.config = {
      cameraPosition: { x: 0, y: 1.5, z: 3 },
      connectionColor: 0x00FF00,
      ...config
    };

    this.canvas = document.getElementById(canvasId);
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    this.renderer = null;
    this.controls = null;
    this.keypoints = new THREE.Group();
    this.connections = new THREE.Group();

    this.initialize();
  }

  initialize() {
    try {
      // Setup renderer
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true,
        alpha: false
      });
      
      // Setup camera
      this.camera.position.set(
        this.config.cameraPosition.x,
        this.config.cameraPosition.y,
        this.config.cameraPosition.z
      );
      this.camera.lookAt(0, 0, 0);
      
      // Setup scene
      this.setupLights();
      this.setupControls();
      this.setupRenderer();
      
      window.addEventListener('resize', () => this.handleResize());
      this.handleResize();
      
    } catch (error) {
      console.error('[3D] Initialization failed:', error);
      this.renderer = null;
    }
  }

  setupLights() {
    const ambient = new THREE.AmbientLight(0xFFFFFF, 0.5);
    const directional = new THREE.DirectionalLight(0xFFFFFF, 0.5);
    directional.position.set(2, 2, 5);
    this.scene.add(ambient, directional);
  }

  setupControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableZoom = false;
    this.controls.enableKeys = false;
  }

  setupRenderer() {
    this.renderer.setClearColor(0xF0F0F0);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.handleResize();
  }

  handleResize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    
    if (this.camera) {
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
    }
    
    if (this.renderer) {
      this.renderer.setSize(width, height);
    }
  }

  updatePose(landmarks) {
    if (!landmarks || !Array.isArray(landmarks)) {
      this.clearScene();
      return;
    }

    this.clearScene();
    this.createLandmarks(landmarks);
    this.createConnections();
    this.render();
  }

  createLandmarks(landmarks) {
    landmarks.forEach((landmark, index) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.04),
        new THREE.MeshPhongMaterial({ color: 0xFF0000 })
      );
      
      sphere.position.set(
        (landmark.x - 0.5) * 2,
        (-landmark.y + 0.5) * 2,
        (landmark.z || 0) * 2
      );
      
      this.keypoints.add(sphere);
    });
    
    this.scene.add(this.keypoints);
  }

  createConnections() {
    const connections = [
      [11, 12], [11, 13], [12, 14],
      [13, 15], [14, 16],
      [23, 24], [23, 25], [24, 26],
      [25, 27], [26, 28]
    ];

    connections.forEach(([start, end]) => {
      const startPoint = this.keypoints.children[start];
      const endPoint = this.keypoints.children[end];
      
      if (startPoint && endPoint) {
        const connection = this.createConnection(startPoint, endPoint);
        this.connections.add(connection);
      }
    });
    
    this.scene.add(this.connections);
  }

  createConnection(start, end) {
    const material = new THREE.MeshPhongMaterial({
      color: this.config.connectionColor,
      transparent: true,
      opacity: 0.9
    });

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
    this.keypoints.clear();
    this.connections.clear();
  }

  render() {
    if (this.renderer) {
      this.renderer.render(this.scene, this.camera);
    }
  }
} 