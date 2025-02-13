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

// Update MediaPipe configuration
try {
  pose.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    enableSegmentation: false,
    smoothSegmentation: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  });
} catch (error) {
  console.error('[MediaPipe] Initialization error:', error);
  alert('Failed to initialize MediaPipe. Check your internet connection.');
}

pose.onResults(onResults);

// Add after pose initialization
console.log('[Init] MediaPipe Pose initialized:', !!pose);
console.log('[Init] Camera system initialized:', !!Camera);
console.log('[Init] Video element:', videoElement);
console.log('[Init] Canvas context:', canvasCtx);

// Replace the existing POSE_CONNECTIONS with these custom connections
const customConnections = [
  // Face and head
  [0,1], [1,2], [2,3], [3,7],    // Left eye/ear
  [0,4], [4,5], [5,6], [6,8],    // Right eye/ear
  [9,10],                         // Mouth
  
  // Upper body
  [11,12], [11,13], [12,14],     // Shoulders and arms
  [13,15], [14,16],               // Elbows to wrists
  [15,17], [15,19], [15,21],     // Left hand
  [16,18], [16,20], [16,22],     // Right hand
  
  // Core
  [11,23], [12,24],               // Shoulders to hips
  [23,24],                        // Hips connection
  
  // Left leg
  [23,25], [25,27], [27,29], [27,31], 
  [29,31],                        // Left foot
  
  // Right leg
  [24,26], [26,28], [28,30], [28,32],
  [30,32],                        // Right foot
  
  // Cross-body connections
  [11,24], [12,23]                // Shoulder to opposite hip
];

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
      // Add small delay for camera warmup
      await new Promise(resolve => setTimeout(resolve, 500));
      updateStatus(statusElements.camera, true);
      document.getElementById("webcamButton").classList.add("active");
      document.getElementById("webcamButton").innerText = "DISABLE WEBCAM";
    } catch (err) {
      console.error('[Camera] Start error:', err);
      updateStatus(statusElements.camera, false);
      webcamRunning = false;
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
let renderer3D, scene3D, camera3D, controls3D, keypoints3D, connections3D;

try {
  const threeCanvas = document.getElementById('3dCanvas');
  if (!threeCanvas) throw new Error('3D canvas element not found');
  
  renderer3D = new THREE.WebGLRenderer({
    canvas: threeCanvas,
    antialias: true
  });
  
  scene3D = new THREE.Scene();
  camera3D = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
  camera3D.position.set(0, 0, 2);
  
  keypoints3D = new THREE.Group();
  scene3D.add(keypoints3D);
  
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene3D.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
  directionalLight.position.set(2, 2, 5);
  scene3D.add(directionalLight);
  
  controls3D = new OrbitControls(camera3D, renderer3D.domElement);
  controls3D.enableZoom = false;
  controls3D.enableKeys = false; // Disable default keyboard controls
  controls3D.screenSpacePanning = true; // Allow panning with mouse
  controls3D.mouseButtons = {
    LEFT: THREE.MOUSE.ROTATE,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.PAN
  };
  
  renderer3D.setClearColor(0xf0f0f0);
  renderer3D.setSize(480, 270);

  connections3D = new THREE.Group();
  scene3D.add(connections3D);
} catch (e) {
  console.error('[3D] Initialization failed:', e);
  renderer3D = null; // Ensure renderer is null if initialization fails
}

if (renderer3D) {
  renderer3D.setPixelRatio(window.devicePixelRatio);
}

// Update 3D initialization
function init3DScene() {
  const container = document.getElementById('q2');
  if (!container) {
    console.error('[3D] Container element not found');
    return;
  }

  // Set fixed size for stability
  const width = 640;
  const height = 480;
  
  renderer3D.setSize(width, height);
  camera3D.aspect = width / height;
  camera3D.updateProjectionMatrix();
  
  console.log('[3D] Initialized with size:', width, 'x', height);
}

// Initialize 3D scene on load
document.addEventListener('DOMContentLoaded', () => {
  init3DScene();
});

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
  customConnections.forEach(([start, end]) => {
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
  // Draw camera feed with masked keypoints
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  
  // Draw camera feed
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
  
  // Draw pose landmarks with masking effect
  if (results.poseLandmarks) {
    canvasCtx.globalCompositeOperation = 'source-atop';
    canvasCtx.fillStyle = 'rgba(0, 127, 139, 0.5)';
    
    // Draw keypoints
    results.poseLandmarks.forEach(landmark => {
      canvasCtx.beginPath();
      canvasCtx.arc(landmark.x * canvasElement.width, 
                    landmark.y * canvasElement.height, 
                    5, 0, 2 * Math.PI);
      canvasCtx.fill();
    });
    
    // Draw connections
    canvasCtx.strokeStyle = '#007f8b';
    canvasCtx.lineWidth = 2;
    customConnections.forEach(([start, end]) => {
      const startPoint = results.poseLandmarks[start];
      const endPoint = results.poseLandmarks[end];
      canvasCtx.beginPath();
      canvasCtx.moveTo(startPoint.x * canvasElement.width, startPoint.y * canvasElement.height);
      canvasCtx.lineTo(endPoint.x * canvasElement.width, endPoint.y * canvasElement.height);
      canvasCtx.stroke();
    });
  }
  canvasCtx.restore();

  // Update 3D visualization
  update3DView(results);
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
renderer3D.setPixelRatio(1);

// Add at the bottom of app.js
function logDimensions() {
  const container = document.querySelector('.grid-container');
  const q1 = document.getElementById('q1');
  const q2 = document.getElementById('q2');
  const q3 = document.getElementById('q3'); // Check if exists
  const q4 = document.getElementById('q4'); // Check if exists
  
  console.group('[DEBUG] Layout Dimensions');
  console.log('Window inner:', window.innerWidth, 'x', window.innerHeight);
  console.log('Grid Container - Width:', container?.clientWidth, 'Height:', container?.clientHeight);
  console.log('Q1 - Width:', q1?.clientWidth, 'Computed Width:', q1 ? getComputedStyle(q1).width : 'N/A');
  console.log('Q2 - Width:', q2?.clientWidth);
  if(q3) console.log('Q3 - Width:', q3.clientWidth);
  if(q4) console.log('Q4 - Width:', q4.clientWidth);
  console.groupEnd();
}

// Log on initial load
window.addEventListener('load', logDimensions);

// Log on resize
window.addEventListener('resize', logDimensions);

// Log after 3D initialization
setTimeout(logDimensions, 1000);

// Add CSS injection to override any other styles
const style = document.createElement('style');
style.textContent = `
  html, body {
    width: 1000px !important;
    height: 1000px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }
  .grid-container {
    width: 1000px !important;
    height: 1000px !important;
    transform: none !important;
  }
  .grid-item {
    width: 500px !important;
    height: 500px !important;
    overflow: visible !important;  // Allow content overflow
  }
  .video-container, #3dCanvas {
    transform: scale(0.9) !important;  // Scale down visual elements
    transform-origin: center center !important;
  }
  .output_canvas, #3dCanvas {
    position: absolute !important;
    z-index: 2 !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) scale(0.8) !important;
  }
  .input_video, .output_canvas {
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
    width: 480px !important;
    height: 270px !important;
    z-index: 3 !important;
  }
  
  #3dCanvas {
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
    width: 480px !important;
    height: 270px !important;
    z-index: 4 !important;  // Higher than video elements
    transform: translate(-50%, -50%) scale(0.8) !important;
  }`;
document.head.appendChild(style);

// Add video element monitoring
const videoObserver = new MutationObserver(() => {
  console.log('[Debug] Video element changed:', {
    src: videoElement.src,
    currentTime: videoElement.currentTime,
    readyState: videoElement.readyState
  });
});
videoObserver.observe(videoElement, { attributes: true });

// Add canvas monitoring
const canvasObserver = new MutationObserver(() => {
  console.log('[Debug] Canvas changed:', {
    width: canvasElement.width,
    height: canvasElement.height,
    data: canvasCtx.getImageData(0, 0, 1, 1).data
  });
});
canvasObserver.observe(canvasElement, { attributes: true });

// Add after renderer3D initialization
function resize3D() {
  renderer3D.setSize(480, 270);
  camera3D.aspect = 480/270;
  camera3D.updateProjectionMatrix();
  console.log('[3D] Forced resize to:', renderer3D.getSize());
}
resize3D();
window.addEventListener('resize', resize3D);

function update3DView(results) {
  if (!renderer3D || !scene3D || !camera3D) return;

  // Clear previous elements
  while(keypoints3D.children.length > 0) keypoints3D.remove(keypoints3D.children[0]);
  while(connections3D.children.length > 0) connections3D.remove(connections3D.children[0]);

  // Create keypoints with adjusted positions
  results.poseLandmarks.forEach((landmark, i) => {
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.04),
      new THREE.MeshPhongMaterial({color: 0xFF0000})
    );
    // Normalize coordinates to [-1, 1] range
    sphere.position.set(
      (landmark.x - 0.5) * 2,  // X: [-1, 1]
      (-landmark.y + 0.5) * 2, // Y: [-1, 1] 
      (landmark.z || 0) * 2    // Z: depth adjustment
    );
    keypoints3D.add(sphere);
  });

  // Create connection lines with proper scaling
  const connectionMaterial = new THREE.MeshPhongMaterial({
    color: 0x00FF00,
    transparent: true,
    opacity: 0.9
  });

  customConnections.forEach(([startIdx, endIdx]) => {
    const start = keypoints3D.children[startIdx];
    const end = keypoints3D.children[endIdx];
    if (!start || !end) return;

    // Calculate direction vector between points
    const direction = new THREE.Vector3()
      .subVectors(end.position, start.position)
      .normalize();
    
    // Create cylinder with proper length and rotation
    const distance = start.position.distanceTo(end.position);
    const geometry = new THREE.CylinderGeometry(0.02, 0.02, distance, 8);
    const cylinder = new THREE.Mesh(geometry, connectionMaterial);
    
    // Position at midpoint between points
    cylinder.position.lerpVectors(start.position, end.position, 0.5);
    
    // Align cylinder to point direction
    cylinder.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0), // Default cylinder orientation
      direction
    );

    connections3D.add(cylinder);
  });

  renderer3D.render(scene3D, camera3D);
}

// Add to the top with other declarations
const cameraControls = {
  speed: 0.1,
  minY: -2,
  maxY: 2,
  minX: -2,
  maxX: 2
};

// Add event listener for keyboard controls
document.addEventListener('keydown', (event) => {
  if (!renderer3D || !camera3D) return;

  const moveStep = 0.1;
  
  switch(event.key.toLowerCase()) {
    case 'i': // Tilt up
      camera3D.position.y = Math.min(camera3D.position.y + moveStep, cameraControls.maxY);
      break;
    case 'k': // Tilt down
      camera3D.position.y = Math.max(camera3D.position.y - moveStep, cameraControls.minY);
      break;
    case 'j': // Pan left
      camera3D.position.x = Math.max(camera3D.position.x - moveStep, cameraControls.minX);
      break;
    case 'l': // Pan right
      camera3D.position.x = Math.min(camera3D.position.x + moveStep, cameraControls.maxX);
      break;
  }

  // Update camera and controls
  camera3D.lookAt(scene3D.position);
  controls3D.update();
  renderer3D.render(scene3D, camera3D);
});
