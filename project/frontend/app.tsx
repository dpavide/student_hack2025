// app.js (JS) or App.tsx (TS)
import React from 'react';
import { View, Text } from 'react-native';
import WorkoutFeedback from './app/components/WorkoutFeedback.tsx';

export default function App() {
  return (
    <View style={{ flex: 1 }}>
      <Text>Welcome to My Fitness App</Text>
      <WorkoutFeedback />
    </View>
  );
}
