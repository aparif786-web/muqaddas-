import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { useAuth } from '../src/contexts/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';

export default function Index() {
  const { user, isLoading, processSessionId } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const handleDeepLink = async () => {
      // Check for session_id in URL (for web)
      if (Platform.OS === 'web') {
        const hash = window.location.hash;
        const search = window.location.search;
        
        let sessionId = null;
        
        if (hash && hash.includes('session_id=')) {
          const params = new URLSearchParams(hash.substring(1));
          sessionId = params.get('session_id');
        } else if (search && search.includes('session_id=')) {
          const params = new URLSearchParams(search);
          sessionId = params.get('session_id');
        }
        
        if (sessionId) {
          // Clear URL fragment
          window.history.replaceState(null, '', window.location.pathname);
          await processSessionId(sessionId);
          return;
        }
      }
      
      // Check for cold start deep link (mobile)
      const initialUrl = await Linking.getInitialURL();
      if (initialUrl) {
        const parsed = Linking.parse(initialUrl);
        const sessionId = parsed.queryParams?.session_id as string;
        if (sessionId) {
          await processSessionId(sessionId);
        }
      }
    };
    
    handleDeepLink();
  }, []);

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        router.replace('/(tabs)/home');
      } else {
        router.replace('/login');
      }
    }
  }, [user, isLoading]);

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <View style={styles.content}>
          <Text style={styles.crown}>👑</Text>
          <Text style={styles.logo}>GYAN SULTANAT</Text>
          <Text style={styles.subtitle}>ज्ञान सल्तनत</Text>
          <Text style={styles.tagline}>Jahan Gyan Raja Hai</Text>
          <ActivityIndicator size="large" color="#FFD700" style={styles.loader} />
          <Text style={styles.loadingText}>Loading The Knowledge Empire...</Text>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0A0F',
  },
  gradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
  },
  logo: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#FFD700',
    textShadowColor: '#FFD700',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 20,
  },
  subtitle: {
    fontSize: 18,
    color: '#A0A0A0',
    marginTop: 8,
  },
  loader: {
    marginTop: 40,
  },
  loadingText: {
    color: '#808080',
    marginTop: 16,
    fontSize: 14,
  },
});
