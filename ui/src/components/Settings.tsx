import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Accessibility, Shield, Users } from 'lucide-react';

export default function Settings() {
  const { i18n } = useTranslation();
  const [onlineMode, setOnlineMode] = useState(false);
  const [highContrast, setHighContrast] = useState(false);

  return (
    <div className="space-y-8 max-w-4xl">
      <h2 className="text-3xl font-bold text-[#2E2B26] mb-6">Settings & Configuration</h2>
      
      {/* Localization */}
      <section className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6">
        <h3 className="text-xl font-bold text-[#4A3B32] flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-[#7C9473]" /> Localization
        </h3>
        <div className="flex items-center gap-4">
          <label className="text-[#7C9473]">Interface Language:</label>
          <select 
            value={i18n.language}
            onChange={(e) => i18n.changeLanguage(e.target.value)}
            className="bg-[#EDE6D6] border border-[#C7BFA6] text-[#2E2B26] rounded p-2 outline-none"
          >
            <option value="en">English</option>
            <option value="hi">हिंदी (Hindi)</option>
          </select>
        </div>
      </section>

      {/* Accessibility */}
      <section className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6">
        <h3 className="text-xl font-bold text-[#4A3B32] flex items-center gap-2 mb-4">
          <Accessibility className="w-5 h-5 text-green-400" /> Accessibility
        </h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <input 
            type="checkbox" 
            checked={highContrast} 
            onChange={(e) => setHighContrast(e.target.checked)} 
          />
          <span className="text-[#7C9473]">Enable High Contrast Mode</span>
        </label>
      </section>

      {/* RBAC Placeholder */}
      <section className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6">
        <h3 className="text-xl font-bold text-[#4A3B32] flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-purple-400" /> RBAC & Users
        </h3>
        <div className="text-[#7C9473] text-sm">
          User management and role assignment module. (Placeholder in this view)
        </div>
      </section>

      {/* Network Policy */}
      <section className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6">
        <h3 className="text-xl font-bold text-[#4A3B32] flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-red-400" /> Network Policy
        </h3>
        <div className="bg-[#EDE6D6] border border-[#C7BFA6] p-4 rounded mb-4 text-sm text-[#7C9473]">
          <strong>NETWORK_POLICY.md Enforcement:</strong> KSHAYA operates fully offline by default. 
          Enabling "Online Mode" permits the platform to reach out to certified update servers 
          and cloud sync destinations. This should only be enabled in environments that explicitly 
          permit outbound connections.
        </div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input 
            type="checkbox" 
            checked={onlineMode} 
            onChange={(e) => setOnlineMode(e.target.checked)} 
          />
          <span className="text-[#7C9473] font-bold">Enable Online Mode</span>
        </label>
      </section>
    </div>
  );
}
