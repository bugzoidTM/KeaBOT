"""
KeaBot Agent - Core (ReAct Loop)
Implementa o loop Thought -> Plan -> Action -> Observation.
Com suporte a Skills dinâmicas.
"""

import asyncio
from typing import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from app.agent.llm import get_provider, LLMProvider
from app.agent.prompts import get_system_prompt, get_skill_injection_prompt
from app.tools.base import get_registry, ToolResult, ToolRegistry
# Import filesystem to trigger registration
import app.tools.filesystem  # noqa: F401


@dataclass
class AgentState:
    """Estado do agente durante uma sessão."""
    session_id: str
    messages: list[dict] = field(default_factory=list)
    visited_files: set[str] = field(default_factory=set)
    activated_skills: set[str] = field(default_factory=set)
    tool_call_count: int = 0
    max_tool_calls: int = 15  # Aumentado para suportar skills
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Resposta do agente."""
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    thinking: str | None = None
    activated_skills: list[str] = field(default_factory=list)
    finished: bool = True


class Agent:
    """
    KeaBot Agent - O cérebro do sistema.
    
    Implementa o loop ReAct (Reasoning + Acting):
    1. Recebe mensagem do usuário
    2. Decide se precisa de ferramentas ou skills
    3. Executa ferramentas/skills se necessário
    4. Usa resultados para formular resposta
    5. Repete até ter resposta final
    """
    
    def __init__(
        self,
        provider: LLMProvider | None = None,
        tools: ToolRegistry | None = None,
        skill_manager = None
    ):
        self.provider = provider or get_provider()
        self.tools = tools or get_registry()
        self.skill_manager = skill_manager
        self._system_prompt = None
    
    def _get_system_prompt(self) -> str:
        """Gera system prompt com skills summary e identity."""
        if self._system_prompt:
            # return self._system_prompt
            # FORCE REFRESH for now to allow dynamic updates
            pass
        
        skills_summary = ""
        identity_content = ""

        if self.skill_manager:
            skills_summary = self.skill_manager.get_skills_summary()
            
            # Tenta carregar identidade customizada
            # Procura por skill com nome "Core Identity" ou slug "core_identity"
            identity_skill = None
            for s in self.skill_manager.skills.values():
                if s.name == "Core Identity" or s._slug() == "core_identity":
                    identity_skill = s
                    break
            
            if identity_skill:
                # Garante que conteúdo está carregado
                self.skill_manager.load_skill_content(identity_skill)
                identity_content = identity_skill.content
        
        self._system_prompt = get_system_prompt(skills_summary, identity_content)
        return self._system_prompt
    
    def _is_skill_call(self, tool_name: str) -> bool:
        """Verifica se é uma chamada de skill."""
        return tool_name.startswith("skill_")
    
    async def _handle_skill_activation(
        self,
        tool_call: dict,
        state: AgentState
    ) -> ToolResult:
        """
        Processa ativação de uma skill.
        Carrega conteúdo completo e injeta no contexto.
        """
        tool_name = tool_call["name"]
        query = tool_call["arguments"].get("query", "")
        
        # Extrai nome da skill (remove prefix "skill_")
        skill_slug = tool_name[6:]  # Remove "skill_"
        
        # Busca skill no manager
        if not self.skill_manager:
            return ToolResult(
                success=False,
                error="Skill manager not available"
            )
        
        # Encontra a skill pelo slug
        skill = None
        for s in self.skill_manager.skills.values():
            if s._slug() == skill_slug:
                skill = s
                break
        
        if not skill:
            return ToolResult(
                success=False,
                error=f"Skill '{skill_slug}' not found"
            )
        
        # Carrega conteúdo completo (lazy loading)
        self.skill_manager.load_skill_content(skill)
        
        # Marca como ativada
        state.activated_skills.add(skill.name)
        
        # Retorna instruções da skill
        return ToolResult(
            success=True,
            data={
                "skill_name": skill.name,
                "instructions": skill.content,
                "message": f"✅ Skill '{skill.name}' ativada!\n\nSiga as instruções abaixo:\n\n{skill.content}"
            }
        )
    
    async def run(
        self,
        message: str,
        state: AgentState | None = None
    ) -> AgentResponse:
        """
        Executa o agente com uma mensagem.
        
        ReAct Loop:
        1. Envia mensagem + histórico para LLM
        2. Se LLM chamar tool/skill → executa e repete
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
        system_prompt = self._get_system_prompt()
        
        while state.tool_call_count < state.max_tool_calls:
            # Chama LLM
            response = await self.provider.chat(
                messages=state.messages,
                tools=self.tools,
                system_prompt=system_prompt
            )
            
            print(f"[Agent] LLM Response: content={response.get('content', '')[:100]}, tool_calls={len(response.get('tool_calls', []))}")
            
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
                    tool_name = tool_call["name"]
                    
                    # Verifica se é skill ou tool normal
                    if self._is_skill_call(tool_name):
                        result = await self._handle_skill_activation(tool_call, state)
                    else:
                        result = await self.tools.execute(
                            tool_name,
                            **tool_call["arguments"]
                        )
                    
                    # Rastreia arquivos visitados
                    if tool_name in ["read_file_chunk", "file_stats"]:
                        path = tool_call["arguments"].get("path", "")
                        if path:
                            state.visited_files.add(path)
                    
                    tool_result = {
                        "tool_name": tool_name,
                        "tool_call_id": tool_call["id"],
                        "success": result.success,
                        "result": result.to_observation()
                    }
                    all_tool_results.append(tool_result)
                    
                    # Adiciona resultado como mensagem de tool
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
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
                activated_skills=list(state.activated_skills),
                finished=True
            )
        
        # Atingiu limite de tool calls
        return AgentResponse(
            content="⚠️ Atingi o limite de operações. Por favor, seja mais específico sobre o que você precisa.",
            tool_results=all_tool_results,
            thinking="\n".join(thinking_parts) if thinking_parts else None,
            activated_skills=list(state.activated_skills),
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
        
        system_prompt = self._get_system_prompt()
        
        while state.tool_call_count < state.max_tool_calls:
            # Streaming da LLM
            full_response = {"content": "", "tool_calls": []}
            
            async for chunk in self.provider.chat_stream(
                messages=state.messages,
                tools=self.tools,
                system_prompt=system_prompt
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
                    tool_name = tool_call["name"]
                    
                    yield {
                        "type": "tool_start",
                        "data": {
                            "name": tool_name,
                            "arguments": tool_call["arguments"],
                            "is_skill": self._is_skill_call(tool_name)
                        }
                    }
                    

                    # Verifica se é skill
                    if self._is_skill_call(tool_name):
                        result = await self._handle_skill_activation(tool_call, state)
                        yield {
                            "type": "skill_activated",
                            "data": {
                                "name": tool_name[6:],  # Remove "skill_"
                                "success": result.success
                            }
                        }
                    else:
                        # Safety Check
                        sensitive_tools = ["write_to_file", "replace_file_content", "run_command", "delete_file"]
                        approved = True
                        
                        if tool_name in sensitive_tools:
                            from app.services.approval import get_approval_service
                            approval_service = get_approval_service()
                            req_id = approval_service.create_request()
                            
                            yield {
                                "type": "approval_required",
                                "data": {
                                    "approval_id": req_id,
                                    "tool_name": tool_name,
                                    "arguments": tool_call["arguments"]
                                }
                            }
                            
                            # Aguarda aprovação
                            approved = await approval_service.wait_for_approval(req_id)
                        
                        if approved:
                            result = await self.tools.execute(
                                tool_name,
                                **tool_call["arguments"]
                            )
                        else:
                            result = ToolResult(
                                success=False,
                                error="Ação rejeitada pelo usuário ou timeout."
                            )
                            # Avisa frontend que foi rejeitado/cancelado
                            yield {
                                "type": "error",
                                "data": "Ação cancelada pelo usuário."
                            }
                    
                    if tool_name in ["read_file_chunk", "file_stats"]:
                        path = tool_call["arguments"].get("path", "")
                        if path:
                            state.visited_files.add(path)
                    
                    yield {
                        "type": "tool_end",
                        "data": {
                            "name": tool_name,
                            "success": result.success,
                            "result": result.to_observation()[:500]  # Truncate for streaming
                        }
                    }
                    
                    state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
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
                    "activated_skills": list(state.activated_skills),
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


def get_agent(skill_manager=None) -> Agent:
    """Retorna instância singleton do agente."""
    global _agent
    if _agent is None:
        _agent = Agent(skill_manager=skill_manager)
    return _agent


def create_agent(provider=None, tools=None, skill_manager=None) -> Agent:
    """Cria nova instância do agente com configurações customizadas."""
    return Agent(provider=provider, tools=tools, skill_manager=skill_manager)

