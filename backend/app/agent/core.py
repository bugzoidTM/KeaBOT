"""
KeaBot Agent - Core (ReAct Loop)
Implementa o loop Thought -> Plan -> Action -> Observation.
"""

import asyncio
from typing import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from app.agent.llm import get_provider, LLMProvider
from app.agent.prompts import get_system_prompt
from app.tools.base import get_registry, ToolResult, ToolRegistry
# Import filesystem to trigger registration
import app.tools.filesystem  # noqa: F401


@dataclass
class AgentState:
    """Estado do agente durante uma sessão."""
    session_id: str
    messages: list[dict] = field(default_factory=list)
    visited_files: set[str] = field(default_factory=set)
    tool_call_count: int = 0
    max_tool_calls: int = 10  # Limite de segurança
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Resposta do agente."""
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    thinking: str | None = None
    finished: bool = True


class Agent:
    """
    KeaBot Agent - O cérebro do sistema.
    
    Implementa o loop ReAct (Reasoning + Acting):
    1. Recebe mensagem do usuário
    2. Decide se precisa de ferramentas
    3. Executa ferramentas se necessário
    4. Usa resultados para formular resposta
    5. Repete até ter resposta final
    """
    
    def __init__(
        self,
        provider: LLMProvider | None = None,
        tools: ToolRegistry | None = None
    ):
        self.provider = provider or get_provider()
        self.tools = tools or get_registry()
        self.system_prompt = get_system_prompt()
    
    async def run(
        self,
        message: str,
        state: AgentState | None = None
    ) -> AgentResponse:
        """
        Executa o agente com uma mensagem.
        
        ReAct Loop:
        1. Envia mensagem + histórico para LLM
        2. Se LLM chamar tool → executa e repete
        3. Se LLM responder texto → retorna resposta
        """
        if state is None:
            state = AgentState(session_id="default")
        
        # Adiciona mensagem do usuário
        state.messages.append({
            "role": "user",
            "content": message
        })
        
        # Loop ReAct
        all_tool_results = []
        thinking_parts = []
        
        while state.tool_call_count < state.max_tool_calls:
            # Chama LLM
            response = await self.provider.chat(
                messages=state.messages,
                tools=self.tools,
                system_prompt=self.system_prompt
            )
            
            # Se houver tool calls, executa
            if response.get("tool_calls"):
                state.tool_call_count += len(response["tool_calls"])
                
                # Adiciona resposta do assistente com tool calls
                state.messages.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "tool_calls": response["tool_calls"]
                })
                
                # Guarda pensamento se houver
                if response.get("content"):
                    thinking_parts.append(response["content"])
                
                # Executa cada tool
                for tool_call in response["tool_calls"]:
                    result = await self.tools.execute(
                        tool_call["name"],
                        **tool_call["arguments"]
                    )
                    
                    # Rastreia arquivos visitados
                    if tool_call["name"] in ["read_file_chunk", "file_stats"]:
                        path = tool_call["arguments"].get("path", "")
                        if path:
                            state.visited_files.add(path)
                    
                    tool_result = {
                        "tool_name": tool_call["name"],
                        "tool_call_id": tool_call["id"],
                        "success": result.success,
                        "result": result.to_observation()
                    }
                    all_tool_results.append(tool_result)
                    
                    # Adiciona resultado como mensagem de tool
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "content": result.to_observation()
                    })
                
                # Continua o loop para processar resultados
                continue
            
            # Se não houver tool calls, temos resposta final
            final_content = response.get("content", "")
            
            # Adiciona resposta do assistente
            state.messages.append({
                "role": "assistant",
                "content": final_content
            })
            
            return AgentResponse(
                content=final_content,
                tool_results=all_tool_results,
                thinking="\n".join(thinking_parts) if thinking_parts else None,
                finished=True
            )
        
        # Atingiu limite de tool calls
        return AgentResponse(
            content="⚠️ Atingi o limite de operações. Por favor, seja mais específico sobre o que você precisa.",
            tool_results=all_tool_results,
            thinking="\n".join(thinking_parts) if thinking_parts else None,
            finished=True
        )
    
    async def run_stream(
        self,
        message: str,
        state: AgentState | None = None
    ) -> AsyncIterator[dict]:
        """
        Versão streaming do agente.
        Emite eventos conforme processa.
        """
        if state is None:
            state = AgentState(session_id="default")
        
        state.messages.append({
            "role": "user",
            "content": message
        })
        
        while state.tool_call_count < state.max_tool_calls:
            # Streaming da LLM
            full_response = {"content": "", "tool_calls": []}
            
            async for chunk in self.provider.chat_stream(
                messages=state.messages,
                tools=self.tools,
                system_prompt=self.system_prompt
            ):
                if chunk.get("content"):
                    full_response["content"] += chunk["content"]
                    yield {
                        "type": "content",
                        "data": chunk["content"]
                    }
                
                if chunk.get("tool_calls"):
                    full_response["tool_calls"].extend(chunk["tool_calls"])
            
            # Processa tool calls
            if full_response["tool_calls"]:
                state.tool_call_count += len(full_response["tool_calls"])
                
                state.messages.append({
                    "role": "assistant",
                    "content": full_response["content"],
                    "tool_calls": full_response["tool_calls"]
                })
                
                for tool_call in full_response["tool_calls"]:
                    yield {
                        "type": "tool_start",
                        "data": {
                            "name": tool_call["name"],
                            "arguments": tool_call["arguments"]
                        }
                    }
                    
                    result = await self.tools.execute(
                        tool_call["name"],
                        **tool_call["arguments"]
                    )
                    
                    if tool_call["name"] in ["read_file_chunk", "file_stats"]:
                        path = tool_call["arguments"].get("path", "")
                        if path:
                            state.visited_files.add(path)
                    
                    yield {
                        "type": "tool_end",
                        "data": {
                            "name": tool_call["name"],
                            "success": result.success,
                            "result": result.to_observation()[:500]  # Truncate for streaming
                        }
                    }
                    
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["name"],
                        "content": result.to_observation()
                    })
                
                continue
            
            # Resposta final
            state.messages.append({
                "role": "assistant",
                "content": full_response["content"]
            })
            
            yield {
                "type": "done",
                "data": {
                    "visited_files": list(state.visited_files),
                    "tool_calls": state.tool_call_count
                }
            }
            return
        
        # Limite atingido
        yield {
            "type": "error",
            "data": "Tool call limit reached"
        }


# Singleton agent instance
_agent: Agent | None = None


def get_agent() -> Agent:
    """Retorna instância singleton do agente."""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent
