import { useEffect, useState } from 'react'

function App() {
  // 1. Saari States ek saath
  const [attacks, setAttacks] = useState([])
  const [stats, setStats] = useState({ total_blocks: 0, unique_attackers: 0 })
  const [searchTerm, setSearchTerm] = useState("")

  // 2. Saare Functions ek saath
  const fetchAttacks = () => {
    fetch('http://localhost:8000/attacks')
      .then(res => res.json())
      .then(data => setAttacks(data))
      .catch(err => console.error("Backend offline", err))
  }

  const fetchStats = () => {
    fetch('http://localhost:8000/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Stats fetch failed", err))
  }

  const deleteAttack = async (id) => {
    if (!window.confirm("Remove this threat from dashboard?")) return;
    try {
      const response = await fetch(`http://localhost:8000/attacks/${id}`, { method: 'DELETE' });
      if (response.ok) {
        setAttacks(prev => prev.filter(a => a.id !== id));
        fetchStats(); // Delete ke baad stats refresh karo
      }
    } catch (err) { console.error(err) }
  };

  // 3. Ek hi useEffect kaafi hai dono ke liye
  useEffect(() => {
    fetchAttacks();
    fetchStats();
    const interval = setInterval(() => {
      fetchAttacks();
      fetchStats();
    }, 5000);
    return () => clearInterval(interval);
  }, [])

  // 4. Filter Logic
  const filteredAttacks = attacks.filter(attack => 
    attack.ip.toLowerCase().includes(searchTerm.toLowerCase()) || 
    attack.geo.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 5. Finally, the UI (Return)
  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 p-6 md:p-12 font-mono selection:bg-red-500/30">
      
      {/* HEADER SECTION */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div>
          <h1 className="text-5xl font-black tracking-tighter text-red-600 uppercase italic drop-shadow-[0_0_15px_rgba(220,38,38,0.5)]">
            L0gVigil
          </h1>
          <div className="flex items-center gap-2 mt-2">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
            <p className="text-slate-500 text-xs uppercase tracking-[0.2em]">Active Defense System Online</p>
          </div>
        </div>
        
        <div className="relative w-full md:w-96">
          <input 
            type="text" 
            placeholder="FILTER BY IP OR GEO..." 
            className="w-full bg-slate-900/50 border border-slate-800 p-3 pl-10 rounded-lg focus:outline-none focus:border-red-500/50 transition-all text-sm font-bold tracking-widest"
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <span className="absolute left-3 top-3.5 text-slate-600">🔍</span>
        </div>
      </header>

      {/* STATS SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-slate-900/40 backdrop-blur-md border border-red-900/20 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">🛡️</div>
          <p className="text-slate-500 text-[10px] font-bold uppercase tracking-[0.3em]">Total Blocks</p>
          <h2 className="text-5xl font-black mt-2 text-red-500">{stats.total_blocks}</h2>
        </div>
        
        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">👥</div>
          <p className="text-slate-500 text-[10px] font-bold uppercase tracking-[0.3em]">Unique Attackers</p>
          <h2 className="text-5xl font-black mt-2 text-blue-500">{stats.unique_attackers}</h2>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 p-6 rounded-2xl">
          <p className="text-slate-500 text-[10px] font-bold uppercase tracking-[0.3em]">System Health</p>
          <h2 className="text-3xl font-black mt-2 text-green-500 tracking-tighter">OPTIMAL</h2>
        </div>
      </div>

      {/* TABLE SECTION */}
      <div className="bg-slate-900/20 border border-slate-800 rounded-3xl overflow-hidden backdrop-blur-xl">
        <div className="bg-slate-800/30 p-5 border-b border-slate-800 flex justify-between items-center">
          <h3 className="font-black text-xs uppercase tracking-widest text-slate-400">Threat Intelligence Feed</h3>
          <span className="text-[10px] text-red-400 font-bold px-2 py-0.5 border border-red-400/30 rounded">AUTO-REFRESH: 5S</span>
        </div>

        <div className="max-h-125 overflow-y-auto custom-scrollbar divide-y divide-slate-800/50">
          {filteredAttacks.length > 0 ? (
            filteredAttacks.map((attack) => (
              <div key={attack.id} className="p-6 hover:bg-red-500/3 transition-all flex items-center justify-between group">
                <div className="flex gap-6 items-center">
                   <div className="w-10 h-10 rounded-full bg-red-900/20 flex items-center justify-center text-red-500 font-bold border border-red-900/30 shadow-[0_0_10px_rgba(220,38,38,0.2)]">!</div>
                   <div>
                    <span className="font-bold text-lg text-white tracking-wider font-mono">{attack.ip}</span>
                    <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-tight font-bold">{attack.geo}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="text-right hidden sm:block">
                    <p className="text-[10px] font-bold text-slate-600 uppercase tracking-tighter">Detection</p>
                    <p className="text-xs font-mono text-slate-400">{new Date(attack.blocked_at).toLocaleTimeString()}</p>
                  </div>
                  <button onClick={() => deleteAttack(attack.id)} className="p-3 bg-slate-800 text-slate-400 rounded-xl hover:bg-red-600 hover:text-white transition-all opacity-0 group-hover:opacity-100 shadow-xl">
                    🗑️
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="p-20 text-center text-slate-700 font-black text-2xl uppercase opacity-20 tracking-tighter italic">NO THREATS IN PERIMETER</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App