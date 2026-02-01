import React from 'react';
import { ToolEvent } from '../services/apiService';

interface AgentActivityProps {
    activities: ToolEvent[];
    isActive: boolean;
}

/**
 * AgentActivity - "Ghost in the Machine"
 * Mostra feedback visual das ferramentas sendo executadas pelo agente.
 */
const AgentActivity: React.FC<AgentActivityProps> = ({ activities, isActive }) => {
    if (!isActive && activities.length === 0) return null;

    // Pega as últimas 3 atividades
    const recentActivities = activities.slice(-3);

    const getToolIcon = (name: string, isSkill?: boolean): string => {
        if (isSkill || name.startsWith('skill_')) return 'auto_awesome';

        switch (name) {
            case 'list_directory': return 'folder_open';
            case 'grep_search': return 'search';
            case 'read_file_chunk': return 'description';
            case 'file_stats': return 'info';
            default: return 'build';
        }
    };

    const getToolLabel = (name: string): string => {
        // Remove prefixo skill_ se existir
        if (name.startsWith('skill_')) {
            return name.replace('skill_', '').replace(/_/g, ' ');
        }
        return name.replace(/_/g, ' ');
    };

    const formatArguments = (args?: Record<string, unknown>): string => {
        if (!args) return '';

        // Mostra argumentos de forma compacta
        const parts: string[] = [];
        if (args.path) parts.push(`"${args.path}"`);
        if (args.term) parts.push(`"${args.term}"`);
        if (args.query) parts.push(`"${args.query}"`);
        if (args.pattern) parts.push(`pattern: ${args.pattern}`);

        return parts.length > 0 ? `(${parts.join(', ')})` : '';
    };

    return (
        <div className="mx-4 sm:mx-10 md:mx-20 lg:mx-40 mb-4">
            <div className="max-w-[800px] mx-auto">
                <div className="bg-[#1a2632]/90 backdrop-blur-sm border border-[#233648] rounded-lg p-3 shadow-lg">
                    {/* Header */}
                    <div className="flex items-center gap-2 mb-2">
                        <div className={`size-2 rounded-full ${isActive ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
                        <span className="text-xs font-medium text-[#92adc9]">
                            {isActive ? 'Agent Working...' : 'Last Operations'}
                        </span>
                    </div>

                    {/* Activity List */}
                    <div className="flex flex-col gap-1.5">
                        {recentActivities.map((activity, index) => {
                            const isLast = index === recentActivities.length - 1;
                            const isRunning = isActive && isLast && activity.type === 'tool_start';

                            return (
                                <div
                                    key={`${activity.name}-${index}`}
                                    className={`flex items-center gap-2 text-sm transition-all ${isRunning ? 'text-white' : 'text-[#5a7690]'
                                        }`}
                                >
                                    {/* Icon */}
                                    <span className={`material-symbols-outlined text-[16px] ${activity.is_skill ? 'text-purple-400' :
                                            isRunning ? 'text-amber-400' :
                                                activity.success === false ? 'text-red-400' :
                                                    activity.success === true ? 'text-emerald-400' :
                                                        'text-[#5a7690]'
                                        }`}>
                                        {activity.type === 'tool_start' && isRunning ? 'sync' : getToolIcon(activity.name, activity.is_skill)}
                                    </span>

                                    {/* Content */}
                                    <div className="flex items-center gap-1.5 overflow-hidden">
                                        <code className={`font-mono text-xs ${isRunning ? 'text-amber-300' : ''}`}>
                                            {getToolLabel(activity.name)}
                                        </code>
                                        <span className="text-[11px] text-[#5a7690] truncate">
                                            {formatArguments(activity.arguments)}
                                        </span>
                                    </div>

                                    {/* Status */}
                                    {activity.type === 'tool_end' && (
                                        <span className={`ml-auto text-[10px] font-medium ${activity.success ? 'text-emerald-400' : 'text-red-400'
                                            }`}>
                                            {activity.success ? '✓' : '✗'}
                                        </span>
                                    )}

                                    {isRunning && (
                                        <span className="ml-auto">
                                            <span className="material-symbols-outlined text-[14px] text-amber-400 animate-spin">
                                                progress_activity
                                            </span>
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Skill Activated Badge */}
                    {activities.some(a => a.type === 'skill_activated') && (
                        <div className="mt-2 pt-2 border-t border-[#233648]">
                            <div className="flex items-center gap-2">
                                <span className="material-symbols-outlined text-[14px] text-purple-400">auto_awesome</span>
                                <span className="text-xs text-purple-300">
                                    Skill ativada: {activities.find(a => a.type === 'skill_activated')?.name}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AgentActivity;
