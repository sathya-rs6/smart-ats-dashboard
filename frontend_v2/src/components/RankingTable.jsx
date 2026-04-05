import React, { useState } from 'react';
import { 
  Trophy, 
  ExternalLink, 
  Mail, 
  MoreHorizontal,
  ChevronRight,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

export const RankingTable = ({ candidates = [], onSelect, selectedJobId }) => {
  const [emailing, setEmailing] = useState({});
  const [openMenuId, setOpenMenuId] = useState(null);

  const handleEmail = async (candidate, e) => {
    e.stopPropagation();
    if (!selectedJobId || emailing[candidate.resume_id]) return;
    
    setEmailing(prev => ({ ...prev, [candidate.resume_id]: 'sending' }));
    try {
      await api.sendShortlistEmail(candidate.resume_id, selectedJobId);
      setEmailing(prev => ({ ...prev, [candidate.resume_id]: 'sent' }));
    } catch (error) {
      console.error("Failed to send email", error);
      setEmailing(prev => ({ ...prev, [candidate.resume_id]: null }));
      alert("Failed to send email");
    }
  };
  return (
    <div className="glass-card overflow-visible">
      <div className="p-6 border-b border-slate-200 flex justify-between items-center">
        <h3 className="text-xl font-bold font-['Outfit'] text-slate-900">Top Ranked Candidates</h3>
        <span className="text-xs font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-lg">
          Updated 2 mins ago
        </span>
      </div>
      
      <div className="overflow-visible">
        <table className="w-full text-left">
          <thead>
            <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
              <th className="px-8 py-4 font-semibold">Rank</th>
              <th className="px-6 py-4 font-semibold">Candidate</th>
              <th className="px-6 py-4 font-semibold">Compatibility</th>
              <th className="px-6 py-4 font-semibold">Skills Match</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {candidates.map((c, i) => (
              <tr 
                key={c.id || c.resume_id} 
                onClick={() => onSelect && onSelect(c)}
                className="hover:bg-slate-50 transition-colors group cursor-pointer"
              >
                <td className="px-8 py-4">
                  <div className="flex items-center gap-3">
                    {i === 0 ? (
                      <div className="p-1 px-2 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-lg text-xs font-bold flex items-center gap-1">
                        <Trophy size={12} /> #1
                      </div>
                    ) : (
                      <span className="text-slate-500 font-medium">#{i + 1}</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold border border-slate-200 group-hover:border-slate-400 transition-colors text-slate-900">
                      {c.candidate_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <p className="font-semibold text-sm text-slate-900">{c.candidate_name}</p>
                      <p className="text-xs text-slate-500">{c.candidate_email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden w-24">
                      <div 
                        className="h-full bg-white rounded-full"
                        style={{ width: `${c.overall_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-slate-900">{c.overall_score}%</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1 max-w-[200px]">
                    {(c.matched_skills || []).slice(0, 3).map(skill => (
                      <span key={skill} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200">
                        {skill}
                      </span>
                    ))}
                    {(c.matched_skills || []).length > 3 && (
                      <span className="text-[10px] text-slate-500">+{(c.matched_skills || []).length - 3}</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`
                    text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-lg border
                    ${c.match_level === 'high' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 
                      c.match_level === 'medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 
                      'bg-slate-500/10 text-slate-500 border-slate-500/20'}
                  `}>
                    {c.match_level}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 hover:bg-slate-100 hover:text-slate-900 rounded-xl transition-colors text-slate-500" title="Quick Analyze">
                      <ExternalLink size={18} />
                    </button>
                    <button 
                      onClick={(e) => handleEmail(c, e)}
                      className={`p-2 transition-colors rounded-xl ${
                        emailing[c.resume_id] === 'sent' 
                          ? 'bg-emerald-500 text-white border border-emerald-600 shadow-sm' 
                          : 'hover:bg-slate-100 text-slate-500 hover:text-slate-900 border border-transparent'
                      }`} 
                      title={emailing[c.resume_id] === 'sent' ? 'Candidate is shortlisted' : 'Email Candidate'}
                      disabled={emailing[c.resume_id] === 'sending' || emailing[c.resume_id] === 'sent'}
                    >
                      {emailing[c.resume_id] === 'sent' ? (
                        <CheckCircle2 size={18} className="text-white" />
                      ) : (
                        <Mail size={18} className={emailing[c.resume_id] === 'sending' ? 'animate-pulse text-slate-900' : ''} />
                      )}
                    </button>
                    <div className="relative">
                      <button 
                        onClick={(e) => { e.stopPropagation(); setOpenMenuId(openMenuId === c.resume_id ? null : c.resume_id); }}
                        className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-500 hover:text-slate-900"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                      {openMenuId === c.resume_id && (
                        <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-xl z-50 py-1 flex flex-col items-start">
                          <button onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); onSelect && onSelect(c); }} className="w-full text-left px-4 py-2 hover:bg-slate-50 text-sm font-medium text-slate-700">View Full Profile</button>
                          <button onClick={(e) => { e.stopPropagation(); setOpenMenuId(null); alert('Remove candidate feature coming soon!'); }} className="w-full text-left px-4 py-2 hover:bg-red-50 text-sm font-medium text-red-600">Remove Candidate</button>
                        </div>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="p-4 border-t border-slate-200 flex justify-center">
        <button className="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1 transition-colors font-medium">
          View all {candidates.length} candidates <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
