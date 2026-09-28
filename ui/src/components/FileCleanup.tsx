import React, { useState, useEffect, useRef } from 'react';
import { FolderSearch, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, Download, FileWarning, Shield, ShieldAlert } from 'lucide-react';

type Step = 'SELECT_FILES' | 'PREVIEW_TRIAGE' | 'METHOD_SELECT' | 'EXECUTE' | 'COMPLETE';

export default function FileCleanup({ token }: { token: string }) {
  const [step, setStep] = useState<Step>('SELECT_FILES');
  
  const [paths, setPaths] = useState<string[]>([]);
  const [previewData, setPreviewData] = useState<any | null>(null);
  
  const [reviewItems, setReviewItems] = useState<any[]>([]);
  const [role, setRole] = useState<string>('');
  
  const [method, setMethod] = useState<string>('logical_overwrite');
  const [quarantine, setQuarantine] = useState<boolean>(false);
  const [overrideCloudSync, setOverrideCloudSync] = useState<boolean>(false);
  
  const [error, setError] = useState<string | null>(null);
  
  const [jobId, setJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [certId, setCertId] = useState<number | null>(null);
  const [manifest, setManifest] = useState<any | null>(null);

  const pollInterval = useRef<any>(null);

  useEffect(() => {
    // Decode JWT payload safely to get role (without external libs for this mock)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      // The backend assigns role name in token upon login.
    } catch(e) {}
    // In our mock, everyone logs in as Admin by default.
    setRole('Admin');
  }, [token]);

  const handleSimulateTauriPicker = () => {
    const mockPaths = [
      "C:\\Users\\MockUser\\Documents\\Sensitive_Tax_Return_2024.pdf",
      "C:\\Users\\MockUser\\OneDrive\\CloudSynced_Project.docx",
      "C:\\Temp\\BrowserCache\\data.bin"
    ];
    setPaths(mockPaths);
  };

  const loadPreview = async () => {
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/file-erasure/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ paths })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Preview failed");
      
      setPreviewData(data);
      await fetchReviewQueue();
      setStep('PREVIEW_TRIAGE');
    } catch (e: any) {
      setError(e.message);
    }
  };

  const fetchReviewQueue = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/file-erasure/review-queue', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        setReviewItems(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleApproveReview = async (id: number) => {
    try {
      const res = await fetch(`/api/file-erasure/review-queue/${id}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        await fetchReviewQueue();
      } else {
        const data = await res.json();
        setError(`Failed to approve: ${data.detail}`);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleExecute = async () => {
    if (reviewItems.length > 0) {
      setError("Cannot proceed: Items in the Review Queue must be approved first.");
      return;
    }
    
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/file-erasure/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          paths: paths,
          method: method,
          quarantine: quarantine,
          override_cloud_sync: overrideCloudSync
        })
      });
      
      const data = await res.json();
      if (!res.ok) {
        if (Array.isArray(data.detail)) {
          throw new Error(data.detail.map((d: any) => d.msg).join(", "));
        }
        throw new Error(data.detail || "Execution failed");
      }
      
      setJobId(data.job_id);
      setJobStatus('in_progress');
      setStep('EXECUTE');
      
      pollInterval.current = setInterval(() => pollJobStatus(data.job_id), 2000);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const pollJobStatus = async (id: number) => {
    try {
      const res = await fetch(`/api/file-erasure/jobs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (res.ok) {
        setJobStatus(data.status);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(pollInterval.current);
          if (data.status === 'completed') {
            setCertId(data.certificate_id);
            fetchReceipt(data.certificate_id);
          } else {
            setError("Job failed during execution.");
          }
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchReceipt = async (id: number) => {
    try {
      const res = await fetch(`/api/file-erasure/receipts/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setManifest(data);
      } else {
        setError(`Receipt fetch failed: ${res.status}`);
      }
      setStep('COMPLETE');
    } catch (e: any) {
      setError(e.message);
      setStep('COMPLETE');
    }
  };

  const handleDownload = async () => {
    try {
      const res = await fetch(`/api/file-erasure/receipts/${certId}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to download PDF");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KSHAYA_File_Receipt_${certId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, []);

  return (
    <div className="space-y-6 pb-20">
      <h2 className="text-3xl font-bold text-[#2E2B26] mb-6">Targeted File Cleanup</h2>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {step === 'SELECT_FILES' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26]">Step 1: Select Targets</h3>
          
          <div className="border-2 border-dashed border-[#C7BFA6] rounded-lg p-10 text-center">
            <FolderSearch className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-[#7C9473] mb-6">Select files or folders for targeted erasure.</p>
            <button 
              onClick={handleSimulateTauriPicker}
              className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] px-6 py-2 rounded font-bold"
            >
              Browse OS Native File Picker...
            </button>
            <p className="text-xs text-gray-600 mt-2">(Simulates Tauri native dialog for demo)</p>
          </div>
          
          {paths.length > 0 && (
            <div className="bg-[#EDE6D6] p-4 rounded border border-[#C7BFA6]">
              <h4 className="text-[#7C9473] text-sm font-bold mb-2">Selected Paths:</h4>
              <ul className="text-sm text-[#7C9473] font-mono space-y-1">
                {paths.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          )}

          <div className="flex justify-end pt-4 border-t border-[#C7BFA6]">
            <button 
              onClick={loadPreview} 
              disabled={paths.length === 0} 
              className="bg-[#7C9473] disabled:bg-[#DCD4C0] hover:bg-[#5F7562] text-[#2E2B26] px-6 py-2 rounded font-bold"
            >
              Preview & Triage <ArrowRight className="w-4 h-4 inline ml-2" />
            </button>
          </div>
        </div>
      )}

      {step === 'PREVIEW_TRIAGE' && (
        <div className="space-y-6">
          <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow">
            <h3 className="text-xl font-semibold text-[#2E2B26] mb-4">Step 2: Preview & Triage</h3>
            
            <div className="flex gap-4 mb-6">
              <div className="bg-[#DCD4C0] p-4 rounded flex-1">
                <div className="text-sm text-[#7C9473]">Total Items</div>
                <div className="text-2xl font-bold text-[#2E2B26]">{previewData?.total_files}</div>
              </div>
              <div className="bg-[#DCD4C0] p-4 rounded flex-1">
                <div className="text-sm text-[#7C9473]">Total Size</div>
                <div className="text-2xl font-bold text-[#2E2B26]">{(previewData?.total_size_bytes / (1024*1024)).toFixed(2)} MB</div>
              </div>
            </div>

            <div className="h-48 overflow-y-auto bg-[#EDE6D6] border border-[#C7BFA6] rounded mb-6">
              <table className="w-full text-left text-sm text-[#7C9473]">
                <thead className="bg-[#DCD4C0] sticky top-0">
                  <tr>
                    <th className="px-4 py-2">Path</th>
                    <th className="px-4 py-2">Flags</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {previewData?.items?.map((item: any, idx: number) => {
                    const isCloud = item.path.toLowerCase().includes('onedrive') || item.path.toLowerCase().includes('dropbox');
                    return (
                      <tr key={idx}>
                        <td className="px-4 py-2 font-mono text-xs">{item.path}</td>
                        <td className="px-4 py-2">
                          {isCloud && <span className="bg-yellow-900/50 text-yellow-400 px-2 py-1 rounded text-xs">Cloud Sync Detected</span>}
                        </td>
                      </tr>
                    );
                  })}
                  {previewData?.items?.length === 0 && <tr><td colSpan={2} className="p-4 text-center text-gray-500">No verifiable files found at selected paths.</td></tr>}
                </tbody>
              </table>
            </div>

            {reviewItems.length > 0 && (
              <div className="bg-orange-950/30 border border-orange-900/50 rounded-lg p-4 mb-6">
                <h4 className="text-orange-400 font-bold flex items-center gap-2 mb-3">
                  <ShieldAlert className="w-5 h-5" /> Mandatory Review Queue
                </h4>
                <p className="text-sm text-[#7C9473] mb-3">
                  Classifiers have flagged some files for PII, financial data, or preservation hold. An Approver must sign off before these can be erased.
                </p>
                <div className="space-y-2">
                  {reviewItems.map(item => (
                    <div key={item.id} className="flex justify-between items-center bg-[#F5F1E7] border border-[#C7BFA6] p-3 rounded">
                      <div>
                        <div className="font-mono text-xs text-[#7C9473]">{item.file_path}</div>
                        <div className="text-xs text-red-400">{item.flag_reason}</div>
                      </div>
                      <button 
                        onClick={() => handleApproveReview(item.id)}
                        className="bg-green-700 hover:bg-green-600 text-[#2E2B26] text-xs px-4 py-2 rounded font-bold"
                      >
                        Approve Exception
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4 border-t border-[#C7BFA6]">
              <button onClick={() => setStep('SELECT_FILES')} className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2">Back</button>
              <button 
                onClick={() => setStep('METHOD_SELECT')} 
                disabled={reviewItems.length > 0}
                className="bg-[#7C9473] disabled:bg-[#DCD4C0] hover:bg-[#5F7562] text-[#2E2B26] px-6 py-2 rounded font-bold"
              >
                Configure Run <ArrowRight className="w-4 h-4 inline ml-2" />
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'METHOD_SELECT' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26]">Step 3: Configuration & Integrity</h3>

          <div className="bg-[#DCD4C0] p-4 rounded space-y-4">
            <h4 className="text-[#4A3B32] font-bold">Action Type</h4>
            <div className="flex gap-4">
              <label className={`flex-1 border p-4 rounded cursor-pointer ${!quarantine ? 'border-[#7C9473] bg-[#7C9473]/20' : 'border-[#C7BFA6] bg-[#F5F1E7]'}`}>
                <input type="radio" name="action" checked={!quarantine} onChange={() => setQuarantine(false)} className="hidden" />
                <div className="font-bold text-[#2E2B26] mb-1">Logical Overwrite</div>
                <div className="text-xs text-[#7C9473]">Standard file-level cryptographic zeroing and OS fsync purge.</div>
              </label>
              <label className={`flex-1 border p-4 rounded cursor-pointer ${quarantine ? 'border-[#7C9473] bg-[#7C9473]/20' : 'border-[#C7BFA6] bg-[#F5F1E7]'}`}>
                <input type="radio" name="action" checked={quarantine} onChange={() => setQuarantine(true)} className="hidden" />
                <div className="font-bold text-[#2E2B26] mb-1">Quarantine</div>
                <div className="text-xs text-[#7C9473]">Move files to the secure KSHAYA vault instead of deleting them.</div>
              </label>
            </div>
          </div>

          <div className="bg-[#DCD4C0] p-4 rounded">
            <label className="flex items-center gap-3">
              <input type="checkbox" checked={overrideCloudSync} onChange={(e) => setOverrideCloudSync(e.target.checked)} className="w-5 h-5 rounded border-[#C7BFA6] text-[#7C9473] focus:ring-[#7C9473]" />
              <div>
                <div className="font-bold text-[#2E2B26]">Override Cloud Sync Block</div>
                <div className="text-xs text-[#7C9473]">WARNING: This logs an auditable exception. Erasing active cloud sync directories may propagate permanent deletions to cloud replicas.</div>
              </div>
            </label>
          </div>

          <div className="bg-[#EDE6D6] border border-[#C7BFA6] p-4 rounded">
            <h4 className="text-[#7C9473] text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
              <Shield className="w-4 h-4" /> Integrity Notice
            </h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              KSHAYA's file-level erasure utilizes native OS I/O primitives followed by forced cache flushes (`fsync`). 
              However, modern SSD wear-leveling algorithms, filesystem journaling (NTFS/ext4), and Copy-on-Write (CoW) snapshots 
              may retain orphaned block remnants invisibly to the OS. 
              <br/><br/>
              <b>Do not imply or guarantee to clients that file-level overwrite secures data against advanced hardware-level forensic recovery.</b> For cryptographically guaranteed destruction, utilize Module 1: Full Disk Sanitisation.
            </p>
          </div>

          <div className="flex justify-between pt-4 border-t border-[#C7BFA6]">
            <button onClick={() => setStep('PREVIEW_TRIAGE')} className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2">Back</button>
            <button 
              onClick={handleExecute} 
              className="bg-red-600 hover:bg-red-500 text-[#2E2B26] px-6 py-2 rounded font-bold flex items-center gap-2"
            >
              Execute Workflow <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {step === 'EXECUTE' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-10 shadow text-center space-y-6">
          <RefreshCw className="w-16 h-16 text-[#7C9473] animate-spin mx-auto" />
          <h3 className="text-2xl font-bold text-[#2E2B26]">Execution In Progress</h3>
          <p className="text-[#7C9473] font-mono">Job ID: {jobId} | Status: {jobStatus}</p>
          <div className="w-full bg-[#DCD4C0] rounded-full h-2 mt-4">
            <div className="bg-blue-500 h-2 rounded-full w-2/3 animate-pulse"></div>
          </div>
        </div>
      )}

      {step === 'COMPLETE' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-8 shadow space-y-6">
          <div className="flex items-center gap-4 text-green-400 mb-6 border-b border-[#C7BFA6] pb-4">
            <CheckCircle className="w-10 h-10" />
            <h3 className="text-2xl font-bold text-[#2E2B26]">Workflow Complete</h3>
          </div>
          
          <div className="bg-[#EDE6D6] border border-[#C7BFA6] rounded p-4 font-mono text-xs text-[#7C9473] h-48 overflow-y-auto">
            {manifest && JSON.stringify(manifest, null, 2)}
          </div>

          <div className="flex justify-between pt-4">
            <button 
              onClick={() => {
                setStep('SELECT_FILES');
                setPaths([]);
              }} 
              className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2"
            >
              Start New Job
            </button>
            {certId && (
              <button 
                onClick={handleDownload}
                className="bg-green-600 hover:bg-green-500 text-[#2E2B26] px-6 py-2 rounded font-bold flex items-center gap-2"
              >
                <Download className="w-5 h-5" /> Download PDF Receipt
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}