import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Alert } from 'react-native';
import { api } from '../api/client';
import * as Location from 'expo-location';

export default function HomeScreen() {
  const [sosActive, setSosActive] = useState(false);
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [status, setStatus] = useState('IDLE');
  const [location, setLocation] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission to access location was denied. Using demo coordinates.');
        setLocation({ coords: { latitude: 12.0, longitude: 80.0 } });
        return;
      }
      try {
        let loc = await Location.getCurrentPositionAsync({});
        setLocation(loc);
      } catch (e) {
        setLocation({ coords: { latitude: 12.0, longitude: 80.0 } });
      }
    })();
  }, []);

  const triggerSOS = async () => {
    setLoading(true);
    setStatus('TRIGGERING...');
    try {
      const lat = location?.coords?.latitude || 12.0;
      const lon = location?.coords?.longitude || 80.0;
      
      const res = await api.triggerSOS({
        vessel_id: '11111111-0000-0000-0000-000000000001',
        lat,
        lon,
        description: 'Mobile App SOS Trigger'
      });
      setIncidentId(res.incident_id || res.id);
      setSosActive(true);
      setStatus('ACTIVE - WAITING FOR RESCUE');
    } catch (e) {
      setStatus('FAILED TO SEND SOS');
      Alert.alert('Error', 'Failed to send SOS');
    } finally {
      setLoading(false);
    }
  };

  const cancelSOS = async () => {
    if (!incidentId) return;
    setLoading(true);
    try {
      await api.cancelSOS(incidentId);
      setSosActive(false);
      setIncidentId(null);
      setStatus('IDLE');
    } catch (e) {
      Alert.alert('Error', 'Failed to cancel SOS');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>MFV SARASWATI</Text>
        <Text style={styles.subtitle}>GPS CONNECTED (DEMO)</Text>
      </View>

      {sosActive ? (
        <View style={styles.sosActiveContainer}>
          <Text style={styles.sosTitle}>SOS SENT</Text>
          <Text style={styles.sosStatus}>{status}</Text>
          <Text style={styles.infoText}>Incident ID: {incidentId}</Text>
          
          <TouchableOpacity style={styles.cancelBtn} onPress={cancelSOS} disabled={loading}>
            <Text style={styles.cancelBtnText}>{loading ? 'CANCELLING...' : 'CANCEL SOS'}</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.content}>
          <TouchableOpacity style={styles.sosBtn} onPress={triggerSOS} disabled={loading}>
            <Text style={styles.sosBtnText}>{loading ? 'SENDING...' : 'DECLARE SOS'}</Text>
          </TouchableOpacity>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Weather & Marine</Text>
            <Text>Status: Clear, 15kn Wind</Text>
            <Text>Nearest PFZ: 12.4 NM</Text>
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { backgroundColor: '#0f766e', padding: 20, paddingTop: 60 },
  title: { color: 'white', fontSize: 24, fontWeight: 'bold' },
  subtitle: { color: '#99f6e4', fontSize: 12, marginTop: 4 },
  content: { padding: 20 },
  sosBtn: { backgroundColor: '#dc2626', padding: 30, borderRadius: 16, alignItems: 'center', marginBottom: 20, elevation: 4 },
  sosBtnText: { color: 'white', fontSize: 24, fontWeight: 'bold' },
  card: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 16, elevation: 2 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 8, color: '#334155' },
  sosActiveContainer: { flex: 1, backgroundColor: '#7f1d1d', padding: 20, justifyContent: 'center', alignItems: 'center' },
  sosTitle: { color: 'white', fontSize: 36, fontWeight: 'bold', marginBottom: 10 },
  sosStatus: { color: '#fca5a5', fontSize: 18, marginBottom: 20, textAlign: 'center' },
  infoText: { color: 'white', fontSize: 14, marginBottom: 30 },
  cancelBtn: { backgroundColor: 'white', padding: 16, borderRadius: 30, width: '100%', alignItems: 'center' },
  cancelBtnText: { color: '#7f1d1d', fontSize: 18, fontWeight: 'bold' }
});
