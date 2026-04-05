import React, { useState, useEffect } from 'react';
import { Save, Lock, Mail, Key } from 'lucide-react';

export const Settings = () => {
  const [smtpPassword, setSmtpPassword] = useState('');
  const [smtpEmail, setSmtpEmail] = useState('');
  const [llmKey, setLlmKey] = useState('');
  const [savedStatus, setSavedStatus] = useState('');

  useEffect(() => {
    const savedSmtp = localStorage.getItem('smtp_app_password');
    const savedEmail = localStorage.getItem('smtp_email');
    const savedLlm = localStorage.getItem('llm_api_key');
    if (savedSmtp) setSmtpPassword(savedSmtp);
    if (savedEmail) setSmtpEmail(savedEmail);
    if (savedLlm) setLlmKey(savedLlm);
  }, []);

  const handleSave = () => {
    localStorage.setItem('smtp_app_password', smtpPassword.replace(/\s+/g, ''));
    localStorage.setItem('smtp_email', smtpEmail);
    localStorage.setItem('llm_api_key', llmKey);
    
    setSavedStatus('Settings saved securely to local storage.');
    setTimeout(() => setSavedStatus(''), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
      <div>
        <h2 className="text-3xl font-bold text-slate-900 mb-1">Settings</h2>
        <p className="text-slate-500">Configure your email and AI provider credentials.</p>
      </div>

      <div className="glass-card p-8 space-y-8">
        {/* Email Settings */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
            <div className="p-2 bg-slate-100 rounded-xl">
              <Mail size={20} className="text-slate-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-slate-900">Email Configuration</h3>
              <p className="text-sm text-slate-500">Used for sending shortlisting emails to candidates.</p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Sender Email Address</label>
            <div className="relative mb-4">
              <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="email"
                value={smtpEmail}
                onChange={e => setSmtpEmail(e.target.value)}
                placeholder="e.g., hr@gmail.com"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 outline-none transition-all text-slate-900"
              />
            </div>
            
            <label className="block text-sm font-semibold text-slate-700 mb-2">Google App Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="password"
                value={smtpPassword}
                onChange={e => setSmtpPassword(e.target.value)}
                placeholder="16-character app password (e.g., abcd efgh ijkl mnop)"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 outline-none transition-all text-slate-900"
              />
            </div>
            <p className="text-xs text-slate-500 mt-2">Required by Google as of 2024. Regular passwords will fail authentication. Generate this from your Google Account settings.</p>
          </div>
        </div>

        {/* AI Provider Settings */}
        <div className="space-y-4 pt-4">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
            <div className="p-2 bg-slate-100 rounded-xl">
              <Key size={20} className="text-slate-600" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-slate-900">AI Provider Configuration</h3>
              <p className="text-sm text-slate-500">Set custom keys for Groq or other LLM APIs.</p>
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">LLM API Key</label>
            <div className="relative">
              <Key size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="password"
                value={llmKey}
                onChange={e => setLlmKey(e.target.value)}
                placeholder="gsk_xxxxxxxxxxxxxxxxxxxxxx"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-slate-900 focus:border-slate-900 outline-none transition-all text-slate-900"
              />
            </div>
            <p className="text-xs text-slate-500 mt-2">Overrides the backend's default `.env` API key.</p>
          </div>
        </div>

        {/* Actions */}
        <div className="pt-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-emerald-600">{savedStatus}</span>
          <button 
            onClick={handleSave}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-xl font-semibold shadow-sm transition-all active:scale-95"
          >
            <Save size={18} />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
