import React, { useState, useEffect } from 'react';
import { Shield, FolderOpen, HardDrive, FileSearch, ShieldAlert, CheckCircle, AlertTriangle, FileCode, Search, Download, FileText, EyeOff } from 'lucide-react';

type Phase = 'CASE_MANAGEMENT' | 'INGESTION' | 'CARVING_ANALYSIS' | 'REPORTING';

export default function ForensicsWorkspace({ token }: { token: string }) {
  const [phase, setPhase] = useState<Phase>('CASE_MANAGEMENT');
  const [error, setError] = useState<string | null>(null);

  // Case & Evidence state
  const [cases, setCases] = useState<any[]>([]);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<any>(null);

  const [newCaseNumber, setNewCaseNumber] = useState('');
  const [newEvidenceTag, setNewEvidenceTag] = useState('');

  // Ingestion state
  const [imagePath, setImagePath] = useState('');
  const [expectedHash, setExpectedHash] = useState('');
  const [ingestionStatus, setIngestionStatus] = useState<string>('');

  // Carving state
  const [candidates, setCandidates] = useState<any[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);
  const [annotations, setAnnotations] = useState<Record<string, string>>({});

  // Reporting state
  const [redacted, setRedacted] = useState(true);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/forensics/cases', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setCases(await res.json());
    } catch (e) {}
  };

  const createCase = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/forensics/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ case_number: newCaseNumber })
      });
      if (res.ok) {
        const c = await res.json();
        setCases([...cases, c]);
        setSelectedCase(c);
        setNewCaseNumber('');
        fetchEvidence(c.id);
      } else {
        const data = await res.json();
        setError(data.detail);
      }
    } catch (e: any) { setError(e.message); }
  };

  const fetchEvidence = async (caseId: number) => {
    try {
      const res = await fetch(`/api/forensics/cases/${caseId}/evidence`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setEvidenceList(await res.json());
    } catch (e) {}
  };

  const registerEvidence = async () => {
    try {
      const res = await fetch(`/api/forensics/cases/${selectedCase.id}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ tag: newEvidenceTag })
      });
      if (res.ok) {
        const e = await res.json();
        setEvidenceList([...evidenceList, e]);
        setNewEvidenceTag('');
      } else {
        const data = await res.json();
        setError(data.detail);
      }
    } catch (e: any) { setError(e.message); }
  };

  const importEvidence = async () => {
    setError(null);
    try {
      const res = await fetch(`/api/forensics/evidence/${selectedEvidence.id}/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ filepath: imagePath, expected_hash: expectedHash })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail);
      }
      setIngestionStatus(data.message);
      setTimeout(() => setPhase('CARVING_ANALYSIS'), 2000);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const triggerCarving = async () => {
    setError(null);
    try {
      const res = await fetch(`/api/forensics/evidence/${selectedEvidence.id}/carve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setCandidates(data.candidates);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const generateReport = async () => {
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/forensics/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ findings: annotations, redacted })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail);
      }
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KSHAYA_Forensic_Report${redacted ? '_Redacted' : ''}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="space-y-4 lg:space-y-6 pb-20">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <h2 className="text-2xl lg:text-3xl font-bold text-[#2E2B26] flex items-center gap-3">
          <Search className="w-7 h-7 lg:w-8 lg:h-8 text-[#7C9473] shrink-0" /> Forensics Workspace
        </h2>
        <div className="bg-[#7C9473]/50 border border-[#7C9473] text-[#DCD4C0] px-3 py-1.5 lg:px-4 lg:py-2 rounded-full font-bold flex items-center gap-2 shadow-lg text-xs lg:text-sm whitespace-nowrap shrink-0">
          <Shield className="w-4 h-4 lg:w-5 lg:h-5" />
          Read-Only Mode Enforced
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* PHASE 1: CASE MANAGEMENT */}
      {phase === 'CASE_MANAGEMENT' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
          <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
            <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2">
              <FolderOpen className="w-6 h-6" /> Case Management
            </h3>
            
            <div className="flex gap-2">
              <input 
                type="text" 
                value={newCaseNumber} 
                onChange={e => setNewCaseNumber(e.target.value)} 
                placeholder="INCIDENT-2024-XXX" 
                className="flex-1 bg-[#EDE6D6] border border-[#C7BFA6] rounded px-3 py-2 text-[#2E2B26]"
              />
              <button onClick={createCase} className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] px-4 py-2 rounded font-bold">Create</button>
            </div>

            <div className="space-y-2">
              {cases.map(c => (
                <div 
                  key={c.id} 
                  onClick={() => { setSelectedCase(c); fetchEvidence(c.id); }}
                  className={`p-3 rounded cursor-pointer border ${selectedCase?.id === c.id ? 'bg-[#7C9473]/30 border-[#7C9473]' : 'bg-[#DCD4C0] border-[#C7BFA6]'}`}
                >
                  <div className="font-bold text-[#4A3B32]">{c.case_number}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
            <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2">
              <HardDrive className="w-6 h-6" /> Evidence Registry
            </h3>

            {!selectedCase ? (
              <div className="text-gray-500 text-center py-10">Select a case first.</div>
            ) : (
              <>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    value={newEvidenceTag} 
                    onChange={e => setNewEvidenceTag(e.target.value)} 
                    placeholder="EVD-01-MOCK" 
                    className="flex-1 bg-[#EDE6D6] border border-[#C7BFA6] rounded px-3 py-2 text-[#2E2B26]"
                  />
                  <button onClick={registerEvidence} className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] px-4 py-2 rounded font-bold">Register</button>
                </div>

                <div className="space-y-2">
                  {evidenceList.map(e => (
                    <div 
                      key={e.id} 
                      className={`p-3 rounded border flex justify-between items-center ${selectedEvidence?.id === e.id ? 'bg-[#7C9473]/30 border-[#7C9473]' : 'bg-[#DCD4C0] border-[#C7BFA6]'}`}
                    >
                      <div className="font-bold text-[#4A3B32]">{e.tag}</div>
                      <button 
                        onClick={() => { setSelectedEvidence(e); setPhase('INGESTION'); }}
                        className="text-[#7C9473] hover:text-[#DCD4C0] text-sm font-bold"
                      >
                        Ingest &rarr;
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* PHASE 2: INGESTION */}
      {phase === 'INGESTION' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2">
            <HardDrive className="w-6 h-6" /> Ingest Raw Image (Evidence: {selectedEvidence?.tag})
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-[#7C9473] mb-1">Image Path (Raw .dd only - .E01 requires libewf)</label>
              <input 
                type="text" 
                value={imagePath} 
                onChange={e => setImagePath(e.target.value)} 
                placeholder="C:\Forensics\image.dd" 
                className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded px-3 py-2 text-[#2E2B26] font-mono"
              />
            </div>
            <div>
              <label className="block text-sm text-[#7C9473] mb-1">Hash Baseline (SHA-256)</label>
              <input 
                type="text" 
                value={expectedHash} 
                onChange={e => setExpectedHash(e.target.value)} 
                placeholder="Paste expected hash (or 'MOCK_VALID' for demo)" 
                className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded px-3 py-2 text-[#2E2B26] font-mono"
              />
            </div>
            <button 
              onClick={importEvidence} 
              className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] px-6 py-2 rounded font-bold"
            >
              Verify Baseline & Import
            </button>
          </div>

          {ingestionStatus && (
            <div className="bg-green-900/30 border border-green-700 text-green-400 p-4 rounded flex items-center gap-3">
              <CheckCircle className="w-6 h-6 shrink-0" />
              <div>
                <div className="font-bold">Hash Verified!</div>
                <div className="text-sm">{ingestionStatus}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* PHASE 3 & 4: CARVING & ANALYSIS */}
      {phase === 'CARVING_ANALYSIS' && (
        <div className="space-y-6">
          <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2">
                <FileSearch className="w-6 h-6" /> Carving & Reconstruction Pipeline
              </h3>
              <button 
                onClick={triggerCarving} 
                className="bg-purple-600 hover:bg-purple-500 text-[#2E2B26] px-4 py-2 rounded font-bold"
              >
                Run Carvers
              </button>
            </div>

            {candidates.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
                <div className="lg:col-span-1 space-y-2 max-h-96 overflow-y-auto pr-2">
                  <h4 className="text-sm font-bold text-[#7C9473] mb-2 uppercase tracking-wider">Carved Candidates</h4>
                  {candidates.map(c => (
                    <div 
                      key={c.id} 
                      onClick={() => setSelectedCandidate(c)}
                      className={`p-3 rounded border cursor-pointer ${selectedCandidate?.id === c.id ? 'bg-[#7C9473]/30 border-[#7C9473]' : 'bg-[#DCD4C0] border-[#C7BFA6]'}`}
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-[#2E2B26] text-sm">{c.type}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${c.confidence.grade === 'High' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                          {c.confidence.score}%
                        </span>
                      </div>
                      <div className="text-xs text-[#7C9473] font-mono">Offset: {c.offset}</div>
                      {c.is_executable && (
                        <div className="mt-2 text-xs text-red-400 flex items-center gap-1 font-bold">
                          <ShieldAlert className="w-3 h-3" /> EXECUTABLE CONTENT
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="lg:col-span-2 bg-[#EDE6D6] border border-[#C7BFA6] rounded-lg p-4 flex flex-col min-h-[200px]">
                  {!selectedCandidate ? (
                    <div className="flex-1 flex items-center justify-center text-gray-500">Select a candidate to view Analyst Workspace</div>
                  ) : (
                    <>
                      <h4 className="text-lg font-bold text-[#2E2B26] mb-4 border-b border-[#C7BFA6] pb-2">
                        Analyst Workspace: {selectedCandidate.id}
                      </h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="space-y-4">
                          <div className="bg-[#F5F1E7] border border-[#C7BFA6] p-3 rounded">
                            <div className="text-xs text-[#7C9473] font-bold mb-2">VALIDATION FLAGS</div>
                            <div className="flex items-center gap-2 text-sm text-[#7C9473]">
                              {selectedCandidate.signature_pass ? <CheckCircle className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-red-500" />}
                              Signature Validation
                            </div>
                            <div className="flex items-center gap-2 text-sm text-[#7C9473] mt-1">
                              {selectedCandidate.structure_pass ? <CheckCircle className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-red-500" />}
                              Structure Validation
                            </div>
                          </div>

                          <div className="bg-[#F5F1E7] border border-[#C7BFA6] p-3 rounded">
                            <div className="text-xs text-[#7C9473] font-bold mb-2">CONFIDENCE SCORING</div>
                            <ul className="text-xs text-[#7C9473] space-y-1 list-disc pl-4">
                              {selectedCandidate.confidence.explanations.map((exp: string, i: number) => (
                                <li key={i}>{exp}</li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        <div className="bg-[#F5F1E7] border border-[#C7BFA6] p-3 rounded flex flex-col">
                          <div className="text-xs text-[#7C9473] font-bold mb-2">HEX / ASCII PREVIEW</div>
                          {selectedCandidate.is_executable ? (
                            <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
                              <EyeOff className="w-8 h-8 text-red-500 mb-2" />
                              <div className="text-red-400 font-bold text-sm">PREVIEW BLOCKED</div>
                              <div className="text-gray-500 text-xs mt-1">Executable format detected. Excluded from rendering to prevent accidental exploitation.</div>
                            </div>
                          ) : (
                            <div className="font-mono text-xs text-[#7C9473] overflow-hidden opacity-50">
                              0x0000 4A 50 45 47 00 11 22 33 ... JPEG..""3<br/>
                              0x0008 44 55 66 77 88 99 AA BB ... DUfw.....<br/>
                              [Mock Hex Viewer Data]
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="mt-auto border-t border-[#C7BFA6] pt-4">
                        <label className="block text-sm text-[#7C9473] mb-1">Analyst Annotation / Bookmark</label>
                        <input 
                          type="text"
                          value={annotations[selectedCandidate.id] || ''}
                          onChange={e => setAnnotations({...annotations, [selectedCandidate.id]: e.target.value})}
                          placeholder="E.g., Suspicious payload hidden in slack space..."
                          className="w-full bg-[#F5F1E7] border border-[#C7BFA6] rounded px-3 py-2 text-[#2E2B26] text-sm"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow">
            <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2 mb-4">
              <FileText className="w-6 h-6" /> Evidentiary Export (Phase 4)
            </h3>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={redacted} onChange={e => setRedacted(e.target.checked)} className="w-5 h-5 rounded border-[#C7BFA6] text-[#7C9473]" />
                <div>
                  <div className="font-bold text-[#2E2B26]">Redact PII / Sensitive Data</div>
                  <div className="text-xs text-[#7C9473]">Generate a sanitized copy suitable for broad distribution.</div>
                </div>
              </label>
              <button 
                onClick={generateReport}
                className="bg-red-600 hover:bg-red-500 text-[#2E2B26] px-6 py-3 rounded font-bold flex items-center gap-2 shadow-lg"
              >
                <Download className="w-5 h-5" /> Generate Court-Ready Report
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-4 text-right">
              Requires <b>approve_reports</b> authorization tier.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}