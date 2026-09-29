import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { api } from '../api/client';

export default function OrcaScreen() {
  const [messages, setMessages] = useState([{ role: 'orca', content: 'Safe journey! I am ORCA, your marine intelligence assistant. How can I help you?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState('en-IN'); // Default to English

  const sendMessage = async () => {
    if (!input.trim()) return;
    const text = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      // Append language instruction
      const res = await api.sendOrcaMessage(`${text} (Respond in language code: ${lang})`);
      const answer = res.answer || res.response || 'No response';
      setMessages(prev => [...prev, { role: 'orca', content: answer }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'orca', content: 'ORCA unavailable or network error.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.header}>
        <Text style={styles.title}>ORCA Assistant</Text>
        <Text style={styles.subtitle} onPress={() => setLang(lang === 'en-IN' ? 'hi-IN' : 'en-IN')}>
          Lang: {lang === 'en-IN' ? 'English' : 'Hindi'} (Tap to switch)
        </Text>
      </View>

      <ScrollView style={styles.chatArea} contentContainerStyle={{ padding: 16 }}>
        {messages.map((m, i) => (
          <View key={i} style={[styles.messageBubble, m.role === 'orca' ? styles.orcaMsg : styles.userMsg]}>
            <Text style={m.role === 'orca' ? styles.orcaText : styles.userText}>{m.content}</Text>
          </View>
        ))}
        {loading && <ActivityIndicator style={{ marginTop: 10 }} color="#0f766e" />}
      </ScrollView>

      <View style={styles.inputArea}>
        <TextInput 
          style={styles.input} 
          value={input} 
          onChangeText={setInput} 
          placeholder="Ask ORCA..." 
          placeholderTextColor="#94a3b8"
        />
        <TouchableOpacity style={styles.sendBtn} onPress={sendMessage} disabled={loading}>
          <Text style={styles.sendBtnText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { backgroundColor: '#0f766e', padding: 20, paddingTop: 60, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  subtitle: { color: '#99f6e4', fontSize: 12 },
  chatArea: { flex: 1 },
  messageBubble: { padding: 12, borderRadius: 16, marginBottom: 10, maxWidth: '85%' },
  orcaMsg: { backgroundColor: '#e2e8f0', alignSelf: 'flex-start', borderTopLeftRadius: 4 },
  userMsg: { backgroundColor: '#0f766e', alignSelf: 'flex-end', borderTopRightRadius: 4 },
  orcaText: { color: '#334155' },
  userText: { color: 'white' },
  inputArea: { flexDirection: 'row', padding: 12, backgroundColor: 'white', borderTopWidth: 1, borderColor: '#e2e8f0' },
  input: { flex: 1, backgroundColor: '#f1f5f9', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, marginRight: 8, color: '#334155' },
  sendBtn: { backgroundColor: '#0f766e', paddingHorizontal: 20, justifyContent: 'center', borderRadius: 20 },
  sendBtnText: { color: 'white', fontWeight: 'bold' }
});
