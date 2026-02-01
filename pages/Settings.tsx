import React, { useState } from 'react';
import { AppSettings, LLMProvider } from '../types';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>({
    provider: LLMProvider.Google,
    model: 'gemini-1.5-pro',
    temperature: 0.7,
    topP: 1.0,
    systemPrompt: '',
    storeHistory: true,
    anonymizePII: false
  });

  const providers = [
    { id: LLMProvider.OpenAI, name: 'OpenAI', desc: 'GPT-4o, GPT-3.5 Turbo', icon: 'auto_awesome' },
    { id: LLMProvider.Anthropic, name: 'Anthropic', desc: 'Claude 3.5 Sonnet, Opus', icon: 'neurology' },
    { id: LLMProvider.Google, name: 'Google Vertex', desc: 'Gemini 1.5 Pro', icon: 'grid_view' },
    { id: LLMProvider.Deepseek, name: 'Deepseek', desc: 'Deepseek Coder V2', icon: 'code_blocks' },
  ];

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#101922]">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 lg:px-12 scroll-smooth">
        <div className="max-w-5xl mx-auto flex flex-col gap-8 pb-24">
          
          {/* Breadcrumbs */}
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="text-text-secondary font-medium">Settings</span>
            <span className="text-text-secondary font-medium">/</span>
            <span className="text-text-secondary font-medium">Engine</span>
            <span className="text-text-secondary font-medium">/</span>
            <span className="text-white font-medium">LLM Configuration</span>
          </div>

          {/* Header */}
          <div className="flex flex-wrap justify-between items-end gap-4 border-b border-border-dark pb-6">
            <div className="flex flex-col gap-2">
              <h1 className="text-white text-3xl md:text-4xl font-bold tracking-tight">LLM Configuration</h1>
              <p className="text-text-secondary text-base max-w-2xl">Manage AI providers, configure API keys, and fine-tune model parameters for optimal performance.</p>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 rounded-lg border border-border-dark text-white hover:bg-surface-dark transition-colors text-sm font-medium">
                Reset Defaults
              </button>
              <button className="px-4 py-2 rounded-lg bg-primary hover:bg-blue-600 text-white shadow-lg shadow-blue-500/20 transition-colors text-sm font-medium flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">save</span>
                Save Changes
              </button>
            </div>
          </div>

          {/* Providers */}
          <div className="flex flex-col gap-4">
            <h3 className="text-white text-lg font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">dns</span>
              Active Provider
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {providers.map((p) => (
                <label 
                  key={p.id}
                  className={`cursor-pointer relative flex flex-col gap-3 rounded-xl border p-4 transition-all
                    ${settings.provider === p.id 
                      ? 'border-primary bg-surface-dark shadow-md shadow-primary/10' 
                      : 'border-border-dark hover:bg-surface-dark/50'
                    }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="bg-white/10 p-2 rounded-lg">
                      <span className="material-symbols-outlined text-white">{p.icon}</span>
                    </div>
                    <input 
                      type="radio" 
                      name="provider" 
                      checked={settings.provider === p.id} 
                      onChange={() => setSettings({...settings, provider: p.id})}
                      className="h-5 w-5 text-primary border-border-dark bg-transparent focus:ring-0 cursor-pointer"
                    />
                  </div>
                  <div>
                    <p className="text-white font-bold">{p.name}</p>
                    <p className="text-text-secondary text-xs">{p.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Config Form */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col gap-6">
              
              {/* API Key */}
              <div className="bg-surface-dark rounded-xl p-6 border border-border-dark/50">
                <h3 className="text-white text-lg font-bold mb-4">Credentials</h3>
                <div className="flex flex-col gap-2">
                  <label className="text-text-secondary text-sm font-medium">API Key (Env Variable Loaded)</label>
                  <div className="relative flex items-center">
                    <span className="absolute left-3 material-symbols-outlined text-text-secondary">key</span>
                    <input 
                      type="password" 
                      disabled
                      value="sk-********************************"
                      className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-2.5 pl-10 pr-10 focus:border-primary focus:ring-1 focus:ring-primary placeholder-gray-600 transition-colors font-mono text-sm opacity-60 cursor-not-allowed"
                    />
                    <button className="absolute right-3 text-text-secondary hover:text-white">
                      <span className="material-symbols-outlined text-[20px]">visibility_off</span>
                    </button>
                  </div>
                  <p className="text-xs text-text-secondary mt-1">Your key is loaded securely from the environment variables.</p>
                </div>
              </div>

              {/* Parameters */}
              <div className="bg-surface-dark rounded-xl p-6 border border-border-dark/50 flex flex-col gap-6">
                <h3 className="text-white text-lg font-bold">Model Parameters</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex flex-col gap-2">
                    <label className="text-text-secondary text-sm font-medium">Model</label>
                    <div className="relative">
                      <select 
                        value={settings.model}
                        onChange={(e) => setSettings({...settings, model: e.target.value})}
                        className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-2.5 pl-4 pr-10 focus:border-primary focus:ring-1 focus:ring-primary appearance-none cursor-pointer"
                      >
                        <option value="gemini-1.5-pro">gemini-1.5-pro (Recommended)</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-secondary pointer-events-none">expand_more</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="text-text-secondary text-sm font-medium">Context Window</label>
                    <div className="relative">
                      <select className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-2.5 pl-4 pr-10 focus:border-primary focus:ring-1 focus:ring-primary appearance-none cursor-pointer">
                        <option>128k Tokens</option>
                        <option>32k Tokens</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-secondary pointer-events-none">expand_more</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
                  <div className="flex flex-col gap-4">
                    <div className="flex justify-between items-center">
                      <label className="text-text-secondary text-sm font-medium">Temperature</label>
                      <span className="bg-background-dark text-primary px-2 py-0.5 rounded text-xs font-mono font-bold border border-border-dark">{settings.temperature}</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.1" 
                      value={settings.temperature}
                      onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
                      className="w-full h-1 bg-border-dark rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-text-secondary">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-4">
                    <div className="flex justify-between items-center">
                      <label className="text-text-secondary text-sm font-medium">Top P</label>
                      <span className="bg-background-dark text-primary px-2 py-0.5 rounded text-xs font-mono font-bold border border-border-dark">{settings.topP}</span>
                    </div>
                    <input 
                       type="range" min="0" max="1" step="0.1" 
                       value={settings.topP}
                       onChange={(e) => setSettings({...settings, topP: parseFloat(e.target.value)})}
                       className="w-full h-1 bg-border-dark rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-text-secondary">
                      <span>Focused</span>
                      <span>Random</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2 pt-2">
                  <label className="text-text-secondary text-sm font-medium flex justify-between">
                     System Prompt
                     <span className="text-xs text-primary cursor-pointer hover:underline">Load Preset</span>
                  </label>
                  <textarea 
                    value={settings.systemPrompt}
                    onChange={(e) => setSettings({...settings, systemPrompt: e.target.value})}
                    className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-3 px-4 focus:border-primary focus:ring-1 focus:ring-primary placeholder-gray-600 transition-colors text-sm leading-relaxed" 
                    placeholder="You are KeaBOT, a helpful AI assistant..." 
                    rows={4}
                  />
                </div>
              </div>
            </div>

            {/* Sidebar Column */}
            <div className="flex flex-col gap-6">
              <div className="bg-surface-dark rounded-xl p-6 border border-border-dark/50">
                <h3 className="text-white text-lg font-bold mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">security</span>
                  Privacy
                </h3>
                <div className="flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <p className="text-white text-sm font-medium">Store Chat History</p>
                      <p className="text-text-secondary text-xs">Keep logs for 30 days</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" checked={settings.storeHistory} onChange={(e) => setSettings({...settings, storeHistory: e.target.checked})} className="sr-only peer" />
                      <div className="w-11 h-6 bg-border-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                  <hr className="border-border-dark/50"/>
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <p className="text-white text-sm font-medium">Anonymize PII</p>
                      <p className="text-text-secondary text-xs">Mask emails & phones</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" checked={settings.anonymizePII} onChange={(e) => setSettings({...settings, anonymizePII: e.target.checked})} className="sr-only peer" />
                      <div className="w-11 h-6 bg-border-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default SettingsPage;