import os
import re

path = r'ui\src\components\SanitisationWizard.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove unused imports and vars
text = text.replace(\"import { HardDrive, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, Download, FileText } from 'lucide-react';\", \"import { HardDrive, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, Download } from 'lucide-react';\")
text = text.replace(\"const [dryRunComplete, setDryRunComplete] = useState(false);\", \"\")
text = text.replace(\"setDryRunComplete(true);\", \"\")
text = text.replace(\"const [manifest, setManifest] = useState<any | null>(null);\", \"\")
text = text.replace(\"setManifest(data);\", \"\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
