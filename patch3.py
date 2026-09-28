import os
import re

# Fix App.tsx
path = r'ui\src\App.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(\"function AppContent({ token, setToken }: { token: string | null, setToken: any })\", \"function AppContent({ token, setToken }: { token: string, setToken: any })\")
text = text.replace(\"bg-gray-950 text-gray-100\", \"bg-[#EDE6D6] text-[#2E2B26]\")
text = text.replace(\"bg-gray-900 border-r border-gray-800\", \"bg-[#DCD4C0] border-r border-[#C7BFA6]\")
text = text.replace(\"bg-gray-900 border-b border-gray-800\", \"bg-[#DCD4C0] border-b border-[#C7BFA6]\")
text = text.replace(\"bg-gray-800 text-blue-400\", \"bg-[#2C425E] text-white\")
text = text.replace(\"hover:bg-gray-800 text-gray-100\", \"hover:bg-[#C7BFA6] text-[#2E2B26]\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

# Fix SanitisationWizard.tsx
path = r'ui\src\components\SanitisationWizard.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace(\"export default function SanitisationWizard({ token }: { token: string })\", \"export default function SanitisationWizard({ token }: { token?: string })\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
