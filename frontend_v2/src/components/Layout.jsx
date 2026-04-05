import React from 'react';
import { 
  History, 
  LayoutDashboard, 
  Settings, 
  Users, 
  FileText,
  Search,
  LogOut,
  Sparkles
} from 'lucide-react';

export const Layout = ({ children, activeTab, setActiveTab, searchQuery, setSearchQuery }) => {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-slate-200 p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="p-2 bg-white rounded-xl shadow-sm">
            <Sparkles size={24} className="text-white" />
          </div>
          <h1 className="text-xl font-bold font-['Outfit'] bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
            ResumeAI v2
          </h1>
        </div>

        <nav className="flex-1 space-y-2">
          <NavItem icon={<LayoutDashboard size={20} />} label="Dashboard" active={activeTab === 'Dashboard'} onClick={() => setActiveTab('Dashboard')} />
          <NavItem icon={<Users size={20} />} label="Candidates" active={activeTab === 'Candidates'} onClick={() => setActiveTab('Candidates')} />
          <NavItem icon={<FileText size={20} />} label="Job Posts" active={activeTab === 'Job Posts'} onClick={() => setActiveTab('Job Posts')} />
          <NavItem icon={<History size={20} />} label="Analysis History" active={activeTab === 'Analysis History'} onClick={() => setActiveTab('Analysis History')} />
        </nav>

        <div className="pt-6 border-t border-slate-200 space-y-2">
          <NavItem icon={<Settings size={20} />} label="Settings" active={activeTab === 'Settings'} onClick={() => setActiveTab('Settings')} />
          <NavItem icon={<LogOut size={20} />} label="Logout" onClick={() => { localStorage.clear(); window.location.reload(); }} />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-auto bg-slate-50">
        <header className="h-20 border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-10">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text" 
              value={searchQuery || ''}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search resumes or candidates..." 
              className="w-full bg-white border border-slate-300 rounded-2xl pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 outline-none transition-all text-slate-900 placeholder-slate-400"
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-900">Senior Recruiter</p>
              <p className="text-xs text-slate-500">Google DeepMind</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-slate-200 border-2 border-white flex items-center justify-center text-slate-500 font-bold">
              SR
            </div>
          </div>
        </header>
        
        <div className="p-8 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
};

const NavItem = ({ icon, label, active = false, onClick }) => (
  <button onClick={onClick} className={`
    w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all
    ${active 
      ? 'bg-slate-900 text-white shadow-sm' 
      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'}
  `}>
    {icon}
    <span>{label}</span>
  </button>
);
