import React, { useState, useEffect } from 'react';
import { ApiClient } from '../apiClient';
import { HardDrive, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, Download } from 'lucide-react';

type Step = 'SELECT_DRIVE' | 'SELECT_METHOD' | 'DRY_RUN' | 'CONFIRM_SERIAL' | 'EXECUTE' | 'COMPLETE';

export default function SanitisationWizard({ token }: any) {
  const [step, setStep] = useState<Step>('SELECT_DRIVE');
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<any | null>(null);
  
  const [capabilities, setCapabilities] = useState<any | null>(null);
  const [recommendedMethods, setRecommendedMethods] = useState<string[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  
  const [dryRunComplete, setDryRunComplete] = useState(false);
  const [serialInput, setSerialInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const [jobId, setJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [certId, setCertId] = useState<number | null>(null);
  const [manifest, setManifest] = useState<any | null>(null);

  useEffect(() => {
    ApiClient.get('/drive-erasure/devices')
      .then((data: any) => setDevices(data.devices || []))
      .catch(err => setError("Failed to load devices"));
  }, []);

  const handleSelectDevice = async (dev: any) => {
    setSelectedDevice(dev);
    setError(null);
    try {
      const data = await ApiClient.get(`/drive-erasure/devices/${dev.device_id}/capability`);
      setCapabilities(data.capabilities);
      setRecommendedMethods(data.recommended_methods);
      if (data.recommended_methods.length > 0) setSelectedMethod(data.recommended_methods[0]);
      setStep('SELECT_METHOD');
    } catch (e: any) {
      setError(e.message);
    }
  };

  const runDryRun = async () => {
    setError(null);
    try {
      await ApiClient.post('/drive-erasure/jobs/dry-run', { device_id: selectedDevice.device_id });
      
      // Security Check: Re-fetch devices to ensure serial hasn't changed before confirming
      const devData: any = await ApiClient.get('/drive-erasure/devices');
      const currentDev = (devData.devices || []).find((d: any) => d.device_id === selectedDevice.device_id);
      
      if (!currentDev || currentDev.serial !== selectedDevice.serial) {
        throw new Error("Device serial mismatch detected! Device may have been swapped.");
      }

      setDryRunComplete(true);
      setStep('CONFIRM_SERIAL');
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleExecute = async () => {
    setError(null);
    try {
      // Security Check: Re-fetch devices to ensure serial hasn't changed before executing
      const devData: any = await ApiClient.get('/drive-erasure/devices');
      const currentDev = (devData.devices || []).find((d: any) => d.device_id === selectedDevice.device_id);
      
      if (!currentDev || currentDev.serial !== selectedDevice.serial) {
        throw new Error("Device serial mismatch detected! Device may have been swapped.");
      }

      if (serialInput !== currentDev.serial) {
        throw new Error("Typed serial does not match actual device serial.");
      }

      const data = await ApiClient.post('/drive-erasure/jobs/execute', {
        device_id: selectedDevice.device_id,
        method: selectedMethod,
        confirmed_serial: serialInput
      });
      
      setJobId(data.job_id);
      setJobStatus('in_progress');
      setStep('EXECUTE');
      
      // Wait for WS broadcast instead of polling (Constraint 2: Single Source of Truth)
      const handleJobUpdate = (e: any) => {
        const msg = e.detail;
        if (msg.job_id === data.job_id) {
          setJobStatus(msg.status);
          if (msg.status === 'completed' || msg.status === 'failed') {
            window.removeEventListener('kshaya:job_update', handleJobUpdate);
            if (msg.status === 'completed') {
              setCertId(msg.details.certificate_id);
              fetchCertificate(msg.details.certificate_id);
            } else {
              setError("Job failed: " + (msg.details.error || 'Unknown error'));
            }
          }
        }
      };
      window.addEventListener('kshaya:job_update', handleJobUpdate);
      
    } catch (e: any) {
      setError(e.message);
    }
  };

  const fetchCertificate = async (id: number) => {
    try {
      const data = await ApiClient.get(`/drive-erasure/certificates/${id}`);
      setManifest(data);
      setStep('COMPLETE');
    } catch (e: any) {
      setError(`Certificate error: ${e.message}`);
      setStep('COMPLETE');
    }
  };

  const handleDownload = async () => {
    try {
      const res: any = await ApiClient.get(`/drive-erasure/certificates/${certId}/download`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KSHAYA_Cert_${certId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-[#2E2B26] mb-6">Sanitisation Wizard</h2>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {step === 'SELECT_DRIVE' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow">
          <h3 className="text-xl font-semibold text-[#2E2B26] mb-4">Step 1: Select Target Device</h3>
          <div className="space-y-4">
            {devices.map(dev => (
              <div 
                key={dev.device_id} 
                onClick={() => handleSelectDevice(dev)}
                className="flex items-center justify-between p-4 bg-[#DCD4C0] rounded border border-[#C7BFA6] hover:border-[#7C9473] cursor-pointer transition"
              >
                <div className="flex items-center gap-4">
                  <HardDrive className="w-8 h-8 text-[#7C9473]" />
                  <div>
                    <div className="font-bold text-[#4A3B32]">{dev.model}</div>
                    <div className="text-sm text-[#7C9473] font-mono">ID: {dev.device_id} | Serial: {dev.serial} | {dev.type}</div>
                  </div>
                </div>
                <div className="text-[#7C9473] font-semibold text-lg">
                  {Math.round(dev.capacity_bytes / (1024*1024*1024))} GB
                </div>
              </div>
            ))}
            {devices.length === 0 && <div className="text-gray-500">Scanning for securely attached devices...</div>}
          </div>
        </div>
      )}

      {step === 'SELECT_METHOD' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26]">Step 2: Select Sanitisation Method</h3>
          
          <div className="bg-[#DCD4C0] p-4 rounded text-sm text-[#7C9473]">
            <strong>Target:</strong> {selectedDevice?.model} (SN: {selectedDevice?.serial})
          </div>

          <div>
            <h4 className="text-[#7C9473] uppercase text-xs font-bold tracking-wider mb-3">Hardware Capabilities</h4>
            <ul className="space-y-1 text-sm text-[#7C9473]">
              <li>ATA Sanitize Support: {capabilities?.ata_sanitize_supported ? '✅' : '❌'}</li>
              <li>NVMe Sanitize Support: {capabilities?.nvme_sanitize_supported ? '✅' : '❌'}</li>
              <li>Crypto Erase Support: {capabilities?.crypto_erase_supported ? '✅' : '❌'}</li>
            </ul>
          </div>

          <div>
            <h4 className="text-[#7C9473] uppercase text-xs font-bold tracking-wider mb-3">Recommended Methods</h4>
            <div className="space-y-3">
              {recommendedMethods.map(method => (
                <label key={method} className={`flex items-start gap-3 p-4 rounded border cursor-pointer transition ${selectedMethod === method ? 'border-[#7C9473] bg-[#7C9473]/20' : 'border-[#C7BFA6] bg-[#DCD4C0]'}`}>
                  <input 
                    type="radio" 
                    name="method" 
                    value={method} 
                    checked={selectedMethod === method}
                    onChange={(e) => setSelectedMethod(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-bold text-[#4A3B32]">{method}</div>
                    <div className="text-sm text-[#7C9473]">Cryptographically guaranteed erasure method compatible with hardware interface.</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-[#C7BFA6]">
            <button onClick={() => setStep('SELECT_DRIVE')} className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2">Back</button>
            <button onClick={() => setStep('DRY_RUN')} disabled={!selectedMethod} className="bg-[#7C9473] hover:bg-[#5F7562] text-[#2E2B26] px-6 py-2 rounded font-bold">
              Proceed to Safety Check
            </button>
          </div>
        </div>
      )}

      {step === 'DRY_RUN' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26]">Step 3a: Mandatory Dry Run Simulation</h3>
          <p className="text-[#7C9473]">
            Before proceeding, KSHAYA must execute a non-destructive dry-run to verify write-blocker states and hardware communication channels.
          </p>
          <div className="flex justify-between pt-4 border-t border-[#C7BFA6]">
            <button onClick={() => setStep('SELECT_METHOD')} className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2">Back</button>
            <button onClick={runDryRun} className="bg-yellow-600 hover:bg-yellow-500 text-[#2E2B26] px-6 py-2 rounded font-bold">
              Execute Dry Run
            </button>
          </div>
        </div>
      )}

      {step === 'CONFIRM_SERIAL' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-6 shadow space-y-6">
          <h3 className="text-xl font-semibold text-[#2E2B26] flex items-center gap-2">
            <CheckCircle className="text-green-500 w-6 h-6" /> Step 3b: Dry Run Passed
          </h3>
          <div className="bg-red-900/20 border border-red-800 rounded p-4">
            <h4 className="text-red-400 font-bold mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> DANGER: Destructive Operation
            </h4>
            <p className="text-sm text-red-200 mb-4">
              You are about to irreversibly destroy all data on the target drive. To proceed, you must manually type the exact serial number of the drive.
            </p>
            <div className="text-[#7C9473] font-mono bg-[#EDE6D6] p-2 text-center text-lg mb-4 tracking-widest border border-[#C7BFA6]">
              {selectedDevice?.serial}
            </div>
            <input 
              type="text" 
              value={serialInput}
              onChange={(e) => setSerialInput(e.target.value)}
              placeholder="Type serial number here..."
              className="w-full bg-[#EDE6D6] border border-[#C7BFA6] text-[#2E2B26] px-4 py-2 rounded font-mono text-center"
            />
          </div>

          <div className="flex justify-between pt-4 border-t border-[#C7BFA6]">
            <button onClick={() => {setStep('DRY_RUN'); setDryRunComplete(false);}} className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2">Back</button>
            <button 
              onClick={handleExecute} 
              disabled={serialInput !== selectedDevice?.serial}
              className="bg-red-600 disabled:bg-gray-700 hover:bg-red-500 text-[#2E2B26] px-6 py-2 rounded font-bold flex items-center gap-2"
            >
              Destroy Data <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {step === 'EXECUTE' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-10 shadow text-center space-y-6">
          <RefreshCw className="w-16 h-16 text-[#7C9473] animate-spin mx-auto" />
          <h3 className="text-2xl font-bold text-[#2E2B26]">Sanitisation In Progress</h3>
          <p className="text-[#7C9473] font-mono">Job ID: {jobId} | Status: {jobStatus}</p>
          <div className="w-full bg-[#DCD4C0] rounded-full h-2 mt-4">
            <div className="bg-blue-500 h-2 rounded-full w-2/3 animate-pulse"></div>
          </div>
          <p className="text-sm text-gray-500">Do not disconnect the drive or power off the system.</p>
        </div>
      )}

      {step === 'COMPLETE' && (
        <div className="bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg p-8 shadow space-y-6">
          <div className="flex items-center gap-4 text-green-400 mb-6 border-b border-[#C7BFA6] pb-4">
            <CheckCircle className="w-10 h-10" />
            <h3 className="text-2xl font-bold text-[#2E2B26]">Sanitisation Complete</h3>
          </div>
          
          <div className="bg-[#EDE6D6] border border-[#C7BFA6] rounded p-4 font-mono text-xs text-[#7C9473] h-48 overflow-y-auto">
            {manifest && JSON.stringify(manifest, null, 2)}
          </div>

          <div className="flex justify-between pt-4">
            <button 
              onClick={() => {
                setStep('SELECT_DRIVE');
                setSelectedDevice(null);
                setSerialInput('');
                setDryRunComplete(false);
              }} 
              className="text-[#7C9473] hover:text-[#2E2B26] px-4 py-2"
            >
              Start New Job
            </button>
            <button 
              onClick={handleDownload}
              className="bg-green-600 hover:bg-green-500 text-[#2E2B26] px-6 py-2 rounded font-bold flex items-center gap-2"
            >
              <Download className="w-5 h-5" /> Download PDF Certificate
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
