import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, ScrollView, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Location from 'expo-location';
import * as Network from 'expo-network';
import 'react-native-get-random-values';
import { v4 as uuidv4 } from 'uuid';
import { api } from '@/api/client';
import { offlineStorage, PendingSOS } from '@/lib/offlineStorage';

export default function HomeScreen() {
  const [isOffline, setIsOffline] = useState(false);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [cachedReport, setCachedReport] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [pendingQueue, setPendingQueue] = useState<PendingSOS[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [sosStatus, setSosStatus] = useState<string | null>(null);
  const [satelliteSimStatus, setSatelliteSimStatus] = useState<Record<string, string>>({});

  const VESSEL_ID = '11111111-0000-0000-0000-000000000001';

  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        console.warn('Permission to access location was denied');
        return;
      }
      let loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);
    })();
    
    checkState();
    const interval = setInterval(checkState, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkState = async () => {
    const net = await Network.getNetworkStateAsync();
    const offline = !net.isConnected;
    setIsOffline(offline);

    const pending = await offlineStorage.getPendingSOS();
    setPendingQueue(pending);

    const cache = await offlineStorage.getCachedReport();
    if (cache) {
      setCachedReport(cache.report);
      setLastUpdated(cache.timestamp);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await checkState();
    setRefreshing(false);
  };

  const handleSOS = async () => {
    if (!location) return;

    const net = await Network.getNetworkStateAsync();
    const offline = !net.isConnected;
    
    const client_event_id = uuidv4();
    const captured_at_device = new Date().toISOString();
    
    const payload = {
      vessel_id: VESSEL_ID,
      lat: location.coords.latitude,
      lon: location.coords.longitude,
      description: 'Emergency (Mobile)',
      client_event_id,
      captured_at_device
    };

    if (offline) {
      // Offline mode
      await offlineStorage.enqueueSOS({
        ...payload,
        queued_at: captured_at_device
      });
      setSosStatus('SOS saved locally. Waiting for a network connection to transmit.');
      setIsOffline(true);
      checkState();
    } else {
      // Online mode
      try {
        const res = await api.triggerSOS(payload);
        setSosStatus('SOS Transmitted! Incident ID: ' + res.id);
        
        setTimeout(async () => {
          try {
            const rep = await fetch(`http://10.0.2.2:8000/api/v1/authority/incidents/${res.id}/report`).then(r => r.json());
            await offlineStorage.saveCachedReport(rep);
            checkState();
          } catch(e) {}
        }, 5000);
      } catch (err) {
        await offlineStorage.enqueueSOS({
          ...payload,
          queued_at: captured_at_device
        });
        setSosStatus('SOS saved locally. Waiting for a network connection to transmit.');
        setIsOffline(true);
        checkState();
      }
    }
  };

  const handleSync = async () => {
    setSosStatus('Syncing...');
    const pending = await offlineStorage.getPendingSOS();
    let successCount = 0;
    
    for (const item of pending) {
      if (satelliteSimStatus[item.client_event_id] && satelliteSimStatus[item.client_event_id] !== 'FAILED' && satelliteSimStatus[item.client_event_id] !== 'DELIVERED') {
        continue; // skip items currently being simulated
      }
      try {
        await api.triggerSOS({
          vessel_id: item.vessel_id,
          lat: item.lat,
          lon: item.lon,
          description: item.description,
          client_event_id: item.client_event_id,
          captured_at_device: item.captured_at_device
        });
        await offlineStorage.removePendingSOS(item.client_event_id);
        successCount++;
      } catch (err) {
        console.error('Failed to sync item', err);
      }
    }
    
    setSosStatus(`Synced ${successCount} SOS events.`);
    checkState();
  };

  const simulateSatellite = async (item: PendingSOS) => {
    setSatelliteSimStatus(prev => ({ ...prev, [item.client_event_id]: 'Aligning with simulated constellation...' }));
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    setSatelliteSimStatus(prev => ({ ...prev, [item.client_event_id]: 'Transmitting...' }));
    
    const startTime = Date.now();
    await new Promise(resolve => setTimeout(resolve, 3000));
    const latency = Date.now() - startTime;
    
    try {
      await api.triggerSOS({
        vessel_id: item.vessel_id,
        lat: item.lat,
        lon: item.lon,
        description: item.description,
        client_event_id: item.client_event_id,
        captured_at_device: item.captured_at_device,
        transmission_medium: 'SATELLITE_SIMULATION',
        transmission_latency_ms: latency
      } as any);
      
      setSatelliteSimStatus(prev => ({ ...prev, [item.client_event_id]: 'Satellite transmission delivered' }));
      await offlineStorage.removePendingSOS(item.client_event_id);
      setTimeout(checkState, 2000);
    } catch (e) {
      setSatelliteSimStatus(prev => ({ ...prev, [item.client_event_id]: 'FAILED' }));
    }
  };

  const isStale = lastUpdated ? (new Date().getTime() - new Date(lastUpdated).getTime()) > 6 * 60 * 60 * 1000 : false;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        {isOffline && (
          <View style={styles.offlineBanner}>
            <Text style={styles.bannerText}>OFFLINE MODE</Text>
          </View>
        )}
        
        {location && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>GPS Location</Text>
            <Text style={styles.mono}>{location.coords.latitude.toFixed(6)}, {location.coords.longitude.toFixed(6)}</Text>
          </View>
        )}

        {pendingQueue.length > 0 && (
          <View style={[styles.card, styles.warningCard]}>
            <Text style={styles.warningTitle}>{pendingQueue.length} PENDING SOS</Text>
            <Text style={styles.warningText}>Waiting for network connection...</Text>
            
            {pendingQueue.map(item => (
              <View key={item.client_event_id} style={styles.queueItem}>
                 <Text style={styles.mono}>ID: {item.client_event_id.split('-')[0]}</Text>
                 <Text style={styles.simBridgeText}>[ SIMULATED SATELLITE BRIDGE ]</Text>
                 {satelliteSimStatus[item.client_event_id] ? (
                   <Text style={styles.simStatus}>{satelliteSimStatus[item.client_event_id]}</Text>
                 ) : (
                   <TouchableOpacity style={styles.simButton} onPress={() => simulateSatellite(item)}>
                     <Text style={styles.buttonText}>Simulate Satellite Transmission</Text>
                   </TouchableOpacity>
                 )}
              </View>
            ))}

            {!isOffline && (
              <TouchableOpacity style={styles.syncButton} onPress={handleSync}>
                <Text style={styles.buttonText}>Tap to Sync Cellular</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        <TouchableOpacity style={styles.sosButton} onPress={handleSOS}>
          <Text style={styles.sosText}>SOS</Text>
        </TouchableOpacity>
        
        {sosStatus && <Text style={styles.statusText}>{sosStatus}</Text>}

        {cachedReport && (
          <View style={[styles.card, isStale && styles.staleCard]}>
            <Text style={styles.cardTitle}>Cached Intelligence</Text>
            {lastUpdated && (
              <Text style={styles.staleText}>
                Last Updated: {new Date(lastUpdated).toLocaleString()}
                {isStale && ' (STALE - >6h)'}
              </Text>
            )}
            
            <Text style={styles.info}>Incident ID: {cachedReport.incident_id}</Text>
            <Text style={styles.info}>Emergency: {cachedReport.incident_type}</Text>
            
            <View style={styles.evidenceContainer}>
              <Text style={styles.sectionTitle}>Data Sources & Provenance</Text>
              {cachedReport.evidence?.map((ev: any, i: number) => (
                <View key={i} style={styles.evidenceRow}>
                  <Text style={styles.mono}>{ev.source}</Text>
                  <Text style={styles.badge}>{ev.is_simulated ? 'SIM' : 'REAL'}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8' },
  offlineBanner: { backgroundColor: '#ef4444', padding: 8, alignItems: 'center' },
  bannerText: { color: 'white', fontWeight: 'bold' },
  card: { backgroundColor: 'white', margin: 16, padding: 16, borderRadius: 8, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4 },
  staleCard: { opacity: 0.6 },
  warningCard: { backgroundColor: '#fffbeb', borderColor: '#f59e0b', borderWidth: 1 },
  cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 8, color: '#1e293b' },
  warningTitle: { fontSize: 16, fontWeight: 'bold', color: '#b45309' },
  warningText: { color: '#b45309', marginBottom: 8 },
  queueItem: { marginVertical: 8, padding: 8, backgroundColor: '#fef3c7', borderRadius: 4 },
  simButton: { backgroundColor: '#0f172a', padding: 8, borderRadius: 4, alignItems: 'center', marginTop: 4 },
  simStatus: { color: '#0f172a', fontWeight: 'bold', marginTop: 4, fontStyle: 'italic' },
  simBridgeText: { color: '#0284c7', fontSize: 10, fontWeight: 'bold', marginVertical: 4 },
  mono: { fontFamily: 'monospace', color: '#475569' },
  info: { color: '#334155', marginBottom: 4 },
  staleText: { color: '#ef4444', fontSize: 12, marginBottom: 8, fontWeight: 'bold' },
  sosButton: { backgroundColor: '#dc2626', margin: 32, height: 120, borderRadius: 60, justifyContent: 'center', alignItems: 'center', elevation: 5 },
  sosText: { color: 'white', fontSize: 40, fontWeight: 'bold' },
  syncButton: { backgroundColor: '#2563eb', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 8 },
  buttonText: { color: 'white', fontWeight: 'bold' },
  statusText: { textAlign: 'center', marginHorizontal: 16, color: '#64748b', fontWeight: 'bold' },
  sectionTitle: { fontWeight: 'bold', marginTop: 12, marginBottom: 8 },
  evidenceContainer: { marginTop: 8, borderTopWidth: 1, borderTopColor: '#e2e8f0', paddingTop: 8 },
  evidenceRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  badge: { backgroundColor: '#f1f5f9', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, fontSize: 10, fontWeight: 'bold' }
});
