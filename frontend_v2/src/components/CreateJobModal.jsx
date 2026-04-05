import React, { useState } from 'react';
import { X, Loader2, FilePlus } from 'lucide-react';
import { api } from '../services/api';

export const CreateJobModal = ({ isOpen, onClose, onJobCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createJob(formData);
      if (onJobCreated) onJobCreated();
      onClose();
    } catch (error) {
      console.error("Failed to create job:", error);
      alert('Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-[#0f172a] border border-slate-200 w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden animate-scale-in">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-100 text-slate-900 rounded-xl">
               <FilePlus size={24} />
            </div>
            <h3 className="text-xl font-bold">Create New Job Post</h3>
          </div>
          <button type="button" onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-colors">
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Job Title</label>
              <input required type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 outline-none" placeholder="e.g. Senior AI Engineer" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</label>
              <input required type="text" value={formData.company} onChange={e => setFormData({...formData, company: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 outline-none" placeholder="e.g. ExampleCorp" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Location</label>
            <input required type="text" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 outline-none" placeholder="e.g. Remote, New York..." />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Description & Requirements</label>
            <p className="text-[10px] text-slate-900 mb-2">Our AI will automatically extract required skills and experience from the description.</p>
            <textarea required value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} rows={6} className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 outline-none resize-none" placeholder="Paste the full job description here..." />
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-6 py-3 rounded-xl font-medium text-slate-600 hover:bg-white/5 transition-colors">Cancel</button>
            <button type="submit" disabled={loading} className="px-6 py-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-xl font-medium shadow-lg shadow-sm transition-all flex items-center gap-2">
              {loading ? <Loader2 size={18} className="animate-spin" /> : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
