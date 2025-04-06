// squat.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import TestWebcamFeedback from './components/TestWebcam';

export default function SquatScreen() {
  return (
    <View style={styles.container}>
      <TestWebcamFeedback presetExercise="squat" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  title: {
    fontSize: 24,
    textAlign: 'center',
    marginVertical: 20,
  },
});
