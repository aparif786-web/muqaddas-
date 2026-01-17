import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Share,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import api from '../../src/services/api';

interface AgencyLevel {
  name: string;
  commission_rate: number;
  monthly_threshold: number;
}

interface AgencyStatus {
  user_id: string;
  agency_level: number;
  referral_code: string;
  total_referrals: number;
  active_referrals: number;
  total_commission_earned: number;
  monthly_volume: number;
  level_info: AgencyLevel;
  next_level_info: AgencyLevel | null;
  referrals: any[];
  all_levels: Record<string, AgencyLevel>;
}

export default function AgencyScreen() {
  const [agencyStatus, setAgencyStatus] = useState<AgencyStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [applyModalVisible, setApplyModalVisible] = useState(false);
  const [referralCode, setReferralCode] = useState('');
  const [applying, setApplying] = useState(false);

  const fetchData = async () => {
    try {
      const response = await api.get('/agency/status');
      setAgencyStatus(response.data);
    } catch (error) {
      console.error('Error fetching agency status:', error);
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

  const copyReferralCode = async () => {
    if (agencyStatus?.referral_code) {
      await Clipboard.setStringAsync(agencyStatus.referral_code);
      Alert.alert('Copied!', 'Referral code copied to clipboard');
    }
  };

  const shareReferralCode = async () => {
    if (agencyStatus?.referral_code) {
      try {
        await Share.share({
          message: `Join Mugaddas Network using my referral code: ${agencyStatus.referral_code}\n\nDownload now and earn rewards!`,
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    }
  };

  const applyReferralCode = async () => {
    if (!referralCode.trim()) {
      Alert.alert('Error', 'Please enter a referral code');
      return;
    }

    setApplying(true);
    try {
      await api.post('/agency/apply-referral', { referral_code: referralCode });
      Alert.alert('Success', 'Referral code applied successfully!');
      setApplyModalVisible(false);
      setReferralCode('');
      await fetchData();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to apply referral code');
    } finally {
      setApplying(false);
    }
  };

  const getLevelColor = (level: number): string[] => {
    switch (level) {
      case 1: return ['#CD7F32', '#8B4513'];
      case 2: return ['#C0C0C0', '#808080'];
      case 3: return ['#FFD700', '#FFA500'];
      default: return ['#404040', '#303030'];
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
              <Text style={styles.headerTitle}>Agency Program</Text>
              <Text style={styles.headerSubtitle}>Earn commissions by referring</Text>
            </View>

            {/* Current Level Card */}
            {agencyStatus && (
              <LinearGradient
                colors={getLevelColor(agencyStatus.agency_level)}
                style={styles.levelCard}
              >
                <View style={styles.levelHeader}>
                  <View style={styles.levelBadge}>
                    <Ionicons name="briefcase" size={32} color="#1A1A2E" />
                  </View>
                  <View style={styles.levelInfo}>
                    <Text style={styles.levelLabel}>Your Level</Text>
                    <Text style={styles.levelName}>{agencyStatus.level_info.name}</Text>
                  </View>
                </View>

                <View style={styles.commissionBadge}>
                  <Text style={styles.commissionRate}>
                    {agencyStatus.level_info.commission_rate}%
                  </Text>
                  <Text style={styles.commissionLabel}>Commission Rate</Text>
                </View>

                {agencyStatus.next_level_info && (
                  <View style={styles.nextLevelInfo}>
                    <Ionicons name="arrow-up" size={14} color="rgba(0,0,0,0.6)" />
                    <Text style={styles.nextLevelText}>
                      ${agencyStatus.next_level_info.monthly_threshold - agencyStatus.monthly_volume} more to reach {agencyStatus.next_level_info.name}
                    </Text>
                  </View>
                )}
              </LinearGradient>
            )}

            {/* Referral Code Card */}
            <View style={styles.referralCard}>
              <Text style={styles.sectionTitle}>Your Referral Code</Text>
              <View style={styles.codeContainer}>
                <Text style={styles.referralCode}>{agencyStatus?.referral_code || '---'}</Text>
                <View style={styles.codeActions}>
                  <TouchableOpacity style={styles.codeButton} onPress={copyReferralCode}>
                    <Ionicons name="copy" size={20} color="#FFD700" />
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.codeButton} onPress={shareReferralCode}>
                    <Ionicons name="share-social" size={20} color="#FFD700" />
                  </TouchableOpacity>
                </View>
              </View>

              <TouchableOpacity
                style={styles.applyButton}
                onPress={() => setApplyModalVisible(true)}
              >
                <Ionicons name="add-circle" size={20} color="#4CAF50" />
                <Text style={styles.applyButtonText}>Apply a Referral Code</Text>
              </TouchableOpacity>
            </View>

            {/* Stats */}
            <View style={styles.statsRow}>
              <View style={styles.statCard}>
                <Ionicons name="people" size={24} color="#4CAF50" />
                <Text style={styles.statValue}>{agencyStatus?.total_referrals || 0}</Text>
                <Text style={styles.statLabel}>Referrals</Text>
              </View>
              <View style={styles.statCard}>
                <Ionicons name="cash" size={24} color="#FFD700" />
                <Text style={styles.statValue}>
                  {agencyStatus?.total_commission_earned?.toLocaleString() || 0}
                </Text>
                <Text style={styles.statLabel}>Earned</Text>
              </View>
              <View style={styles.statCard}>
                <Ionicons name="trending-up" size={24} color="#2196F3" />
                <Text style={styles.statValue}>
                  ${agencyStatus?.monthly_volume?.toLocaleString() || 0}
                </Text>
                <Text style={styles.statLabel}>This Month</Text>
              </View>
            </View>

            {/* Commission Levels */}
            <View style={styles.levelsSection}>
              <Text style={styles.sectionTitle}>Commission Levels</Text>
              {agencyStatus && Object.entries(agencyStatus.all_levels).map(([key, level]) => {
                const levelNum = parseInt(key);
                const isCurrentLevel = levelNum === agencyStatus.agency_level;
                const isUnlocked = levelNum <= agencyStatus.agency_level;
                
                return (
                  <View 
                    key={key} 
                    style={[
                      styles.levelItem,
                      isCurrentLevel && styles.levelItemActive
                    ]}
                  >
                    <View style={styles.levelItemLeft}>
                      <LinearGradient
                        colors={getLevelColor(levelNum)}
                        style={styles.levelItemBadge}
                      >
                        <Ionicons 
                          name={isUnlocked ? "checkmark" : "lock-closed"} 
                          size={16} 
                          color="#1A1A2E" 
                        />
                      </LinearGradient>
                      <View>
                        <Text style={styles.levelItemName}>{level.name}</Text>
                        <Text style={styles.levelItemThreshold}>
                          ${level.monthly_threshold}/month
                        </Text>
                      </View>
                    </View>
                    <View style={styles.levelItemRight}>
                      <Text style={styles.levelItemRate}>{level.commission_rate}%</Text>
                    </View>
                  </View>
                );
              })}
            </View>

            {/* How It Works */}
            <View style={styles.howItWorks}>
              <Text style={styles.sectionTitle}>How It Works</Text>
              
              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>1</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Share Your Code</Text>
                  <Text style={styles.stepDescription}>
                    Share your unique referral code with friends
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>2</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>They Join & Play</Text>
                  <Text style={styles.stepDescription}>
                    When they sign up and make transactions
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>3</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Earn Commissions</Text>
                  <Text style={styles.stepDescription}>
                    Get commissions in COINS (12-20% based on level)
                  </Text>
                </View>
              </View>

              <View style={styles.stepItem}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>4</Text>
                </View>
                <View style={styles.stepContent}>
                  <Text style={styles.stepTitle}>Level Up</Text>
                  <Text style={styles.stepDescription}>
                    Reach $3,000/month to become Agency Level 20!
                  </Text>
                </View>
              </View>
            </View>

            <View style={{ height: 20 }} />
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>

      {/* Apply Referral Modal */}
      <Modal
        visible={applyModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setApplyModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Apply Referral Code</Text>
              <TouchableOpacity onPress={() => setApplyModalVisible(false)}>
                <Ionicons name="close" size={24} color="#FFFFFF" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>
              Enter the referral code shared by your friend
            </Text>

            <View style={styles.inputContainer}>
              <Ionicons name="ticket" size={20} color="#FFD700" />
              <TextInput
                style={styles.input}
                placeholder="Enter code (e.g., MN12345678)"
                placeholderTextColor="#808080"
                value={referralCode}
                onChangeText={setReferralCode}
                autoCapitalize="characters"
              />
            </View>

            <TouchableOpacity
              style={styles.submitButton}
              onPress={applyReferralCode}
              disabled={applying}
            >
              <Text style={styles.submitButtonText}>
                {applying ? 'Applying...' : 'Apply Code'}
              </Text>
            </TouchableOpacity>
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
  levelCard: {
    borderRadius: 20,
    padding: 24,
    marginBottom: 20,
  },
  levelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  levelBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  levelInfo: {},
  levelLabel: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  levelName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  commissionBadge: {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  commissionRate: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  commissionLabel: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  nextLevelInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  nextLevelText: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  referralCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  codeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  referralCode: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFD700',
    letterSpacing: 2,
  },
  codeActions: {
    flexDirection: 'row',
    gap: 12,
  },
  codeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  applyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
    borderRadius: 12,
    padding: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(76, 175, 80, 0.3)',
  },
  applyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4CAF50',
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
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 11,
    color: '#808080',
    marginTop: 4,
  },
  levelsSection: {
    marginBottom: 24,
  },
  levelItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  levelItemActive: {
    borderWidth: 2,
    borderColor: '#FFD700',
  },
  levelItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  levelItemBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  levelItemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  levelItemThreshold: {
    fontSize: 12,
    color: '#808080',
  },
  levelItemRight: {},
  levelItemRate: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  howItWorks: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1A1A2E',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#808080',
    marginBottom: 24,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  input: {
    flex: 1,
    paddingVertical: 16,
    paddingHorizontal: 12,
    fontSize: 18,
    color: '#FFFFFF',
  },
  submitButton: {
    backgroundColor: '#FFD700',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
  },
});
