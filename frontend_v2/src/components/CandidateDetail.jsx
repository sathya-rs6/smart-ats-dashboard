import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  MapPin, 
  Calendar,
  Briefcase,
  GraduationCap,
  Award,
  Zap
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  ResponsiveContainer 
} from 'recharts';

export const CandidateDetail = ({ candidate, onClose }) => {
  if (!candidate) return null;

  const skillData = [
    { subject: 'Technical', A: candidate.skill_score || 0, fullMark: 100 },
    { subject: 'Experience', A: candidate.experience_score || 0, fullMark: 100 },
    { subject: 'Education', A: candidate.education_score || 0, fullMark: 100 },
    { subject: 'Keywords', A: candidate.keyword_score || 0, fullMark: 100 },
    { subject: 'Certs', A: candidate.certification_score || 0, fullMark: 100 },
  ];

  return (
    <div className="p-8 space-y-8 animate-fade-in h-fit">
      {/* Profile Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-slate-900 to-slate-700 flex items-center justify-center text-3xl font-bold text-white shadow-sm">
            {candidate.candidate_name ? candidate.candidate_name.charAt(0) : 'U'}
          </div>
          <div>
            <h3 className="text-3xl font-bold font-['Outfit'] mb-2 text-slate-900">{candidate.candidate_name}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Radar Chart */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200">
          <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6 px-2">Skill Profile Analysis</h4>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={skillData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10 }} />
                <Radar
                   name="Candidate"
                   dataKey="A"
                   stroke="#0f172a"
                   fill="#0f172a"
                   fillOpacity={0.1}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skill Gap Analysis */}
        <div className="space-y-6">
          <div>
             <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 px-2">Skill Match</h4>
             <div className="flex flex-wrap gap-2">
               {(candidate.matched_skills || []).map(skill => (
                 <span key={skill} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 text-xs font-semibold rounded-xl border border-emerald-500/20">
                   <CheckCircle2 size={12} /> {skill}
                 </span>
               ))}
             </div>
          </div>
          <div>
             <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 px-2">Missing Skills</h4>
             <div className="flex flex-wrap gap-2">
               {(candidate.missing_skills || []).map(skill => (
                 <span key={skill} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 text-red-400 text-xs font-semibold rounded-xl border border-red-500/20">
                   <XCircle size={12} /> {skill}
                 </span>
               ))}
               {(!candidate.missing_skills || candidate.missing_skills.length === 0) && (
                 <span className="text-sm text-slate-500">None detected</span>
               )}
             </div>
          </div>
        </div>
      </div>

      {/* Experience History */}
      <div className="space-y-6">
        <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 px-2">Experience Timeline</h4>
        <div className="space-y-4">
          {(candidate.experience && candidate.experience.length > 0) ? candidate.experience.map((exp, i) => (
            <TimelineItem 
              key={i}
              title={exp.title || exp.role || 'Role'} 
              company={exp.company || 'Company'} 
              date={exp.duration || exp.dates || 'Date'} 
              icon={<Briefcase size={16} />}
            />
          )) : (
            <p className="text-sm text-slate-500">No experience extracted</p>
          )}
        </div>
      </div>
    </div>
  );
};

const TimelineItem = ({ title, company, date, icon }) => (
  <div className="flex gap-4 group">
    <div className="flex flex-col items-center">
      <div className="p-2 bg-slate-100 text-slate-600 rounded-lg group-hover:bg-white group-hover:text-white transition-all shadow-sm group-hover:shadow-md">
        {icon}
      </div>
      <div className="w-px flex-1 bg-slate-200 my-2" />
    </div>
    <div className="pb-6">
      <h5 className="font-bold text-sm mb-1 text-slate-900">{title}</h5>
      <p className="text-xs text-slate-500 mb-2">{company}</p>
      <div className="flex items-center gap-1 text-[10px] text-slate-500 font-medium">
        <Calendar size={10} /> {date}
      </div>
    </div>
  </div>
);
