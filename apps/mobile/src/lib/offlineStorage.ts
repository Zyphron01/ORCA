import AsyncStorage from '@react-native-async-storage/async-storage';

export interface PendingSOS {
  client_event_id: string;
  captured_at_device: string;
  queued_at: string;
  lat: number;
  lon: number;
  vessel_id: string;
  description: string;
}

const KEYS = {
  CACHED_REPORT: '@orca_cached_report',
  CACHED_REPORT_TIME: '@orca_cached_report_time',
  PENDING_SOS: '@orca_pending_sos',
};

export const offlineStorage = {
  async saveCachedReport(report: any) {
    await AsyncStorage.setItem(KEYS.CACHED_REPORT, JSON.stringify(report));
    await AsyncStorage.setItem(KEYS.CACHED_REPORT_TIME, new Date().toISOString());
  },

  async getCachedReport(): Promise<{ report: any; timestamp: string | null } | null> {
    const reportStr = await AsyncStorage.getItem(KEYS.CACHED_REPORT);
    const timeStr = await AsyncStorage.getItem(KEYS.CACHED_REPORT_TIME);
    if (!reportStr) return null;
    return { report: JSON.parse(reportStr), timestamp: timeStr };
  },

  async enqueueSOS(sos: PendingSOS) {
    const existing = await this.getPendingSOS();
    existing.push(sos);
    await AsyncStorage.setItem(KEYS.PENDING_SOS, JSON.stringify(existing));
  },

  async getPendingSOS(): Promise<PendingSOS[]> {
    const str = await AsyncStorage.getItem(KEYS.PENDING_SOS);
    if (!str) return [];
    return JSON.parse(str);
  },

  async removePendingSOS(client_event_id: string) {
    const existing = await this.getPendingSOS();
    const filtered = existing.filter(x => x.client_event_id !== client_event_id);
    await AsyncStorage.setItem(KEYS.PENDING_SOS, JSON.stringify(filtered));
  }
};
