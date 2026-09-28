import React, { useState } from 'react';
import { Search } from 'lucide-react';

export default function GlobalSearch({ token }: { token: string }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const res = await fetch(`/api/core/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setResults(data.audit_results || []);
      setIsOpen(true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="relative w-96">
      <form onSubmit={handleSearch} className="relative">
        <Search className="w-5 h-5 absolute left-3 top-2.5 text-gray-500" />
        <input 
          type="text" 
          placeholder="Search jobs, cases, audit logs..."
          className="w-full bg-[#EDE6D6] border border-[#C7BFA6] rounded-full py-2 pl-10 pr-4 text-sm text-[#2E2B26] focus:border-[#7C9473] outline-none"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => { if(results.length > 0) setIsOpen(true) }}
        />
      </form>

      {isOpen && (
        <div className="absolute top-12 left-0 w-full bg-[#F5F1E7] border border-[#C7BFA6] rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
          <div className="p-2 flex justify-between items-center border-b border-[#C7BFA6]">
            <span className="text-xs text-[#7C9473] font-bold uppercase">Results</span>
            <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-[#2E2B26] text-xs">Close</button>
          </div>
          {results.length === 0 ? (
            <div className="p-4 text-sm text-[#7C9473] text-center">No results found for "{query}".</div>
          ) : (
            <ul className="divide-y divide-gray-800">
              {results.map(r => (
                <li key={r.id} className="p-3 hover:bg-[#DCD4C0] cursor-pointer">
                  <div className="text-sm font-semibold text-[#4A3B32]">{r.action}</div>
                  <div className="text-xs text-gray-500">Event #{r.id} • Actor: {r.actor}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
