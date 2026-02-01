import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatPage from './pages/Chat';
import SettingsPage from './pages/Settings';
import SkillsPage from './pages/Skills';

const App: React.FC = () => {
  return (
    <HashRouter>
      <div className="flex h-screen w-full bg-[#101922] text-white">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/skills" element={<SkillsPage />} />
            {/* Fallbacks for demo buttons */}
            <Route path="/automations" element={<Navigate to="/skills" replace />} />
            <Route path="/history" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </HashRouter>
  );
};

export default App;