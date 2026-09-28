import os
import re

path = r'ui\src\components\SanitisationWizard.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(\"import React, { useState, useEffect, useRef } from 'react';\", \"import React, { useState, useEffect } from 'react';\\nimport { ApiClient } from '../apiClient';\")
content = content.replace(\"const pollInterval = useRef<any>(null);\", \"\")
content = content.replace(\"pollInterval.current = setInterval(() => pollJobStatus(data.job_id), 2000);\",
\"\"\"      // Wait for WS broadcast instead of polling
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
              setError(\"Job failed: \" + (msg.details.error || 'Unknown'));
            }
          }
        }
      };
      window.addEventListener('kshaya:job_update', handleJobUpdate);\"\"\")

# Remove useEffect block
content = re.sub(r'\\s*useEffect\\(\\(\\) => \\{\\s*return \\(\\) => \\{\\s*if \\(pollInterval\\.current\\) clearInterval\\(pollInterval\\.current\\);\\s*\\};\\s*\\}, \\[\\]\\);', '', content, flags=re.MULTILINE)

# Replace fetch calls with ApiClient
content = re.sub(r'fetch\\(\\'([^\\']+)\\',\\s*\\{.*?\\}\\)', r\"ApiClient.get('\\1')\", content, flags=re.DOTALL)
content = re.sub(r'fetch\\(([^]+),\\s*\\{\\s*headers.*?\\}\\)', r\"ApiClient.get(\\1)\", content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Script finished')
