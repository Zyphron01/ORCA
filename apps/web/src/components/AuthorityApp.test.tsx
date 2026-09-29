import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AuthorityApp from './AuthorityApp';

// Mock map component since we don't need to test WebGL here
vi.mock('./MarineMap', () => {
  return {
    default: () => <div data-testid="marine-map">Map</div>
  };
});

describe('AuthorityApp (Phase 13)', () => {
  let mockWebSocket: any;

  beforeEach(() => {
    vi.resetAllMocks();
    globalThis.fetch = vi.fn();

    class MockWebSocket {
      onopen: any; onmessage: any; onclose: any; onerror: any;
      constructor() {
        mockWebSocket = this;
      }
      close = vi.fn();
    }
    globalThis.WebSocket = MockWebSocket as any;
  });

  it('loads active incidents on mount', async () => {
    const mockIncidents = [
      { id: 'inc-1', vessel_id: 'vessel-abc', incident_type: 'SOS', status: 'ACTIVE', lkp_lat: 12.0, lkp_lon: 80.0 }
    ];

    (globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockIncidents,
    });

    render(<AuthorityApp onLogout={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/ACTIVE INCIDENTS/)).toBeDefined();
      expect(screen.getByText('vessel-a...')).toBeDefined();
    });
    expect(globalThis.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/authority/incidents');
  });

  it('loads SAR intelligence when an incident is selected', async () => {
    const mockIncidents = [
      { id: 'inc-1', vessel_id: 'vessel-abc', incident_type: 'SOS', status: 'ACTIVE', lkp_lat: 12.0, lkp_lon: 80.0 }
    ];
    
    const mockSar = {
      incident_id: 'inc-1',
      predictions: [{ horizon_h: 1, predicted_lat: 12.1, predicted_lon: 80.1 }],
      agent_trace: [{ agent: 'SARPlanningAgent' }]
    };

    (globalThis.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/sar')) {
        return Promise.resolve({ ok: true, json: async () => mockSar });
      }
      return Promise.resolve({ ok: true, json: async () => mockIncidents });
    });

    render(<AuthorityApp onLogout={() => {}} />);
    
    // Select the incident
    const btn = await screen.findByText('vessel-a...');
    fireEvent.click(btn);

    // Verify SAR call
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/authority/incidents/inc-1/sar');
    });

    // Should display SAR Physics Projections
    await waitFor(() => {
      expect(screen.getByText(/T\+1 Drift Forecast/i)).toBeDefined();
    });
  });

  it('handles WebSocket real-time events', async () => {
    (globalThis.fetch as any).mockResolvedValue({ ok: true, json: async () => [] });
    render(<AuthorityApp onLogout={() => {}} />);
    
    // Trigger open
    mockWebSocket.onopen();

    // Send a message
    mockWebSocket.onmessage({
      data: JSON.stringify({
        event: 'SOS_TRIGGERED',
        incident_id: 'new-inc',
        state: 'ACTIVE'
      })
    });

    // Check if fetch was called again to refresh incidents
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledTimes(2); // Mount + WS Event
    });
  });
  
  it('handles operational actions', async () => {
    const mockIncidents = [
      { id: 'inc-1', vessel_id: 'vessel-abc', incident_type: 'SOS', status: 'ACTIVE', lkp_lat: 12.0, lkp_lon: 80.0 }
    ];
    (globalThis.fetch as any).mockResolvedValue({ ok: true, json: async () => mockIncidents });

    render(<AuthorityApp onLogout={() => {}} />);
    
    const btn = await screen.findByText('vessel-a...');
    fireEvent.click(btn);

    const resolveBtn = await screen.findByText('RESOLVE');
    fireEvent.click(resolveBtn);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/sos/inc-1/transition?next_state=RESOLVED',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('generates and displays an intelligence report', async () => {
    const mockIncidents = [
      { id: 'inc-1', vessel_id: 'vessel-abc', incident_type: 'SOS', status: 'ACTIVE', lkp_lat: 12.0, lkp_lon: 80.0 }
    ];
    
    const mockReport = {
      report_id: 'REP-123',
      generated_at: '2026-09-26T12:00:00Z',
      incident_id: 'inc-1',
      vessel_id: 'vessel-abc',
      vessel_name: 'Sea Explorer',
      vessel_type: 'FISHING',
      incident_type: 'SOS',
      status: 'ACTIVE',
      lkp: { lat: 12.0, lon: 80.0 },
      lkp_time: '2026-09-26T10:00:00Z',
      sar_predictions: [
        { horizon_h: 1, position: { lat: 12.1, lon: 80.1 }, force_breakdown: { current_pct: 60, wind_pct: 40 }, uncertainty_radius_nm: 5.0 }
      ],
      search_radius_nm: 5.0,
      agent_traces: [
        { agent_name: 'SARPlanningAgent', status: 'DONE' }
      ],
      environment: {
        weather_summary: 'Clear',
        marine_conditions: 'Calm',
        hazards: 'None'
      },
      actions_taken: ['Generated SAR'],
      evidence: [
        {
          source: 'MOCK-IMD-TEST',
          summary: 'Test wind',
          agent: 'EnvironmentAgent',
          confidence: 0.99,
          is_simulated: true
        }
      ]
    };

    (globalThis.fetch as any).mockImplementation((url: string) => {
      console.log('FETCH CALLED', url);
      if (url.includes('/report')) {
        return Promise.resolve({ ok: true, json: async () => {
          document.body.setAttribute('data-mock-json-called', 'yes');
          return mockReport;
        } });
      }
      if (url.includes('/sar')) {
        return Promise.resolve({ ok: true, json: async () => ({ predictions: [], search_areas: null, agent_trace: [] }) });
      }
      return Promise.resolve({ ok: true, json: async () => mockIncidents });
    });

    render(<AuthorityApp onLogout={() => {}} />);
    
    // Select the incident
    const btn = await screen.findByText('vessel-a...');
    fireEvent.click(btn);

    // Click Generate Report
    const generateBtn = await screen.findByText(/GENERATE INTELLIGENCE REPORT/i);
    fireEvent.click(generateBtn);

    // Verify fetch call
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/authority/incidents/inc-1/report');
    });

    // Check report modal contents
    await waitFor(() => {
      expect(screen.getByText(/ORCA INTELLIGENCE REPORT/i)).toBeDefined();
      expect(screen.getByText(/Sea Explorer/i)).toBeDefined();
      expect(screen.getAllByText(/SARPlanningAgent/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/T\+1/).length).toBeGreaterThan(0);
      expect(screen.getByText(/MOCK-IMD-TEST/i)).toBeDefined();
    });
  });

});
