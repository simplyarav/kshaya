import os

path = r'ui\src\App.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix App.tsx main export to include LandingPage
text = text.replace(\"import { ApiClient } from './apiClient';\", \"import { ApiClient } from './apiClient';\\nimport LandingPage from './components/LandingPage';\")

replacement = \"\"\"export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);
  const [showLanding, setShowLanding] = useState<boolean>(true);

  useEffect(() => {
    ApiClient.get('/core/setup/status')
      .then((data: any) => setIsInitialized(data.is_initialized))
      .catch(() => setIsInitialized(false));
  }, []);

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />;
  }

  if (isInitialized === null) return <div className="text-[#2E2B26] p-8 bg-[#EDE6D6] h-screen">Loading...</div>;\"\"\"

original = \"\"\"export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);

  useEffect(() => {
    ApiClient.get('/core/setup/status')
      .then((data: any) => setIsInitialized(data.is_initialized))
      .catch(() => setIsInitialized(false));
  }, []);

  if (isInitialized === null) return <div className="text-[#2E2B26] p-8 bg-[#EDE6D6] h-screen">Loading...</div>;\"\"\"

text = text.replace(original, replacement)

# Restore Police Sweep Colors
text = text.replace(\"className=\\\"absolute top-0 left-0 w-full bg-[#5C4033] transition-transform duration-300 ease-in-out z-10\\\"\", \"className=\\\"absolute top-0 left-0 w-full bg-[#2C425E] transition-transform duration-300 ease-in-out z-10\\\"\")
text = text.replace(\"className=\\\"absolute bottom-0 left-0 w-full h-1/2 bg-[#D2691E] transition-transform duration-300 ease-in-out z-0\\\"\", \"className=\\\"absolute bottom-0 left-0 w-full h-1/2 bg-[#D32F2F] transition-transform duration-300 ease-in-out z-0\\\"\")
text = text.replace(\"className=\\\"absolute bottom-0 left-0 w-full h-1/2 bg-[#8B5A2B] transition-transform duration-300 ease-in-out z-0\\\"\", \"className=\\\"absolute bottom-0 left-0 w-full h-1/2 bg-[#D32F2F] transition-transform duration-300 ease-in-out z-0\\\"\")
# The previous script might have replaced D32F2F with something else? No, D32F2F was untouched unless it was replaced manually. Let's make sure.

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
