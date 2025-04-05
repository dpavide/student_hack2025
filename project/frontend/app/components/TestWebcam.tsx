import React, { useRef, useState, useEffect } from 'react';
import ReactWebcam from 'react-webcam';
import axios from 'axios';

const TestWebcamFeedback: React.FC = () => {
  const webcamRef = useRef<ReactWebcam>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [annotatedImage, setAnnotatedImage] = useState<string>('');

  // Function to capture a frame and send it to the backend
  const analyzeFrame = async () => {
    const imageData = webcamRef.current?.getScreenshot();
    if (!imageData) {
      setFeedback('Could not capture image.');
      return;
    }

    try {
      const response = await axios.post('http://127.0.0.1:5000/analyze', {
        image: imageData,
      });
      // Expecting backend to return JSON with "feedback" and "annotated_image"
      const { feedback, annotated_image } = response.data;
      setFeedback(feedback);
      setAnnotatedImage(annotated_image);
    } catch (error) {
      console.error('Error analyzing frame:', error);
      setFeedback('Error analyzing frame.');
    }
  };

  // Automatically capture and analyze frames every second
  useEffect(() => {
    const interval = setInterval(() => {
      analyzeFrame();
    }, 100); // Adjust interval (in ms) as needed
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.container}>
      <h2>Continuous Webcam Feedback</h2>
      <ReactWebcam
        ref={webcamRef}
        audio={false}
        screenshotFormat="image/jpeg"
        videoConstraints={{ facingMode: 'user' }}
        style={styles.webcam}
      />
      <div style={styles.output}>
        <h3>Feedback: {feedback}</h3>
        {annotatedImage && (
          <img src={annotatedImage} alt="Annotated" style={styles.annotatedImage} />
        )}
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    fontFamily: 'Arial, sans-serif',
    padding: 20,
  },
  webcam: {
    width: 640,
    height: 480,
    border: '1px solid #ccc',
    marginBottom: 20,
  },
  output: {
    textAlign: 'center',
  },
  annotatedImage: {
    width: 640,
    height: 480,
    border: '1px solid #ccc',
    marginTop: 10,
  },
};

export default TestWebcamFeedback;
