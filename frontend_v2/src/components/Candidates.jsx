import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { FileText, AlertCircle, RefreshCw, Mail, CheckCircle2, ChevronDown } from 'lucide-react';

export const Candidates = ({ searchQuery = '' }) => {
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [emailing, setEmailing] = useState({});  // resumeId => 'sending'|'sent'|null
  const [selectedJob, setSelectedJob] = useState('');
  const [matchScores, setMatchScores] = useState({});

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.getResumes(), api.getJobs()])
      .then(([resumeData, jobData]) => {
        setCandidates(Array.isArray(resumeData) ? resumeData : []);
        setJobs(Array.isArray(jobData) ? jobData : []);
        if (jobData?.length > 0) setSelectedJob(String(jobData[0].id));
        setLoading(false);
      })
      .catch(err => {
        setError(err?.response?.data?.detail || err.message || 'Failed to fetch data');
        setLoading(false);
      });
  };

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (!selectedJob) return;
    api.getRankings(selectedJob)
      .then(data => {
        const mapping = {};
        (data.rankings || []).forEach(r => {
          mapping[r.resume_id] = { score: r.overall_score };
        });
        setMatchScores(mapping);
      })
      .catch(console.error);
  }, [selectedJob]);

  const handleSendEmail = async (candidate) => {
    if (!selectedJob) {
      alert('Please select a job to associate the email with.');
      return;
    }
    if (emailing[candidate.id] === 'sending') return;

    setEmailing(prev => ({ ...prev, [candidate.id]: 'sending' }));
    try {
      await api.sendShortlistEmail(candidate.id, parseInt(selectedJob));
      setEmailing(prev => ({ ...prev, [candidate.id]: 'sent' }));
    } catch (err) {
      console.error('Email error:', err);
      alert(`Failed to send email: ${err?.response?.data?.detail || err.message}`);
      setEmailing(prev => ({ ...prev, [candidate.id]: null }));
    }
  };

  const filteredCandidates = candidates.filter(c => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const name = (c.candidate_name || '').toLowerCase();
    const email = (c.candidate_email || '').toLowerCase();
    const file = (c.file_name || '').toLowerCase();
    return name.includes(q) || email.includes(q) || file.includes(q);
  });

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full" />
    </div>
  );

  if (error) return (
    <div className="glass-card p-8 text-center mt-4">
      <AlertCircle size={36} className="text-red-400 mx-auto mb-3" />
      <p className="text-red-400 font-semibold mb-1">Failed to load candidates</p>
      <p className="text-slate-500 text-sm mb-4">{error}</p>
      <button onClick={loadData} className="flex items-center gap-2 mx-auto px-4 py-2 bg-slate-900 rounded-xl text-sm font-medium hover:bg-slate-800 transition-colors">
        <RefreshCw size={14} /> Retry
      </button>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20 mt-4">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Global Candidate Pool</h2>
          <p className="text-slate-500 text-sm mt-1">{filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? 's' : ''} found</p>
        </div>

        {/* Job selector for emails */}
        {jobs.length > 0 && (
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-600 uppercase tracking-wider font-semibold whitespace-nowrap">Email for Job:</label>
            <div className="relative">
              <select
                value={selectedJob}
                onChange={e => setSelectedJob(e.target.value)}
                className="bg-white border border-slate-200 rounded-xl px-4 py-2 pr-8 text-sm text-slate-900 appearance-none outline-none focus:ring-2 focus:ring-slate-900"
              >
                {jobs.map(j => (
                  <option key={j.id} value={j.id}>{j.title}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
            </div>
          </div>
        )}
      </div>

      <div className="glass-card p-0 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
              <th className="px-6 py-4 font-semibold">ID</th>
              <th className="px-6 py-4 font-semibold">Name</th>
              <th className="px-6 py-4 font-semibold">Email</th>
              <th className="px-6 py-4 font-semibold">File</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Match %</th>
              <th className="px-6 py-4 font-semibold text-center">Shortlist</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filteredCandidates.map(c => (
              <tr key={c.id} className="hover:bg-slate-50 transition-colors group">
                <td className="px-6 py-4 font-semibold text-sm text-slate-600">#{c.id}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-white flex items-center justify-center text-[11px] font-bold shadow-sm text-white shrink-0">
                      {(c.candidate_name && c.candidate_name !== 'Unknown' ? c.candidate_name : c.file_name)?.charAt(0)?.toUpperCase() || 'R'}
                    </div>
                    <span className="font-semibold text-sm text-slate-900">
                      {c.candidate_name !== 'Unknown' ? c.candidate_name : c.file_name}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">{c.candidate_email || 'N/A'}</td>
                <td className="px-6 py-4 text-xs text-slate-500 max-w-[160px] truncate">{c.file_name}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-[10px] uppercase tracking-wider font-bold rounded-lg border ${
                    c.status === 'processed' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                    : c.status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20'
                    : 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                  }`}>
                    {c.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {matchScores[c.id] ? (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden w-16">
                        <div 
                          className="h-full bg-slate-900 rounded-full"
                          style={{ width: `${matchScores[c.id].score}%` }}
                        />
                      </div>
                      <span className="font-bold text-sm text-slate-900">{matchScores[c.id].score}%</span>
                    </div>
                  ) : (
                    <span className="text-slate-400 text-sm">--</span>
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  <button
                    onClick={() => handleSendEmail(c)}
                    disabled={emailing[c.id] === 'sending' || emailing[c.id] === 'sent' || c.status !== 'processed'}
                    title={c.status !== 'processed' ? 'Resume must be fully processed first' : emailing[c.id] === 'sent' ? 'Candidate is shortlisted' : 'Send shortlist invitation email'}
                    className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                      emailing[c.id] === 'sent'
                        ? 'bg-emerald-500 text-white border-emerald-600 shadow-inner'
                        : emailing[c.id] === 'sending'
                        ? 'bg-slate-100 text-slate-900 border-slate-200 animate-pulse'
                        : c.status !== 'processed'
                        ? 'opacity-30 cursor-not-allowed text-slate-500 border-slate-500/10'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-900 hover:border-slate-300'
                    }`}
                  >
                    {emailing[c.id] === 'sent' ? (
                      <><CheckCircle2 size={13} /> Shortlisted</>
                    ) : emailing[c.id] === 'sending' ? (
                      <><Mail size={13} className="animate-pulse" /> Sending…</>
                    ) : (
                      <><Mail size={13} /> Shortlist</>
                    )}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredCandidates.length === 0 && candidates.length > 0 && (
          <div className="p-12 text-center text-slate-500">
            No candidates found matching '{searchQuery}'.
          </div>
        )}
        {candidates.length === 0 && (
          <div className="p-12 text-center">
            <FileText size={36} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No candidates uploaded yet.</p>
            <p className="text-slate-600 text-sm mt-1">Use the Bulk Upload button on the Dashboard to add resumes.</p>
          </div>
        )}
      </div>
    </div>
  );
};
