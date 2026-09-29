import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text, SafeAreaView } from 'react-native';
import HomeScreen from './src/screens/HomeScreen';
import OrcaScreen from './src/screens/OrcaScreen';
import RouteScreen from './src/screens/RouteScreen';

export default function App() {
  const [currentTab, setCurrentTab] = useState('Home');

  const renderScreen = () => {
    switch (currentTab) {
      case 'Home': return <HomeScreen />;
      case 'Orca': return <OrcaScreen />;
      case 'Route': return <RouteScreen />;
      default: return <HomeScreen />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {renderScreen()}
      </View>
      <View style={styles.tabBar}>
        <TouchableOpacity style={styles.tab} onPress={() => setCurrentTab('Home')}>
          <Text style={[styles.tabText, currentTab === 'Home' && styles.activeTab]}>Home</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tab} onPress={() => setCurrentTab('Orca')}>
          <Text style={[styles.tabText, currentTab === 'Orca' && styles.activeTab]}>ORCA</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.tab} onPress={() => setCurrentTab('Route')}>
          <Text style={[styles.tabText, currentTab === 'Route' && styles.activeTab]}>Route</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'white' },
  content: { flex: 1 },
  tabBar: { 
    flexDirection: 'row', 
    backgroundColor: '#0f766e', 
    height: 60,
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingBottom: 10
  },
  tab: { padding: 10 },
  tabText: { color: '#99f6e4', fontSize: 16 },
  activeTab: { color: 'white', fontWeight: 'bold' }
});
