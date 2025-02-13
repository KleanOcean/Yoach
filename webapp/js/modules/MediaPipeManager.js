export class MediaPipeManager {
  constructor(videoElement, canvasElement) {
    this.video = videoElement;
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.pose = null;
    this.camera = null;
    this.webcamRunning = false;
  }

  async initialize() {
    try {
      const { Pose, Camera } = window;
      this.pose = new Pose({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
      });

      this.pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
      });

      this.camera = new Camera(this.video, {
        onFrame: async () => {
          if (this.webcamRunning) {
            await this.pose.send({ image: this.video });
          }
        },
        width: 480,
        height: 270
      });

      return true;
    } catch (error) {
      console.error('[MediaPipe] Initialization error:', error);
      return false;
    }
  }

  async toggleWebcam() {
    if (!this.webcamRunning) {
      await this.startWebcam();
    } else {
      this.stopWebcam();
    }
    return this.webcamRunning;
  }

  async startWebcam() {
    try {
      this.webcamRunning = true;
      await this.camera.start();
      return true;
    } catch (error) {
      console.error('[Camera] Start error:', error);
      this.webcamRunning = false;
      return false;
    }
  }

  stopWebcam() {
    this.webcamRunning = false;
    this.camera.stop();
  }

  drawResults(results) {
    this.ctx.save();
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Always draw camera feed
    this.drawCameraFeed(results);

    // Only draw landmarks if detected
    if (results?.poseLandmarks?.length > 0) {
      this.drawLandmarks(results.poseLandmarks);
      this.drawConnectors(results.poseLandmarks, this.getConnections());
    }
    
    this.ctx.restore();
    return results;
  }

  drawCameraFeed(results) {
    this.ctx.drawImage(results.image, 0, 0, this.canvas.width, this.canvas.height);
  }

  drawLandmarks(landmarks) {
    this.ctx.globalCompositeOperation = 'source-atop';
    this.ctx.fillStyle = 'rgba(0, 127, 139, 0.5)';

    landmarks.forEach(landmark => {
      this.ctx.beginPath();
      this.ctx.arc(
        landmark.x * this.canvas.width,
        landmark.y * this.canvas.height,
        5, 0, 2 * Math.PI
      );
      this.ctx.fill();
    });
  }

  drawConnectors(landmarks, connections) {
    this.ctx.strokeStyle = '#30FF30';
    this.ctx.lineWidth = 3;

    connections.forEach(([start, end]) => {
      const startLandmark = landmarks[start];
      const endLandmark = landmarks[end];

      this.ctx.beginPath();
      this.ctx.moveTo(
        startLandmark.x * this.canvas.width,
        startLandmark.y * this.canvas.height
      );
      this.ctx.lineTo(
        endLandmark.x * this.canvas.width,
        endLandmark.y * this.canvas.height
      );
      this.ctx.stroke();
    });
  }

  getConnections() {
    return [
      [0,1], [1,2], [2,3], [3,7],    // Face left
      [0,4], [4,5], [5,6], [6,8],    // Face right
      [9,10],                         // Mouth
      [11,12], [11,13], [12,14],     // Shoulders
      [13,15], [14,16],               // Arms
      [23,24], [23,25], [24,26],     // Hips
      [25,27], [26,28]                // Legs
    ];
  }
} 