/**
 * KeaBot API Service
 * Conecta o frontend React ao backend Python via SSE streaming.
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface ToolEvent {
    type: 'tool_start' | 'tool_end' | 'skill_activated';
    name: string;
    arguments?: Record<string, unknown>;
    success?: boolean;
    result?: string;
    is_skill?: boolean;
}

export interface ApprovalRequest {
    approval_id: string;
    tool_name: string;
    arguments: Record<string, unknown>;
}

export interface ChatStreamCallbacks {
    onContent: (text: string) => void;
    onToolStart: (event: ToolEvent) => void;
    onToolEnd: (event: ToolEvent) => void;
    onSkillActivated: (event: ToolEvent) => void;
    onApprovalRequired: (request: ApprovalRequest) => void;
    onDone: (data: { visited_files: string[]; activated_skills: string[]; tool_calls: number }) => void;
    onError: (error: string) => void;
    onSession: (sessionId: string) => void;
}

// ... (interfaces BackendSkill, ChatResponse unchanged) ...

// ... (sendMessageStream implementation) ...


// ... (rest of switch) ...

// ... (API Functions) ...

/**
 * Aprova uma ação pendente.
 */
export async function approveAction(reqId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/approval/${reqId}/approve`, { method: 'POST' });
}

/**
 * Rejeita uma ação pendente.
 */
export async function rejectAction(reqId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/approval/${reqId}/reject`, { method: 'POST' });
}

// ... (existing updateConfig) ...


export interface BackendSkill {
    name: string;
    description: string;
    triggers: string[];
    author?: string;
    version?: string;
    is_loaded: boolean;
}

export interface ChatResponse {
    session_id: string;
    content: string;
    tool_calls: unknown[];
    tool_results: unknown[];
    thinking?: string;
    visited_files: string[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Envia mensagem com streaming via SSE.
 * Esta é a função principal para o chat.
 */
export async function sendMessageStream(
    message: string,
    callbacks: ChatStreamCallbacks,
    options: {
        sessionId?: string;
        llmProvider?: 'gemini' | 'openai';
    } = {}
): Promise<void> {
    const { sessionId, llmProvider } = options;

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                llm_provider: llmProvider,
                stream: true,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let buffer = '';
        let currentEventType = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('event:')) {
                    currentEventType = line.replace('event:', '').trim();
                    continue;
                }

                if (line.startsWith('data:')) {
                    const dataStr = line.replace('data:', '').trim();
                    if (!dataStr) continue;

                    try {
                        const data = JSON.parse(dataStr);

                        // Usa o tipo de evento SSE para determinar o handler
                        switch (currentEventType) {
                            case 'content':
                                // data é string de conteúdo
                                if (typeof data === 'string') {
                                    callbacks.onContent(data);
                                }
                                break;

                            case 'session':
                                if (data.session_id) {
                                    callbacks.onSession(data.session_id);
                                }
                                break;

                            case 'done':
                                callbacks.onDone(data);
                                break;

                            case 'tool_start':
                                callbacks.onToolStart({
                                    type: 'tool_start',
                                    name: data.name,
                                    arguments: data.arguments,
                                    is_skill: data.is_skill,
                                });
                                break;

                            case 'tool_end':
                                callbacks.onToolEnd({
                                    type: 'tool_end',
                                    name: data.name,
                                    success: data.success,
                                    result: data.result,
                                });
                                break;

                            case 'skill_activated':
                                callbacks.onSkillActivated({
                                    type: 'skill_activated',
                                    name: data.name,
                                    success: data.success,
                                });
                                break;

                            case 'approval_required':
                                callbacks.onApprovalRequired({
                                    approval_id: data.approval_id,
                                    tool_name: data.tool_name,
                                    arguments: data.arguments
                                });
                                break;

                            case 'error':
                                if (data.error) {
                                    callbacks.onError(String(data.error));
                                }
                                break;

                            default:
                                // Fallback: tenta detectar pelo conteúdo
                                if (typeof data === 'string') {
                                    callbacks.onContent(data);
                                } else if (data.error) {
                                    callbacks.onError(String(data.error));
                                }
                        }
                    } catch {
                        // JSON parse error, ignore
                    }

                    // Reset event type after processing
                    currentEventType = '';
                }
            }
        }
    } catch (error) {
        callbacks.onError(error instanceof Error ? error.message : 'Unknown error');
    }
}

/**
 * Envia mensagem sem streaming (resposta única).
 */
export async function sendMessage(
    message: string,
    options: {
        sessionId?: string;
        llmProvider?: 'gemini' | 'openai';
    } = {}
): Promise<ChatResponse> {
    const { sessionId, llmProvider } = options;

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message,
            session_id: sessionId,
            llm_provider: llmProvider,
            stream: false,
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Lista todas as skills disponíveis no backend.
 */
export async function getSkills(): Promise<{ skills: BackendSkill[] }> {
    const response = await fetch(`${API_BASE_URL}/api/skills`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Força recarga de todas as skills.
 */
export async function reloadSkills(): Promise<{ success: boolean; skills_loaded: number; skills: string[] }> {
    const response = await fetch(`${API_BASE_URL}/api/skills/reload`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Verifica saúde do backend.
 */
export async function healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}/api/health`);

    if (!response.ok) {
        throw new Error('Backend not available');
    }

    return response.json();
}

/**
 * Retorna configurações do sistema.
 */
export async function getSettings(): Promise<{
    llm_provider: string;
    allowed_paths: string[];
    safety_mode: string;
    available_tools: string[];
}> {
    const response = await fetch(`${API_BASE_URL}/api/settings`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Retorna configuração atual (provider, model, api key status).
 */
export async function getConfig(): Promise<{
    provider: string;
    model: string;
    has_api_key: boolean;
    api_key_source: string;
}> {
    const response = await fetch(`${API_BASE_URL}/api/config`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Atualiza configurações em runtime.
 */
export async function updateConfig(config: {
    api_key?: string;
    provider?: string;
    model?: string;
}): Promise<{
    success: boolean;
    message: string;
    config: {
        provider: string;
        model: string;
        has_api_key: boolean;
    };
}> {
    const response = await fetch(`${API_BASE_URL}/api/config`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}
