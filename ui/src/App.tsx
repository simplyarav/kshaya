import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, HardDrive, FileTerminal, Search, Settings as SettingsIcon, LogOut, AlertTriangle, LayoutDashboard } from 'lucide-react';

import Dashboard from './components/Dashboard';
import FirstRunSetup from './components/FirstRunSetup';
import AuditLedgerViewer from './components/AuditLedgerViewer';
import Settings from './components/Settings';
import GlobalSearch from './components/GlobalSearch';
import Login from './components/Login';
import SanitisationWizard from './components/SanitisationWizard';
import FileCleanup from './components/FileCleanup';
import ForensicsWorkspace from './components/ForensicsWorkspace';
import LandingPage from './components/LandingPage';
import { ApiClient } from './apiClient';

function AppContent({ token, setToken }: { token: string, setToken: any }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const [simModeActive, setSimModeActive] = useState(false);
  const [isVaultClosed, setIsVaultClosed] = useState(false);
  const [isVaultAnimating, setIsVaultAnimating] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!token) return;

    // Connect to WebSocket using the single source of truth
    const ws = new WebSocket(`ws://127.0.0.1:8000/api/core/ws/jobs`);
    
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "JOB_UPDATE") {
          setSimModeActive(msg.status === "in_progress");
          window.dispatchEvent(new CustomEvent('kshaya:job_update', { detail: msg }));
        }
      } catch(e) {}
    };

    ApiClient.get('/core/system/status')
      .then((data: any) => setSimModeActive(data.simulation_mode_active))
      .catch(console.error);

    return () => { ws.close(); };
  }, [token]);

  const navigateWithSweep = (path: string) => {
    if (isVaultAnimating || location.pathname === path) return;
    setSidebarOpen(false);
    setIsVaultAnimating(true);
    setIsVaultClosed(true);

    setTimeout(() => {
      navigate(path);
      setTimeout(() => {
        setIsVaultClosed(false);
        setTimeout(() => setIsVaultAnimating(false), 250);
      }, 150);
    }, 250);
  };

  const NavItem = ({ to, icon: Icon, label }: any) => (
    <button 
      onClick={() => navigateWithSweep(to)} 
      className={`w-full flex items-center gap-3 px-3 py-2 rounded transition text-sm lg:text-base ${location.pathname === to ? 'bg-[#7C9473] text-[#EDE6D6]' : 'hover:bg-[#C7BFA6] text-[#2E2B26]'}`}
    >
      <Icon className="w-5 h-5 shrink-0" /> <span className="truncate">{label}</span>
    </button>
  );

  return (
    <div className="flex h-screen bg-[#EDE6D6] text-[#2E2B26] font-sans relative overflow-hidden">
      {/* Solid blackout layer */}
      <div 
        className="fixed inset-0 bg-[#EDE6D6] transition-opacity duration-200 ease-in-out pointer-events-none"
        style={{ zIndex: 9998, opacity: isVaultClosed ? 1 : 0 }}
      />
      
      {/* Diagonal Police Sweep Overlays */}
      <div
        className="fixed top-1/2 left-1/2 pointer-events-none"
        style={{
          width: '300vmax', height: '300vmax',
          transform: 'translate(-50%, -50%) rotate(-45deg)',
          zIndex: 9999,
        }}
      >
        <div
          className="absolute top-0 left-0 w-full bg-[#2C425E]/50 transition-transform duration-300 ease-in-out z-10 flex items-end justify-center pb-12"
          style={{
            height: 'calc(50% + 2px)',
            transform: isVaultClosed ? 'translateY(0)' : 'translateY(-100%)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.5), inset 0 -4px 10px rgba(255,255,255,0.2)',
            pointerEvents: isVaultAnimating ? 'auto' : 'none',
          }}
        >
          <span className="logo-font text-[#2E2B26]/30 text-[8vw] tracking-[0.2em] font-black pointer-events-none select-none">KSHAYA</span>
        </div>
        <div
          className="absolute bottom-0 left-0 w-full h-1/2 bg-[#D32F2F]/50 transition-transform duration-300 ease-in-out z-0 flex items-start justify-center pt-12"
          style={{
            transform: isVaultClosed ? 'translateY(0)' : 'translateY(100%)',
            boxShadow: 'inset 0 4px 10px rgba(255,255,255,0.2), inset 0 8px 20px rgba(0,0,0,0.3)',
            pointerEvents: isVaultAnimating ? 'auto' : 'none',
          }}
        >
          <span className="logo-font text-[#2E2B26]/30 text-[8vw] tracking-[0.2em] font-black pointer-events-none select-none">KSHAYA</span>
        </div>
      </div>

      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-[60] lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar — fixed on mobile, static on desktop */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-[70] 
        w-56 lg:w-52 xl:w-60 
        bg-[#DCD4C0] border-r border-[#C7BFA6] flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-3 lg:p-4 flex items-center gap-2 border-b border-[#C7BFA6]">
          <Shield className="w-7 h-7 text-[#7C9473] shrink-0" />
          <span className="font-bold text-lg lg:text-xl tracking-wider">KSHAYA</span>
        </div>
        
        <nav className="flex-1 p-3 lg:p-4 space-y-1.5 overflow-y-auto">
          <NavItem to="/dashboard" icon={LayoutDashboard} label={t('dashboard')} />
          <NavItem to="/module1" icon={HardDrive} label={t('sanitisation')} />
          <NavItem to="/module2" icon={FileTerminal} label={t('file_cleanup')} />
          <NavItem to="/module3" icon={Search} label={t('forensics')} />
          <div className="pt-3 mt-3 border-t border-[#C7BFA6] space-y-1.5">
            <NavItem to="/audit" icon={Shield} label={t('audit_ledger')} />
            <NavItem to="/settings" icon={SettingsIcon} label={t('settings')} />
          </div>
        </nav>
        
        <div className="p-3 lg:p-4 border-t border-[#C7BFA6]">
          <button onClick={() => { localStorage.removeItem('token'); setToken(null); }} className="flex items-center gap-3 text-[#2E2B26] hover:text-[#D32F2F] transition w-full text-sm">
            <LogOut className="w-5 h-5 shrink-0" /> Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-40 min-w-0">
        <header className="h-14 lg:h-16 bg-[#DCD4C0] border-b border-[#C7BFA6] flex items-center gap-3 px-3 lg:px-6 relative z-50 shrink-0">
          {/* Mobile hamburger */}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-1.5 rounded hover:bg-[#C7BFA6]">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <div className="flex-1 min-w-0">
            <GlobalSearch token={token} />
          </div>
        </header>
        
        {simModeActive && <div className="h-10 shrink-0" />}

        <main className="flex-1 overflow-auto p-3 sm:p-4 lg:p-6 relative z-40">
          <Routes>
            <Route path="/dashboard" element={<Dashboard token={token} />} />
            <Route path="/module1" element={<SanitisationWizard token={token} />} />
            <Route path="/module2" element={<FileCleanup token={token} />} />
            <Route path="/module3" element={<ForensicsWorkspace token={token} />} />
            <Route path="/audit" element={<AuditLedgerViewer token={token} />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>

      {/* Simulation Banner */}
      {simModeActive && (
        <div 
          className="fixed top-14 lg:top-16 left-0 lg:left-52 xl:left-60 right-0 bg-yellow-600 text-[#2E2B26] font-bold px-4 py-2 flex items-center justify-center gap-2 shadow-lg text-sm" 
          style={{ zIndex: 10000 }}
        >
          <AlertTriangle className="w-5 h-5 shrink-0" />
          {t('simulation_active')}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);
  const [showLanding, setShowLanding] = useState<boolean>(true);

  useEffect(() => {
    let retries = 0;
    const checkStatus = () => {
      ApiClient.get('/core/setup/status')
        .then((data: any) => setIsInitialized(data.is_initialized))
        .catch(() => {
          retries++;
          if (retries < 10) {
            setTimeout(checkStatus, 1000); // Retry every 1s up to 10 times
          } else {
            setIsInitialized(false);
          }
        });
    };
    checkStatus();
  }, []);

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />;
  }

  if (isInitialized === null) return <div className="text-[#2E2B26] p-8 bg-[#EDE6D6] h-screen">Loading...</div>;

  if (!isInitialized) {
    return <FirstRunSetup onComplete={() => setIsInitialized(true)} />;
  }

  if (!token) {
    return <Login onLogin={(t: string) => { localStorage.setItem('token', t); setToken(t); }} />;
  }

  return (
    <Router>
      <AppContent token={token} setToken={setToken} />
    </Router>
  );
}
