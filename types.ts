export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

export enum LLMProvider {
  OpenAI = 'OpenAI',
  Anthropic = 'Anthropic',
  Google = 'Google Vertex',
  Deepseek = 'Deepseek'
}

export interface AppSettings {
  provider: LLMProvider;
  model: string;
  temperature: number;
  topP: number;
  systemPrompt: string;
  storeHistory: boolean;
  anonymizePII: boolean;
}

export interface AutomationTask {
    id: string;
    name: string;
    description: string;
    status: 'active' | 'failed' | 'paused';
    lastRun: string;
    schedule: string;
    error?: string;
}

export interface Skill {
    id: string;
    name: string;
    description: string;
    icon: string;
    active: boolean;
    color: string;
}