import React, { useEffect, useRef, useState } from 'react';
import { View, Text, Button, StyleSheet, Platform } from 'react-native';
import { Camera } from 'expo-camera';
import * as ImageManipulator from 'expo-image-manipulator';
import { Audio } from 'expo-av';
import axios from 'axios';
import ReactWebcam from 'react-webcam'; // Install react-webcam for web support

const WorkoutFeedback: React.FC = () => {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const cameraRef = useRef<Camera>(null);
  const webcamRef = useRef(null);

  useEffect(() => {
    if (Platform.OS !== 'web') {
      (async () => {
        const { status } = await Camera.requestCameraPermissionsAsync();
        setHasPermission(status === 'granted');
      })();
    } else {
      // For web, we assume permission is granted if getUserMedia works
      setHasPermission(true);
    }
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  const analyzeForm = async () => {
    let imageData: string | null = null;

    if (Platform.OS === 'web') {
      if (webcamRef.current) {
        const screenshot = (webcamRef.current as any).getScreenshot();
        imageData = screenshot;
      }
    } else {
      if (cameraRef.current) {
        const photo = await cameraRef.current.takePictureAsync({ base64: true });
        const manipulatedImage = await ImageManipulator.manipulateAsync(
          photo.uri,
          [{ resize: { width: 640 } }],
          { base64: true, compress: 0.7 }
        );
        imageData = manipulatedImage.base64;
      }
    }

    if (!imageData) return;

    try {
      const response = await axios.post('http://localhost:5000/analyze', {
        image: imageData,
      });
      setFeedback(response.data.feedback);
      playFeedbackAudio(response.data.audioUrl);
    } catch (error) {
      console.error('Error sending image for analysis:', error);
    }
  };

  const playFeedbackAudio = async (audioUrl: string) => {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: audioUrl });
      setSound(sound);
      await sound.playAsync();
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  // Use conditional rendering based on platform
  return (
    <View style={styles.container}>
      {Platform.OS === 'web' ? (
        <ReactWebcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          videoConstraints={{
            facingMode: 'user',
          }}
          style={styles.camera}
        />
      ) : (
        <Camera
          style={styles.camera}
          ref={cameraRef}
          type={Camera.Constants.Type.front}
        />
      )}
      <View style={styles.controls}>
        <Button title="Analyze Form" onPress={analyzeForm} />
        {feedback ? (
          <View style={styles.feedbackContainer}>
            <Text style={styles.feedbackText}>Feedback: {feedback}</Text>
            <Button title="Play Feedback Audio" onPress={() => playFeedbackAudio('')} />
          </View>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  camera: { flex: 0.7 },
  controls: { flex: 0.3, alignItems: 'center', justifyContent: 'center' },
  feedbackContainer: { marginTop: 20, paddingHorizontal: 20 },
  feedbackText: { fontSize: 16, textAlign: 'center' },
});

export default WorkoutFeedback;
