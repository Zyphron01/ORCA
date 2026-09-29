import { useState, useRef, useEffect } from 'react';
import { AlertCircle, Cloud, Navigation2, Phone, Power, Send, Mic, MicOff, Volume2, Square } from 'lucide-react';
import { VoiceInputService, VoiceOutputService } from '../services/voice';
import EvidencePanel from './EvidencePanel';
import EvidenceMap from './EvidenceMap';

interface ChatMessage {
  role: 'user' | 'orca';
  content: string;
  evidence?: any[];
}

const LANGUAGES = [
  { code: 'en-IN', label: 'English' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'hi-IN', label: 'हिन्दी (Hindi)' },
  { code: 'ta-IN', label: 'தமிழ் (Tamil)' },
  { code: 'te-IN', label: 'తెలుగు (Telugu)' }
];

export default function FishermanApp({ onLogout }: { onLogout: () => void }) {
  const [sosActive, setSosActive] = useState(false);
  const [sosStatus, setSosStatus] = useState('IDLE');
  const [incidentId, setIncidentId] = useState<string | null>(null);

  const [activeEvidence, setActiveEvidence] = useState<any[] | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'orca', content: 'Safe journey! I am ORCA, your marine intelligence assistant. How can I help you?' }
  ]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Voice States
  const [selectedLang, setSelectedLang] = useState('en-IN');
  const [voiceState, setVoiceState] = useState<'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'ERROR'>('IDLE');
  const [voiceErrorMsg, setVoiceErrorMsg] = useState('');
  
  const voiceInputRef = useRef<VoiceInputService | null>(null);
  const voiceOutputRef = useRef<VoiceOutputService | null>(null);

  useEffect(() => {
    voiceOutputRef.current = new VoiceOutputService();
    voiceInputRef.current = new VoiceInputService(
      (transcript) => {
        handleVoiceTranscript(transcript);
      },
      (error) => {
        if (error === 'browser-unsupported') {
          setVoiceErrorMsg('Browser unsupported');
        } else if (error === 'not-allowed') {
          setVoiceErrorMsg('Mic permission denied');
        } else {
          setVoiceErrorMsg('Speech error');
        }
        setVoiceState('ERROR');
        setTimeout(() => setVoiceState('IDLE'), 3000);
      },
      () => {
        if (voiceState === 'LISTENING') setVoiceState('PROCESSING');
      }
    );
    return () => {
      voiceInputRef.current?.stopListening();
      voiceOutputRef.current?.stop();
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleListening = () => {
    if (voiceState === 'LISTENING') {
      voiceInputRef.current?.stopListening();
      setVoiceState('IDLE');
    } else {
      voiceOutputRef.current?.stop();
      setVoiceErrorMsg('');
      setVoiceState('LISTENING');
      voiceInputRef.current?.startListening(selectedLang);
    }
  };

  const handleVoiceTranscript = async (transcript: string) => {
    setVoiceState('PROCESSING');
    await sendChatMessage(transcript, true);
  };

  const triggerSOS = async () => {
    try {
      setSosStatus('TRIGGERING...');
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/sos/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vessel_id: 'bc123-abc',
          lat: 12.0,
          lon: 80.0,
          description: 'Fisherman Distress - Capsize Simulation'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setIncidentId(data.incident_id || data.id);
        setSosActive(true);
        setSosStatus('ACTIVE - WAITING FOR ACKNOWLEDGE');
      } else {
        setSosStatus('SOS transmission failed - retry');
      }
    } catch (e) {
      console.error(e);
      setSosStatus('SOS transmission failed - retry');
    }
  };

  const cancelSOS = async () => {
    if (!incidentId) {
      setSosActive(false);
      return;
    }
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/sos/cancel?incident_id=${incidentId}`, {
        method: 'POST'
      });
      setSosActive(false);
      setIncidentId(null);
      setSosStatus('IDLE');
    } catch (e) {
      console.error(e);
    }
  };

  const sendChatMessage = async (textOverride?: string, fromVoice: boolean = false) => {
    if (isChatLoading) return;
    const textToSend = textOverride !== undefined ? textOverride : chatInput;
    if (!textToSend.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    if (!fromVoice) setChatInput('');
    setIsChatLoading(true);
    if (!fromVoice) setVoiceState('PROCESSING');

    abortControllerRef.current = new AbortController();

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/orca/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({ 
          message: textToSend, 
          language_hint: selectedLang,
          session_id: sessionId
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        const answer = data.message || data.answer || data.response || 'No response';
        const evidence = data.evidence || [];
        setMessages(prev => [...prev, { role: 'orca', content: answer, evidence }]);
        
        if (fromVoice) {
          setVoiceState('SPEAKING');
          voiceOutputRef.current?.speak(answer, selectedLang, () => {
            setVoiceState('IDLE');
          });
        } else {
          setVoiceState('IDLE');
        }
      } else {
        let errorMsg = 'ORCA unavailable';
        try {
          const errorData = await res.json();
          if (errorData.detail) {
            errorMsg = errorData.detail;
          }
        } catch (err) {
          // Fallback if not JSON
          if (res.status === 503) {
            errorMsg = 'ORCA is temporarily unavailable because the AI service is busy. Please try again.';
          }
        }
        setMessages(prev => [...prev, { role: 'orca', content: errorMsg }]);
        setVoiceState('ERROR');
        setVoiceErrorMsg(res.status === 503 ? 'Service Busy' : 'API Error');
        setTimeout(() => setVoiceState('IDLE'), 3000);
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        return;
      }
      console.error(e);
      setMessages(prev => [...prev, { role: 'orca', content: 'ORCA unavailable' }]);
      setVoiceState('ERROR');
      setVoiceErrorMsg('Network Error');
      setTimeout(() => setVoiceState('IDLE'), 3000);
    } finally {
      setIsChatLoading(false);
    }
  };

  const stopChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsChatLoading(false);
    if (voiceState === 'PROCESSING') {
      setVoiceState('IDLE');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col max-w-md mx-auto shadow-2xl relative overflow-hidden">
      {/* HEADER */}
      <header className="bg-teal-700 text-white p-4 flex justify-between items-center z-10 shadow-md">
        <div>
          <h1 className="font-bold text-xl tracking-tight">MFV SARASWATI</h1>
          <p className="text-xs text-teal-200 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-400"></span> GPS CONNECTED (DEMO)
          </p>
        </div>
        <button onClick={onLogout} className="p-2 bg-teal-800 rounded-lg"><Power size={20}/></button>
      </header>

      {/* SOS OVERLAY */}
      {sosActive && (
        <div className="absolute inset-0 bg-red-900/90 z-50 flex flex-col items-center justify-center text-white p-6 text-center">
          <div className="w-24 h-24 rounded-full bg-red-500 animate-ping absolute opacity-50"></div>
          <AlertCircle size={64} className="text-white relative z-10 mb-4" />
          <h2 className="text-3xl font-bold mb-2">SOS SENT</h2>
          <p className="text-lg text-red-200 mb-8">{sosStatus}</p>
          <div className="bg-black/20 p-4 rounded-xl mb-8 w-full">
            <p className="text-sm uppercase text-red-200 font-bold mb-1">Incident ID</p>
            <p className="font-mono text-sm break-all mb-4">{incidentId || 'Pending'}</p>
            <p className="text-sm uppercase text-red-200 font-bold mb-1">Last Known Position</p>
            <p className="font-mono text-xl">12.000° N, 80.000° E</p>
          </div>
          <button 
            onClick={cancelSOS}
            className="px-8 py-3 bg-white text-red-900 font-bold rounded-full w-full"
          >
            CANCEL SOS
          </button>
        </div>
      )}

      {/* CONTENT */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        {/* QUICK STATS */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <Cloud className="text-blue-500 mb-2" size={24}/>
            <p className="text-xs text-slate-500 font-medium">WEATHER</p>
            <p className="font-bold text-lg text-slate-800">Clear, 15kn</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <Navigation2 className="text-teal-500 mb-2" size={24}/>
            <p className="text-xs text-slate-500 font-medium">NEAREST PFZ</p>
            <p className="font-bold text-lg text-slate-800">12.4 NM</p>
          </div>
        </div>

        {/* MAIN MARINE MAP */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-2 mb-6 h-64 overflow-hidden relative">
          <EvidenceMap 
            type="pfz" 
            data={{
              origin_lat: 12.0,
              origin_lon: 80.0,
              pfz_zones: [
                { lat: 12.5, lon: 80.8, distance_nm: 30 }
              ]
            }} 
          />
        </div>

        {/* ORCA CHAT */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-6 h-96 flex flex-col">
          <div className="flex items-center justify-between mb-4 border-b pb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-bold">O</div>
              <h3 className="font-bold text-slate-800 text-sm">ORCA Assistant</h3>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => {
                  setSessionId(crypto.randomUUID());
                  setMessages([{ role: 'orca', content: 'New chat started. How can I help?' }]);
                }}
                className="text-xs text-teal-600 hover:text-teal-800 font-medium"
              >
                New Chat
              </button>
              <select 
                className="text-xs bg-slate-100 border-none outline-none rounded p-1 text-slate-700 font-medium cursor-pointer"
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  voiceInputRef.current?.stopListening();
                  setVoiceState('IDLE');
                }}
              >
                {LANGUAGES.map(l => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto text-sm space-y-4 pb-2">
            {messages.map((msg, idx) => (
              <div key={idx} className={`w-full flex ${msg.role === 'orca' ? 'justify-start' : 'justify-end'}`}>
                <div className={`p-3 max-w-[85%] ${msg.role === 'orca' ? 'bg-slate-100 rounded-tr-xl rounded-br-xl rounded-bl-xl text-slate-700' : 'bg-teal-600 text-white rounded-tl-xl rounded-br-xl rounded-bl-xl'}`}>
                  {msg.content}
                  {msg.role === 'orca' && msg.evidence && msg.evidence.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-200">
                      <button 
                        onClick={() => setActiveEvidence(msg.evidence!)}
                        className="text-xs font-bold text-teal-600 hover:text-teal-800 flex items-center gap-1 uppercase tracking-wider"
                      >
                        Show Evidence ({msg.evidence.length})
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="bg-slate-100 p-3 rounded-tr-xl rounded-br-xl rounded-bl-xl w-5/6 text-slate-500 animate-pulse">
                ORCA is analyzing...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="mt-2 pt-2 border-t flex flex-col gap-2">
            {/* Voice Status Indicator */}
            <div className="flex justify-center items-center h-6">
              {voiceState === 'LISTENING' && <span className="text-xs text-red-500 font-bold animate-pulse flex items-center gap-1"><Mic size={14}/> Listening...</span>}
              {voiceState === 'PROCESSING' && <span className="text-xs text-blue-500 font-bold flex items-center gap-1"><Cloud size={14}/> ORCA is thinking...</span>}
              {voiceState === 'SPEAKING' && <span className="text-xs text-teal-500 font-bold flex items-center gap-1"><Volume2 size={14}/> ORCA is responding...</span>}
              {voiceState === 'ERROR' && <span className="text-xs text-amber-600 font-bold flex items-center gap-1"><AlertCircle size={14}/> {voiceErrorMsg}</span>}
              {voiceState === 'IDLE' && <span className="text-xs text-slate-400 flex items-center gap-1"><Mic size={14}/> Ask ORCA</span>}
            </div>

            <div className="flex gap-2 items-center">
              <button 
                onClick={toggleListening} 
                className={`p-3 rounded-full flex items-center justify-center transition-colors ${
                  voiceState === 'LISTENING' ? 'bg-red-100 text-red-600 animate-pulse' : 
                  voiceState === 'SPEAKING' ? 'bg-teal-100 text-teal-600' :
                  'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {voiceState === 'LISTENING' ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
              
              <input 
                type="text" 
                placeholder="Type message..." 
                className="flex-1 bg-slate-100 rounded-lg px-3 py-2 text-sm outline-none" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !isChatLoading && sendChatMessage()}
              />
              <button 
                onClick={() => isChatLoading ? stopChat() : sendChatMessage()} 
                className={`${isChatLoading ? 'bg-red-500 hover:bg-red-600' : 'bg-teal-600 hover:bg-teal-700'} text-white p-2 rounded-lg flex items-center justify-center`}
              >
                {isChatLoading ? <Square size={18} fill="currentColor" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </div>

        {/* SOS BUTTON */}
        <button 
          onClick={triggerSOS}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-bold text-xl py-6 rounded-2xl shadow-lg shadow-red-600/30 active:scale-95 transition-transform flex items-center justify-center gap-3"
        >
          <Phone fill="currentColor" size={28}/>
          DECLARE SOS
        </button>
      </div>

      {/* EVIDENCE PANEL */}
      {activeEvidence && (
        <EvidencePanel 
          evidence={activeEvidence} 
          onClose={() => setActiveEvidence(null)} 
        />
      )}
    </div>
  );
}
