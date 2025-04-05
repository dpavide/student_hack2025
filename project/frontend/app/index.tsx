// app/index.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import WorkoutFeedback from './components/WorkoutFeedback';
import TestWebcamFeedback from './components/TestWebcam';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to My Fitness App</Text>
      <TestWebcamFeedback />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
  },
    camera: {
    width: '100%',     // Use the full width of the device
    height: '70%',     // Use 70% of the screen's height; adjust as needed
  },
  controls: {
    flex: 0.3,
    alignItems: 'center',
    justifyContent: 'center',
  },
});