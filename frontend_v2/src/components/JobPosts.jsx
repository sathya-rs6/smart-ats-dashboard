import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Plus, Briefcase, MapPin } from 'lucide-react';

export const JobPosts = ({ onOpenCreateModal, searchQuery = '' }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = () => {
    api.getJobs().then(data => {
      setJobs(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  };

  if (loading) return <div className="text-slate-500 p-8 flex justify-center">Loading jobs...</div>;

  const filteredJobs = jobs.filter(job => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const title = (job.title || '').toLowerCase();
    const company = (job.company || '').toLowerCase();
    const loc = (job.location || '').toLowerCase();
    const desc = (job.description || '').toLowerCase();
    return title.includes(q) || company.includes(q) || loc.includes(q) || desc.includes(q);
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20 mt-4">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-1">Active Job Posts</h2>
          <p className="text-slate-500">Manage your open positions and requirements.</p>
        </div>
        <button 
          onClick={onOpenCreateModal}
          className="flex items-center gap-2 bg-slate-900 text-white hover:bg-slate-800 transition-all px-6 py-3 rounded-2xl shadow-lg shadow-sm font-semibold active:scale-95"
        >
          <Plus size={20} />
          <span>Create Job</span>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {filteredJobs.map(job => (
          <div key={job.id} className="glass-card p-6 hover:border-slate-900/30 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold mb-1 group-hover:text-slate-900 transition-colors">{job.title}</h3>
                <div className="flex gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1"><Briefcase size={12} /> {job.company || 'Company'}</span>
                  <span className="flex items-center gap-1"><MapPin size={12} /> {job.location || 'Remote'}</span>
                </div>
              </div>
              <span className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider rounded-lg border border-emerald-500/20">
                Active
              </span>
            </div>
            <p className="text-sm text-slate-600 line-clamp-2 mb-4">
              {job.description}
            </p>
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-200">
              {(job.required_skills?.length > 0 ? job.required_skills : ['No skills specified']).map(skill => (
                <span key={skill} className="px-2 py-1 bg-slate-50 text-slate-600 text-[10px] font-medium rounded-md">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
        {filteredJobs.length === 0 && jobs.length > 0 && (
          <div className="col-span-2 p-12 text-center text-slate-500 glass-card">
            No job posts found matching '{searchQuery}'.
          </div>
        )}
        {jobs.length === 0 && (
          <div className="col-span-2 p-12 text-center text-slate-500 glass-card">
            No job posts created yet. Click "Create Job" to get started!
          </div>
        )}
      </div>
    </div>
  );
};
