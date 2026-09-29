import { useState, useEffect } from 'react';
import { X, ExternalLink, Image as ImageIcon, Map, Thermometer, Wind, Target } from 'lucide-react';
import EvidenceMap from './EvidenceMap';

interface EvidenceItem {
  type: string;
  asset_id?: string;
  value?: number;
  unit?: string;
  summary: string;
  source: string;
  is_simulated: boolean;
  confidence?: number;
  data?: any;
  agent?: string;
  tool?: string;
  evidence_context?: { domain: string; purpose: string; [key: string]: any };
}

interface EvidenceRegistryAsset {
  id: string;
  type: string;
  title: string;
  path: string;
  source: string;
  date: string;
  is_simulated: boolean;
}

interface EvidencePanelProps {
  evidence: EvidenceItem[];
  onClose: () => void;
}

export default function EvidencePanel({ evidence, onClose }: EvidencePanelProps) {
  const [registry, setRegistry] = useState<{ assets: EvidenceRegistryAsset[] }>({ assets: [] });

  useEffect(() => {
    fetch('/evidence/registry.json')
      .then(res => res.json())
      .then(data => setRegistry(data))
      .catch(err => console.error("Could not load evidence registry", err));
  }, []);

  const getAsset = (id?: string) => {
    if (!id) return null;
    return registry.assets.find(a => a.id === id);
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'sst': return <Thermometer className="text-red-500" />;
      case 'weather':
      case 'wave': return <Wind className="text-blue-500" />;
      case 'sar':
      case 'pfz': return <Target className="text-teal-500" />;
      default: return <Map className="text-slate-500" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
        
        {/* HEADER */}
        <div className="flex items-center justify-between p-4 border-b bg-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <ImageIcon size={20} className="text-teal-600" />
              Evidence & Analysis
            </h2>
            <p className="text-xs text-slate-500">Supporting data for ORCA's conclusion</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-500">
            <X size={20} />
          </button>
        </div>

        {/* CONTENT */}
        <div className="p-4 overflow-y-auto flex-1 bg-slate-100 space-y-4">
          {(() => {
            if (evidence.length === 0) return <p className="text-slate-500 text-center py-8">No specific evidence available.</p>;

            // Find primary domain from the first item with a context
            const primaryContext = evidence.find(e => e.evidence_context)?.evidence_context;
            
            // Filter evidence items by the primary domain (if it exists)
            const filteredEvidence = primaryContext 
              ? evidence.filter(e => e.evidence_context?.domain === primaryContext.domain)
              : evidence;

            if (filteredEvidence.length === 0) return <p className="text-slate-500 text-center py-8">No specific evidence available.</p>;

            return filteredEvidence.map((item, idx) => {
              const asset = getAsset(item.asset_id);
              
              return (
                <div key={idx} className="bg-white border rounded-xl overflow-hidden shadow-sm flex flex-col">
                  {/* KEY FINDING */}
                  <div className="p-4 border-b flex justify-between items-center bg-slate-50">
                    <div className="flex gap-3 items-center">
                      <div className="bg-white p-2 rounded-lg border shadow-sm">
                        {getIcon(item.type)}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-800 text-lg">
                          {asset ? asset.title : ((item.type || 'Marine').toUpperCase() + " Evidence")}
                        </h3>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded border tracking-wider ${
                      item.is_simulated || (asset && asset.is_simulated)
                        ? 'bg-amber-50 text-amber-800 border-amber-200' 
                        : 'bg-green-50 text-green-800 border-green-200'
                    }`}>
                      {item.is_simulated || (asset && asset.is_simulated) ? 'SIMULATED DEMO DATA' : 'REAL DATA'}
                    </span>
                  </div>

                  {/* INTERACTIVE EVIDENCE MAP */}
                  {item.data && (
                    <div className="p-4 border-b">
                      <h4 className="text-xs font-bold text-slate-400 tracking-wider mb-3 flex items-center gap-1">
                        <Map size={14} /> INTERACTIVE EVIDENCE MAP
                      </h4>
                      <EvidenceMap type={item.type || 'marine'} data={item.data} />
                    </div>
                  )}

                  {/* REFERENCE / SUPPORTING IMAGERY */}
                  <div className="p-4 border-b bg-slate-50">
                    <h4 className="text-xs font-bold text-slate-400 tracking-wider mb-3 flex items-center gap-1">
                      <ImageIcon size={14} /> REFERENCE / SUPPORTING IMAGERY
                    </h4>
                    {asset ? (
                      <div className="w-full max-w-sm mx-auto relative rounded-lg overflow-hidden border shadow-sm bg-white">
                        <img src={asset.path} alt={asset.title} className="w-full h-auto object-contain max-h-48" />
                        <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/60 backdrop-blur text-white text-[9px] font-mono tracking-widest rounded border border-white/20 shadow-sm">
                          {asset.is_simulated ? 'SIMULATED DATA' : 'REFERENCE ASSET'}
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 bg-slate-100 rounded text-center text-sm text-slate-500 italic">
                        No reference imagery available
                      </div>
                    )}
                  </div>

                  {/* SUPPORTING DATA */}
                  <div className="p-4 border-b flex flex-wrap gap-6">
                    <div className="w-full">
                      <h4 className="text-xs font-bold text-slate-400 tracking-wider mb-2">SUPPORTING DATA</h4>
                    </div>
                    {item.value !== undefined ? (
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Primary Value</span>
                        <span className="text-lg font-mono font-bold text-teal-800">
                          {item.value} {item.unit}
                        </span>
                      </div>
                    ) : (
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Data Points</span>
                        <span className="text-sm font-mono font-bold text-slate-700">
                          Structured Geo-Data Present
                        </span>
                      </div>
                    )}
                    {item.confidence && (
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Confidence</span>
                        <span className="text-lg font-mono font-bold text-blue-800">
                          {Math.round(item.confidence * 100)}%
                        </span>
                      </div>
                    )}
                  </div>

                  {/* WHY IT MATTERS */}
                  <div className="p-4 border-b bg-teal-50/30">
                    <h4 className="text-xs font-bold text-slate-400 tracking-wider mb-2">WHY IT MATTERS</h4>
                    <p className="text-sm text-slate-700 leading-relaxed font-medium">
                      {item.summary || "This data supports the advisory conclusion by confirming the underlying marine and meteorological conditions."}
                    </p>
                  </div>

                  {/* PROVENANCE */}
                  <div className="px-4 py-3 bg-slate-100 text-[10px] text-slate-500 font-mono flex justify-between items-center">
                    <div className="flex flex-col gap-1">
                      <span><strong className="text-slate-700">SOURCE:</strong> {asset?.source || item.source || 'Prototype Marine Dataset'}</span>
                      <span><strong className="text-slate-700">AGENT:</strong> {item.agent || 'ORCA'} ({item.tool})</span>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <button className="flex items-center gap-1 text-teal-600 hover:text-teal-700 font-bold uppercase tracking-wider transition-colors">
                        <ExternalLink size={12} /> Full Source Data
                      </button>
                      <span>ID: {Math.random().toString(36).substring(2, 10).toUpperCase()}</span>
                    </div>
                  </div>
                </div>
              );
            });
          })()}
        </div>
      </div>
    </div>
  );
}
