import { useState } from 'react';
import { Shield, Anchor, Radio, Activity, Navigation, Lock, User, Key, ChevronRight } from 'lucide-react';
import FishermanApp from './components/FishermanApp';
import AuthorityApp from './components/AuthorityApp';

type AppState = 'LANDING' | 'AUTHORITY_LOGIN' | 'FISHERMAN' | 'AUTHORITY';

function App() {
  const [appState, setAppState] = useState<AppState>('LANDING');
  const [officerId, setOfficerId] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Demo access mechanism: bypass actual authentication
    setAppState('AUTHORITY');
  };

  if (appState === 'LANDING') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300 p-4 font-sans">
        
        <div className="text-center mb-16 space-y-4">
          <div className="flex justify-center mb-6">
            <Shield className="w-16 h-16 text-cyan-500" />
          </div>
          <h1 className="text-5xl font-extrabold tracking-widest text-slate-100">
            ORCA
          </h1>
          <p className="text-lg text-cyan-400 tracking-wider">
            AI-Powered Marine Safety & Search-and-Rescue Intelligence
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
          
          {/* Fisherman Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col relative overflow-hidden group shadow-2xl">
            <div className="absolute top-0 right-0 bg-teal-500/10 text-teal-400 text-[10px] font-bold px-3 py-1 rounded-bl-lg">MOBILE UX</div>
            <div className="w-12 h-12 rounded-lg bg-teal-500/20 flex items-center justify-center mb-6">
              <Anchor className="text-teal-400 w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-100 mb-4">FISHERMAN</h2>
            <ul className="space-y-3 mb-10 flex-1">
              <li className="flex items-center gap-3 text-sm text-slate-400"><Navigation className="w-4 h-4 text-teal-500" /> Route intelligence</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Activity className="w-4 h-4 text-teal-500" /> Marine safety</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Radio className="w-4 h-4 text-teal-500" /> ORCA assistant</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Shield className="w-4 h-4 text-teal-500" /> Emergency SOS</li>
            </ul>
            <button 
              onClick={() => setAppState('FISHERMAN')}
              className="w-full py-3 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              OPEN FISHERMAN EXPERIENCE <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Authority Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col relative overflow-hidden group shadow-2xl">
            <div className="absolute top-0 right-0 bg-blue-500/10 text-blue-400 text-[10px] font-bold px-3 py-1 rounded-bl-lg">DESKTOP UX</div>
            <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center mb-6">
              <Shield className="text-blue-400 w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-100 mb-4">COASTAL AUTHORITY</h2>
            <ul className="space-y-3 mb-10 flex-1">
              <li className="flex items-center gap-3 text-sm text-slate-400"><Activity className="w-4 h-4 text-blue-500" /> Incident command</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Radio className="w-4 h-4 text-blue-500" /> Live vessel intelligence</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Navigation className="w-4 h-4 text-blue-500" /> Multi-agent SAR</li>
              <li className="flex items-center gap-3 text-sm text-slate-400"><Shield className="w-4 h-4 text-blue-500" /> Emergency response</li>
            </ul>
            <button 
              onClick={() => setAppState('AUTHORITY_LOGIN')}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              AUTHORITY LOGIN <ChevronRight className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>
    );
  }

  if (appState === 'AUTHORITY_LOGIN') {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300 p-4 font-sans">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-900/30 border border-blue-500/30 mb-4">
              <Lock className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold text-slate-100 tracking-wider">COASTAL AUTHORITY PORTAL</h1>
            <p className="text-blue-400 mt-2 tracking-widest text-sm uppercase">Authorized Personnel Access</p>
          </div>

          <form onSubmit={handleLogin} className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
            
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold tracking-widest text-amber-500 uppercase px-2 py-1 bg-amber-500/10 border border-amber-500/20 rounded">DEMO ENVIRONMENT</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                No active authentication backend is configured. Use any credentials to proceed into the demo environment.
              </p>
            </div>

            <div className="space-y-5 mb-8">
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Officer ID</label>
                <div className="relative">
                  <User className="w-5 h-5 text-slate-500 absolute left-3 top-2.5" />
                  <input 
                    type="text" 
                    required
                    value={officerId}
                    onChange={(e) => setOfficerId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                    placeholder="Enter ID"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Password</label>
                <div className="relative">
                  <Key className="w-5 h-5 text-slate-500 absolute left-3 top-2.5" />
                  <input 
                    type="password" 
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit"
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold tracking-widest rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              SIGN IN
            </button>

            <button 
              type="button"
              onClick={() => setAppState('LANDING')}
              className="w-full mt-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-300 transition-colors"
            >
              CANCEL
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <>
      {appState === 'FISHERMAN' && <FishermanApp onLogout={() => setAppState('LANDING')} />}
      {appState === 'AUTHORITY' && <AuthorityApp onLogout={() => setAppState('LANDING')} />}
    </>
  );
}

export default App;
