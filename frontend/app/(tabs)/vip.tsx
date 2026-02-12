import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/services/api';

interface VIPLevel {
  level: number;
  name: string;
  recharge_requirement: number;
  monthly_fee: number;
  gift_bonus: number;
  free_spins_daily: number;
  education_discount: number;
  priority_support: boolean;
  withdrawal_priority: boolean;
  exclusive_games: boolean;
  badge_color: string;
  icon: string;
}

interface VIPStatus {
  user_id: string;
  vip_level: number;
  subscription_start: string | null;
  subscription_end: string | null;
  total_recharged: number;
  is_active: boolean;
  auto_renew: boolean;
  days_remaining: number | null;
  eligible_level: number;
  current_level_data: VIPLevel;
}

export default function VIPScreen() {
  const [vipLevels, setVipLevels] = useState<VIPLevel[]>([]);
  const [vipStatus, setVipStatus] = useState<VIPStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<VIPLevel | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [levelsRes, statusRes] = await Promise.all([
        api.get('/vip/levels'),
        api.get('/vip/status'),
      ]);
      
      setVipLevels(levelsRes.data.levels);
      setVipStatus(statusRes.data);
    } catch (error) {
      console.error('Error fetching VIP data:', error);
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
      case 1: return ['#CD7F32', '#8B4513'];
      case 2: return ['#C0C0C0', '#808080'];
      case 3: return ['#FFD700', '#FFA500'];
      case 4: return ['#E5E4E2', '#B9B8B6'];
      case 5: return ['#B9F2FF', '#89CFF0'];
      default: return ['#404040', '#303030'];
    }
  };

  const handleSubscribe = async () => {
    if (!selectedLevel) return;

    setLoading(true);
    try {
      await api.post('/vip/subscribe', { level: selectedLevel.level });
      setModalVisible(false);
      await fetchData();
      Alert.alert(
        'Welcome to VIP!',
        `You are now a ${selectedLevel.name} member! Enjoy your exclusive benefits.`
      );
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to subscribe');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAutoRenew = async () => {
    try {
      await api.post('/vip/toggle-auto-renew');
      await fetchData();
    } catch (error) {
      console.error('Error toggling auto-renew:', error);
    }
  };

  const isLevelUnlocked = (level: number) => {
    return vipStatus && vipStatus.eligible_level >= level;
  };

  const isCurrentLevel = (level: number) => {
    return vipStatus && vipStatus.vip_level === level && vipStatus.is_active;
  };

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
              <Text style={styles.headerTitle}>VIP Club</Text>
              <Text style={styles.headerSubtitle}>Exclusive rewards & benefits</Text>
            </View>

            {/* Current Status Card */}
            {vipStatus && (
              <LinearGradient
                colors={getVIPGradient(vipStatus.vip_level)}
                style={styles.statusCard}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.statusHeader}>
                  <View style={styles.statusBadge}>
                    <Ionicons
                      name={vipStatus.current_level_data?.icon as any || 'star'}
                      size={32}
                      color="#1A1A2E"
                    />
                  </View>
                  <View style={styles.statusInfo}>
                    <Text style={styles.statusLabel}>Current Status</Text>
                    <Text style={styles.statusLevel}>
                      {vipStatus.current_level_data?.name || 'Basic'}
                    </Text>
                  </View>
                </View>

                {vipStatus.is_active && vipStatus.days_remaining !== null && (
                  <View style={styles.statusFooter}>
                    <Ionicons name="time" size={16} color="rgba(0,0,0,0.6)" />
                    <Text style={styles.statusDays}>
                      {vipStatus.days_remaining} days remaining
                    </Text>
                  </View>
                )}

                <View style={styles.rechargeProgress}>
                  <Text style={styles.rechargeLabel}>Total Recharged</Text>
                  <Text style={styles.rechargeAmount}>
                    {vipStatus.total_recharged.toLocaleString()} coins
                  </Text>
                </View>

                {vipStatus.is_active && (
                  <TouchableOpacity
                    style={styles.autoRenewToggle}
                    onPress={handleToggleAutoRenew}
                  >
                    <Ionicons
                      name={vipStatus.auto_renew ? 'checkbox' : 'square-outline'}
                      size={20}
                      color="#1A1A2E"
                    />
                    <Text style={styles.autoRenewText}>Auto-renew subscription</Text>
                  </TouchableOpacity>
                )}
              </LinearGradient>
            )}

            {/* VIP Levels */}
            <Text style={styles.sectionTitle}>VIP Levels</Text>
            {vipLevels.filter(l => l.level > 0).map((level) => {
              const unlocked = isLevelUnlocked(level.level);
              const current = isCurrentLevel(level.level);
              
              return (
                <TouchableOpacity
                  key={level.level}
                  style={[
                    styles.levelCard,
                    current && styles.levelCardActive,
                    !unlocked && styles.levelCardLocked,
                  ]}
                  onPress={() => {
                    if (unlocked && !current) {
                      setSelectedLevel(level);
                      setModalVisible(true);
                    } else if (!unlocked) {
                      Alert.alert(
                        'Level Locked',
                        `Recharge ${level.recharge_requirement.toLocaleString()} coins to unlock ${level.name} VIP.`
                      );
                    }
                  }}
                  activeOpacity={0.8}
                >
                  <View style={styles.levelHeader}>
                    <LinearGradient
                      colors={getVIPGradient(level.level)}
                      style={styles.levelBadge}
                    >
                      <Ionicons name={level.icon as any} size={24} color="#1A1A2E" />
                    </LinearGradient>
                    <View style={styles.levelInfo}>
                      <Text style={styles.levelName}>{level.name}</Text>
                      <Text style={styles.levelFee}>
                        {level.monthly_fee > 0 ? `${level.monthly_fee}/month` : 'Free'}
                      </Text>
                    </View>
                    {current && (
                      <View style={styles.currentBadge}>
                        <Text style={styles.currentBadgeText}>ACTIVE</Text>
                      </View>
                    )}
                    {!unlocked && (
                      <Ionicons name="lock-closed" size={20} color="#808080" />
                    )}
                  </View>

                  <View style={styles.levelBenefits}>
                    {level.charity_bonus > 0 && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="heart" size={14} color="#4CAF50" />
                        <Text style={styles.benefitText}>+{level.charity_bonus}% Charity Bonus</Text>
                      </View>
                    )}
                    {level.free_spins_daily > 0 && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="gift" size={14} color="#2196F3" />
                        <Text style={styles.benefitText}>{level.free_spins_daily} Lucky Wallet Spins</Text>
                      </View>
                    )}
                    {level.education_discount > 0 && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="school" size={14} color="#9C27B0" />
                        <Text style={styles.benefitText}>{level.education_discount}% Education Discount</Text>
                      </View>
                    )}
                    {level.priority_support && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="headset" size={14} color="#FF9800" />
                        <Text style={styles.benefitText}>Priority Support</Text>
                      </View>
                    )}
                    {level.withdrawal_priority && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="flash" size={14} color="#FFD700" />
                        <Text style={styles.benefitText}>Fast Withdrawals</Text>
                      </View>
                    )}
                    {level.exclusive_games && (
                      <View style={styles.benefitItem}>
                        <Ionicons name="star" size={14} color="#E91E63" />
                        <Text style={styles.benefitText}>Exclusive Features</Text>
                      </View>
                    )}
                  </View>

                  {!unlocked && (
                    <View style={styles.unlockRequirement}>
                      <Ionicons name="information-circle" size={14} color="#808080" />
                      <Text style={styles.unlockText}>
                        Recharge {level.recharge_requirement.toLocaleString()} to unlock
                      </Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}

            <View style={{ height: 20 }} />
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>

      {/* Subscribe Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedLevel && (
              <>
                <LinearGradient
                  colors={getVIPGradient(selectedLevel.level)}
                  style={styles.modalBadge}
                >
                  <Ionicons name={selectedLevel.icon as any} size={40} color="#1A1A2E" />
                </LinearGradient>

                <Text style={styles.modalTitle}>Subscribe to {selectedLevel.name}</Text>
                <Text style={styles.modalSubtitle}>
                  Unlock exclusive benefits for {selectedLevel.monthly_fee} coins/month
                </Text>

                <View style={styles.modalBenefits}>
                  {selectedLevel.charity_bonus > 0 && (
                    <Text style={styles.modalBenefitText}>
                      • +{selectedLevel.charity_bonus}% Charity Lucky Wallet Bonus
                    </Text>
                  )}
                  {selectedLevel.free_spins_daily > 0 && (
                    <Text style={styles.modalBenefitText}>
                      • {selectedLevel.free_spins_daily} Lucky Wallet Spins Daily
                    </Text>
                  )}
                  {selectedLevel.education_discount > 0 && (
                    <Text style={styles.modalBenefitText}>
                      • {selectedLevel.education_discount}% Education Discount
                    </Text>
                  )}
                  {selectedLevel.priority_support && (
                    <Text style={styles.modalBenefitText}>• Priority Support</Text>
                  )}
                  {selectedLevel.withdrawal_priority && (
                    <Text style={styles.modalBenefitText}>• Fast Withdrawals</Text>
                  )}
                  {selectedLevel.exclusive_games && (
                    <Text style={styles.modalBenefitText}>• Exclusive Features Access</Text>
                  )}
                </View>

                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={styles.modalCancelButton}
                    onPress={() => setModalVisible(false)}
                  >
                    <Text style={styles.modalCancelText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.modalSubscribeButton}
                    onPress={handleSubscribe}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#1A1A2E" />
                    ) : (
                      <Text style={styles.modalSubscribeText}>Subscribe Now</Text>
                    )}
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
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
    marginTop: 16,
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#A0A0A0',
    marginTop: 4,
  },
  statusCard: {
    borderRadius: 20,
    padding: 24,
    marginBottom: 24,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  statusBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  statusInfo: {},
  statusLabel: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  statusLevel: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  statusFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 16,
  },
  statusDays: {
    fontSize: 14,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  rechargeProgress: {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  rechargeLabel: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  rechargeAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  autoRenewToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  autoRenewText: {
    fontSize: 14,
    color: '#1A1A2E',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  levelCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  levelCardActive: {
    borderColor: '#FFD700',
    borderWidth: 2,
  },
  levelCardLocked: {
    opacity: 0.7,
  },
  levelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  levelBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  levelInfo: {
    flex: 1,
  },
  levelName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  levelFee: {
    fontSize: 14,
    color: '#A0A0A0',
  },
  currentBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  currentBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  levelBenefits: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  benefitText: {
    fontSize: 12,
    color: '#FFFFFF',
  },
  unlockRequirement: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  unlockText: {
    fontSize: 12,
    color: '#808080',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: '#1A1A2E',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
  },
  modalBadge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#A0A0A0',
    textAlign: 'center',
    marginBottom: 24,
  },
  modalBenefits: {
    alignSelf: 'stretch',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  modalBenefitText: {
    fontSize: 14,
    color: '#FFFFFF',
    marginBottom: 8,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalSubscribeButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#FFD700',
    alignItems: 'center',
  },
  modalSubscribeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
  },
});
