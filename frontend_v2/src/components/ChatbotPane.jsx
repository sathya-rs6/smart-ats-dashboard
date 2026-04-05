import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles,
  Command,
  ArrowDownCircle,
  X
} from 'lucide-react';
import { api } from '../services/api';

export const ChatbotPane = ({ candidate, onClose }) => {
  const [messages, setMessages] = useState([
    { role: 'bot', content: `Hello! I've analyzed ${candidate?.candidate_name}'s resume. What would you like to know about their experience?` }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    
    setIsTyping(true);
    try {
      if (candidate?.resume_id) {
        const response = await api.askAssistant(candidate.resume_id, userMsg);
        setMessages(prev => [...prev, { role: 'bot', content: response.answer }]);
      } else {
        await new Promise(r => setTimeout(r, 1000));
        setMessages(prev => [...prev, { role: 'bot', content: "Please select a candidate first." }]);
      }
    } catch (error) {
       console.error(error);
       setMessages(prev => [...prev, { role: 'bot', content: "Sorry, I couldn't process that query correctly right now." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/80 backdrop-blur-xl border-l border-slate-200 animate-slide-in-right">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50 transition-colors">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-100 rounded-xl text-slate-900">
            <Bot size={20} />
          </div>
          <div>
            <h4 className="font-bold text-sm">AI Resume Assistant</h4>
            <p className="text-[10px] text-slate-500">Querying: {candidate?.candidate_name}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-colors">
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center shrink-0 border border-slate-200
              ${msg.role === 'bot' ? 'bg-slate-100 text-slate-900' : 'bg-slate-700 text-slate-600'}
            `}>
              {msg.role === 'bot' ? <Sparkles size={14} /> : <User size={14} />}
            </div>
            <div className={`
              max-w-[80%] p-3 rounded-2xl text-xs leading-relaxed
              ${msg.role === 'bot' ? 'bg-white text-slate-700' : 'bg-slate-800 text-white shadow-lg shadow-sm'}
            `}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-3">
             <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-900 flex items-center justify-center shrink-0 border border-slate-200">
               <Sparkles size={14} />
             </div>
             <div className="bg-white p-3 rounded-2xl flex gap-1 items-center h-8">
               <div className="w-1 h-1 bg-slate-900 rounded-full animate-bounce [animation-delay:-0.3s]" />
               <div className="w-1 h-1 bg-slate-900 rounded-full animate-bounce [animation-delay:-0.15s]" />
               <div className="w-1 h-1 bg-slate-900 rounded-full animate-bounce" />
             </div>
          </div>
        )}
      </div>

      {/* Suggested Queries */}
      <div className="p-4 bg-slate-800/20 border-t border-slate-200">
        <div className="flex flex-wrap gap-2 mb-4">
          <SuggestedQuery text="Summary" icon={<Command size={10} />} onClick={() => setInput("Summarize their experience")} />
          <SuggestedQuery text="Skills" icon={<Sparkles size={10} />} onClick={() => setInput("What are their top technical skills?")} />
        </div>
        
        {/* Input */}
        <div className="relative">
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Ask about candidate's skills, projects..." 
            className="w-full bg-white text-slate-900 border border-slate-200 rounded-2xl pl-4 pr-12 py-3 text-xs outline-none focus:ring-2 focus:ring-slate-900/50 transition-all resize-none max-h-32"
            rows={1}
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-xl shadow-lg transition-all"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

const SuggestedQuery = ({ text, icon, onClick }) => (
  <button 
    onClick={onClick}
    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-700 text-[10px] text-slate-500 hover:text-slate-700 border border-slate-200 rounded-full transition-all active:scale-95"
  >
    {icon}
    {text}
  </button>
);
