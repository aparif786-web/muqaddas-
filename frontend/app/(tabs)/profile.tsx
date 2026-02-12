import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../../src/contexts/AuthContext';
import api from '../../src/services/api';

interface VIPStatus {
  vip_level: number;
  is_active: boolean;
  current_level_data: {
    name: string;
    badge_color: string;
  };
}

interface Wallet {
  coins_balance: number;
  bonus_balance: number;
  stars_balance: number;
  withdrawable_balance: number;
}

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [vipStatus, setVipStatus] = useState<VIPStatus | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [vipRes, walletRes] = await Promise.all([
        api.get('/vip/status'),
        api.get('/wallet'),
      ]);
      setVipStatus(vipRes.data);
      setWallet(walletRes.data);
    } catch (error) {
      console.error('Error fetching profile data:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const menuItems = [
    {
      icon: 'receipt',
      label: 'Transaction History',
      onPress: () => router.push('/(tabs)/wallet'),
    },
    {
      icon: 'diamond',
      label: 'VIP Status',
      sublabel: vipStatus?.current_level_data?.name || 'Basic',
      onPress: () => router.push('/(tabs)/vip'),
    },
    {
      icon: 'notifications',
      label: 'Notifications',
      onPress: () => {},
    },
    {
      icon: 'settings',
      label: 'Settings',
      onPress: () => {},
    },
    {
      icon: 'help-circle',
      label: 'Help & Support',
      onPress: () => {},
    },
    {
      icon: 'document-text',
      label: 'Terms & Privacy',
      onPress: () => {},
    },
  ];

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <ScrollView
            style={styles.scrollView}
            showsVerticalScrollIndicator={false}
          >
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.headerTitle}>Profile</Text>
            </View>

            {/* Profile Card */}
            <View style={styles.profileCard}>
              <View style={styles.profileImageContainer}>
                {user?.picture ? (
                  <Image
                    source={{ uri: user.picture }}
                    style={styles.profileImage}
                  />
                ) : (
                  <LinearGradient
                    colors={['#FFD700', '#FFA500']}
                    style={styles.profileImagePlaceholder}
                  >
                    <Text style={styles.profileInitial}>
                      {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </Text>
                  </LinearGradient>
                )}
                {vipStatus?.is_active && (
                  <View
                    style={[
                      styles.vipBadge,
                      { backgroundColor: vipStatus.current_level_data?.badge_color || '#FFD700' },
                    ]}
                  >
                    <Ionicons name="diamond" size={12} color="#1A1A2E" />
                  </View>
                )}
              </View>
              <Text style={styles.profileName}>{user?.name || 'User'}</Text>
              <Text style={styles.profileEmail}>{user?.email || ''}</Text>
              
              {vipStatus?.is_active && (
                <View style={styles.vipStatusBadge}>
                  <Ionicons name="star" size={14} color="#FFD700" />
                  <Text style={styles.vipStatusText}>
                    {vipStatus.current_level_data?.name} Member
                  </Text>
                </View>
              )}
            </View>

            {/* Wallet Section - SULTAN's PSYCHOLOGY: Withdraw here, not on home */}
            <View style={styles.walletSection}>
              <View style={styles.walletHeader}>
                <Ionicons name="wallet" size={20} color="#FFD700" />
                <Text style={styles.walletTitle}>My Wallet</Text>
              </View>
              
              {/* Triple Wallet Display */}
              <View style={styles.tripleWallet}>
                <View style={styles.walletCard}>
                  <LinearGradient
                    colors={['#4CAF50', '#2E7D32']}
                    style={styles.walletCardGradient}
                  >
                    <Ionicons name="wallet" size={24} color="#FFFFFF" />
                    <Text style={styles.walletCardLabel}>Main Balance</Text>
                    <Text style={styles.walletCardAmount}>
                      {wallet?.coins_balance?.toLocaleString() || '0'}
                    </Text>
                    <Text style={styles.walletCardCurrency}>Coins</Text>
                  </LinearGradient>
                </View>
                
                <View style={styles.walletCard}>
                  <LinearGradient
                    colors={['#FFD700', '#FFA500']}
                    style={styles.walletCardGradient}
                  >
                    <Ionicons name="trending-up" size={24} color="#1A1A2E" />
                    <Text style={[styles.walletCardLabel, { color: '#1A1A2E' }]}>Earnings</Text>
                    <Text style={[styles.walletCardAmount, { color: '#1A1A2E' }]}>
                      {wallet?.withdrawable_balance?.toLocaleString() || '0'}
                    </Text>
                    <Text style={[styles.walletCardCurrency, { color: '#1A1A2E' }]}>Withdrawable</Text>
                  </LinearGradient>
                </View>
                
                <View style={styles.walletCard}>
                  <LinearGradient
                    colors={['#E91E63', '#C2185B']}
                    style={styles.walletCardGradient}
                  >
                    <Ionicons name="gift" size={24} color="#FFFFFF" />
                    <Text style={styles.walletCardLabel}>Bonus Wallet</Text>
                    <Text style={styles.walletCardAmount}>
                      {wallet?.bonus_balance?.toLocaleString() || '0'}
                    </Text>
                    <Text style={styles.walletCardCurrency}>Rewards</Text>
                  </LinearGradient>
                </View>
              </View>
              
              {/* Wallet Action Buttons */}
              <View style={styles.walletActions}>
                <TouchableOpacity 
                  style={styles.walletActionBtn}
                  onPress={() => router.push('/(tabs)/wallet')}
                >
                  <Ionicons name="add-circle" size={20} color="#4CAF50" />
                  <Text style={styles.walletActionText}>Deposit</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.walletActionBtn}
                  onPress={() => router.push('/(tabs)/wallet')}
                >
                  <Ionicons name="swap-horizontal" size={20} color="#2196F3" />
                  <Text style={styles.walletActionText}>Transfer</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={[styles.walletActionBtn, styles.withdrawBtn]}
                  onPress={() => {
                    if ((wallet?.withdrawable_balance || 0) < 100) {
                      Alert.alert(
                        'Minimum Balance Required',
                        'You need at least 100 coins in Earnings to withdraw.',
                        [{ text: 'OK' }]
                      );
                    } else {
                      setShowWithdrawModal(true);
                    }
                  }}
                >
                  <Ionicons name="cash" size={20} color="#FF9800" />
                  <Text style={styles.walletActionText}>Withdraw</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Stats Row - Stars Only */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {wallet?.stars_balance?.toLocaleString() || '0'}
                </Text>
                <Text style={styles.statLabel}>⭐ Stars</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {vipStatus?.vip_level || 0}
                </Text>
                <Text style={styles.statLabel}>VIP Level</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>0</Text>
                <Text style={styles.statLabel}>Achievements</Text>
              </View>
            </View>

            {/* Menu Items */}
            <View style={styles.menuSection}>
              {menuItems.map((item, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.menuItem}
                  onPress={item.onPress}
                  activeOpacity={0.7}
                >
                  <View style={styles.menuItemLeft}>
                    <View style={styles.menuIconContainer}>
                      <Ionicons name={item.icon as any} size={20} color="#FFD700" />
                    </View>
                    <View>
                      <Text style={styles.menuItemLabel}>{item.label}</Text>
                      {item.sublabel && (
                        <Text style={styles.menuItemSublabel}>{item.sublabel}</Text>
                      )}
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#808080" />
                </TouchableOpacity>
              ))}
            </View>

            {/* Logout Button */}
            <TouchableOpacity
              style={styles.logoutButton}
              onPress={handleLogout}
            >
              <Ionicons name="log-out" size={20} color="#FF5252" />
              <Text style={styles.logoutText}>Logout</Text>
            </TouchableOpacity>

            {/* App Version */}
            <Text style={styles.versionText}>Gyan Sultanat v1.0.0</Text>

            <View style={{ height: 20 }} />
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
      
      {/* Withdraw Modal */}
      <Modal
        visible={showWithdrawModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowWithdrawModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>💸 Withdraw Earnings</Text>
              <TouchableOpacity onPress={() => setShowWithdrawModal(false)}>
                <Ionicons name="close" size={24} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.modalBody}>
              <Text style={styles.withdrawLabel}>Available to Withdraw:</Text>
              <Text style={styles.withdrawAvailable}>
                {wallet?.withdrawable_balance?.toLocaleString() || '0'} Coins
              </Text>
              
              <Text style={styles.withdrawNote}>
                Minimum withdrawal: 100 coins{'\n'}
                Processing time: 24-48 hours
              </Text>
              
              <TouchableOpacity 
                style={styles.withdrawSubmitBtn}
                onPress={() => {
                  Alert.alert(
                    'Withdrawal Requested',
                    'Your withdrawal request has been submitted. Processing time is 24-48 hours.',
                    [{ text: 'OK', onPress: () => setShowWithdrawModal(false) }]
                  );
                }}
              >
                <LinearGradient
                  colors={['#FF9800', '#F57C00']}
                  style={styles.withdrawSubmitGradient}
                >
                  <Text style={styles.withdrawSubmitText}>Request Withdrawal</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
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
  profileCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    marginBottom: 20,
  },
  profileImageContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#FFD700',
  },
  profileImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInitial: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  vipBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#1A1A2E',
  },
  profileName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
    color: '#A0A0A0',
    marginBottom: 12,
  },
  vipStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 6,
  },
  vipStatusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFD700',
  },
  // Wallet Section Styles
  walletSection: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  walletHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  walletTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  tripleWallet: {
    gap: 12,
  },
  walletCard: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  walletCardGradient: {
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  walletCardLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    flex: 1,
    marginLeft: 12,
  },
  walletCardAmount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  walletCardCurrency: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.6)',
    marginLeft: 4,
  },
  walletActions: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 8,
  },
  walletActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 10,
    padding: 12,
    gap: 6,
  },
  withdrawBtn: {
    backgroundColor: 'rgba(255, 152, 0, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 152, 0, 0.3)',
  },
  walletActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  menuSection: {
    marginBottom: 24,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  menuItemLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  menuItemSublabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 82, 82, 0.1)',
    borderRadius: 12,
    padding: 16,
    gap: 8,
    marginBottom: 16,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF5252',
  },
  versionText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#808080',
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
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
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  modalBody: {
    alignItems: 'center',
  },
  withdrawLabel: {
    fontSize: 14,
    color: '#808080',
    marginBottom: 8,
  },
  withdrawAvailable: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 16,
  },
  withdrawNote: {
    fontSize: 12,
    color: '#808080',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 18,
  },
  withdrawSubmitBtn: {
    width: '100%',
    borderRadius: 12,
    overflow: 'hidden',
  },
  withdrawSubmitGradient: {
    padding: 16,
    alignItems: 'center',
  },
  withdrawSubmitText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
});
