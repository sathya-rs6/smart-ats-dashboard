import React, { useState, useEffect } from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { 
  Users, 
  FileText, 
  Sparkles,
  Search,
  FilePlus,
  Upload,
  ArrowUpRight,
  Plus,
  LineChart as ChartIcon,
  Bot
} from 'lucide-react';
import { RankingTable } from './RankingTable';
import { UploadModal } from './UploadModal';
import { CandidateDetail } from './CandidateDetail';
import { ChatbotPane } from './ChatbotPane';
import { api } from '../services/api';

const defaultStats = {
  total_resumes: 0,
  total_jobs: 0,
  total_analyses: 0,
  distribution: { high: 0, medium: 0, low: 0 }
};

const data = [
  { name: 'High', count: 45 },
  { name: 'Med', count: 32 },
  { name: 'Low', count: 18 },
];

// mockCandidates removed

export const Dashboard = ({ onOpenCreateModal, setActiveTab, searchQuery = '' }) => {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  const [stats, setStats] = useState(defaultStats);
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [loading, setLoading] = useState(true);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const filteredCandidates = candidates.filter(c => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const name = (c.candidate_name || '').toLowerCase();
    const email = (c.candidate_email || '').toLowerCase();
    const file = (c.file_name || '').toLowerCase();
    const skills = (c.experience || []).join(' ').toLowerCase();
    return name.includes(q) || email.includes(q) || file.includes(q) || skills.includes(q);
  });

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const jobsData = await api.getJobs();
      setJobs(jobsData || []);
      
      const defaultJobId = jobsData?.length > 0 ? jobsData[0].id : "";
      setSelectedJobId(defaultJobId);

      const statsPromise = api.getDashboardStats();
      const rankingsPromise = defaultJobId ? api.getRankings(defaultJobId) : Promise.resolve({ rankings: [] });
      
      const [statsData, rankingsData] = await Promise.all([statsPromise, rankingsPromise]);
      
      setStats(statsData);

      if (rankingsData.rankings?.length > 0) {
        setCandidates(rankingsData.rankings);
        setSelectedCandidate(rankingsData.rankings[0]);
      } else {
        // Fallback: no job-specific rankings → show global top resumes
        try {
          const topData = await api.getTopResumes();
          setCandidates(topData.rankings || []);
          if (topData.rankings?.length > 0) {
            setSelectedCandidate(topData.rankings[0]);
          }
        } catch {
          setCandidates([]);
          setSelectedCandidate(null);
        }
      }
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
      setCandidates([]);
      setSelectedCandidate(null);
    } finally {
      setLoading(false);
    }
  };

  const handleJobChange = async (e) => {
    const jobId = e.target.value;
    setSelectedJobId(jobId);
    if (!jobId) return;
    try {
        setLoading(true);
        const rankingsData = await api.getRankings(jobId);
        let ranked = rankingsData.rankings || [];
        if (ranked.length === 0) {
          // Fallback to top resumes globally
          const topData = await api.getTopResumes();
          ranked = topData.rankings || [];
        }
        setCandidates(ranked);
        if (rankingsData.rankings?.length > 0) {
          setSelectedCandidate(rankingsData.rankings[0]);
        } else {
          setSelectedCandidate(null);
        }
    } catch (error) {
        console.error("Failed to fetch rankings for job:", error);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-20">
      {/* Header Section */}
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-900 mb-1">
            Recruiter Dashboard
          </h2>
          <p className="text-slate-500">Manage your candidates and analyze resumes with AI.</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={onOpenCreateModal}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-800 transition-colors px-6 py-3 rounded-2xl border border-slate-200 font-medium"
          >
            <FilePlus size={20} className="text-slate-500" />
            <span>Create Job</span>
          </button>
          <button 
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white transition-all px-6 py-3 rounded-2xl shadow-sm font-semibold active:scale-95"
          >
            <Upload size={20} />
            <span>Bulk Upload</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-6">
        <StatCard 
          title="Total Resumes" 
          value={stats.total_resumes} 
          change="+12.5%" 
          icon={<Users size={24} />} 
          secondary="Total across all jobs" 
          onClick={() => setActiveTab && setActiveTab('Candidates')}
        />
        <StatCard 
          title="Top Matches" 
          value={stats.distribution.high} 
          change="+5.2%" 
          icon={<Sparkles size={24} />} 
          secondary="High match level" 
        />
        <StatCard 
          title="Active Jobs" 
          value={stats.total_jobs} 
          change="+1" 
          icon={<FileText size={24} />} 
          secondary="Currently hiring" 
          onClick={() => setActiveTab && setActiveTab('Job Posts')}
        />
        <StatCard 
          title="Analyses Performed" 
          value={stats.total_analyses} 
          change="Trending" 
          icon={<ChartIcon size={24} />} 
          secondary="Total resume scans" 
          onClick={() => setActiveTab && setActiveTab('Analysis History')}
        />
      </div>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 space-y-8">
           {/* Chart */}
           <div className="glass-card p-8">
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-xl font-bold font-['Outfit']">Candidate Score Distribution</h3>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500">Current Job:</span>
                  <select 
                    value={selectedJobId}
                    onChange={handleJobChange}
                    className="bg-white border border-slate-200 rounded-xl px-4 py-1 text-sm outline-none text-slate-900">
                    {jobs.length > 0 ? jobs.map(job => (
                      <option key={job.id} value={job.id}>{job.title}</option>
                    )) : (
                      <option value="">No jobs available</option>
                    )}
                  </select>
                </div>
              </div>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={[
                    { name: 'High', count: stats.distribution.high },
                    { name: 'Med', count: stats.distribution.medium },
                    { name: 'Low', count: stats.distribution.low }
                  ]}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0f172a" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#0f172a" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', fontSize: '10px' }}
                      itemStyle={{ color: '#0f172a' }}
                    />
                    <Area type="monotone" dataKey="count" stroke="#0f172a" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Ranking Table */}
            <RankingTable candidates={filteredCandidates} onSelect={(c) => { setSelectedCandidate(c); setIsDetailOpen(true); }} selectedJobId={selectedJobId} />
            
            {/* Chat Sidebar Launcher */}
            <div className="flex justify-start">
               <button 
                  onClick={() => setIsChatOpen(true)}
                  className="group flex items-center gap-4 p-4 glass-card border-slate-200 hover:border-slate-300 transition-all text-left w-fit pr-8"
                >
                 <div className="p-3 bg-slate-900 rounded-2xl text-white shadow-sm group-hover:scale-110 transition-transform">
                   <Bot size={24} />
                 </div>
                 <div>
                   <h4 className="font-bold text-sm">Ask AI about {selectedCandidate?.candidate_name?.split(' ')[0] || 'Candidate'}</h4>
                   <p className="text-xs text-slate-500 mt-0.5 max-w-xs">Query specific skills or experience details directly from this candidate's resume.</p>
                 </div>
               </button>
            </div>
        </div>
      </div>

      {/* Modals & Overlays */}
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} onUploadComplete={loadDashboardData} />
      
      {isChatOpen && (
        <div className="fixed inset-y-0 right-0 w-[400px] z-[60] shadow-2xl">
          <ChatbotPane candidate={selectedCandidate} onClose={() => setIsChatOpen(false)} />
        </div>
      )}

      {/* Split-Screen Resume Detail Overlay */}
      {isDetailOpen && selectedCandidate && (
        <div className="fixed inset-0 z-[70] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="w-full max-w-[90vw] h-[90vh] bg-white rounded-3xl overflow-hidden shadow-2xl flex relative animate-fade-in">
            {/* Left Side: Physical Resume Viewer */}
            <div className="w-1/2 bg-slate-100 flex flex-col border-r border-slate-200">
              <div className="p-4 bg-slate-900 text-white flex justify-between items-center text-sm font-semibold">
                <span>Original Document</span>
                <span className="text-slate-400 font-normal">{selectedCandidate.file_name}</span>
              </div>
              <iframe 
                src={`http://localhost:8000/resumes/file/${selectedCandidate.resume_id}`} 
                className="flex-1 w-full border-none"
                title={`${selectedCandidate.candidate_name}'s Resume`}
              />
            </div>
            
            {/* Right Side: AI Insights */}
            <div className="w-1/2 relative bg-slate-50 overflow-y-auto custom-scrollbar">
              <button 
                onClick={() => setIsDetailOpen(false)} 
                className="absolute top-6 right-6 p-2 bg-white rounded-full text-slate-500 hover:text-slate-900 shadow-sm border border-slate-200 z-10 transition-colors"
                title="Close Profile"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
              <CandidateDetail candidate={selectedCandidate} onClose={() => setIsDetailOpen(false)} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard = ({ title, value, change, icon, secondary, onClick }) => (
  <div 
    onClick={onClick}
    className={`glass-card p-6 group transition-all duration-300 ${onClick ? 'cursor-pointer hover:border-slate-300 hover:bg-slate-50' : ''}`}
  >
    <div className="flex justify-between mb-4">
      <div className="p-3 bg-slate-100 rounded-2xl group-hover:bg-slate-200 transition-colors">
        {React.cloneElement(icon, { className: "text-slate-500 group-hover:text-slate-900 transition-colors" })}
      </div>
      <div className="flex items-center gap-1 text-emerald-600 text-sm font-medium bg-emerald-100 px-2 py-1 rounded-lg h-fit">
        <ArrowUpRight size={14} />
        {change}
      </div>
    </div>
    <p className="text-slate-600 text-sm mb-1">{title}</p>
    <h4 className="text-3xl font-bold mb-2 text-slate-900">{value}</h4>
    <p className="text-xs text-slate-500">{secondary}</p>
  </div>
);

const JobItem = ({ title, company, status, color }) => (
  <div className="flex items-center justify-between p-3 hover:bg-white/5 rounded-2xl transition-all cursor-pointer group">
    <div className="flex items-center gap-3">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <div>
        <p className="font-semibold text-sm group-hover:text-slate-900 transition-colors">{title}</p>
        <p className="text-xs text-slate-500">{company}</p>
      </div>
    </div>
    <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500">{status}</span>
  </div>
);

