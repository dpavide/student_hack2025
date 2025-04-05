import React, { useEffect, useRef } from 'react';

const OpenCVVideoComponent = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const capRef = useRef(null);

  useEffect(() => {
    // Wait until opencv.js is loaded.
    const waitForOpenCV = setInterval(() => {
      if (window.cv && window.cv.VideoCapture) {
        clearInterval(waitForOpenCV);
        startVideo();
      }
    }, 100);

    const startVideo = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
          streamRef.current = stream;
          video.srcObject = stream;
          video.play();

          video.addEventListener('loadedmetadata', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            // Create a VideoCapture instance from the video element.
            capRef.current = new cv.VideoCapture(video);
            processVideo();
          });
        })
        .catch((err) => {
          console.error('Error accessing webcam:', err);
        });
    };

    const processVideo = () => {
      const canvas = canvasRef.current;
      const cap = capRef.current;
      // Create matrices for frame processing.
      let src = new cv.Mat(canvas.height, canvas.width, cv.CV_8UC4);
      let dst = new cv.Mat(canvas.height, canvas.width, cv.CV_8UC1);

      const processFrame = () => {
        try {
          cap.read(src);
          // Example processing: convert the frame to grayscale.
          cv.cvtColor(src, dst, cv.COLOR_RGBA2GRAY);
          // Display the processed frame on the canvas.
          cv.imshow(canvas, dst);
        } catch (err) {
          console.error('Error during frame processing:', err);
        }
        requestAnimationFrame(processFrame);
      };
      requestAnimationFrame(processFrame);
    };

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return (
    <div>
      {/* Hidden video element used for capturing the webcam stream */}
      <video ref={videoRef} style={{ display: 'none' }}></video>
      {/* Canvas element to display the processed video */}
      <canvas ref={canvasRef} style={{ border: '1px solid black' }}></canvas>
    </div>
  );
};

export default OpenCVVideoComponent;
