import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, StyleSheet, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function TabLayout() {
  const insets = useSafeAreaInsets();
  
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#1A1A2E',
          borderTopColor: '#2A2A3E',
          borderTopWidth: 1,
          height: 60 + insets.bottom,
          paddingBottom: insets.bottom,
          paddingTop: 8,
        },
        tabBarActiveTintColor: '#FFD700',
        tabBarInactiveTintColor: '#808080',
        tabBarLabelStyle: {
          fontSize: 9,
          fontWeight: '500',
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="leaderboard"
        options={{
          title: 'Rank',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="trophy" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="ai-teacher"
        options={{
          title: 'AI Guru',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="school" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="wallet"
        options={{
          title: 'Wallet',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="wallet" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={22} color={color} />
          ),
        }}
      />
      {/* Hidden tabs - not shown in tab bar */}
      <Tabs.Screen
        name="rewards"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="agency"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="education"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="vip"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="withdrawal"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="talent-register"
        options={{
          href: null,
        }}
      />
    </Tabs>
  );
}
