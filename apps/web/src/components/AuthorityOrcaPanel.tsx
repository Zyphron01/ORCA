import { useState, useRef, useEffect } from 'react';
import { Activity, Anchor, AlertTriangle, Send, FileText, CheckCircle, Clock } from 'lucide-react';

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

export default function AuthorityOrcaPanel({ 
  selectedIncident, 
  sarData, 
  events, 
  generateReport, 
  acknowledgeIncident, 
  resolveIncident, 
  cancelIncident 
}: any) {
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [orcaResponse, setOrcaResponse] = useState<any>(null);
  const [lastQuery, setLastQuery] = useState('');
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [orcaResponse, lastQuery, isChatLoading]);

  const sendChatMessage = async (textOverride?: string) => {
    const textToSend = textOverride !== undefined ? textOverride : chatInput;
    if (!textToSend.trim() || !selectedIncident) return;
    
    setLastQuery(textToSend);
    setChatInput('');
    setIsChatLoading(true);
    setOrcaResponse(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/orca/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: textToSend,
          incident_id: selectedIncident.id
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setOrcaResponse(data);
      } else {
        let errorMsg = 'ORCA unavailable';
        try {
          const errorData = await res.json();
          if (errorData.detail) {
            errorMsg = errorData.detail;
          }
        } catch (err) {
          if (res.status === 503) {
            errorMsg = 'ORCA is temporarily unavailable because the AI service is busy. Please try again.';
          }
        }
        setOrcaResponse({ message: errorMsg });
      }
    } catch (e) {
      console.error(e);
      setOrcaResponse({ message: 'Network Error' });
    } finally {
      setIsChatLoading(false);
    }
  };

  if (!selectedIncident) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
        <Anchor size={48} className="mb-4 opacity-20" />
        <p className="text-sm">Select an incident to view intelligence and SAR operations.</p>
      </div>
    );
  }

  const handleQuickAction = (action: string) => {
    sendChatMessage(`What is the ${action.toLowerCase()}?`);
  };

  const answerText = orcaResponse?.message || orcaResponse?.answer || orcaResponse?.response;
  
  return (
    <div className="flex flex-col h-full bg-slate-800/50">
      {/* 1. ORCA Intelligence header/status */}
      <div className="p-4 border-b border-slate-700 bg-slate-800 flex flex-col gap-2">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-teal-400 flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            ORCA INTELLIGENCE
          </h2>
          <span className="text-xs px-2 py-1 rounded font-bold bg-teal-500/20 text-teal-400 border border-teal-500/30 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
            READY
          </span>
        </div>
        <p className="text-xs text-slate-400 font-mono tracking-wider">MARINE INTELLIGENCE ASSISTANT</p>
        
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-1 mt-2">
          {['Weather', 'Ocean', 'Wind & Currents', 'Hazards', 'SAR Status', 'Nearby Vessels', 'Incident Summary'].map(action => (
            <button 
              key={action}
              onClick={() => handleQuickAction(action)}
              className="text-[10px] bg-slate-700 hover:bg-teal-700/50 text-slate-300 px-2 py-1 rounded transition-colors border border-slate-600 hover:border-teal-500"
            >
              {action}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* 2 & 3. User Query & ORCA Response */}
        {lastQuery && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <div className="bg-slate-700 text-white p-3 rounded-tl-xl rounded-bl-xl rounded-br-xl text-sm max-w-[85%] shadow">
                {lastQuery}
              </div>
            </div>
            
            <div className="flex justify-start">
              <div className="bg-slate-900 border border-teal-900/50 text-slate-300 p-4 rounded-tr-xl rounded-bl-xl rounded-br-xl text-sm w-full font-mono whitespace-pre-wrap leading-relaxed shadow">
                {isChatLoading ? (
                  <span className="animate-pulse text-teal-500">ORCA is analyzing...</span>
                ) : (
                  answerText
                )}
              </div>
            </div>
          </div>
        )}

        {!lastQuery && !isChatLoading && (
          <div className="text-center p-6 text-slate-500 text-sm border border-dashed border-slate-700 rounded-xl">
            Ask ORCA a question or select a quick action above to begin analysis of this incident.
          </div>
        )}

        {/* 4. Structured operational information */}
        <div className="space-y-4 border-t border-slate-700 pt-4">
          <h3 className="text-xs font-bold text-slate-400 tracking-wider flex items-center gap-2">
            <AlertTriangle size={14} className="text-slate-500" /> OPERATIONAL CONTEXT
          </h3>
          
          <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-700 space-y-2">
            <div className="flex justify-between border-b border-slate-700/50 pb-1">
              <span className="text-slate-500 text-xs">VESSEL ID</span>
              <span className="text-slate-200 text-xs font-mono">{selectedIncident.vessel_id}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700/50 pb-1">
              <span className="text-slate-500 text-xs">INCIDENT TYPE</span>
              <span className="text-red-400 text-xs font-bold">{selectedIncident.incident_type}</span>
            </div>
            <div className="flex justify-between border-b border-slate-700/50 pb-1">
              <span className="text-slate-500 text-xs">LKP</span>
              <span className="text-slate-200 text-xs font-mono">{selectedIncident.lkp_lat.toFixed(4)}, {selectedIncident.lkp_lon.toFixed(4)}</span>
            </div>
            <div className="flex justify-between pb-1">
              <span className="text-slate-500 text-xs">STATUS</span>
              <span className={`text-[10px] px-1 rounded font-bold ${selectedIncident.status === 'ACTIVE' ? 'bg-red-500 text-white' : 'bg-amber-500 text-white'}`}>
                {selectedIncident.status}
              </span>
            </div>
          </div>
          
          {sarData?.predictions?.length > 0 && (
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-700">
              <h4 className="text-[10px] text-blue-400 font-bold mb-2 flex items-center gap-1"><Activity size={12}/> SAR PROJECTIONS</h4>
              {sarData.predictions.map((pred: any, i: number) => (
                <div key={i} className="mb-1">
                  <span className="text-[10px] text-slate-500">T+{pred.horizon_h || pred.horizon_hours}</span>
                  <span className="text-xs text-slate-300 font-mono ml-2">
                    {(pred.predicted_lat || pred.position?.lat)?.toFixed(4)}° N, {(pred.predicted_lon || pred.position?.lon)?.toFixed(4)}° E
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 5. Source / provenance */}
        {(orcaResponse?.evidence?.length > 0 || answerText) && !isChatLoading && (
          <div className="text-[10px] text-slate-500 italic text-right mt-4">
            Prototype Data · Verify with official navigation systems
          </div>
        )}

        {/* 7. Agent Execution / evidence */}
        <details className="group bg-slate-900/50 border border-slate-700 rounded-lg mt-4">
          <summary className="p-3 text-xs font-bold text-slate-400 cursor-pointer flex items-center justify-between hover:text-slate-300 transition-colors">
            AGENT EXECUTION & EVIDENCE
            <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
              {((orcaResponse?.evidence?.length || 0) + (sarData?.agent_trace?.length || 0))} ITEMS
            </span>
          </summary>
          <div className="p-3 pt-0 border-t border-slate-700 space-y-2 max-h-48 overflow-y-auto mt-2">
            {orcaResponse?.evidence?.map((ev: any, i: number) => (
              <div key={`ev-${i}`} className="bg-slate-800 p-2 rounded text-[10px] border-l-2 border-teal-500 shadow-sm">
                <span className="text-teal-400 font-bold mr-2">[{ev.tool}]</span>
                <span className="text-slate-300">{ev.summary}</span>
              </div>
            ))}
            
            {sarData?.agent_trace?.map((t: any, i: number) => (
              <div key={`trace-${i}`} className="bg-slate-800 p-2 rounded text-[10px] border-l-2 border-blue-500 shadow-sm">
                <span className="text-blue-400 font-bold mr-2">[{t.agent}]</span>
                <span className="text-slate-300">Executed</span>
              </div>
            ))}
            {(!orcaResponse?.evidence?.length && !sarData?.agent_trace?.length) && (
              <div className="text-[10px] text-slate-500">No agent execution data available.</div>
            )}
          </div>
        </details>
        
        <div ref={chatEndRef} />
      </div>

      {/* 8. Ask ORCA input */}
      <div className="p-4 border-t border-slate-700 bg-slate-800 shrink-0 shadow-lg">
        <div className="flex gap-2 relative">
          <input 
            type="text" 
            placeholder="Ask ORCA..." 
            className="flex-1 bg-slate-900 border border-slate-600 rounded-lg pl-3 pr-10 py-2 text-sm text-white outline-none focus:border-teal-500 transition-colors placeholder:text-slate-500" 
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendChatMessage()}
          />
          <button 
            onClick={() => sendChatMessage()} 
            disabled={isChatLoading || !chatInput.trim()}
            className="absolute right-1 top-1 bottom-1 bg-teal-600/20 text-teal-400 p-1.5 rounded-md flex items-center justify-center hover:bg-teal-600 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>

      {/* INCIDENT CONTROLS */}
      <div className="p-4 border-t border-slate-700 bg-slate-900 grid grid-cols-2 gap-2 shrink-0">
        <button onClick={generateReport} className="col-span-2 py-2 mb-1 border border-blue-500/50 text-blue-400 hover:bg-blue-900/30 text-[10px] font-bold rounded shadow transition-colors flex items-center justify-center gap-2 tracking-wider">
          <FileText size={14} /> GENERATE REPORT
        </button>
        <button onClick={acknowledgeIncident} className="col-span-2 py-2 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded shadow transition-colors tracking-wider">ACKNOWLEDGE</button>
        <button onClick={resolveIncident} className="py-2 bg-green-900/50 hover:bg-green-900/80 text-green-400 border border-green-500/30 text-[10px] font-bold rounded transition-colors tracking-wider">RESOLVE</button>
        <button onClick={cancelIncident} className="py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-[10px] font-bold rounded transition-colors tracking-wider">CANCEL</button>
      </div>
    </div>
  );
}
