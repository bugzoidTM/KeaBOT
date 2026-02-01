import React, { useState, useEffect } from 'react';
import { getSkills, reloadSkills, BackendSkill } from '../services/apiService';
import { AutomationTask } from '../types';

const SkillsPage: React.FC = () => {
  const [skills, setSkills] = useState<BackendSkill[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isReloading, setIsReloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const automations: AutomationTask[] = [
    { id: '1', name: 'Daily Digest', description: 'Summarize unread Slack messages', status: 'active', lastRun: '10m ago', schedule: 'Every 24h' },
    { id: '2', name: 'Database Backup', description: 'SQL dump to S3 Bucket', status: 'failed', lastRun: '1h ago', schedule: 'Cron: 0 0 * * *', error: 'Error: Connection timed out (504)' },
    { id: '3', name: 'Competitor Analysis', description: 'Scrape pricing pages weekly', status: 'paused', lastRun: '', schedule: 'Weekly' },
  ];

  // Load skills from backend
  const loadSkills = async () => {
    try {
      setError(null);
      const response = await getSkills();
      setSkills(response.skills);
    } catch (err) {
      setError('Não foi possível carregar as skills. Backend está rodando?');
      console.error('Failed to load skills:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
  }, []);

  const handleReloadSkills = async () => {
    setIsReloading(true);
    try {
      const response = await reloadSkills();
      if (response.success) {
        await loadSkills();
      }
    } catch (err) {
      setError('Erro ao recarregar skills');
      console.error('Failed to reload skills:', err);
    } finally {
      setIsReloading(false);
    }
  };

  const getSkillIcon = (name: string): string => {
    const nameLower = name.toLowerCase();
    if (nameLower.includes('log') || nameLower.includes('clean')) return 'delete_sweep';
    if (nameLower.includes('file')) return 'folder';
    if (nameLower.includes('search') || nameLower.includes('grep')) return 'search';
    if (nameLower.includes('deploy')) return 'cloud_upload';
    if (nameLower.includes('test')) return 'science';
    if (nameLower.includes('git')) return 'commit';
    if (nameLower.includes('database') || nameLower.includes('sql')) return 'database';
    if (nameLower.includes('api')) return 'api';
    if (nameLower.includes('template')) return 'description';
    return 'auto_awesome';
  };

  const getSkillColor = (index: number): string => {
    const colors = [
      'text-primary',
      'text-purple-500',
      'text-green-500',
      'text-orange-500',
      'text-pink-500',
      'text-cyan-500',
    ];
    return colors[index % colors.length];
  };

  return (
    <main className="flex-1 flex flex-col items-center px-4 md:px-10 py-6 md:py-8 w-full max-w-[1440px] mx-auto h-full overflow-y-auto bg-background-light dark:bg-background-dark text-slate-900 dark:text-white">
      {/* Header Section */}
      <div className="w-full flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-10 border-b border-gray-200 dark:border-[#233648] pb-6">
        <div className="flex flex-col gap-3 max-w-2xl">
          <h1 className="text-3xl md:text-4xl font-bold leading-tight tracking-[-0.033em]">Skills & Automations</h1>
          <p className="text-gray-600 dark:text-[#92adc9] text-base leading-relaxed">
            Skills são capacidades modulares carregadas de arquivos Markdown na pasta <code className="bg-[#233648] px-1.5 py-0.5 rounded text-sm">/skills</code>. O agente pode ativá-las sob demanda.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleReloadSkills}
            disabled={isReloading}
            className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-white dark:bg-[#233648] border border-gray-200 dark:border-transparent text-sm font-bold shadow-sm hover:bg-gray-50 dark:hover:bg-[#2f455a] transition-colors disabled:opacity-50"
          >
            <span className={`material-symbols-outlined text-[20px] ${isReloading ? 'animate-spin' : ''}`}>
              {isReloading ? 'progress_activity' : 'refresh'}
            </span>
            <span>{isReloading ? 'Recarregando...' : 'Reload Skills'}</span>
          </button>
          <button className="flex items-center justify-center gap-2 rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-blue-600 transition-colors">
            <span className="material-symbols-outlined text-[20px]">add_circle</span>
            <span>Nova Skill</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="w-full mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-center gap-3">
          <span className="material-symbols-outlined">error</span>
          <span>{error}</span>
          <button onClick={loadSkills} className="ml-auto text-sm underline hover:no-underline">
            Tentar novamente
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 w-full pb-20">
        {/* Left: Skills */}
        <div className="xl:col-span-8 flex flex-col gap-6">
          <h3 className="text-xl font-bold flex items-center gap-2 self-start md:self-auto">
            <span className="material-symbols-outlined text-primary">auto_awesome</span>
            Skills Library
            {!isLoading && (
              <span className="text-sm font-normal text-[#92adc9]">({skills.length} carregadas)</span>
            )}
          </h3>

          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <div className="flex flex-col items-center gap-3">
                <span className="material-symbols-outlined text-4xl text-primary animate-spin">progress_activity</span>
                <span className="text-[#92adc9]">Carregando skills...</span>
              </div>
            </div>
          ) : skills.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 bg-[#1a2632] rounded-xl border border-dashed border-[#233648]">
              <span className="material-symbols-outlined text-4xl text-[#5a7690] mb-3">extension_off</span>
              <p className="text-[#92adc9] mb-2">Nenhuma skill encontrada</p>
              <p className="text-sm text-[#5a7690]">
                Adicione arquivos .md na pasta <code className="bg-[#233648] px-1 rounded">backend/skills/</code>
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {skills.map((skill, index) => (
                <div
                  key={skill.name}
                  className={`group relative flex flex-col p-5 rounded-xl bg-white dark:bg-card-dark border ${skill.is_loaded
                      ? 'border-primary/40 dark:border-primary/30 shadow-lg shadow-primary/5'
                      : 'border-gray-200 dark:border-[#2f455a]'
                    } transition-all duration-300 hover:scale-[1.01]`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className={`size-10 rounded-lg flex items-center justify-center ${skill.is_loaded ? 'bg-primary/10' : 'bg-gray-100 dark:bg-[#233648]'
                      } ${getSkillColor(index)}`}>
                      <span className="material-symbols-outlined">{getSkillIcon(skill.name)}</span>
                    </div>
                    {skill.version && (
                      <span className="text-[10px] text-[#5a7690] bg-[#233648] px-2 py-0.5 rounded-full">
                        v{skill.version}
                      </span>
                    )}
                  </div>

                  <h4 className="font-bold text-lg mb-1">{skill.name}</h4>
                  <p className="text-gray-500 dark:text-[#92adc9] text-sm leading-snug line-clamp-2">
                    {skill.description}
                  </p>

                  {/* Triggers */}
                  {skill.triggers && skill.triggers.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {skill.triggers.slice(0, 3).map((trigger, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-[#233648] text-[#92adc9]"
                        >
                          {trigger}
                        </span>
                      ))}
                      {skill.triggers.length > 3 && (
                        <span className="text-[10px] text-[#5a7690]">
                          +{skill.triggers.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Author */}
                  {skill.author && (
                    <div className="mt-3 pt-3 border-t border-[#233648]">
                      <span className="text-xs text-[#5a7690]">by {skill.author}</span>
                    </div>
                  )}

                  {/* Status */}
                  <div className="mt-auto pt-3">
                    <div className="flex items-center gap-2 text-xs font-medium text-primary">
                      <span className={`size-1.5 rounded-full ${skill.is_loaded ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></span>
                      {skill.is_loaded ? 'Loaded' : 'Lazy'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
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

          {/* Info Box */}
          <div className="mt-4 p-4 bg-[#1a2632] rounded-xl border border-[#233648]">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-primary">info</span>
              <div>
                <h4 className="font-bold text-sm mb-1">Como criar uma skill?</h4>
                <p className="text-xs text-[#92adc9] leading-relaxed">
                  Crie um arquivo <code className="bg-[#233648] px-1 rounded">.md</code> na pasta <code className="bg-[#233648] px-1 rounded">backend/skills/</code> com frontmatter YAML contendo name, description e triggers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default SkillsPage;