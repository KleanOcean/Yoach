export const APP_CONFIG = {
  mediaPipe: {
    modelComplexity: 1,
    minDetectionConfidence: 0.5,
    cameraResolution: { width: 640, height: 480 }
  },
  threeJS: {
    initialCameraPosition: { x: 0, y: 1.5, z: 3 },
    connectionColors: {
      default: '#00FF00',
      highlighted: '#FF0000'
    }
  },
  ui: {
    refreshInterval: 100, // ms
    statusIndicatorTimeout: 3000
  }
}; 