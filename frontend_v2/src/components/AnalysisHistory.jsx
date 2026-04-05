import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const AnalysisHistory = ({ searchQuery = '' }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalyses().then(data => {
      setHistory(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="text-slate-500 p-8 flex justify-center">Loading analysis history...</div>;

  const filteredHistory = history.filter(item => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const name = (item.candidate_name || '').toLowerCase();
    const job = (item.job_title || '').toLowerCase();
    return name.includes(q) || job.includes(q);
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20 mt-4">
      <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-6">Analysis History</h2>
      <div className="glass-card p-6 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
              <th className="px-6 py-4 font-semibold">Timestamp</th>
              <th className="px-6 py-4 font-semibold">Candidate</th>
              <th className="px-6 py-4 font-semibold">Role Tested Against</th>
              <th className="px-6 py-4 font-semibold">Score</th>
              <th className="px-6 py-4 font-semibold">Match Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredHistory.map(item => (
              <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                <td className="px-6 py-4 text-xs text-slate-500">{new Date(item.date).toLocaleString()}</td>
                <td className="px-6 py-4 font-semibold text-sm">{item.candidate_name}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{item.job_title}</td>
                <td className="px-6 py-4 font-bold text-slate-900">{item.overall_score}%</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-[10px] uppercase font-bold tracking-wider rounded-lg border ${item.match_level === 'high' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : item.match_level === 'medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-slate-500/10 text-slate-500 border-slate-500/20'}`}>
                    {item.match_level}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredHistory.length === 0 && history.length > 0 && <div className="p-8 text-center text-slate-500">No analyses found matching '{searchQuery}'.</div>}
        {history.length === 0 && <div className="p-8 text-center text-slate-500">No analyses have been run yet.</div>}
      </div>
    </div>
  );
};
