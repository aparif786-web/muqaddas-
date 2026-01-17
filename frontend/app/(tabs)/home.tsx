import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../../src/contexts/AuthContext';
import api from '../../src/services/api';

interface Wallet {
  coins_balance: number;
  stars_balance: number;
  bonus_balance: number;
  withdrawable_balance: number;
}

interface VIPStatus {
  vip_level: number;
  is_active: boolean;
  days_remaining: number | null;
  current_level_data: {
    name: string;
    badge_color: string;
    icon: string;
  };
}

interface Notification {
  notification_id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export default function HomeScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [vipStatus, setVipStatus] = useState<VIPStatus | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [walletRes, vipRes, notifRes] = await Promise.all([
        api.get('/wallet'),
        api.get('/vip/status'),
        api.get('/notifications?limit=3'),
      ]);
      
      setWallet(walletRes.data);
      setVipStatus(vipRes.data);
      setNotifications(notifRes.data.notifications);
      setUnreadCount(notifRes.data.unread_count);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const getVIPGradient = (level: number): string[] => {
    switch (level) {
      case 1: return ['#CD7F32', '#8B4513']; // Bronze
      case 2: return ['#C0C0C0', '#808080']; // Silver
      case 3: return ['#FFD700', '#FFA500']; // Gold
      case 4: return ['#E5E4E2', '#B9B8B6']; // Platinum
      case 5: return ['#B9F2FF', '#89CFF0']; // Diamond
      default: return ['#404040', '#303030']; // Basic
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={["#1A1A2E', '#16213E', '#0F3460"] as const}
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
              <View style={styles.headerLeft}>
                <Text style={styles.greeting}>Welcome back,</Text>
                <Text style={styles.userName}>{user?.name || 'User'}</Text>
              </View>
              <TouchableOpacity style={styles.notificationButton}>
                <Ionicons name="notifications" size={24} color="#FFFFFF" />
                {unreadCount > 0 && (
                  <View style={styles.notificationBadge}>
                    <Text style={styles.notificationBadgeText}>{unreadCount}</Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>

            {/* VIP Card */}
            <TouchableOpacity onPress={() => router.push('/(tabs)/vip')}>
              <LinearGradient
                colors={vipStatus ? getVIPGradient(vipStatus.vip_level) : ['#404040', '#303030"] as const}
                style={styles.vipCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.vipCardContent}>
                  <View style={styles.vipCardLeft}>
                    <View style={styles.vipBadge}>
                      <Ionicons
                        name={vipStatus?.current_level_data?.icon as any || 'star'}
                        size={24}
                        color="#1A1A2E"
                      />
                    </View>
                    <View>
                      <Text style={styles.vipLabel}>VIP Status</Text>
                      <Text style={styles.vipLevel}>
                        {vipStatus?.current_level_data?.name || 'Basic'}
                      </Text>
                    </View>
                  </View>
                  <View style={styles.vipCardRight}>
                    {vipStatus?.is_active && vipStatus?.days_remaining !== null && (
                      <Text style={styles.vipDays}>
                        {vipStatus.days_remaining} days left
                      </Text>
                    )}
                    <Ionicons name="chevron-forward" size={20} color="rgba(0,0,0,0.5)" />
                  </View>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            {/* Balance Card */}
            <View style={styles.balanceCard}>
              <Text style={styles.balanceTitle}>Total Balance</Text>
              <Text style={styles.balanceAmount}>
                {wallet ? (wallet.coins_balance + wallet.bonus_balance + wallet.stars_balance).toLocaleString() : '0'}
              </Text>
              <Text style={styles.balanceCurrency}>Coins</Text>
              
              <View style={styles.balanceBreakdown}>
                <View style={styles.balanceItem}>
                  <Ionicons name="wallet" size={16} color="#FFD700" />
                  <Text style={styles.balanceItemLabel}>Main</Text>
                  <Text style={styles.balanceItemValue}>
                    {wallet?.coins_balance?.toLocaleString() || '0'}
                  </Text>
                </View>
                <View style={styles.balanceDivider} />
                <View style={styles.balanceItem}>
                  <Ionicons name="gift" size={16} color="#FF69B4" />
                  <Text style={styles.balanceItemLabel}>Bonus</Text>
                  <Text style={styles.balanceItemValue}>
                    {wallet?.bonus_balance?.toLocaleString() || '0'}
                  </Text>
                </View>
                <View style={styles.balanceDivider} />
                <View style={styles.balanceItem}>
                  <Ionicons name="star" size={16} color="#00CED1" />
                  <Text style={styles.balanceItemLabel}>Stars</Text>
                  <Text style={styles.balanceItemValue}>
                    {wallet?.stars_balance?.toLocaleString() || '0'}
                  </Text>
                </View>
              </View>
            </View>

            {/* Quick Actions */}
            <View style={styles.quickActions}>
              <Text style={styles.sectionTitle}>Quick Actions</Text>
              <View style={styles.actionsGrid}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => router.push('/(tabs)/wallet')}
                >
                  <LinearGradient
                    colors={["#4CAF50', '#45a049"] as const}
                    style={styles.actionIconContainer}
                  >
                    <Ionicons name="add" size={24} color="#FFFFFF" />
                  </LinearGradient>
                  <Text style={styles.actionText}>Deposit</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => router.push('/(tabs)/wallet')}
                >
                  <LinearGradient
                    colors={["#2196F3', '#1976D2"] as const}
                    style={styles.actionIconContainer}
                  >
                    <Ionicons name="arrow-up" size={24} color="#FFFFFF" />
                  </LinearGradient>
                  <Text style={styles.actionText}>Withdraw</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => router.push('/(tabs)/vip')}
                >
                  <LinearGradient
                    colors={["#FFD700', '#FFA500"] as const}
                    style={styles.actionIconContainer}
                  >
                    <Ionicons name="diamond" size={24} color="#1A1A2E" />
                  </LinearGradient>
                  <Text style={styles.actionText}>VIP</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.actionButton}>
                  <LinearGradient
                    colors={["#9C27B0', '#7B1FA2"] as const}
                    style={styles.actionIconContainer}
                  >
                    <Ionicons name="game-controller" size={24} color="#FFFFFF" />
                  </LinearGradient>
                  <Text style={styles.actionText}>Games</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Recent Notifications */}
            {notifications.length > 0 && (
              <View style={styles.notificationsSection}>
                <Text style={styles.sectionTitle}>Recent Updates</Text>
                {notifications.map((notif) => (
                  <View key={notif.notification_id} style={styles.notificationItem}>
                    <View style={styles.notificationDot} />
                    <View style={styles.notificationContent}>
                      <Text style={styles.notificationTitle}>{notif.title}</Text>
                      <Text style={styles.notificationMessage}>{notif.message}</Text>
                    </View>
                  </View>
                ))}
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
  headerLeft: {},
  greeting: {
    fontSize: 14,
    color: '#A0A0A0',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  notificationBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
  },
  notificationBadgeText: {
    fontSize: 10,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  vipCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  vipCardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  vipCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  vipBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  vipLabel: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  vipLevel: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  vipCardRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  vipDays: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
    marginRight: 8,
  },
  balanceCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  balanceTitle: {
    fontSize: 14,
    color: '#A0A0A0',
    marginBottom: 8,
  },
  balanceAmount: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  balanceCurrency: {
    fontSize: 16,
    color: '#808080',
    marginBottom: 20,
  },
  balanceBreakdown: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 12,
    padding: 16,
  },
  balanceItem: {
    flex: 1,
    alignItems: 'center',
  },
  balanceItemLabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
  balanceItemValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 2,
  },
  balanceDivider: {
    width: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  quickActions: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    alignItems: 'center',
    width: '23%',
  },
  actionIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    color: '#FFFFFF',
    fontWeight: '500',
  },
  notificationsSection: {
    marginBottom: 16,
  },
  notificationItem: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  notificationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFD700',
    marginRight: 12,
    marginTop: 6,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  notificationMessage: {
    fontSize: 12,
    color: '#A0A0A0',
  },
});
