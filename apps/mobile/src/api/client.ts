import { Platform } from 'react-native';

const BASE_URL = 'http://10.0.2.2:8000/api/v1'; // 10.0.2.2 is Android emulator's localhost

export interface SOSRequest {
  vessel_id: string;
  lat: number;
  lon: number;
  description: string;
  client_event_id?: string;
  captured_at_device?: string;
}

export interface RouteRequest {
  vessel_id: string;
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
}

class ApiClient {
  private getBaseUrl() {
    if (process.env.EXPO_PUBLIC_API_URL) {
        return process.env.EXPO_PUBLIC_API_URL;
    }
    if (__DEV__) {
      if (Platform.OS === 'android') {
          return BASE_URL;
      }
      return 'http://localhost:8000/api/v1'; // For iOS/web
    }
    return 'https://orca-1jo3.onrender.com/api/v1';
  }

  async triggerSOS(req: SOSRequest) {
    const res = await fetch(`${this.getBaseUrl()}/sos/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    if (!res.ok) throw new Error('SOS Failed');
    return res.json();
  }

  async cancelSOS(incidentId: string) {
    const res = await fetch(`${this.getBaseUrl()}/sos/cancel?incident_id=${incidentId}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Cancel Failed');
    return res.json();
  }

  async sendOrcaMessage(message: string, context?: any) {
    const res = await fetch(`${this.getBaseUrl()}/orca/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, context })
    });
    if (!res.ok) throw new Error('ORCA Failed');
    return res.json();
  }

  async getMarineStatus(lat: number, lon: number) {
    const res = await fetch(`${this.getBaseUrl()}/marine/status?lat=${lat}&lon=${lon}`);
    if (!res.ok) throw new Error('Marine API Failed');
    return res.json();
  }

  async evaluateRoute(req: RouteRequest) {
    const res = await fetch(`${this.getBaseUrl()}/route/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    if (!res.ok) throw new Error('Route API Failed');
    return res.json();
  }
}

export const api = new ApiClient();
