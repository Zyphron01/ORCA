import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Activity, Radio, Search, Anchor, Shield, Power, CheckCircle, Clock, FileText } from 'lucide-react';
import MarineMap from './MarineMap';
import IntelligenceReportModal from './IntelligenceReportModal';
import AuthorityOrcaPanel from './AuthorityOrcaPanel';

interface Incident {
  id: string;
  vessel_id: string;
  incident_type: string;
  status: string;
  lkp_lat: number;
  lkp_lon: number;
  lkp_time?: string;
  description?: string;
  transmission_medium?: string;
  transmission_latency_ms?: number;
}

interface SARData {
  predictions: any[];
  search_areas: any;
  agent_trace?: any[];
}

export default function AuthorityApp({ onLogout }: { onLogout: () => void }) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [sarData, setSarData] = useState<SARData | null>(null);
  const [wsStatus, setWsStatus] = useState<'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'>('CONNECTING');
  const [events, setEvents] = useState<{time: string, type: string}[]>([]);
  const [reportData, setReportData] = useState<any>(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/authority/incidents`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);
      }
    } catch (err) {
      console.error("Could not load incidents", err);
    }
  };

  const fetchSarData = async (incidentId: string) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/authority/incidents/${incidentId}/sar`);
      if (res.ok) {
        const data = await res.json();
        setSarData(data);
      }
    } catch (err) {
      console.error("Could not load SAR data", err);
    }
  };

  const generateReport = async () => {
    if (!selectedIncident) return;
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/authority/incidents/${selectedIncident.id}/report`);
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
        setIsReportOpen(true);
      } else {
        document.body.setAttribute('data-error', 'res_not_ok');
      }
    } catch (err) {
      document.body.setAttribute('data-error', String(err));
      console.error("Failed to generate report", err);
    }
  };

  useEffect(() => {
    fetchIncidents();
    
    let reconnectTimer: any;
    
    const connectWs = () => {
      setWsStatus('CONNECTING');
      const ws = new WebSocket(`${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/authority`);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('CONNECTED');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setEvents(prev => [...prev, { time: new Date().toLocaleTimeString(), type: data.event }]);
          fetchIncidents();

          if (data.event === 'DRIFT_UPDATED') {
            setSarData(prev => {
              // Refresh full SAR data if the selected incident was updated
              return {
                ...prev,
                predictions: data.predictions || prev?.predictions || [],
                agent_trace: data.agent_trace || prev?.agent_trace || []
              } as SARData;
            });
          }
        } catch (e) {
          console.error(e);
        }
      };

      ws.onclose = () => {
        setWsStatus('DISCONNECTED');
        reconnectTimer = setTimeout(connectWs, 3000);
      };
      
      ws.onerror = () => {
        ws.close();
      };
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    if (selectedIncident) {
      fetchSarData(selectedIncident.id);
    } else {
      setSarData(null);
    }
  }, [selectedIncident?.id]);

  const acknowledgeIncident = async () => {
    if (!selectedIncident) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/sos/${selectedIncident.id}/acknowledge`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const resolveIncident = async () => {
    if (!selectedIncident) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/sos/${selectedIncident.id}/transition?next_state=RESOLVED`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const cancelIncident = async () => {
    if (!selectedIncident) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/sos/cancel?incident_id=${selectedIncident.id}`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm('Are you sure you want to reset all demo incidents?')) return;
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/demo/reset`, { method: 'POST' });
      setSelectedIncident(null);
      setEvents([]);
      fetchIncidents();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="h-screen w-full bg-slate-900 text-slate-300 flex flex-col font-sans overflow-hidden">
      {/* TOPBAR */}
      <header className="h-14 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3 text-blue-400">
          <Shield size={24} />
          <h1 className="font-bold text-lg tracking-widest text-slate-100">COASTAL AUTHORITY <span className="text-blue-500 font-normal">COMMAND CENTER</span></h1>
          <span className="ml-4 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 uppercase">DEMO MODE</span>
          <span className={`ml-2 px-2 py-0.5 rounded text-[10px] font-bold border ${wsStatus === 'CONNECTED' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>
            WS: {wsStatus}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={handleResetDemo} className="text-xs font-bold text-red-400 hover:text-red-300 px-3 py-1 border border-red-500/30 hover:bg-red-500/10 rounded">RESET DEMO</button>
          <div className="flex items-center gap-2">
            <Radio size={16} className="text-slate-500"/>
            <span className="text-xs text-slate-400">VHF CH 16 MOCK</span>
          </div>
          <button onClick={onLogout} className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-white"><Power size={18}/></button>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="flex flex-1 h-[calc(100vh-3.5rem)]">
        
        {/* LEFT PANEL: INCIDENTS */}
        <div className="w-80 bg-slate-800/50 border-r border-slate-700 flex flex-col shrink-0">
          <div className="p-4 border-b border-slate-700 bg-slate-800">
            <h2 className="text-xs font-bold text-slate-400 tracking-wider mb-3">ACTIVE INCIDENTS ({incidents.length})</h2>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-2.5 text-slate-500" />
              <input type="text" placeholder="Search vessels..." className="w-full bg-slate-900 border border-slate-700 rounded-md pl-9 pr-3 py-2 text-sm text-slate-300 outline-none focus:border-blue-500" />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {incidents.map(inc => (
              <button 
                key={inc.id}
                onClick={() => setSelectedIncident(inc)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  selectedIncident?.id === inc.id 
                  ? 'bg-blue-900/40 border-blue-500/50' 
                  : 'bg-slate-800/80 border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm font-bold text-slate-100">{inc.vessel_id.substring(0,8)}...</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${inc.status === 'ACTIVE' ? 'bg-red-500/20 text-red-400 border-red-500/30' : inc.status === 'SAR_ACTIVE' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-slate-500/20 text-slate-400 border-slate-500/30'}`}>
                    {inc.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-1">
                  <AlertTriangle size={12} className={inc.incident_type === 'SOS' ? 'text-amber-500' : 'text-red-500'}/>
                  {inc.incident_type}
                </div>
              </button>
            ))}
            {incidents.length === 0 && (
              <div className="text-center p-8 text-slate-500 text-sm">
                <Shield size={32} className="mx-auto mb-2 opacity-50"/>
                No active incidents
              </div>
            )}
          </div>
        </div>

        {/* CENTER: MAP */}
        <div className="flex-1 bg-black relative">
          <MarineMap incidents={incidents} selected={selectedIncident} sarData={sarData} />
        </div>

        {/* RIGHT PANEL: INCIDENT INTELLIGENCE */}
        <div className="w-96 bg-slate-800/50 border-l border-slate-700 flex flex-col shrink-0">
          <AuthorityOrcaPanel
            selectedIncident={selectedIncident}
            sarData={sarData}
            events={events}
            generateReport={generateReport}
            acknowledgeIncident={acknowledgeIncident}
            resolveIncident={resolveIncident}
            cancelIncident={cancelIncident}
          />
        </div>

      </div>
      {isReportOpen && (
        <div className="print:visible">
          <IntelligenceReportModal 
            reportData={reportData} 
            onClose={() => setIsReportOpen(false)} 
          />
        </div>
      )}
    </div>
  );
}
