import React, { useRef, useState, useEffect } from 'react';
import ReactWebcam from 'react-webcam';
import axios from 'axios';

const TestWebcamFeedback: React.FC = () => {
  const webcamRef = useRef<ReactWebcam>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [annotatedImage, setAnnotatedImage] = useState<string>('');
  const [isStopped, setIsStopped] = useState<boolean>(false);

  // Function to capture a frame and send it to the backend
  const analyzeFrame = async () => {
    if (isStopped) return; // Stop analyzing if we've stopped the camera

    const imageData = webcamRef.current?.getScreenshot();
    if (!imageData) {
      setFeedback('Could not capture image.');
      return;
    }

    try {
      const response = await axios.post('http://127.0.0.1:5000/analyze', {
        image: imageData,
      });
      const { feedback, annotated_image } = response.data;
      setFeedback(feedback);
      setAnnotatedImage(annotated_image);
    } catch (error) {
      console.error('Error analyzing frame:', error);
      setFeedback('Error analyzing frame.');
    }
  };

  // Set up a timer to continuously analyze frames (every 1 second)
  useEffect(() => {
    if (isStopped) return;
    const interval = setInterval(() => {
      analyzeFrame();
    }, 100);
    return () => clearInterval(interval);
  }, [isStopped]);

  // Stop handler: first start Gemini, wait 2 seconds, then shut down app.py
  const handleStop = async () => {
    try {
      // Start Gemini process first
      await axios.post('http://127.0.0.1:5000/start-gemini');
      
      // Wait 2 seconds to let gemini.py launch
      setTimeout(async () => {
        await axios.post('http://127.0.0.1:5000/shutdown');
      }, 2000);
      
      // Stop the webcam stream
      if (webcamRef.current) {
        const stream = webcamRef.current.video?.srcObject;
        if (stream) {
          const tracks = (stream as MediaStream).getTracks();
          tracks.forEach(track => track.stop());
        }
      }
      setIsStopped(true);
      setFeedback("Switched to AI mode - Camera stopped");
    } catch (error) {
      console.error('Shutdown failed:', error);
      setFeedback("Error switching to AI mode");
    }
  };

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
      <button onClick={handleStop} style={styles.button}>
        Stop & Switch to AI Mode
      </button>
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
  button: {
    marginTop: 20,
    padding: '10px 20px',
    fontSize: '16px',
    cursor: 'pointer',
  },
};

export default TestWebcamFeedback;
