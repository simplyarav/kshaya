import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function FirstRunSetup({ onComplete }: { onComplete: () => void }) {
  const [isElevated, setIsElevated] = useState<boolean | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [lawfulAuth, setLawfulAuth] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/core/setup/privilege-check')
      .then(res => res.json())
      .then(data => setIsElevated(data.is_elevated))
      .catch(() => setIsElevated(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!lawfulAuth) {
      setError('You must acknowledge lawful authority to proceed.');
      return;
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/api/core/setup/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          admin_username: username,
          admin_password: password,
          lawful_authority_acknowledged: true
        })
      });
      
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Setup failed');
      }
      
      onComplete();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (isElevated === null) return <div className="p-8 text-[#2E2B26]">Checking privileges...</div>;

  return (
    <div className="min-h-screen bg-[#EDE6D6] flex flex-col items-center justify-center p-4">
      <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-8 max-w-md w-full shadow-2xl">
        <div className="flex items-center gap-3 mb-6 justify-center">
          <Shield className="w-10 h-10 text-[#7C9473]" />
          <h1 className="text-2xl font-bold text-[#2E2B26] tracking-wider">KSHAYA INIT</h1>
        </div>
        
        {!isElevated && (
          <div className="bg-yellow-900/50 border border-yellow-700 rounded p-4 mb-6 flex gap-3 text-yellow-200">
            <AlertTriangle className="w-6 h-6 shrink-0" />
            <div className="text-sm">
              <strong>Reduced Mode Active:</strong> This application is not running with OS administrative privileges. 
              Modules 1 and 2 (Sanitisation & Cleanup) will be completely disabled. Only Read-Only Forensics (Module 3) is permitted.
              Relaunch as Administrator/Root for full functionality.
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-[#4A3B32]">
          <div>
            <label className="block text-sm font-medium mb-1">Master Admin Username</label>
            <input 
              required
              className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded p-2 focus:border-[#7C9473] outline-none" 
              value={username} onChange={e => setUsername(e.target.value)} 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Master Admin Password</label>
            <input 
              required type="password"
              className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded p-2 focus:border-[#7C9473] outline-none" 
              value={password} onChange={e => setPassword(e.target.value)} 
            />
          </div>
          
          <div className="border border-[#C7BFA6] rounded p-4 bg-[#EDE6D6] mt-6">
            <label className="flex items-start gap-3 cursor-pointer">
              <input 
                type="checkbox" required className="mt-1"
                checked={lawfulAuth} onChange={e => setLawfulAuth(e.target.checked)}
              />
              <span className="text-sm">
                <strong>Legal Acknowledgement:</strong> I confirm I possess lawful authority to execute forensic and sanitisation actions on attached media. 
                I understand all actions are immutably logged to the cryptographic ledger.
              </span>
            </label>
          </div>

          {error && <div className="text-red-400 text-sm font-bold">{error}</div>}

          <button type="submit" className="w-full bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] font-bold py-2 px-4 rounded transition flex justify-center gap-2 items-center">
            <ShieldCheck className="w-5 h-5" /> Initialize Platform
          </button>
        </form>
      </div>
    </div>
  );
}