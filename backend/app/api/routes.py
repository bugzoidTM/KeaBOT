"""
KeaBot API Routes
REST endpoints para o agente.
"""

from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.core import Agent, AgentState, get_agent
from app.agent.llm import get_provider
from app.agent.memory import SessionMemory, list_sessions
from app.config import get_settings

import json
import asyncio


router = APIRouter(prefix="/api", tags=["chat"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Requisição de chat."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    llm_provider: Optional[str] = Field(default=None, description="gemini or openai")
    stream: bool = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Resposta de chat."""
    session_id: str
    content: str
    tool_calls: list[dict] = []
    tool_results: list[dict] = []
    thinking: Optional[str] = None
    visited_files: list[str] = []


class SessionResponse(BaseModel):
    """Resposta de sessão."""
    id: str
    title: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    llm_provider: str
    tool_call_count: int


class SettingsResponse(BaseModel):
    """Configurações do sistema."""
    llm_provider: str
    allowed_paths: list[str]
    safety_mode: str
    available_tools: list[str]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal de chat.
    
    Recebe uma mensagem e retorna a resposta do agente.
    O agente pode usar ferramentas para navegar o sistema de arquivos.
    """
    # Carrega ou cria sessão
    if request.session_id:
        memory = await SessionMemory.load(request.session_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        memory = await SessionMemory.create(
            llm_provider=request.llm_provider or "gemini"
        )
    
    # Cria provider customizado se necessário
    provider = None
    if request.llm_provider:
        provider = get_provider(request.llm_provider)
    
    # Cria estado do agente
    state = AgentState(
        session_id=memory.session_id,
        messages=memory.messages,
        visited_files=set(memory.visited_files)
    )
    
    # Executa agente
    agent = Agent(provider=provider) if provider else get_agent()
    response = await agent.run(request.message, state)
    
    # Salva mensagens no memory
    await memory.add_message("user", request.message)
    await memory.add_message("assistant", response.content)
    
    for file in state.visited_files:
        await memory.add_visited_file(file)
    
    return ChatResponse(
        session_id=memory.session_id,
        content=response.content,
        tool_calls=[tc for tc in response.tool_results if tc.get("tool_name")],
        tool_results=response.tool_results,
        thinking=response.thinking,
        visited_files=list(state.visited_files)
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Endpoint de chat com streaming.
    
    Retorna eventos SSE conforme o agente processa.
    """
    # Carrega ou cria sessão
    if request.session_id:
        memory = await SessionMemory.load(request.session_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        memory = await SessionMemory.create(
            llm_provider=request.llm_provider or "gemini"
        )
    
    provider = None
    if request.llm_provider:
        provider = get_provider(request.llm_provider)
    
    state = AgentState(
        session_id=memory.session_id,
        messages=memory.messages,
        visited_files=set(memory.visited_files)
    )
    
    agent = Agent(provider=provider) if provider else get_agent()
    
    async def event_generator():
        """Gera eventos SSE."""
        full_content = ""
        
        try:
            async for event in agent.run_stream(request.message, state):
                event_type = event.get("type", "unknown")
                data = event.get("data", "")
                
                if event_type == "content":
                    full_content += data
                
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # Salva após completar
            await memory.add_message("user", request.message)
            await memory.add_message("assistant", full_content)
            
            for file in state.visited_files:
                await memory.add_visited_file(file)
            
            # Evento final com session_id
            yield f"event: session\n"
            yield f"data: {json.dumps({'session_id': memory.session_id})}\n\n"
            
        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def get_sessions(limit: int = 20):
    """Lista sessões recentes."""
    sessions = await list_sessions(limit)
    return [SessionResponse(**s) for s in sessions]


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retorna detalhes de uma sessão."""
    memory = await SessionMemory.load(session_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": memory.session_id,
        "messages": memory.messages,
        "visited_files": memory.visited_files
    }


@router.get("/settings", response_model=SettingsResponse)
async def get_system_settings():
    """Retorna configurações do sistema."""
    settings = get_settings()
    
    from app.tools.base import get_registry
    registry = get_registry()
    
    return SettingsResponse(
        llm_provider=settings.llm_provider,
        allowed_paths=[str(p) for p in settings.allowed_paths_list],
        safety_mode=settings.keabot_safety_mode,
        available_tools=[t.name for t in registry.get_all()]
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "keabot-backend"}
