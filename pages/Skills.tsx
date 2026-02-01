import React, { useState } from 'react';
import { Skill, AutomationTask } from '../types';

const SkillsPage: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([
    { id: '1', name: 'Web Browsing', description: 'Allows Kea to browse the internet for real-time data.', icon: 'travel_explore', active: true, color: 'text-primary' },
    { id: '2', name: 'Python Interpreter', description: 'Executes Python code in a secure sandboxed environment.', icon: 'terminal', active: false, color: 'text-gray-400' },
    { id: '3', name: 'Gmail Connector', description: 'Read, draft and organize emails via secure OAuth.', icon: 'mail', active: true, color: 'text-orange-500' },
    { id: '4', name: 'Calendar Agent', description: 'Manage invites and schedule meetings autonomously.', icon: 'calendar_month', active: false, color: 'text-purple-500' },
    { id: '5', name: 'Knowledge Base', description: 'RAG capabilities over uploaded documents and wikis.', icon: 'database', active: true, color: 'text-green-500' },
    { id: '6', name: 'Image Gen', description: 'Create images using DALL-E 3 or Stable Diffusion.', icon: 'image', active: false, color: 'text-pink-500' },
  ]);

  const automations: AutomationTask[] = [
    { id: '1', name: 'Daily Digest', description: 'Summarize unread Slack messages', status: 'active', lastRun: '10m ago', schedule: 'Every 24h' },
    { id: '2', name: 'Database Backup', description: 'SQL dump to S3 Bucket', status: 'failed', lastRun: '1h ago', schedule: 'Cron: 0 0 * * *', error: 'Error: Connection timed out (504)' },
    { id: '3', name: 'Competitor Analysis', description: 'Scrape pricing pages weekly', status: 'paused', lastRun: '', schedule: 'Weekly' },
  ];

  const toggleSkill = (id: string) => {
    setSkills(prev => prev.map(s => s.id === id ? { ...s, active: !s.active } : s));
  };

  return (
    <main className="flex-1 flex flex-col items-center px-4 md:px-10 py-6 md:py-8 w-full max-w-[1440px] mx-auto h-full overflow-y-auto bg-background-light dark:bg-background-dark text-slate-900 dark:text-white">
      {/* Header Section */}
      <div className="w-full flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-10 border-b border-gray-200 dark:border-[#233648] pb-6">
        <div className="flex flex-col gap-3 max-w-2xl">
          <h1 className="text-3xl md:text-4xl font-bold leading-tight tracking-[-0.033em]">Skills & Automations</h1>
          <p className="text-gray-600 dark:text-[#92adc9] text-base leading-relaxed">Configure KeaBOT's capabilities and manage recurring tasks. Enable plugins to extend functionality or schedule automated jobs.</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-white dark:bg-[#233648] border border-gray-200 dark:border-transparent text-sm font-bold shadow-sm hover:bg-gray-50 dark:hover:bg-[#2f455a] transition-colors">
            <span className="material-symbols-outlined text-[20px]">add_circle</span>
            <span>New Skill</span>
          </button>
          <button className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-blue-600 transition-colors">
            <span className="material-symbols-outlined text-[20px]">bolt</span>
            <span>Create Automation</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 w-full pb-20">
        {/* Left: Skills */}
        <div className="xl:col-span-8 flex flex-col gap-6">
          <h3 className="text-xl font-bold flex items-center gap-2 self-start md:self-auto">
            <span className="material-symbols-outlined text-primary">extension</span>
            Skills Library
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {skills.map(skill => (
              <div key={skill.id} className={`group relative flex flex-col p-5 rounded-xl bg-white dark:bg-card-dark border ${skill.active ? 'border-primary/40 dark:border-primary/30 shadow-lg shadow-primary/5' : 'border-gray-200 dark:border-[#2f455a]'} transition-all duration-300 hover:scale-[1.01]`}>
                <div className="flex justify-between items-start mb-3">
                  <div className={`size-10 rounded-lg flex items-center justify-center ${skill.active ? 'bg-primary/10' : 'bg-gray-100 dark:bg-[#233648]'} ${skill.color}`}>
                    <span className="material-symbols-outlined">{skill.icon}</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={skill.active} onChange={() => toggleSkill(skill.id)} className="sr-only peer" />
                    <div className="w-9 h-5 bg-gray-300 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                <h4 className="font-bold text-lg mb-1">{skill.name}</h4>
                <p className="text-gray-500 dark:text-[#92adc9] text-sm leading-snug">{skill.description}</p>
                {skill.active && (
                  <div className="mt-4 flex items-center gap-2 text-xs text-primary font-medium">
                    <span className="size-1.5 rounded-full bg-primary animate-pulse"></span> Active
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Automations */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-green-500">schedule</span>
              Active Automations
            </h3>
          </div>
          <div className="flex flex-col gap-4">
            {automations.map(task => (
              <div key={task.id} className={`flex flex-col bg-white dark:bg-[#151f2b] rounded-xl border ${task.status === 'paused' ? 'border-dashed border-gray-300 dark:border-[#2f455a] opacity-80' : 'border-gray-200 dark:border-[#2f455a]'} overflow-hidden`}>
                <div className="p-4 flex items-start justify-between border-b border-gray-100 dark:border-[#2f455a]/50">
                  <div className="flex gap-3">
                    <div className="mt-1">
                      {task.status === 'active' && (
                        <span className="relative flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                      )}
                      {task.status === 'failed' && <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>}
                      {task.status === 'paused' && <span className="relative inline-flex rounded-full h-3 w-3 bg-gray-400 dark:bg-gray-600 border-2 border-white dark:border-[#151f2b]"></span>}
                    </div>
                    <div>
                      <h4 className="font-bold text-base">{task.name}</h4>
                      <p className="text-xs text-gray-500 dark:text-[#92adc9] mt-0.5">{task.description}</p>
                    </div>
                  </div>
                  {task.status === 'paused' ? (
                     <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-gray-400 dark:text-gray-600">Paused</span>
                        <span className="material-symbols-outlined text-gray-400 text-[20px] cursor-pointer">play_circle</span>
                     </div>
                  ) : (
                    <button className="text-gray-400 hover:text-white">
                      <span className="material-symbols-outlined text-[20px]">more_vert</span>
                    </button>
                  )}
                </div>
                {task.status !== 'paused' && (
                  <div className="px-4 py-3 bg-gray-50 dark:bg-[#1a2632] flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                         <span className={`material-symbols-outlined text-[16px] ${task.status === 'failed' ? 'text-red-500' : 'text-gray-400'}`}>{task.status === 'failed' ? 'error' : 'history'}</span>
                         <span className={`text-xs font-mono ${task.status === 'failed' ? 'text-red-400' : 'text-gray-500 dark:text-[#92adc9]'}`}>{task.status === 'failed' ? `Failed: ${task.lastRun}` : `Last run: ${task.lastRun}`}</span>
                      </div>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                        {task.schedule}
                      </span>
                    </div>
                    {task.error && (
                      <div className="mt-1 p-2 bg-black/80 rounded border border-red-500/20 font-mono text-[10px] text-red-300 overflow-x-auto whitespace-nowrap">
                        {task.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
};

export default SkillsPage;