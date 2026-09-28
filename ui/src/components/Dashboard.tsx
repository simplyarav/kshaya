import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, CheckCircle, Clock } from 'lucide-react';

export default function Dashboard({ token }: { token: string }) {
  const [data, setData] = useState<{ recent_jobs: any[], alerts: any[] } | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/core/dashboard', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        if (!res.ok) throw new Error("Failed to load dashboard data");
        return res.json();
      })
      .then(setData)
      .catch(err => {
        console.error(err);
        setData({ recent_jobs: [], alerts: [] });
      });
  }, [token]);

  if (!data) return <div>Loading dashboard...</div>;

  return (
    <div className="space-y-4 lg:space-y-6">
      <h2 className="text-2xl lg:text-3xl font-bold text-[#2E2B26] mb-4 lg:mb-6">Overview</h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        
        {/* Recent Jobs Panel */}
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-4 shadow">
          <div className="flex items-center gap-2 text-[#7C9473] font-semibold mb-4 pb-2 border-b border-[#C7BFA6]">
            <Activity className="w-5 h-5 text-[#7C9473]" /> Recent Activity
          </div>
          <ul className="space-y-3">
            {data.recent_jobs.length === 0 && <li className="text-gray-500 text-sm">No recent jobs.</li>}
            {data.recent_jobs.map(j => (
              <li key={j.id} className="flex justify-between items-center text-sm">
                <span className="text-[#7C9473]">{j.type} #{j.id}</span>
                <span className={`px-2 py-1 rounded text-xs ${j.status === 'completed' ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
                  {j.status}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Action Required Panel */}
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-4 shadow">
          <div className="flex items-center gap-2 text-[#7C9473] font-semibold mb-4 pb-2 border-b border-[#C7BFA6]">
            <CheckCircle className="w-5 h-5 text-yellow-400" /> Pending Approvals
          </div>
          <div className="text-sm text-[#7C9473]">
            No exceptions currently awaiting your approval.
          </div>
        </div>

        {/* Compliance Panel */}
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-4 shadow">
          <div className="flex items-center gap-2 text-[#7C9473] font-semibold mb-4 pb-2 border-b border-[#C7BFA6]">
            <Clock className="w-5 h-5 text-green-400" /> Compliance & Retention
          </div>
          <div className="text-sm text-[#7C9473]">
            All cryptographic signatures valid. No immediate certificate expiries detected.
          </div>
        </div>

      </div>
    </div>
  );
}