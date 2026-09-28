import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';

export default function AuditLedgerViewer({ token }: { token: string }) {
  const [events, setEvents] = useState<any[]>([]);
  const [verifyStatus, setVerifyStatus] = useState<{status: 'idle' | 'running' | 'pass' | 'fail', broken_id?: number}>({status: 'idle'});

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/core/audit', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        if (!res.ok) throw new Error("Failed to load audit events");
        return res.json();
      })
      .then(data => setEvents(Array.isArray(data) ? data : []))
      .catch(console.error);
  }, [token]);

  const verifyChain = async () => {
    setVerifyStatus({ status: 'running' });
    try {
      // We need to implement this endpoint on the backend next
      const res = await fetch('http://127.0.0.1:8000/api/core/audit/verify', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.valid) {
        setVerifyStatus({ status: 'pass' });
      } else {
        setVerifyStatus({ status: 'fail', broken_id: data.broken_id });
      }
    } catch (e) {
      setVerifyStatus({ status: 'fail' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-[#2E2B26]">Audit Ledger</h2>
        <button 
          onClick={verifyChain}
          disabled={verifyStatus.status === 'running'}
          className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] font-bold py-2 px-4 rounded flex items-center gap-2"
        >
          <ShieldCheck className="w-5 h-5" />
          Verify Cryptographic Chain
        </button>
      </div>
      
      {verifyStatus.status === 'pass' && (
        <div className="bg-green-900/50 border border-green-700 text-green-200 p-4 rounded flex items-center gap-2">
          <ShieldCheck className="w-6 h-6" /> Complete cryptographic chain-of-custody validated successfully.
        </div>
      )}
      
      {verifyStatus.status === 'fail' && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded flex items-center gap-2">
          <AlertCircle className="w-6 h-6" /> Chain verification failed! {verifyStatus.broken_id && `Broken link detected at Event #${verifyStatus.broken_id}`}
        </div>
      )}

      <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg overflow-hidden">
        <table className="w-full text-left text-sm text-[#7C9473]">
          <thead className="bg-[#DCD4C0] text-[#7C9473]">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Timestamp (UTC)</th>
              <th className="px-4 py-3">Actor</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {events.map(e => (
              <tr key={e.id} className="hover:bg-[#DCD4C0]/50">
                <td className="px-4 py-3 font-mono text-xs">{e.id}</td>
                <td className="px-4 py-3">{e.timestamp}</td>
                <td className="px-4 py-3">{e.actor}</td>
                <td className="px-4 py-3 font-semibold">{e.action}</td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-500">No audit events recorded.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}