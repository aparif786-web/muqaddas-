import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Platform,
  ScrollView,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { useAuth } from '../src/contexts/AuthContext';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const { width } = Dimensions.get('window');

export default function LoginScreen() {
  const { processSessionId } = useAuth();
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Pulse animation for logo
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.1, duration: 1000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ])
    ).start();

    // Fade in animation
    Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }).start();
  }, []);

  const handleOpenLink = async (path: string) => {
    try {
      const url = `${BACKEND_URL}${path}`;
      await WebBrowser.openBrowserAsync(url);
    } catch (error) {
      console.error('Error opening link:', error);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      // Get proper redirect URL based on platform
      let redirectUrl: string;
      
      if (Platform.OS === 'web') {
        // For web, use current origin or backend URL
        const currentOrigin = typeof window !== 'undefined' ? window.location.origin : '';
        redirectUrl = currentOrigin || process.env.EXPO_PUBLIC_BACKEND_URL || 'https://sultanat-auth-fix.preview.emergentagent.com';
      } else {
        // For mobile app, use deep link
        redirectUrl = Linking.createURL('auth-callback');
      }
      
      // Ensure redirect URL is valid
      if (!redirectUrl || redirectUrl === 'undefined' || redirectUrl === '') {
        redirectUrl = 'https://sultanat-auth-fix.preview.emergentagent.com';
      }
      
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      console.log('Auth URL:', authUrl);
      console.log('Redirect URL:', redirectUrl);
      
      if (Platform.OS === 'web') {
        // @ts-ignore
        window.location.href = authUrl;
      } else {
        const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
        
        if (result.type === 'success' && result.url) {
          const parsed = Linking.parse(result.url);
          const sessionId = parsed.queryParams?.session_id as string;
          if (sessionId) {
            await processSessionId(sessionId);
          }
        }
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const features = [
    { icon: 'videocam', title: 'Live', subtitle: 'Streaming', colors: ['#FF416C', '#FF4B2B'], viewers: '10K+' },
    { icon: 'mic', title: 'Audio', subtitle: 'Rooms', colors: ['#11998e', '#38ef7d'], viewers: '5K+' },
    { icon: 'gift', title: 'Gift', subtitle: '& Earn', colors: ['#8E2DE2', '#4A00E0'], viewers: '₹Lakhs' },
    { icon: 'school', title: 'Gyan', subtitle: 'Education', colors: ['#F7971E', '#FFD200'], viewers: 'Free' },
    { icon: 'trophy', title: 'Gyan', subtitle: 'Yuddh', colors: ['#00b09b', '#96c93d'], viewers: 'Win' },
    { icon: 'people', title: 'Make', subtitle: 'Friends', colors: ['#fc4a1a', '#f7b733'], viewers: 'Global' },
  ];

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#FFECD2', '#FCB69F', '#FFECD2']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            
            {/* Animated Logo Section */}
            <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
              <Animated.View style={[styles.logoOuter, { transform: [{ scale: pulseAnim }] }]}>
                <LinearGradient colors={['#00C853', '#1B5E20']} style={styles.logoGradient}>
                  <Text style={styles.heartEmoji}>💚</Text>
                </LinearGradient>
              </Animated.View>
              
              <Text style={styles.title}>GYAN SULTANAT</Text>
              <Text style={styles.hindiTitle}>ज्ञान सल्तनत</Text>
              
              <View style={styles.taglineContainer}>
                <Text style={styles.tagline}>✨ Gyaan se Aay, Apne Sapne Sajaye! ✨</Text>
              </View>

              {/* Stats Row */}
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>10L+</Text>
                  <Text style={styles.statLabel}>Users</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>50K+</Text>
                  <Text style={styles.statLabel}>Hosts</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>20+</Text>
                  <Text style={styles.statLabel}>Countries</Text>
                </View>
              </View>

              {/* Free Badge with Glow */}
              <View style={styles.freeBadgeContainer}>
                <LinearGradient colors={['#00C853', '#1B5E20']} style={styles.freeBadge}>
                  <Text style={styles.freeBadgeText}>🎁 100% FREE • No Hidden Charges</Text>
                </LinearGradient>
              </View>
            </Animated.View>

            {/* Feature Cards Grid */}
            <Animated.View style={[styles.featuresGrid, { opacity: fadeAnim }]}>
              {features.map((feature, index) => (
                <TouchableOpacity key={index} style={styles.featureCard} activeOpacity={0.8}>
                  <LinearGradient colors={feature.colors} style={styles.featureGradient}>
                    <View style={styles.featureIconContainer}>
                      <Ionicons name={feature.icon as any} size={26} color="#FFF" />
                    </View>
                    <Text style={styles.featureTitle}>{feature.title}</Text>
                    <Text style={styles.featureSubtitle}>{feature.subtitle}</Text>
                    <View style={styles.featureBadge}>
                      <Text style={styles.featureBadgeText}>{feature.viewers}</Text>
                    </View>
                  </LinearGradient>
                </TouchableOpacity>
              ))}
            </Animated.View>

            {/* Login Section */}
            <View style={styles.loginSection}>
              <TouchableOpacity style={styles.googleButton} onPress={handleGoogleLogin} activeOpacity={0.9}>
                <LinearGradient colors={['#4285F4', '#34A853', '#FBBC05', '#EA4335']} 
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.googleGradientBorder}>
                  <View style={styles.googleInner}>
                    <Text style={styles.googleIcon}>G</Text>
                    <Text style={styles.googleButtonText}>Continue with Google</Text>
                  </View>
                </LinearGradient>
              </TouchableOpacity>

              <View style={styles.orContainer}>
                <View style={styles.orLine} />
                <Text style={styles.orText}>or</Text>
                <View style={styles.orLine} />
              </View>

              <TouchableOpacity style={styles.phoneButton} activeOpacity={0.9}>
                <LinearGradient colors={['#00C853', '#1B5E20']} style={styles.phoneGradient}>
                  <Ionicons name="call" size={20} color="#FFF" />
                  <Text style={styles.phoneButtonText}>Continue with Phone</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {/* Trust Badges */}
            <View style={styles.trustBadges}>
              <View style={styles.trustItem}>
                <Ionicons name="shield-checkmark" size={16} color="#00C853" />
                <Text style={styles.trustText}>Secure</Text>
              </View>
              <View style={styles.trustItem}>
                <Ionicons name="lock-closed" size={16} color="#00C853" />
                <Text style={styles.trustText}>Private</Text>
              </View>
              <View style={styles.trustItem}>
                <Ionicons name="checkmark-circle" size={16} color="#00C853" />
                <Text style={styles.trustText}>Verified</Text>
              </View>
            </View>

            {/* Terms */}
            <View style={styles.termsContainer}>
              <Text style={styles.termsText}>By continuing, you agree to our </Text>
              <TouchableOpacity onPress={() => handleOpenLink('/api/legal/terms')}>
                <Text style={styles.termsLink}>Terms</Text>
              </TouchableOpacity>
              <Text style={styles.termsText}> & </Text>
              <TouchableOpacity onPress={() => handleOpenLink('/api/legal/privacy-policy')}>
                <Text style={styles.termsLink}>Privacy Policy</Text>
              </TouchableOpacity>
            </View>

            {/* Company Footer */}
            <View style={styles.footer}>
              <Text style={styles.footerLogo}>💚</Text>
              <Text style={styles.footerTitle}>Muqaddas Technology</Text>
              <Text style={styles.footerSubtitle}>Powered by Aayushka Designing</Text>
              <Text style={styles.footerWebsite}>www.muqaddasnetwork.com</Text>
            </View>

          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingBottom: 30,
  },
  header: {
    alignItems: 'center',
    marginTop: 15,
    marginBottom: 20,
  },
  logoOuter: {
    marginBottom: 12,
  },
  logoGradient: {
    width: 90,
    height: 90,
    borderRadius: 45,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#00C853',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 12,
  },
  heartEmoji: {
    fontSize: 45,
  },
  title: {
    fontSize: 26,
    fontWeight: '900',
    color: '#1B5E20',
    letterSpacing: 3,
    textShadowColor: 'rgba(0,0,0,0.1)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  hindiTitle: {
    fontSize: 16,
    color: '#2E7D32',
    fontWeight: '600',
    marginTop: 2,
  },
  taglineContainer: {
    marginTop: 8,
    paddingHorizontal: 15,
    paddingVertical: 5,
    backgroundColor: 'rgba(255,255,255,0.7)',
    borderRadius: 20,
  },
  tagline: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 15,
    backgroundColor: 'rgba(255,255,255,0.8)',
    borderRadius: 15,
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  statItem: {
    alignItems: 'center',
    paddingHorizontal: 15,
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1B5E20',
  },
  statLabel: {
    fontSize: 10,
    color: '#666',
  },
  statDivider: {
    width: 1,
    height: 25,
    backgroundColor: '#DDD',
  },
  freeBadgeContainer: {
    marginTop: 12,
  },
  freeBadge: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 25,
  },
  freeBadgeText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 13,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  featureCard: {
    width: (width - 48) / 3,
    marginBottom: 12,
  },
  featureGradient: {
    paddingVertical: 15,
    paddingHorizontal: 8,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 6,
  },
  featureIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  featureTitle: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 13,
  },
  featureSubtitle: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 10,
  },
  featureBadge: {
    marginTop: 6,
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  featureBadgeText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '600',
  },
  loginSection: {
    marginBottom: 15,
  },
  googleButton: {
    borderRadius: 30,
    overflow: 'hidden',
  },
  googleGradientBorder: {
    padding: 2,
    borderRadius: 30,
  },
  googleInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    paddingVertical: 14,
    borderRadius: 28,
  },
  googleIcon: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4285F4',
    marginRight: 10,
  },
  googleButtonText: {
    color: '#333',
    fontSize: 15,
    fontWeight: '600',
  },
  orContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 12,
  },
  orLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(0,0,0,0.15)',
  },
  orText: {
    marginHorizontal: 15,
    color: '#888',
    fontSize: 12,
  },
  phoneButton: {
    borderRadius: 30,
    overflow: 'hidden',
  },
  phoneGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 30,
  },
  phoneButtonText: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: 10,
  },
  trustBadges: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 12,
  },
  trustItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 12,
    backgroundColor: 'rgba(255,255,255,0.7)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 15,
  },
  trustText: {
    fontSize: 11,
    color: '#333',
    marginLeft: 4,
    fontWeight: '500',
  },
  termsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: 15,
  },
  termsText: {
    fontSize: 11,
    color: '#666',
  },
  termsLink: {
    fontSize: 11,
    color: '#1B5E20',
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  footerLogo: {
    fontSize: 24,
  },
  footerTitle: {
    fontSize: 14,
    color: '#1B5E20',
    fontWeight: 'bold',
    marginTop: 4,
  },
  footerSubtitle: {
    fontSize: 10,
    color: '#888',
  },
  footerWebsite: {
    fontSize: 11,
    color: '#2E7D32',
    marginTop: 4,
    fontWeight: '500',
  },
});
