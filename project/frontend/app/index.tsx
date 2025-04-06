// LandingPage.tsx
import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { Link } from 'expo-router';

export default function LandingPage() {
  const screenWidth = Dimensions.get('window').width;
  const imageSize = 400; // Increased image size

  return (
    <View style={styles.container}>
      {/* Header with dark background */}
      <View style={styles.header}>
        <Text style={styles.title}>Gym Bro</Text>
        <Text style={styles.subtitle}>The Only Gym Bro You Will Ever Need</Text>
      </View>

      {/* Main content with white background */}
      <View style={styles.content}>
        <View style={styles.imageRow}>
          <Link href="/squat" asChild>
            <TouchableOpacity style={styles.card}>
              <Image 
                source={require('../assets/images/squat.jpg')} 
                style={[styles.image, { width: imageSize, height: imageSize }]} 
                resizeMode="cover"
              />
              <Text style={styles.cardTitle}>Squat</Text>
            </TouchableOpacity>
          </Link>
          <Link href="/pushup" asChild>
            <TouchableOpacity style={styles.card}>
              <Image 
                source={require('../assets/images/pushup.jpg')} 
                style={[styles.image, { width: imageSize, height: imageSize }]} 
                resizeMode="cover"
              />
              <Text style={styles.cardTitle}>Pushup</Text>
            </TouchableOpacity>
          </Link>
          <Link href="/bicep" asChild>
            <TouchableOpacity style={styles.card}>
              <Image 
                source={require('../assets/images/bicep.jpg')} 
                style={[styles.image, { width: imageSize, height: imageSize }]} 
                resizeMode="cover"
              />
              <Text style={styles.cardTitle}>Bicep Curl</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </View>

      {/* Footer pinned at the bottom */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>© 2025 Gym Bro. All rights reserved.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff', // White background for main page
  },
  header: {
    backgroundColor: '#1a1a1a', // Keep dark header
    paddingVertical: 40,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 56,
    fontWeight: 'bold',
    color: '#fff',
    letterSpacing: 3,
    textShadowColor: '#000',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 24,
    color: '#ccc',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    backgroundColor: '#ffffff', // Main content background remains white
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  imageRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 30,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 20,
    overflow: 'hidden',
    marginVertical: 15,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    alignItems: 'center',
    marginHorizontal: 10,
  },
  image: {
    borderRadius: 20,
  },
  cardTitle: {
    fontSize: 28,
    fontWeight: '600',
    color: '#333',
    paddingVertical: 10,
  },
  footer: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#777',
    textAlign: 'center',
  },
});

export default LandingPage;
