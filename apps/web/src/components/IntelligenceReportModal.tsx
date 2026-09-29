import { FileText, X, AlertTriangle, MapPin, Activity } from 'lucide-react';

interface ReportProps {
  reportData: any;
  onClose: () => void;
}

export default function IntelligenceReportModal({ reportData, onClose }: ReportProps) {
  console.log("RENDER REPORT MODAL", !!reportData);
  if (!reportData) return null;
  console.log("agent_traces:", reportData.agent_traces);

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-8">
      <div className="bg-slate-50 text-slate-900 w-full max-w-4xl max-h-full rounded-lg shadow-2xl flex flex-col overflow-hidden font-sans">
        
        {/* Header - Printable area begins below conceptually */}
        <div className="flex justify-between items-center p-4 bg-slate-800 text-white shrink-0 print:hidden">
          <h2 className="font-bold flex items-center gap-2">
            <FileText size={20} />
            ORCA INTELLIGENCE REPORT
          </h2>
          <div className="flex gap-4">
            <button 
              onClick={() => window.print()}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-bold shadow"
            >
              PRINT REPORT
            </button>
            <button onClick={onClose} className="p-1.5 hover:bg-slate-700 rounded text-slate-300">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Printable Content */}
        <div className="p-10 overflow-y-auto flex-1 bg-white print:p-0">
          <div className="border-b-2 border-slate-800 pb-6 mb-8 flex justify-between items-end">
            <div>
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">INTELLIGENCE REPORT</h1>
              <p className="text-slate-500 font-mono mt-1">REPORT ID: {reportData.report_id}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-slate-800">ORCA / COASTAL COMMAND</p>
              <p className="text-xs text-slate-500 font-mono mt-1">
                Generated: {new Date(reportData.generated_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 mb-8">
            {/* Incident Context */}
            <div>
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2 flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-500"/> Incident Context
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold w-1/3">Incident ID</td>
                    <td className="py-2 font-mono text-xs">{reportData.incident_id}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Vessel</td>
                    <td className="py-2 font-bold">{reportData.vessel_name} <span className="font-mono text-xs text-slate-500 ml-2">({reportData.vessel_id})</span></td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Vessel Type</td>
                    <td className="py-2">{reportData.vessel_type}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Emergency</td>
                    <td className="py-2 font-bold text-red-600">{reportData.incident_type}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Current Status</td>
                    <td className="py-2 font-bold">{reportData.status}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Location & Environment */}
            <div>
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2 flex items-center gap-2">
                <MapPin size={16} className="text-blue-500"/> Location & Environment
              </h3>
              <table className="w-full text-sm">
                <tbody>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold w-1/3">Last Known Pos</td>
                    <td className="py-2 font-mono font-bold">
                      {reportData.lkp.lat.toFixed(4)}° N, {reportData.lkp.lon.toFixed(4)}° E
                    </td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">LKP Time</td>
                    <td className="py-2 font-mono text-xs">{new Date(reportData.lkp_time).toLocaleString()}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Weather</td>
                    <td className="py-2">{reportData.environment.weather_summary || 'Data unavailable'}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Marine Cond.</td>
                    <td className="py-2">{reportData.environment.marine_conditions || 'Data unavailable'}</td>
                  </tr>
                  <tr className="border-b border-slate-100">
                    <td className="py-2 text-slate-500 font-semibold">Hazards</td>
                    <td className="py-2">{reportData.environment.hazards || 'None detected'}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* SAR Physics */}
          <div className="mb-8">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2 flex items-center gap-2">
              <Activity size={16} className="text-indigo-500"/> SAR Physics Projections
            </h3>
            {reportData.sar_predictions && reportData.sar_predictions.length > 0 ? (
              <div className="bg-slate-50 rounded border border-slate-200 overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-100 text-slate-600 text-xs">
                    <tr>
                      <th className="px-4 py-2">Horizon</th>
                      <th className="px-4 py-2">Predicted Position (Lat, Lon)</th>
                      <th className="px-4 py-2">Uncertainty Radius</th>
                      <th className="px-4 py-2">Force Breakdown</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.sar_predictions.map((p: any, i: number) => (
                      <tr key={i} className="border-t border-slate-200">
                        <td className="px-4 py-3 font-bold">T+{p.horizon_h}</td>
                        <td className="px-4 py-3 font-mono">{p.position.lat.toFixed(4)}°, {p.position.lon.toFixed(4)}°</td>
                        <td className="px-4 py-3">{p.uncertainty_radius_nm} NM</td>
                        <td className="px-4 py-3 text-xs text-slate-500">
                          Cur: {p.force_breakdown?.current_pct}%, Win: {p.force_breakdown?.wind_pct}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">No SAR projections generated.</p>
            )}
          </div>

          {/* Agents & Tactical Summary */}
          <div className="grid grid-cols-2 gap-8">
            <div>
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2">
                Multi-Agent Analysis
              </h3>
              {reportData.agent_traces && reportData.agent_traces.length > 0 ? (
                <ul className="space-y-2">
                  {reportData.agent_traces.map((trace: any, i: number) => (
                    <li key={i} className="flex justify-between items-center text-sm border border-slate-100 p-2 rounded">
                      <span className="font-semibold text-slate-700">{trace.agent_name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded font-bold ${trace.status === 'DONE' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                        {trace.status}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 italic">No multi-agent trace available.</p>
              )}
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2">
                Tactical Summary
              </h3>
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                {reportData.actions_taken?.map((action: string, i: number) => (
                  <li key={i}>{action}</li>
                )) || <li className="italic text-slate-500">No actions recorded.</li>}
              </ul>
            </div>
          </div>

          {/* Evidence & Provenance */}
          <div className="mt-8">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2 flex items-center gap-2">
              <FileText size={16} className="text-emerald-600"/> Data Sources & Provenance
            </h3>
            {reportData.evidence && reportData.evidence.length > 0 ? (
              <div className="bg-slate-50 rounded border border-slate-200 overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-100 text-slate-600 text-xs">
                    <tr>
                      <th className="px-4 py-2">Source</th>
                      <th className="px-4 py-2">Summary</th>
                      <th className="px-4 py-2">Agent</th>
                      <th className="px-4 py-2">Confidence</th>
                      <th className="px-4 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.evidence.map((item: any, i: number) => (
                      <tr key={i} className="border-t border-slate-200">
                        <td className="px-4 py-3 font-bold text-slate-800">{item.source}</td>
                        <td className="px-4 py-3 text-slate-600">{item.summary}</td>
                        <td className="px-4 py-3 font-mono text-xs">{item.agent}</td>
                        <td className="px-4 py-3 text-emerald-600 font-bold">
                          {item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : 'N/A'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${item.is_simulated ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                            {item.is_simulated ? 'Simulated' : 'Real'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">No data provenance records available.</p>
            )}
          </div>

          <div className="mt-12 text-center text-xs text-slate-400 font-mono border-t border-slate-200 pt-4">
            CONFIDENTIAL // RESTRICTED ACCESS // ORCA AUTOMATED INTELLIGENCE
          </div>
        </div>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          body * {
            visibility: hidden;
          }
          .fixed { position: absolute; }
          .bg-black\\/80 { background: white !important; }
          .fixed > div {
            box-shadow: none !important;
            max-width: 100% !important;
          }
          .print\\:hidden { display: none !important; }
          .print\\:p-0 { padding: 0 !important; }
          .print\\:visible, .print\\:visible * {
            visibility: visible;
          }
          .print\\:visible {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
        }
      `}} />
    </div>
  );
}
