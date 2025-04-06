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
    {/* Header Section */}
    <header style={styles.header}>
      <h1 style={styles.logo}>FitnessIn</h1>
    </header>

    {/* Main Content */}
    <main style={styles.mainContent}>
      <h2 style={styles.heading}>LOREM IPSUM DOLOR SIT AMET</h2>
      
      <div style={styles.webcamSection}>
        <ReactWebcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          videoConstraints={{ facingMode: 'user' }}
          style={styles.webcam}
        />
        
        <div style={styles.controls}>
          <div style={styles.buttonContainer}>
            <button 
              onClick={() => setExercise('pushup')} 
              style={{...styles.button, ...(exercise === 'pushup' && styles.activeButton)}}
            >
              Pushup
            </button>
            <button 
              onClick={() => setExercise('squat')} 
              style={{...styles.button, ...(exercise === 'squat' && styles.activeButton)}}
            >
              Squat
            </button>
            <button 
              onClick={() => setExercise('bicep')} 
              style={{...styles.button, ...(exercise === 'bicep' && styles.activeButton)}}
            >
              Bicep Curls
            </button>
            <button>
              stop
            </button>
          </div>
          
          <div style={styles.feedbackContainer}>
            <h3 style={styles.feedbackHeading}>Feedback:</h3>
            <div style={styles.feedbackBox}>{feedback}</div>
            {annotatedImage && (
              <img src={annotatedImage} alt="Annotated" style={styles.annotatedImage} />
            )}
          </div>
        </div>
      </div>
    </main>
  </div>
);
};

const styles: { [key: string]: React.CSSProperties } = {
container: {
  minHeight: '100vh',
  backgroundColor: '#f8f9fa',
  fontFamily: "'Roboto', sans-serif",
},
header: {
  backgroundColor: '#1a1a1a',
  padding: '1rem 2rem',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
},
logo: {
  color: '#fff',
  fontSize: '2rem',
  fontWeight: '700',
  textTransform: 'uppercase',
  letterSpacing: '2px',
  margin: 0,
},
nav: {
  display: 'flex',
  gap: '2rem',
  alignItems: 'center',
},
navLink: {
  color: '#fff',
  textDecoration: 'none',
  fontWeight: '500',
  fontSize: '1.1rem',
  transition: 'color 0.3s ease',
},
mailLink: {
  backgroundColor: '#ff4757',
  padding: '0.5rem 1.5rem',
  borderRadius: '20px',
  color: '#fff',
  textDecoration: 'none',
  transition: 'opacity 0.3s ease',
},
mainContent: {
  maxWidth: '1200px',
  margin: '2rem auto',
  padding: '0 2rem',
},
heading: {
  textAlign: 'center',
  fontSize: '2.5rem',
  color: '#1a1a1a',
  marginBottom: '3rem',
  fontWeight: '500',
},
webcamSection: {
  display: 'flex',
  gap: '2rem',
  alignItems: 'flex-start',
},
webcam: {
  width: 640,
  height: 480,
  borderRadius: '10px',
  boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
},
controls: {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: '2rem',
},
buttonContainer: {
  display: 'flex',
  gap: '1rem',
  justifyContent: 'center',
  flexWrap: 'wrap',
},
button: {
  padding: '12px 30px',
  fontSize: '1.1rem',
  fontWeight: '600',
  backgroundColor: '#f8f9fa',
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
feedbackContainer: {
  backgroundColor: '#fff',
  padding: '1.5rem',
  borderRadius: '10px',
  boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
},
feedbackHeading: {
  color: '#1a1a1a',
  marginTop: 0,
  marginBottom: '1rem',
  fontSize: '1.5rem',
},
feedbackBox: {
  backgroundColor: '#f8f9fa',
  padding: '1rem',
  borderRadius: '8px',
  minHeight: '100px',
  color: '#333',
  fontSize: '1.1rem',
},
annotatedImage: {
  width: '100%',
  height: 'auto',
  borderRadius: '8px',
  marginTop: '1rem',
},
};

export default TestWebcamFeedback;