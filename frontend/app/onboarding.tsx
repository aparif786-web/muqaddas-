import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface OnboardingStep {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  icon: string;
  color: string;
  aiMessage: string;
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: 1,
    title: "🙏 Swagat hai!",
    subtitle: "GYAN SULTANAT mein",
    description: "Yeh sirf ek app nahi - yeh ek REVOLUTION hai! Gyaan se Aay, Apne Sapne Sajaye!",
    icon: "👑",
    color: "#FFD700",
    aiMessage: "Main aapka Gyan Guide hoon. Main aapko step-by-step samjhaunga ki Gyan Sultanat kaise kaam karti hai!"
  },
  {
    id: 2,
    title: "📚 Seekho",
    subtitle: "Gyan Guru se",
    description: "Koi bhi sawaal poochho - Math, Science, Law, Health - Gyan Guru 24/7 available hai!",
    icon: "🧠",
    color: "#4CAF50",
    aiMessage: "Gyan Guru aapka personal tutor hai. Koi bhi subject, koi bhi sawaal - instant jawab milega!"
  },
  {
    id: 3,
    title: "💰 Kamao",
    subtitle: "Gyaan se Income",
    description: "Teacher bano, content banao, 70-75% revenue kamao! Sirf ₹1 mein registration!",
    icon: "💵",
    color: "#2196F3",
    aiMessage: "Yahan sirf padhte nahi, kamate bhi hain! Teachers ko 75% revenue milta hai. Aap bhi shuru kar sakte hain!"
  },
  {
    id: 4,
    title: "🏆 Jeeto",
    subtitle: "Gyan Yuddh mein",
    description: "Compete karo, Crown jeeto, Leaderboard mein aao! iPhone, Samsung - sab prizes!",
    icon: "🎮",
    color: "#9C27B0",
    aiMessage: "Gyan Yuddh mein participate karo - Bronze, Silver, Gold Crowns jeeto. Top 10 ko real prizes milte hain!"
  },
  {
    id: 5,
    title: "❤️ Charity",
    subtitle: "Duniya Badlo",
    description: "Aapki har activity se 5% charity mein jaata hai. ₹10 Billion ka lakshya!",
    icon: "🌍",
    color: "#E91E63",
    aiMessage: "Gyan Sultanat sirf business nahi - ek mission hai. Aapki madad se hum duniya badlenge!"
  },
  {
    id: 6,
    title: "🚀 Shuru Karo",
    subtitle: "Abhi!",
    description: "Aap taiyaar hain! Gyan Guru se sawaal poochho, Talent ban kar kamao!",
    icon: "✨",
    color: "#FF9800",
    aiMessage: "Congratulations! Ab aap Gyan Sultanat ke member hain. Koi bhi help chahiye - main yahan hoon!"
  }
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [showGyanMessage, setShowGyanMessage] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    // Animate on step change
    fadeAnim.setValue(0);
    slideAnim.setValue(50);
    
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();

    // Show Gyan message after delay
    const timer = setTimeout(() => {
      setShowGyanMessage(true);
    }, 800);

    return () => clearTimeout(timer);
  }, [currentStep]);

  const handleNext = () => {
    setShowGyanMessage(false);
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    completeOnboarding();
  };

  const completeOnboarding = async () => {
    try {
      await AsyncStorage.setItem('onboarding_complete', 'true');
      router.replace('/(tabs)/home');
    } catch (error) {
      router.replace('/(tabs)/home');
    }
  };

  const step = ONBOARDING_STEPS[currentStep];

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          {/* Skip Button */}
          <View style={styles.header}>
            <View style={styles.progressContainer}>
              {ONBOARDING_STEPS.map((_, index) => (
                <View
                  key={index}
                  style={[
                    styles.progressDot,
                    index <= currentStep && { backgroundColor: step.color }
                  ]}
                />
              ))}
            </View>
            <TouchableOpacity onPress={handleSkip} style={styles.skipButton}>
              <Text style={styles.skipText}>Skip</Text>
            </TouchableOpacity>
          </View>

          {/* Main Content */}
          <ScrollView 
            style={styles.content}
            contentContainerStyle={styles.contentContainer}
            showsVerticalScrollIndicator={false}
          >
            <Animated.View
              style={[
                styles.stepContent,
                {
                  opacity: fadeAnim,
                  transform: [{ translateY: slideAnim }],
                },
              ]}
            >
              {/* Icon */}
              <View style={[styles.iconContainer, { backgroundColor: step.color + '20' }]}>
                <Text style={styles.icon}>{step.icon}</Text>
              </View>

              {/* Title */}
              <Text style={styles.title}>{step.title}</Text>
              <Text style={[styles.subtitle, { color: step.color }]}>{step.subtitle}</Text>
              
              {/* Description */}
              <Text style={styles.description}>{step.description}</Text>

              {/* Gyan Guide Message */}
              {showGyanMessage && (
                <Animated.View style={styles.aiMessageContainer}>
                  <View style={styles.aiAvatar}>
                    <Text style={styles.aiAvatarText}>🤖</Text>
                  </View>
                  <View style={styles.aiMessageBubble}>
                    <Text style={styles.gyanLabel}>Gyan Guide</Text>
                    <Text style={styles.aiMessage}>{step.aiMessage}</Text>
                  </View>
                </Animated.View>
              )}
            </Animated.View>
          </ScrollView>

          {/* Bottom Navigation */}
          <View style={styles.bottomNav}>
            <TouchableOpacity
              style={styles.nextButton}
              onPress={handleNext}
            >
              <LinearGradient
                colors={[step.color, step.color + 'CC']}
                style={styles.nextButtonGradient}
              >
                <Text style={styles.nextButtonText}>
                  {currentStep === ONBOARDING_STEPS.length - 1 ? "Shuru Karein! 🚀" : "Aage Badhein →"}
                </Text>
              </LinearGradient>
            </TouchableOpacity>

            <Text style={styles.stepIndicator}>
              {currentStep + 1} / {ONBOARDING_STEPS.length}
            </Text>
          </View>
        </SafeAreaView>
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
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  progressContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  progressDot: {
    width: 24,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  skipButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  skipText: {
    color: '#808080',
    fontSize: 14,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 24,
    paddingTop: 40,
  },
  stepContent: {
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
  },
  icon: {
    fontSize: 56,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 22,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    color: '#A0A0A0',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  aiMessageContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 20,
    padding: 16,
    marginTop: 16,
    width: '100%',
  },
  aiAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  aiAvatarText: {
    fontSize: 24,
  },
  aiMessageBubble: {
    flex: 1,
  },
  gyanLabel: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
    marginBottom: 4,
  },
  aiMessage: {
    fontSize: 14,
    color: '#FFFFFF',
    lineHeight: 20,
  },
  bottomNav: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    alignItems: 'center',
  },
  nextButton: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
  },
  nextButtonGradient: {
    paddingVertical: 18,
    alignItems: 'center',
  },
  nextButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  stepIndicator: {
    fontSize: 14,
    color: '#808080',
  },
});
