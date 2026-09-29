import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { api } from '../api/client';

export default function RouteScreen() {
  const [startLat, setStartLat] = useState('12.0');
  const [startLon, setStartLon] = useState('80.0');
  const [endLat, setEndLat] = useState('12.5');
  const [endLon, setEndLon] = useState('80.5');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const evaluateRoute = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await api.evaluateRoute({
        vessel_id: '11111111-0000-0000-0000-000000000001',
        start_lat: parseFloat(startLat),
        start_lon: parseFloat(startLon),
        end_lat: parseFloat(endLat),
        end_lon: parseFloat(endLon)
      });
      setResult(res);
    } catch (e) {
      Alert.alert('Error', 'Route evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Route Intelligence</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Origin (Lat, Lon)</Text>
          <View style={styles.row}>
            <TextInput style={styles.input} value={startLat} onChangeText={setStartLat} keyboardType="numeric" />
            <TextInput style={styles.input} value={startLon} onChangeText={setStartLon} keyboardType="numeric" />
          </View>
        </View>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Destination (Lat, Lon)</Text>
          <View style={styles.row}>
            <TextInput style={styles.input} value={endLat} onChangeText={setEndLat} keyboardType="numeric" />
            <TextInput style={styles.input} value={endLon} onChangeText={setEndLon} keyboardType="numeric" />
          </View>
        </View>

        <TouchableOpacity style={styles.evalBtn} onPress={evaluateRoute} disabled={loading}>
          {loading ? <ActivityIndicator color="white" /> : <Text style={styles.evalBtnText}>Evaluate Route</Text>}
        </TouchableOpacity>

        {result && (
          <View style={styles.resultCard}>
            <Text style={styles.resultTitle}>Safety Evaluation</Text>
            <Text style={styles.resultText}>Status: {result.status}</Text>
            <Text style={styles.resultText}>Distance: {result.distance_nm} NM</Text>
            
            <Text style={styles.sectionTitle}>Hazards:</Text>
            {result.hazards && result.hazards.length > 0 ? (
              result.hazards.map((h: any, i: number) => <Text key={i} style={styles.hazard}>- {h.description || h}</Text>)
            ) : (
              <Text style={styles.safe}>No hazards detected.</Text>
            )}

            <Text style={styles.sectionTitle}>Weather/Conditions:</Text>
            <Text>Wind: {result.weather?.wind_speed_ms} m/s</Text>
            <Text>Waves: {result.weather?.wave_height_m} m</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { backgroundColor: '#0f766e', padding: 20, paddingTop: 60 },
  title: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  content: { padding: 20 },
  inputGroup: { marginBottom: 16 },
  label: { fontSize: 14, color: '#64748b', marginBottom: 8, fontWeight: 'bold' },
  row: { flexDirection: 'row', gap: 10 },
  input: { flex: 1, backgroundColor: 'white', padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#cbd5e1' },
  evalBtn: { backgroundColor: '#0f766e', padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 10 },
  evalBtnText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
  resultCard: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginTop: 20, elevation: 2 },
  resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#0f766e', marginBottom: 10 },
  resultText: { fontSize: 16, marginBottom: 4 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', marginTop: 16, marginBottom: 8 },
  hazard: { color: '#dc2626', marginBottom: 4 },
  safe: { color: '#16a34a' }
});
