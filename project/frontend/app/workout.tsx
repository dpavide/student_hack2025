// app/workout.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import WorkoutFeedback from './components/WorkoutFeedback';

export default function WorkoutScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Workout Feedback</Text>
      <WorkoutFeedback />
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
});
