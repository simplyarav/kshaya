import os

path = r'ui\src\components\SanitisationWizard.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace device fetch capability
text = text.replace(
\"\"\"const res = await fetch(\/api/drive-erasure/devices/\/capability\, {
        headers: { Authorization: \Bearer \\ }
      });
      if (!res.ok) throw new Error(\"Failed to load capabilities\");
      const data = await res.json();\"\"\",
\"\"\"const data = await ApiClient.get(\/drive-erasure/devices/\/capability\);\"\"\"
)

# Replace dry-run POST
text = text.replace(
\"\"\"const res = await fetch('/api/drive-erasure/jobs/dry-run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: \Bearer \\ },
        body: JSON.stringify({
          device_id: selectedDevice.device_id,
          method: selectedMethod
        })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || \"Dry run failed\");\"\"\",
\"\"\"const data = await ApiClient.post('/drive-erasure/jobs/dry-run', {
        device_id: selectedDevice.device_id,
        method: selectedMethod
      });\"\"\"
)

# Replace security checks re-fetching devices
text = text.replace(
\"\"\"const devRes = await fetch('/api/drive-erasure/devices', { headers: { Authorization: \Bearer \\ } });
      const devData = await devRes.json();\"\"\",
\"\"\"const devData: any = await ApiClient.get('/drive-erasure/devices');\"\"\"
)


with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print(\"Patched fetch calls.\")
