import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import TestWebcamFeedback from './components/TestWebcam';

export default function BicepScreen() {
  return (
    <View style={styles.container}>
      <TestWebcamFeedback presetExercise="bicep" />
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
