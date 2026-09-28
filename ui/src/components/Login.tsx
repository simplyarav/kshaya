import React, { useState } from 'react';
import { Shield } from 'lucide-react';

export default function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/core/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) throw new Error('Invalid credentials');
      
      const data = await res.json();
      onLogin(data.access_token);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#EDE6D6] flex flex-col items-center justify-center p-4">
      <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-8 max-w-sm w-full shadow-2xl">
        <div className="flex items-center gap-3 mb-6 justify-center">
          <Shield className="w-10 h-10 text-[#7C9473]" />
          <h1 className="text-2xl font-bold text-[#2E2B26] tracking-wider">KSHAYA LOGIN</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-[#4A3B32]">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input 
              required
              className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded p-2 focus:border-[#7C9473] outline-none" 
              value={username} onChange={e => setUsername(e.target.value)} 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
              required type="password"
              className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded p-2 focus:border-[#7C9473] outline-none" 
              value={password} onChange={e => setPassword(e.target.value)} 
            />
          </div>

          {error && <div className="text-red-400 text-sm font-bold">{error}</div>}

          <button type="submit" className="w-full bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] font-bold py-2 px-4 rounded transition">
            Authenticate
          </button>
        </form>
      </div>
    </div>
  );
}