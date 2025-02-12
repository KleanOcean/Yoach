import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

try {
  const { Pose, Camera } = window;
  if (!Pose || !Camera) throw new Error('MediaPipe dependencies not loaded');
} catch (e) {
  console.error('MediaPipe initialization error:', e);
  alert('Failed to load MediaPipe libraries. Check your internet connection.');
}

const videoElement = document.getElementsByClassName('input_video')[0];
const canvasElement = document.getElementsByClassName('output_canvas')[0];
const canvasCtx = canvasElement.getContext('2d');
const controls = window;
let webcamRunning = false;

// Add these at the top
const statusElements = {
  camera: document.getElementById('cameraStatus'),
  pose: document.getElementById('poseStatus')
};

function updateStatus(element, active) {
  element.classList.remove(active ? 'status-red' : 'status-green');
  element.classList.add(active ? 'status-green' : 'status-red');
  element.textContent = `● ${element.id.replace('Status', '')}: ${active ? 'Active' : 'Inactive'}`;
}

// Configure pose detection
const pose = new Pose({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
});

pose.setOptions({
  modelComplexity: 1,
  smoothLandmarks: true,
  enableSegmentation: false,
  smoothSegmentation: true,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});

pose.onResults(onResults);

// Add after pose initialization
console.log('[Init] MediaPipe Pose initialized:', !!pose);
console.log('[Init] Camera system initialized:', !!Camera);
console.log('[Init] Video element:', videoElement);
console.log('[Init] Canvas context:', canvasCtx);

// Use MediaPipe's built-in connections
const POSE_CONNECTIONS = window.POSE_CONNECTIONS;

// Camera setup
const camera = new window.Camera(videoElement, {
  onFrame: async () => {
    if (webcamRunning) {
      try {
        await pose.send({image: videoElement});
        updateStatus(statusElements.pose, true);
      } catch (e) {
        console.error('[Pose] Processing error:', e);
        updateStatus(statusElements.pose, false);
      }
    }
  },
  width: 480,
  height: 270
});

// Control handlers
document.getElementById("webcamButton").addEventListener("click", async () => {
  if (!webcamRunning) {
    try {
      console.log('[Camera] Starting camera processing');
      webcamRunning = true;
      await camera.start();
      updateStatus(statusElements.camera, true);
      document.getElementById("webcamButton").classList.add("active");
      document.getElementById("webcamButton").innerText = "DISABLE WEBCAM";
    } catch (err) {
      console.error('[Camera] Start error:', err);
      updateStatus(statusElements.camera, false);
    }
  } else {
    console.log('[Camera] Stopping camera processing');
    webcamRunning = false;
    camera.stop();
    updateStatus(statusElements.camera, false);
    document.getElementById("webcamButton").classList.remove("active");
    document.getElementById("webcamButton").innerText = "ENABLE WEBCAM";
  }
});

// Initialize statuses on load
document.addEventListener('DOMContentLoaded', () => {
  updateStatus(statusElements.camera, false);
  updateStatus(statusElements.pose, false);
});

// Three.js initialization
const scene3D = new THREE.Scene();
const camera3D = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
const renderer3D = new THREE.WebGLRenderer({
  canvas: document.getElementById('3dCanvas'),
  antialias: true,
  width: 480,
  height: 270
});
renderer3D.setClearColor(0xe0e0e0); // Light gray
renderer3D.setPixelRatio(window.devicePixelRatio);
const keypoints3D = new THREE.Group();

// Update 3D initialization
function init3DScene() {
  const container = document.getElementById('q3');
  const width = 480;
  const height = 270;
  
  camera3D.position.set(0, 1.5, 2);
  camera3D.lookAt(0, 1, 0);
  
  // Add keypoints group to scene
  scene3D.add(keypoints3D);

  // Add controls
  const controls = new OrbitControls(camera3D, renderer3D.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // Add ambient light
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene3D.add(ambientLight);

  // Add directional light
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(1, 1, 1);
  scene3D.add(directionalLight);

  // Add grid helper
  const gridHelper = new THREE.GridHelper(3, 20);
  scene3D.add(gridHelper);

  camera3D.aspect = width/height;
  camera3D.updateProjectionMatrix();
  renderer3D.setSize(width, height);

  // Start animation loop
  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer3D.render(scene3D, camera3D);
  }
  animate();
}

// Initialize 3D scene on load
init3DScene();

// Update 3D visualization based on pose results
function update3DKeypoints(landmarks) {
  keypoints3D.clear();

  landmarks.forEach((landmark, i) => {
    const geometry = new THREE.SphereGeometry(0.08); // Increased from 0.05
    const material = new THREE.MeshPhongMaterial({ color: 0xff0000 });
    const sphere = new THREE.Mesh(geometry, material);
    
    // Convert to 3D space (MediaPipe coordinates are normalized)
    sphere.position.set(
      landmark.x * 2 - 1,     // X: [-1, 1]
      (1 - landmark.y) * 1.5, // Y: [0, 1.5]
      (landmark.z || 0) * -2  // Z: depth adjustment (fallback to 0 if undefined
    );
    
    keypoints3D.add(sphere);
  });

  // Add connections
  POSE_CONNECTIONS.forEach(([start, end]) => {
    const startPos = landmarks[start];
    const endPos = landmarks[end];
    
    const points = [];
    points.push(new THREE.Vector3(
      startPos.x * 2 - 1,
      (1 - startPos.y) * 1.5,
      startPos.z * -2
    ));
    points.push(new THREE.Vector3(
      endPos.x * 2 - 1,
      (1 - endPos.y) * 1.5,
      endPos.z * -2
    ));
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ 
      color: 0x00ff00,
      linewidth: 4 // Thicker lines
    });
    const line = new THREE.Line(geometry, material);
    keypoints3D.add(line);
  });
}

// Update the onResults function to include 3D updates
function onResults(results) {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  
  // Draw camera feed
  canvasCtx.drawImage(
    results.image,
    0, 0, canvasElement.width, canvasElement.height
  );

  // Draw pose landmarks
  if (results.poseLandmarks) {
    drawLandmarks(results.poseLandmarks);
    drawConnectors(results.poseLandmarks, POSE_CONNECTIONS);
    update3DKeypoints(results.poseLandmarks);
  }
  
  canvasCtx.restore();
}

// Drawing utilities
function drawLandmarks(landmarks) {
  landmarks.forEach(landmark => {
    const x = landmark.x * canvasElement.width;
    const y = landmark.y * canvasElement.height;
    
    canvasCtx.beginPath();
    canvasCtx.arc(x, y, 4, 0, 2 * Math.PI);
    canvasCtx.fillStyle = '#FF3030';
    canvasCtx.fill();
  });
}

function drawConnectors(landmarks, connections) {
  connections.forEach(([start, end]) => {
    const startLandmark = landmarks[start];
    const endLandmark = landmarks[end];
    
    canvasCtx.beginPath();
    canvasCtx.moveTo(
      startLandmark.x * canvasElement.width,
      startLandmark.y * canvasElement.height
    );
    canvasCtx.lineTo(
      endLandmark.x * canvasElement.width,
      endLandmark.y * canvasElement.height
    );
    canvasCtx.strokeStyle = '#30FF30';
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();
  });
}

// Test logging
console.log('[TEST] Basic console.log working');
setTimeout(() => {
  alert('If you see this, JavaScript is running!');
}, 1000);

// Enable line width support
renderer3D.localClippingEnabled = true;
