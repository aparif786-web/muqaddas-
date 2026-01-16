import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Animated,
  AppState,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/services/api';

interface ActivityStatus {
  today: string;
  total_active_minutes: number;
  minutes_towards_next: number;
  minutes_required: number;
  progress_percent: number;
  rewards_claimed_today: number;
  rewards_available: number;
  max_daily_rewards: number;
  coins_per_reward: number;
}

interface DailySummary {
  today: string;
  total_earned_today: number;
  rewards_today: number;
  activity_streak: number;
  weekly_activities: any[];
  config: any;
}

export default function RewardsScreen() {
  const [activityStatus, setActivityStatus] = useState<ActivityStatus | null>(null);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  
  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const trackingInterval = useRef<NodeJS.Timeout | null>(null);
  const appState = useRef(AppState.currentState);

  const fetchData = async () => {
    try {
      const [statusRes, summaryRes] = await Promise.all([
        api.get('/rewards/activity-status'),
        api.get('/rewards/daily-summary'),
      ]);
      
      setActivityStatus(statusRes.data);
      setDailySummary(summaryRes.data);
      
      // Animate progress
      Animated.timing(progressAnim, {
        toValue: statusRes.data.progress_percent,
        duration: 500,
        useNativeDriver: false,
      }).start();
    } catch (error) {
      console.error('Error fetching rewards data:', error);
    }
  };

  useEffect(() => {
    fetchData();
    startTracking();
    
    // Handle app state changes
    const subscription = AppState.addEventListener('change', nextAppState => {
      if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
        // App came to foreground, resume tracking
        startTracking();
      } else if (nextAppState.match(/inactive|background/)) {
        // App went to background, stop tracking
        stopTracking();
      }
      appState.current = nextAppState;
    });
    
    return () => {
      stopTracking();
      subscription.remove();
    };
  }, []);

  const startTracking = () => {
    if (trackingInterval.current) return;
    
    setIsTracking(true);
    trackingInterval.current = setInterval(async () => {
      try {
        const response = await api.post('/rewards/track-activity');
        if (response.data.can_claim) {
          // Start pulse animation when reward is available
          Animated.loop(
            Animated.sequence([
              Animated.timing(pulseAnim, {
                toValue: 1.1,
                duration: 500,
                useNativeDriver: true,
              }),
              Animated.timing(pulseAnim, {
                toValue: 1,
                duration: 500,
                useNativeDriver: true,
              }),
            ])
          ).start();
        }
        await fetchData();
      } catch (error) {
        console.error('Error tracking activity:', error);
      }
    }, 60000); // Track every minute
  };

  const stopTracking = () => {
    if (trackingInterval.current) {
      clearInterval(trackingInterval.current);
      trackingInterval.current = null;
    }
    setIsTracking(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleClaimReward = async () => {
    if (!activityStatus || activityStatus.rewards_available <= 0) {
      Alert.alert('No Rewards', 'Keep using the app to earn rewards!');
      return;
    }

    setClaiming(true);
    try {
      const response = await api.post('/rewards/claim-activity-reward');
      
      if (response.data.success) {
        Alert.alert(
          'Reward Claimed! 🎉',
          `You earned ${response.data.reward_amount} coins!${response.data.daily_bonus_included ? '\n(Includes daily bonus!)' : ''}`
        );
        await fetchData();
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to claim reward');
    } finally {
      setClaiming(false);
    }
  };

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <ScrollView
            style={styles.scrollView}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor="#FFD700"
              />
            }
            showsVerticalScrollIndicator={false}
          >
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.headerTitle}>Daily Rewards</Text>
              <View style={styles.trackingBadge}>
                <View style={[styles.trackingDot, isTracking && styles.trackingDotActive]} />
                <Text style={styles.trackingText}>
                  {isTracking ? 'Tracking' : 'Paused'}
                </Text>
              </View>
            </View>

            {/* Main Reward Card */}
            <LinearGradient
              colors={['#2A2A4E', '#1A1A3E']}
              style={styles.rewardCard}
            >
              <View style={styles.rewardHeader}>
                <Ionicons name="time" size={24} color="#FFD700" />
                <Text style={styles.rewardTitle}>Activity Reward</Text>
              </View>
              
              <Text style={styles.rewardDescription}>
                Stay active for 15 minutes to earn 200 coins!
              </Text>

              {/* Progress Section */}
              <View style={styles.progressSection}>
                <View style={styles.progressInfo}>
                  <Text style={styles.progressTime}>
                    {activityStatus?.minutes_towards_next || 0} / {activityStatus?.minutes_required || 15} min
                  </Text>
                  <Text style={styles.progressPercent}>
                    {Math.round(activityStatus?.progress_percent || 0)}%
                  </Text>
                </View>
                
                <View style={styles.progressBarContainer}>
                  <Animated.View 
                    style={[
                      styles.progressBar, 
                      { width: progressWidth }
                    ]} 
                  />
                </View>
              </View>

              {/* Claim Button */}
              <Animated.View style={{ transform: [{ scale: activityStatus?.rewards_available ? pulseAnim : 1 }] }}>
                <TouchableOpacity
                  style={[
                    styles.claimButton,
                    (!activityStatus?.rewards_available || claiming) && styles.claimButtonDisabled
                  ]}
                  onPress={handleClaimReward}
                  disabled={!activityStatus?.rewards_available || claiming}
                >
                  <LinearGradient
                    colors={activityStatus?.rewards_available ? ['#FFD700', '#FFA500'] : ['#404040', '#303030']}
                    style={styles.claimButtonGradient}
                  >
                    <Ionicons 
                      name={activityStatus?.rewards_available ? "gift" : "hourglass"} 
                      size={24} 
                      color={activityStatus?.rewards_available ? "#1A1A2E" : "#808080"} 
                    />
                    <Text style={[
                      styles.claimButtonText,
                      !activityStatus?.rewards_available && styles.claimButtonTextDisabled
                    ]}>
                      {claiming ? 'Claiming...' : 
                       activityStatus?.rewards_available ? `Claim ${activityStatus.coins_per_reward} Coins` : 
                       'Keep Going!'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </Animated.View>

              {/* Rewards Counter */}
              <View style={styles.rewardsCounter}>
                <Text style={styles.rewardsCounterText}>
                  Rewards claimed today: {activityStatus?.rewards_claimed_today || 0} / {activityStatus?.max_daily_rewards || 6}
                </Text>
                {activityStatus?.rewards_available ? (
                  <Text style={styles.rewardsAvailable}>
                    {activityStatus.rewards_available} reward(s) ready to claim!
                  </Text>
                ) : null}
              </View>
            </LinearGradient>

            {/* Stats Cards */}
            <View style={styles.statsRow}>
              <View style={styles.statCard}>
                <Ionicons name="flame" size={28} color="#FF6B6B" />
                <Text style={styles.statValue}>{dailySummary?.activity_streak || 0}</Text>
                <Text style={styles.statLabel}>Day Streak</Text>
              </View>
              <View style={styles.statCard}>
                <Ionicons name="wallet" size={28} color="#4CAF50" />
                <Text style={styles.statValue}>{dailySummary?.total_earned_today || 0}</Text>
                <Text style={styles.statLabel}>Earned Today</Text>
              </View>
              <View style={styles.statCard}>
                <Ionicons name="time" size={28} color="#2196F3" />
                <Text style={styles.statValue}>{activityStatus?.total_active_minutes || 0}</Text>
                <Text style={styles.statLabel}>Minutes</Text>
              </View>
            </View>

            {/* How It Works */}
            <View style={styles.howItWorks}>
              <Text style={styles.sectionTitle}>How It Works</Text>
              
              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>1</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Stay Active</Text>
                  <Text style={styles.stepDescription}>
                    Use the app for 15 minutes to earn a reward
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>2</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Claim Coins</Text>
                  <Text style={styles.stepDescription}>
                    Tap the claim button to get 200 coins
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>3</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Daily Bonus</Text>
                  <Text style={styles.stepDescription}>
                    First claim each day gives +50 bonus coins!
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>4</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Max 6 Rewards/Day</Text>
                  <Text style={styles.stepDescription}>
                    Earn up to 1,250 coins daily (200×6 + 50 bonus)
                  </Text>
                </View>
              </View>
            </View>

            {/* Weekly Activity */}
            {dailySummary?.weekly_activities && dailySummary.weekly_activities.length > 0 && (
              <View style={styles.weeklySection}>
                <Text style={styles.sectionTitle}>This Week</Text>
                <View style={styles.weeklyGrid}>
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => {
                    const activity = dailySummary.weekly_activities.find((a: any) => {
                      const date = new Date(a.date);
                      return date.getDay() === (index === 6 ? 0 : index + 1);
                    });
                    const hasActivity = activity && activity.rewards_claimed > 0;
                    
                    return (
                      <View key={day} style={styles.weeklyDay}>
                        <Text style={styles.weeklyDayText}>{day}</Text>
                        <View style={[
                          styles.weeklyDot,
                          hasActivity && styles.weeklyDotActive
                        ]}>
                          {hasActivity && (
                            <Ionicons name="checkmark" size={12} color="#1A1A2E" />
                          )}
                        </View>
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            <View style={{ height: 20 }} />
          </ScrollView>
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
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  trackingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  trackingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#808080',
    marginRight: 6,
  },
  trackingDotActive: {
    backgroundColor: '#4CAF50',
  },
  trackingText: {
    fontSize: 12,
    color: '#A0A0A0',
  },
  rewardCard: {
    borderRadius: 20,
    padding: 24,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  rewardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  rewardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginLeft: 12,
  },
  rewardDescription: {
    fontSize: 14,
    color: '#A0A0A0',
    marginBottom: 20,
  },
  progressSection: {
    marginBottom: 24,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressTime: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  progressPercent: {
    fontSize: 14,
    color: '#FFD700',
    fontWeight: '600',
  },
  progressBarContainer: {
    height: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 6,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#FFD700',
    borderRadius: 6,
  },
  claimButton: {
    marginBottom: 16,
  },
  claimButtonDisabled: {
    opacity: 0.7,
  },
  claimButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 10,
  },
  claimButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  claimButtonTextDisabled: {
    color: '#808080',
  },
  rewardsCounter: {
    alignItems: 'center',
  },
  rewardsCounterText: {
    fontSize: 12,
    color: '#808080',
  },
  rewardsAvailable: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: '600',
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
  howItWorks: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  stepItem: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#FFD700',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  stepDescription: {
    fontSize: 12,
    color: '#808080',
  },
  weeklySection: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  weeklyGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  weeklyDay: {
    alignItems: 'center',
  },
  weeklyDayText: {
    fontSize: 12,
    color: '#808080',
    marginBottom: 8,
  },
  weeklyDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  weeklyDotActive: {
    backgroundColor: '#4CAF50',
  },
});
