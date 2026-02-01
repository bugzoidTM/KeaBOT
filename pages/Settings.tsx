import React, { useState, useEffect } from 'react';
import { getConfig, updateConfig } from '../services/apiService';

// Simplified provider type for actual backend
type Provider = 'gemini' | 'openai' | 'anthropic' | 'deepseek';

interface ConfigState {
  provider: Provider;
  model: string;
  apiKey: string;
  hasApiKey: boolean;
  apiKeySource: string;
}

const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<ConfigState>({
    provider: 'gemini',
    model: 'gemini-2.5-flash',
    apiKey: '',
    hasApiKey: false,
    apiKeySource: 'none',
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  // Load config on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const data = await getConfig();
      setConfig(prev => ({
        ...prev,
        provider: data.provider as Provider,
        model: data.model,
        hasApiKey: data.has_api_key,
        apiKeySource: data.api_key_source,
      }));
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao carregar configurações' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setMessage(null);

      const updateData: { api_key?: string; provider?: string; model?: string } = {
        provider: config.provider,
        model: config.model,
      };

      // Only send API key if user entered one
      if (config.apiKey) {
        updateData.api_key = config.apiKey;
      }

      const result = await updateConfig(updateData);

      if (result.success) {
        setMessage({ type: 'success', text: '✅ ' + result.message });
        setConfig(prev => ({
          ...prev,
          apiKey: '', // Clear input after save
          hasApiKey: result.config.has_api_key,
          apiKeySource: 'runtime',
        }));
      }
    } catch (error) {
      setMessage({ type: 'error', text: '❌ Erro ao salvar configurações' });
    } finally {
      setIsSaving(false);
    }
  };

  const providers = [
    { id: 'gemini' as Provider, name: 'Google Gemini', desc: 'Models: 2.0 Flash, 2.5 Pro', icon: 'grid_view' },
    { id: 'openai' as Provider, name: 'OpenAI', desc: 'GPT-4o, GPT-4o Mini', icon: 'auto_awesome' },
    { id: 'anthropic' as Provider, name: 'Anthropic', desc: 'Claude 3.5 Sonnet, Haiku', icon: 'psychology', disabled: true },
    { id: 'deepseek' as Provider, name: 'DeepSeek', desc: 'DeepSeek V3/R1', icon: 'code_blocks' },
  ];

  const getModelsForProvider = (provider: Provider) => {
    switch (provider) {
      case 'gemini':
        return [
          { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash (Recomendado)' },
          { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
          { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
        ];
      case 'openai':
        return [
          { id: 'gpt-4o', name: 'GPT-4o' },
          { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
        ];
      case 'anthropic':
        return [
          { id: 'claude-3-5-sonnet-20240620', name: 'Claude 3.5 Sonnet' },
          { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
        ];
      case 'deepseek':
        return [
          { id: 'deepseek-chat', name: 'DeepSeek V3' },
          { id: 'deepseek-reasoner', name: 'DeepSeek R1 (Reasoner)' },
        ];
      default:
        return [];
    }
  };

  const models = getModelsForProvider(config.provider);

  const getApiKeyHelpText = (provider: Provider) => {
    switch (provider) {
      case 'gemini': return 'Obtenha sua chave em: https://aistudio.google.com/';
      case 'openai': return 'Obtenha sua chave em: https://platform.openai.com/';
      case 'anthropic': return 'Obtenha sua chave em: https://console.anthropic.com/';
      case 'deepseek': return 'Obtenha sua chave em: https://platform.deepseek.com/';
      default: return '';
    }
  };

  if (isLoading) {
    return (
      <main className="flex-1 flex items-center justify-center bg-[#101922]">
        <div className="text-white">Carregando configurações...</div>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#101922]">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 lg:px-12 scroll-smooth">
        <div className="max-w-4xl mx-auto flex flex-col gap-8 pb-24">

          {/* Breadcrumbs */}
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="text-text-secondary font-medium">Settings</span>
            <span className="text-text-secondary font-medium">/</span>
            <span className="text-white font-medium">LLM Configuration</span>
          </div>

          {/* Header */}
          <div className="flex flex-wrap justify-between items-end gap-4 border-b border-border-dark pb-6">
            <div className="flex flex-col gap-2">
              <h1 className="text-white text-3xl md:text-4xl font-bold tracking-tight">Configuração LLM</h1>
              <p className="text-text-secondary text-base max-w-2xl">
                Configure o provider de IA e sua API key. As configurações são salvas em memória.
              </p>
            </div>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 rounded-lg bg-primary hover:bg-blue-600 text-white shadow-lg shadow-blue-500/20 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[18px]">save</span>
              {isSaving ? 'Salvando...' : 'Salvar Configurações'}
            </button>
          </div>

          {/* Message */}
          {message && (
            <div className={`p-4 rounded-lg border ${message.type === 'success'
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
              }`}>
              {message.text}
            </div>
          )}

          {/* API Key Status */}
          <div className={`p-4 rounded-lg border ${config.hasApiKey
            ? 'bg-green-500/10 border-green-500/30'
            : 'bg-yellow-500/10 border-yellow-500/30'
            }`}>
            <div className="flex items-center gap-3">
              <span className={`material-symbols-outlined ${config.hasApiKey ? 'text-green-400' : 'text-yellow-400'}`}>
                {config.hasApiKey ? 'check_circle' : 'warning'}
              </span>
              <div>
                <p className={`font-medium ${config.hasApiKey ? 'text-green-400' : 'text-yellow-400'}`}>
                  {config.hasApiKey
                    ? `API Key configurada (${config.apiKeySource === 'runtime' ? 'via Settings' : 'via .env'})`
                    : 'API Key não configurada'}
                </p>
                <p className="text-text-secondary text-sm">
                  {config.hasApiKey
                    ? 'Você pode usar o chat normalmente.'
                    : 'Configure sua API key abaixo para usar o chat.'}
                </p>
              </div>
            </div>
          </div>

          {/* Provider Selection */}
          <div className="flex flex-col gap-4">
            <h3 className="text-white text-lg font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">dns</span>
              Provider
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {providers.map((p) => (
                <label
                  key={p.id}
                  className={`cursor-pointer relative flex flex-col gap-3 rounded-xl border p-4 transition-all
                    ${config.provider === p.id
                      ? 'border-primary bg-surface-dark shadow-md shadow-primary/10'
                      : 'border-border-dark hover:bg-surface-dark/50'
                    }
                    ${p.disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="bg-white/10 p-2 rounded-lg">
                      <span className="material-symbols-outlined text-white">{p.icon}</span>
                    </div>
                    <input
                      type="radio"
                      name="provider"
                      checked={config.provider === p.id}
                      onChange={() => !p.disabled && setConfig({ ...config, provider: p.id })}
                      disabled={p.disabled}
                      className="h-5 w-5 text-primary border-border-dark bg-transparent focus:ring-0 cursor-pointer"
                    />
                  </div>
                  <div>
                    <p className="text-white font-bold">{p.name}</p>
                    <p className="text-text-secondary text-xs">{p.desc}</p>
                    {p.disabled && <p className="text-yellow-400 text-xs mt-1">Em breve</p>}
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* API Key Input */}
          <div className="bg-surface-dark rounded-xl p-6 border border-border-dark/50">
            <h3 className="text-white text-lg font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">key</span>
              API Key
            </h3>
            <div className="flex flex-col gap-2">
              <label className="text-text-secondary text-sm font-medium">
                {config.provider === 'gemini' ? 'Gemini API Key' :
                  config.provider === 'openai' ? 'OpenAI API Key' :
                    config.provider === 'anthropic' ? 'Anthropic API Key' : 'DeepSeek API Key'}
              </label>
              <div className="relative flex items-center">
                <span className="absolute left-3 material-symbols-outlined text-text-secondary">key</span>
                <input
                  type={showApiKey ? "text" : "password"}
                  value={config.apiKey}
                  onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                  placeholder={config.hasApiKey ? "•••• (já configurada)" : "Cole sua API key aqui"}
                  className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-2.5 pl-10 pr-10 focus:border-primary focus:ring-1 focus:ring-primary placeholder-gray-600 transition-colors font-mono text-sm"
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 text-text-secondary hover:text-white"
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showApiKey ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
              </div>
              <p className="text-xs text-text-secondary mt-1">
                {getApiKeyHelpText(config.provider)}
              </p>
            </div>
          </div>

          {/* Model Selection */}
          <div className="bg-surface-dark rounded-xl p-6 border border-border-dark/50">
            <h3 className="text-white text-lg font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">psychology</span>
              Modelo
            </h3>
            <div className="flex flex-col gap-2">
              <label className="text-text-secondary text-sm font-medium">Modelo ativo</label>
              <div className="relative">
                <select
                  value={config.model}
                  onChange={(e) => setConfig({ ...config, model: e.target.value })}
                  className="w-full bg-background-dark text-white border border-border-dark rounded-lg py-2.5 pl-4 pr-10 focus:border-primary focus:ring-1 focus:ring-primary appearance-none cursor-pointer"
                >
                  {models.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
                <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-secondary pointer-events-none">expand_more</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </main>
  );
};

export default SettingsPage;