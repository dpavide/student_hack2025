import React, { useRef, useState, useEffect } from 'react';
import ReactWebcam from 'react-webcam';
import axios from 'axios';

const TestWebcamFeedback: React.FC<{ presetExercise?: string }> = ({ presetExercise }) => {
  // Initialize with preset exercise if provided
  const [exercise, setExercise] = useState<string>(presetExercise || '');
  const webcamRef = useRef<ReactWebcam>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [annotatedImage, setAnnotatedImage] = useState<string>('');
  const [isStopped, setIsStopped] = useState<boolean>(false);

  // Function to capture a frame and send it to the backend
  const analyzeFrame = async () => {
    if (isStopped) return;
    const imageData = webcamRef.current?.getScreenshot();
    if (!imageData) {
      setFeedback('Could not capture image.');
      return;
    }
    try {
      const response = await axios.post('http://127.0.0.1:5000/analyze', {
        image: imageData,
        exercise: exercise,
      });
      const { feedback, annotated_image } = response.data;
      setFeedback(feedback);
      setAnnotatedImage(annotated_image);
    } catch (error) {
      console.error('Error analyzing frame:', error);
      setFeedback('Error analyzing frame.');
    }
  };

  // Set up a timer to continuously analyze frames every second
  useEffect(() => {
    if (isStopped) return;
    const interval = setInterval(() => {
      analyzeFrame();
    }, 100);
    return () => clearInterval(interval);
  }, [exercise, isStopped]);

  // Stop handler: calls endpoints to shutdown app.py and start Gemini, then stops the webcam
  const handleStop = async () => {
    try {
      await axios.post('http://127.0.0.1:5000/start-gemini');
      setTimeout(async () => {
        await axios.post('http://127.0.0.1:5000/shutdown');
      }, 3000);
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
    <div style={styles.pageContainer}>
      <header style={styles.header}>
        <h1 style={styles.logo}>AI Gym Bro</h1>
      </header>

      <main style={styles.mainContent}>
        <div style={styles.heroSection}>
          <div style={styles.videoContainer}>
            <h2 style={styles.sectionTitle}>Live Feed</h2>
            <ReactWebcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: 'user' }}
              style={styles.webcam}
            />
          </div>
          <div style={styles.videoContainer}>
            <h2 style={styles.sectionTitle}>Processed Output</h2>
            {annotatedImage ? (
              <img src={annotatedImage} alt="Annotated" style={styles.annotatedImage} />
            ) : (
              <div style={styles.placeholder}>Processed image will appear here</div>
            )}
          </div>
        </div>

        <div style={styles.controls}>
          <div style={styles.buttonRow}>
            <button
                onClick={() => setExercise('squat')}
                style={{ ...styles.button, ...(exercise === 'squat' && styles.activeButton) }}
              >
                Squat
            </button>
            <button
              onClick={() => setExercise('pushup')}
              style={{ ...styles.button, ...(exercise === 'pushup' && styles.activeButton) }}
            >
              Pushup
            </button>
            <button
              onClick={() => setExercise('bicep')}
              style={{ ...styles.button, ...(exercise === 'bicep' && styles.activeButton) }}
            >
              Bicep Curl
            </button>
          </div>
          <div style={styles.buttonRow}>
            <button onClick={handleStop} style={styles.stopButton}>
              {isStopped ? 'AI Mode Active' : 'Stop & Switch to AI'}
            </button>
          </div>
          <div style={styles.feedbackContainer}>
            <h3 style={styles.feedbackHeading}>Feedback</h3>
            <div style={styles.feedbackBox}>{feedback}</div>
          </div>
        </div>
      </main>

      <footer style={styles.footer}>
        <p style={styles.footerText}>© 2025 AI Gym Bro. All rights reserved.</p>
      </footer>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  pageContainer: {
    minHeight: '100vh',
    backgroundColor: '#f2f2f2',
    fontFamily: "'Roboto', sans-serif",
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    backgroundColor: '#1a1a1a',
    padding: '1rem 2rem',
    textAlign: 'center',
  },
  logo: {
    color: '#fff',
    fontSize: '2.5rem',
    margin: 0,
  },
  mainContent: {
    flex: 1,
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  heroSection: {
    display: 'flex',
    gap: '2rem',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  videoContainer: {
    width: 640,
    maxWidth: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: '1.8rem',
    marginBottom: '1rem',
    color: '#333',
  },
  webcam: {
    width: '100%',
    height: 480,
    borderRadius: '10px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  annotatedImage: {
    width: '100%',
    height: 480,
    borderRadius: '10px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  placeholder: {
    width: '100%',
    height: 480,
    borderRadius: '10px',
    backgroundColor: '#ddd',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.2rem',
    color: '#555',
  },
  controls: {
    width: '100%',
    maxWidth: '800px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1.5rem',
  },
  buttonRow: {
    display: 'flex',
    gap: '1rem',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  button: {
    padding: '12px 30px',
    fontSize: '1.1rem',
    fontWeight: '600',
    backgroundColor: '#fff',
    border: '2px solid #ff4757',
    color: '#ff4757',
    borderRadius: '25px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  activeButton: {
    backgroundColor: '#ff4757',
    color: '#fff',
  },
  stopButton: {
    padding: '12px 30px',
    fontSize: '1.1rem',
    fontWeight: '600',
    backgroundColor: '#ff4757',
    border: '2px solid #ff4757',
    color: '#fff',
    borderRadius: '25px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  feedbackContainer: {
    width: '100%',
    backgroundColor: '#fff',
    padding: '1.5rem',
    borderRadius: '10px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  feedbackHeading: {
    fontSize: '1.5rem',
    color: '#333',
    marginBottom: '1rem',
  },
  feedbackBox: {
    backgroundColor: '#f8f9fa',
    padding: '1rem',
    borderRadius: '8px',
    minHeight: '80px',
    fontSize: '1.1rem',
    color: '#333',
  },
  footer: {
    backgroundColor: '#1a1a1a',
    padding: '1rem',
    alignItems: 'center',
    justifyContent: 'center',
  },
  footerText: {
    color: '#fff',
    fontSize: '0.9rem',
    textAlign: 'center',
  },
};

export default TestWebcamFeedback;
