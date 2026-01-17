import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import api from '../../src/services/api';

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  user_name: string;
  user_picture?: string;
  total_likes?: number;
  total_views?: number;
  score?: number;
  prize?: string;
  prize_coins?: number;
  crown?: string;
  crown_icon?: string;
  tier?: string;
}

interface Prize {
  prize: string;
  coins: number;
}

type TabType = 'monthly' | 'top150' | 'crowns';

export default function LeaderboardScreen() {
  const [activeTab, setActiveTab] = useState<TabType>('monthly');
  const [monthlyLeaderboard, setMonthlyLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [top150, setTop150] = useState<LeaderboardEntry[]>([]);
  const [prizes, setPrizes] = useState<Record<string, Prize>>({});
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [monthlyRes, top150Res] = await Promise.all([
        api.get('/leaderboard/video/monthly'),
        api.get('/leaderboard/top-150')
      ]);
      
      setMonthlyLeaderboard(monthlyRes.data.leaderboard || []);
      setPrizes(monthlyRes.data.prizes || {});
      setTop150(top150Res.data.top_models || []);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return '#FFD700';
    if (rank === 2) return '#C0C0C0';
    if (rank === 3) return '#CD7F32';
    return '#FFFFFF';
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getTierGradient = (tier: string): [string, string] => {
    switch (tier) {
      case 'gold': return ['#FFD700', '#FFA500'];
      case 'silver': return ['#C0C0C0', '#A0A0A0'];
      case 'bronze': return ['#CD7F32', '#8B4513'];
      default: return ['#404040', '#303030'];
    }
  };

  const renderLeaderboardItem = (item: LeaderboardEntry, showPrize: boolean = true) => (
    <View key={item.user_id} style={styles.leaderboardItem}>
      <View style={styles.rankContainer}>
        {item.rank <= 3 ? (
          <Text style={styles.rankBadge}>{getRankBadge(item.rank)}</Text>
        ) : (
          <View style={styles.rankNumber}>
            <Text style={[styles.rankText, { color: getRankColor(item.rank) }]}>
              {item.rank}
            </Text>
          </View>
        )}
      </View>
      
      <View style={styles.userInfo}>
        {item.user_picture ? (
          <Image source={{ uri: item.user_picture }} style={styles.avatar} />
        ) : (
          <LinearGradient
            colors={getTierGradient(item.tier || 'default')}
            style={styles.avatarPlaceholder}
          >
            <Text style={styles.avatarInitial}>
              {item.user_name?.charAt(0).toUpperCase() || 'U'}
            </Text>
          </LinearGradient>
        )}
        
        <View style={styles.userDetails}>
          <View style={styles.nameRow}>
            <Text style={styles.userName} numberOfLines={1}>
              {item.user_name}
            </Text>
            {item.crown_icon && (
              <Text style={styles.crownIcon}>{item.crown_icon}</Text>
            )}
          </View>
          <View style={styles.statsRow}>
            {item.total_likes !== undefined && (
              <Text style={styles.statText}>❤️ {item.total_likes.toLocaleString()}</Text>
            )}
            {item.total_views !== undefined && (
              <Text style={styles.statText}>👁️ {item.total_views.toLocaleString()}</Text>
            )}
            {item.score !== undefined && (
              <Text style={styles.statText}>⭐ {item.score.toLocaleString()}</Text>
            )}
          </View>
        </View>
      </View>
      
      {showPrize && item.prize && (
        <View style={styles.prizeContainer}>
          <Text style={styles.prizeText}>{item.prize}</Text>
          {item.prize_coins && (
            <Text style={styles.prizeCoins}>+{item.prize_coins.toLocaleString()} 💰</Text>
          )}
        </View>
      )}
      
      {item.tier && (
        <LinearGradient
          colors={getTierGradient(item.tier)}
          style={styles.tierBadge}
        >
          <Text style={styles.tierText}>{item.tier.toUpperCase()}</Text>
        </LinearGradient>
      )}
    </View>
  );

  const renderPrizesSection = () => (
    <View style={styles.prizesSection}>
      <Text style={styles.sectionTitle}>🏆 Monthly Prizes</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {Object.entries(prizes).slice(0, 5).map(([rank, prize]) => (
          <View key={rank} style={styles.prizeCard}>
            <LinearGradient
              colors={rank === '1' ? ['#FFD700', '#FFA500'] : ['#2A2A4A', '#1A1A3A']}
              style={styles.prizeCardGradient}
            >
              <Text style={styles.prizeRank}>{getRankBadge(parseInt(rank))}</Text>
              <Text style={[
                styles.prizeTitle,
                rank === '1' && { color: '#1A1A2E' }
              ]}>{prize.prize}</Text>
              <Text style={[
                styles.prizeCoinsCard,
                rank === '1' && { color: '#1A1A2E' }
              ]}>+{prize.coins.toLocaleString()} Coins</Text>
            </LinearGradient>
          </View>
        ))}
      </ScrollView>
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#1A1A2E', '#16213E', '#0F3460']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>🏆 Leaderboard</Text>
            <TouchableOpacity onPress={onRefresh}>
              <Ionicons name="refresh" size={24} color="#FFD700" />
            </TouchableOpacity>
          </View>

          {/* Tabs */}
          <View style={styles.tabContainer}>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'monthly' && styles.tabActive]}
              onPress={() => setActiveTab('monthly')}
            >
              <Text style={[styles.tabText, activeTab === 'monthly' && styles.tabTextActive]}>
                📅 Monthly
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'top150' && styles.tabActive]}
              onPress={() => setActiveTab('top150')}
            >
              <Text style={[styles.tabText, activeTab === 'top150' && styles.tabTextActive]}>
                👑 Top 150
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'crowns' && styles.tabActive]}
              onPress={() => setActiveTab('crowns')}
            >
              <Text style={[styles.tabText, activeTab === 'crowns' && styles.tabTextActive]}>
                🎖️ Crowns
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.scrollView}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFD700" />
            }
          >
            {activeTab === 'monthly' && (
              <>
                {renderPrizesSection()}
                
                <View style={styles.leaderboardSection}>
                  <Text style={styles.sectionTitle}>📊 This Month's Ranking</Text>
                  
                  {monthlyLeaderboard.length > 0 ? (
                    monthlyLeaderboard.map(item => renderLeaderboardItem(item, true))
                  ) : (
                    <View style={styles.emptyState}>
                      <Text style={styles.emptyIcon}>📭</Text>
                      <Text style={styles.emptyText}>Abhi koi data nahi hai</Text>
                      <Text style={styles.emptySubtext}>Videos upload karein aur compete karein!</Text>
                    </View>
                  )}
                </View>
              </>
            )}

            {activeTab === 'top150' && (
              <View style={styles.leaderboardSection}>
                <Text style={styles.sectionTitle}>👑 Top 150 Models</Text>
                <Text style={styles.sectionSubtitle}>All-time best performers</Text>
                
                {/* Tier Info */}
                <View style={styles.tierInfo}>
                  <View style={styles.tierItem}>
                    <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.tierDot} />
                    <Text style={styles.tierLabel}>Gold (1-10)</Text>
                  </View>
                  <View style={styles.tierItem}>
                    <LinearGradient colors={['#C0C0C0', '#A0A0A0']} style={styles.tierDot} />
                    <Text style={styles.tierLabel}>Silver (11-50)</Text>
                  </View>
                  <View style={styles.tierItem}>
                    <LinearGradient colors={['#CD7F32', '#8B4513']} style={styles.tierDot} />
                    <Text style={styles.tierLabel}>Bronze (51-150)</Text>
                  </View>
                </View>
                
                {top150.length > 0 ? (
                  top150.map(item => renderLeaderboardItem(item, false))
                ) : (
                  <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>🏆</Text>
                    <Text style={styles.emptyText}>Top 150 jaldi aayega!</Text>
                  </View>
                )}
              </View>
            )}

            {activeTab === 'crowns' && (
              <View style={styles.leaderboardSection}>
                <Text style={styles.sectionTitle}>🎖️ Crown System</Text>
                
                <View style={styles.crownGrid}>
                  {[
                    { type: 'Bronze', icon: '🥉', req: '100 likes, 5 videos', color: '#CD7F32' },
                    { type: 'Silver', icon: '🥈', req: '1K likes, 20 videos', color: '#C0C0C0' },
                    { type: 'Gold', icon: '🥇', req: '10K likes, 50 videos', color: '#FFD700' },
                    { type: 'Gifter', icon: '🎁', req: '10K gifts sent', color: '#E91E63' },
                    { type: 'Queen', icon: '👑', req: 'Special achievement', color: '#9C27B0' },
                    { type: 'Creator', icon: '🎬', req: '100 videos, 100K views', color: '#2196F3' },
                  ].map((crown) => (
                    <View key={crown.type} style={styles.crownCard}>
                      <View style={[styles.crownIconContainer, { backgroundColor: crown.color + '20' }]}>
                        <Text style={styles.crownEmoji}>{crown.icon}</Text>
                      </View>
                      <Text style={[styles.crownTitle, { color: crown.color }]}>{crown.type}</Text>
                      <Text style={styles.crownReq}>{crown.req}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            <View style={{ height: 100 }} />
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    alignItems: 'center',
  },
  tabActive: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  tabText: {
    fontSize: 12,
    color: '#808080',
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#FFD700',
  },
  scrollView: {
    flex: 1,
  },
  prizesSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#808080',
    marginBottom: 16,
    marginTop: -8,
  },
  prizeCard: {
    width: 140,
    marginRight: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  prizeCardGradient: {
    padding: 16,
    alignItems: 'center',
  },
  prizeRank: {
    fontSize: 32,
    marginBottom: 8,
  },
  prizeTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 4,
  },
  prizeCoinsCard: {
    fontSize: 10,
    color: '#FFD700',
  },
  leaderboardSection: {
    paddingHorizontal: 16,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  rankContainer: {
    width: 40,
    alignItems: 'center',
  },
  rankBadge: {
    fontSize: 24,
  },
  rankNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rankText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  userInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 8,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
  },
  avatarPlaceholder: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarInitial: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  userDetails: {
    flex: 1,
    marginLeft: 12,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  userName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    maxWidth: 120,
  },
  crownIcon: {
    fontSize: 14,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 4,
  },
  statText: {
    fontSize: 11,
    color: '#808080',
  },
  prizeContainer: {
    alignItems: 'flex-end',
  },
  prizeText: {
    fontSize: 10,
    color: '#FFD700',
    fontWeight: '600',
    maxWidth: 80,
    textAlign: 'right',
  },
  prizeCoins: {
    fontSize: 9,
    color: '#4CAF50',
    marginTop: 2,
  },
  tierBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  tierText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#1A1A2E',
  },
  tierInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  tierItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tierDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  tierLabel: {
    fontSize: 10,
    color: '#A0A0A0',
  },
  crownGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  crownCard: {
    width: '47%',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  crownIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  crownEmoji: {
    fontSize: 28,
  },
  crownTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  crownReq: {
    fontSize: 10,
    color: '#808080',
    textAlign: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 12,
    color: '#808080',
  },
});
