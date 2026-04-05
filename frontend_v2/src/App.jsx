import React, { useState } from 'react';
import { useAuth, AuthProvider } from './context/AuthContext';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { Candidates } from './components/Candidates';
import { JobPosts } from './components/JobPosts';
import { AnalysisHistory } from './components/AnalysisHistory';
import { CreateJobModal } from './components/CreateJobModal';
import { Settings } from './components/Settings';

const AuthFlowWrapper = () => {
  const { isAuthenticated } = useAuth();
  const [showLogin, setShowLogin] = useState(true);
  
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [isCreateJobOpen, setIsCreateJobOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  if (!isAuthenticated) {
    if (showLogin) {
      return <Login onSwitchToSignup={() => setShowLogin(false)} />;
    }
    return <Signup onSwitchToLogin={() => setShowLogin(true)} />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'Dashboard': 
        return <Dashboard onOpenCreateModal={() => setIsCreateJobOpen(true)} setActiveTab={setActiveTab} searchQuery={searchQuery} />;
      case 'Candidates': 
        return <Candidates searchQuery={searchQuery} />;
      case 'Job Posts': 
        return <JobPosts onOpenCreateModal={() => setIsCreateJobOpen(true)} searchQuery={searchQuery} />;
      case 'Analysis History': 
        return <AnalysisHistory searchQuery={searchQuery} />;
      case 'Settings':
        return <Settings />;
      default: 
        return <Dashboard onOpenCreateModal={() => setIsCreateJobOpen(true)} setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Layout activeTab={activeTab} setActiveTab={setActiveTab} searchQuery={searchQuery} setSearchQuery={setSearchQuery}>
        {renderContent()}
      </Layout>
      <CreateJobModal 
        isOpen={isCreateJobOpen} 
        onClose={() => setIsCreateJobOpen(false)} 
        onJobCreated={() => {}} 
      />
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-slate-900/30">
        <AuthFlowWrapper />
      </div>
    </AuthProvider>
  );
};

export default App;
