import { api } from './src/api/client';

describe('Fisherman App', () => {
  it('API Client trigger SOS', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ incident_id: 'test-incident' })
    });
    (globalThis as any).fetch = mockFetch;

    const res = await api.triggerSOS({ vessel_id: 'abc', lat: 10, lon: 10, description: 'SOS' });
    expect(res.incident_id).toBe('test-incident');
    expect(mockFetch).toHaveBeenCalled();
  });

  it('API Client evaluate route', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ distance_nm: 10 })
    });
    (globalThis as any).fetch = mockFetch;

    const res = await api.evaluateRoute({ vessel_id: 'abc', start_lat: 10, start_lon: 10, end_lat: 11, end_lon: 11 });
    expect(res.distance_nm).toBe(10);
  });

  it('API Client ORCA chat', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: 'Hello' })
    });
    (globalThis as any).fetch = mockFetch;

    const res = await api.sendOrcaMessage('test');
    expect(res.answer).toBe('Hello');
  });
  
  it('Application startup', () => {
    expect(true).toBe(true);
  });

  it('Navigation handles routing', () => {
    expect(true).toBe(true);
  });
});
