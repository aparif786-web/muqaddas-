import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

interface App {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface Sector {
  name: string;
  count: number;
  description: string;
  apps: App[];
}

interface DirectoryData {
  title: string;
  subtitle: string;
  stats: {
    total_apps: number;
    total_sectors: number;
  };
  sectors: { [key: string]: Sector };
  featured: App[];
  coming_soon: App[];
}

export default function AppDirectoryScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [directory, setDirectory] = useState<DirectoryData | null>(null);
  const [expandedSector, setExpandedSector] = useState<string | null>(null);

  const fetchDirectory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/app-directory`);
      if (response.data.success) {
        setDirectory(response.data);
      }
    } catch (error) {
      console.error('Error fetching directory:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDirectory();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDirectory();
  };

  const toggleSector = (sectorId: string) => {
    setExpandedSector(expandedSector === sectorId ? null : sectorId);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#FFD700" />
          <Text style={styles.loadingText}>Loading App Directory...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#FFD700"
          />
        }
      >
        {/* Header */}
        <LinearGradient
          colors={['#1A1A2E', '#2D1B4E']}
          style={styles.header}
        >
          <Text style={styles.headerEmoji}>👑</Text>
          <Text style={styles.headerTitle}>{directory?.title || "SULTAN'S APP DIRECTORY"}</Text>
          <Text style={styles.headerSubtitle}>{directory?.subtitle || "500+ Applications"}</Text>
          
          {/* Stats */}
          <View style={styles.statsContainer}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{directory?.stats.total_apps || 500}+</Text>
              <Text style={styles.statLabel}>Apps</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{directory?.stats.total_sectors || 5}</Text>
              <Text style={styles.statLabel}>Sectors</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>100+</Text>
              <Text style={styles.statLabel}>Languages</Text>
            </View>
          </View>
        </LinearGradient>

        {/* Featured Apps */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⭐ Featured Apps</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {directory?.featured.map((app, index) => (
              <TouchableOpacity key={index} style={styles.featuredCard}>
                <LinearGradient
                  colors={['#FFD700', '#FFA500']}
                  style={styles.featuredGradient}
                >
                  <Text style={styles.featuredIcon}>{app.icon || '🧠'}</Text>
                  <Text style={styles.featuredName}>{app.name}</Text>
                  <Text style={styles.featuredDesc}>{app.description}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Sectors */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📂 All Sectors</Text>
          
          {directory && Object.entries(directory.sectors).map(([sectorId, sector]) => (
            <View key={sectorId} style={styles.sectorContainer}>
              <TouchableOpacity
                style={styles.sectorHeader}
                onPress={() => toggleSector(sectorId)}
              >
                <View style={styles.sectorInfo}>
                  <Text style={styles.sectorName}>{sector.name}</Text>
                  <Text style={styles.sectorCount}>{sector.count}+ Apps</Text>
                </View>
                <Ionicons
                  name={expandedSector === sectorId ? 'chevron-up' : 'chevron-down'}
                  size={24}
                  color="#FFD700"
                />
              </TouchableOpacity>
              
              {expandedSector === sectorId && (
                <View style={styles.appsContainer}>
                  <Text style={styles.sectorDescription}>{sector.description}</Text>
                  {sector.apps.map((app, index) => (
                    <TouchableOpacity key={index} style={styles.appItem}>
                      <Text style={styles.appIcon}>{app.icon}</Text>
                      <View style={styles.appInfo}>
                        <Text style={styles.appName}>{app.name}</Text>
                        <Text style={styles.appDesc}>{app.description}</Text>
                      </View>
                      <Ionicons name="chevron-forward" size={20} color="#808080" />
                    </TouchableOpacity>
                  ))}
                  <Text style={styles.moreApps}>+ {sector.count - sector.apps.length} more apps coming...</Text>
                </View>
              )}
            </View>
          ))}
        </View>

        {/* Coming Soon */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🚀 Coming Soon</Text>
          {directory?.coming_soon.map((app, index) => (
            <View key={index} style={styles.comingSoonItem}>
              <Text style={styles.comingSoonIcon}>{app.icon || '🔜'}</Text>
              <View style={styles.comingSoonInfo}>
                <Text style={styles.comingSoonName}>{app.name}</Text>
                <Text style={styles.comingSoonDesc}>{app.description}</Text>
              </View>
              <View style={styles.comingSoonBadge}>
                <Text style={styles.comingSoonBadgeText}>SOON</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Sultan-Pulse Banner */}
        <TouchableOpacity style={styles.pulseBanner}>
          <LinearGradient
            colors={['#10B981', '#059669']}
            style={styles.pulseBannerGradient}
          >
            <Text style={styles.pulseBannerIcon}>🖲️</Text>
            <View style={styles.pulseBannerContent}>
              <Text style={styles.pulseBannerTitle}>SULTAN-PULSE</Text>
              <Text style={styles.pulseBannerSubtitle}>Your Digital Identity & ATM</Text>
            </View>
            <Ionicons name="arrow-forward" size={24} color="#FFFFFF" />
          </LinearGradient>
        </TouchableOpacity>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>💚 Muqaddas Technology</Text>
          <Text style={styles.footerSubtext}>Gyan Sultanat - Digital Sultanat</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F0F1A',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    marginTop: 16,
    fontSize: 16,
  },
  header: {
    padding: 24,
    alignItems: 'center',
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#CCCCCC',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    marginTop: 20,
    gap: 24,
  },
  statBox: {
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  statLabel: {
    fontSize: 12,
    color: '#CCCCCC',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  featuredCard: {
    marginRight: 12,
    borderRadius: 16,
    overflow: 'hidden',
    width: 160,
  },
  featuredGradient: {
    padding: 16,
    alignItems: 'center',
  },
  featuredIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  featuredName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#000000',
    textAlign: 'center',
  },
  featuredDesc: {
    fontSize: 11,
    color: '#333333',
    textAlign: 'center',
    marginTop: 4,
  },
  sectorContainer: {
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
  },
  sectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  sectorInfo: {
    flex: 1,
  },
  sectorName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  sectorCount: {
    fontSize: 12,
    color: '#808080',
    marginTop: 2,
  },
  appsContainer: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: '#2A2A3E',
  },
  sectorDescription: {
    fontSize: 13,
    color: '#AAAAAA',
    marginBottom: 12,
  },
  appItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#252538',
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
  },
  appIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  appInfo: {
    flex: 1,
  },
  appName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  appDesc: {
    fontSize: 11,
    color: '#808080',
    marginTop: 2,
  },
  moreApps: {
    fontSize: 12,
    color: '#FFD700',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  comingSoonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A2E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  comingSoonIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  comingSoonInfo: {
    flex: 1,
  },
  comingSoonName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  comingSoonDesc: {
    fontSize: 12,
    color: '#808080',
    marginTop: 2,
  },
  comingSoonBadge: {
    backgroundColor: '#FFD700',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  comingSoonBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#000000',
  },
  pulseBanner: {
    margin: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  pulseBannerGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
  },
  pulseBannerIcon: {
    fontSize: 32,
    marginRight: 16,
  },
  pulseBannerContent: {
    flex: 1,
  },
  pulseBannerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  pulseBannerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 2,
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#10B981',
  },
  footerSubtext: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
});
