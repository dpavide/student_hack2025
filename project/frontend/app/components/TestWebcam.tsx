import React, { useRef, useState, useEffect } from 'react';
import ReactWebcam from 'react-webcam';
import axios from 'axios';

const TestWebcamFeedback: React.FC = () => {
  const webcamRef = useRef<ReactWebcam>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [annotatedImage, setAnnotatedImage] = useState<string>('');
  const [exercise, setExercise] = useState<string>(''); // "pushup" or "squat"

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
        exercise: exercise, // sending exercise type along with image
      });
      // Assuming your backend returns a JSON with "feedback" and "annotated_image"
      const { feedback, annotated_image } = response.data;
      setFeedback(feedback);
      setAnnotatedImage(annotated_image);
    } catch (error) {
      console.error('Error analyzing frame:', error);
      setFeedback('Error analyzing frame.');
    }
  };

  // Set up a timer to continuously analyze frames (e.g., every 100ms)
  useEffect(() => {
    const interval = setInterval(() => {
      analyzeFrame();
    }, 100);
    return () => clearInterval(interval);
  }, [exercise]); // re-run if exercise state changes

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
      <div style={styles.buttonContainer}>
        <button onClick={() => setExercise('pushup')} style={styles.button}>
          Pushup
        </button>
        <button onClick={() => setExercise('squat')} style={styles.button}>
          Squat
        </button>
        <button 
          onClick={() => setExercise('bicep')}
          style={styles.button}>
        Bicep Curls
        </button>
      </div>
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
  buttonContainer: {
    display: 'flex',
    gap: '10px',
    marginBottom: 20,
  },
  button: {
    padding: '10px 20px',
    fontSize: '16px',
    cursor: 'pointer',
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
