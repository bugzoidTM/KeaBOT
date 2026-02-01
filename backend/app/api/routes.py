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
    from app.main import get_skill_manager
    skill_manager = get_skill_manager()
    agent = Agent(provider=provider, skill_manager=skill_manager) if provider else get_agent(skill_manager)
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
    
    from app.main import get_skill_manager
    skill_manager = get_skill_manager()
    agent = Agent(provider=provider, skill_manager=skill_manager) if provider else get_agent(skill_manager)
    
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
            error_msg = str(e)
            # Detecta erros comuns e traduz para mensagens amigáveis
            if "API key" in error_msg or "api_key" in error_msg.lower():
                friendly_msg = "🔑 **API Key não configurada!**\n\nPor favor, configure sua chave no arquivo `backend/.env`:\n```\nGEMINI_API_KEY=sua_chave_aqui\n```\n\nObtenha sua chave em: https://aistudio.google.com/"
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                friendly_msg = "⏳ **Limite de requisições atingido!**\n\nAguarde alguns minutos antes de tentar novamente."
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                friendly_msg = "🌐 **Erro de conexão!**\n\nVerifique sua conexão com a internet."
            else:
                friendly_msg = f"😅 **Ops! Algo deu errado:**\n\n`{error_msg}`"
            
            yield f"event: content\n"
            yield f"data: {json.dumps(friendly_msg, ensure_ascii=False)}\n\n"
            yield f"event: done\n"
            yield f"data: {json.dumps({'error': True})}\n\n"
    
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


# Runtime config storage (in-memory, per session)
_runtime_config = {
    "api_key": None,
    "provider": None,
    "model": None,
}


class ConfigUpdateRequest(BaseModel):
    """Request para atualizar configurações."""
    api_key: Optional[str] = None
    provider: Optional[str] = Field(None, description="gemini or openai")
    model: Optional[str] = None


class ConfigResponse(BaseModel):
    """Resposta de configuração."""
    provider: str
    model: str
    has_api_key: bool
    api_key_source: str  # "runtime" or "env"


@router.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """
    Atualiza configurações em runtime.
    API keys são mantidas apenas em memória por segurança.
    """
    if request.api_key:
        _runtime_config["api_key"] = request.api_key
    if request.provider:
        _runtime_config["provider"] = request.provider
    if request.model:
        _runtime_config["model"] = request.model
    
    return {
        "success": True,
        "message": "Configurações atualizadas!",
        "config": {
            "provider": _runtime_config["provider"] or get_settings().llm_provider,
            "model": _runtime_config["model"] or get_settings().gemini_model,
            "has_api_key": bool(_runtime_config["api_key"]),
        }
    }


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Retorna configuração atual."""
    settings = get_settings()
    
    has_runtime_key = bool(_runtime_config["api_key"])
    has_env_key = bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here")
    
    return ConfigResponse(
        provider=_runtime_config["provider"] or settings.llm_provider,
        model=_runtime_config["model"] or settings.gemini_model,
        has_api_key=has_runtime_key or has_env_key,
        api_key_source="runtime" if has_runtime_key else ("env" if has_env_key else "none")
    )


def get_runtime_api_key() -> str | None:
    """Retorna API key do runtime ou None."""
    return _runtime_config.get("api_key")


def get_runtime_provider() -> str | None:
    """Retorna provider do runtime ou None."""
    return _runtime_config.get("provider")


def get_runtime_model() -> str | None:
    """Retorna model do runtime ou None."""
    return _runtime_config.get("model")



class ScheduleRequest(BaseModel):
    """Requisição de agendamento."""
    instruction: str
    name: str = "Scheduled Task"


@router.post("/schedule")
async def schedule_task(request: ScheduleRequest):
    """
    Cria um novo agendamento usando LLM para parsear cron.
    """
    # 1. Usa LLM para converter instrução em CRON
    from app.config import get_settings
    from app.agent.llm import get_provider
    import re
    
    settings = get_settings()
    provider = get_provider(settings.llm_provider)
    
    prompt = f"""
    Converta a seguinte instrução de agendamento para uma expressão CRON padrão (5 campos).
    Instrução: "{request.instruction}"
    
    Responda APENAS a expressão cron. Exemplo: "0 9 * * *"
    Se não conseguir entender, responda "ERROR".
    """
    
    response = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        tools=[],
        system_prompt="You are a system scheduler helper."
    )
    
    cron_expr = response["content"].strip().replace('`', '')
    
    if "ERROR" in cron_expr or len(cron_expr.split()) < 5:
        raise HTTPException(status_code=400, detail="Não consegui entender a frequência de agendamento.")
    
    # 2. Agenda o job
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    
    try:
        job_id = await scheduler.add_job(
            name=request.name,
            instruction=request.instruction,
            schedule=cron_expr
        )
        return {
            "success": True,
            "job_id": job_id,
            "schedule": cron_expr,
            "message": f"Tarefa agendada: {cron_expr}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approval/{req_id}/approve")
async def approve_request(req_id: str):
    """Aprova uma solicitação de ação sensível."""
    from app.services.approval import get_approval_service
    get_approval_service().approve(req_id)
    return {"success": True}


@router.post("/approval/{req_id}/reject")
async def reject_request(req_id: str):
    """Rejeita uma solicitação de ação sensível."""
    from app.services.approval import get_approval_service
    get_approval_service().reject(req_id)
    return {"success": True}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "keabot-backend"}


# --- Skills Management ---

class SkillRequest(BaseModel):
    name: str = Field(..., min_length=1)
    content: str
    description: Optional[str] = ""

@router.get("/skills")
async def list_skills():
    """Lista todas as skills (resumo)."""
    from app.main import get_skill_manager
    manager = get_skill_manager()
    
    # Force reload to ensure file sync
    # manager.reload_skills() # Too heavy? Maybe
    
    return {
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "author": s.author,
                "version": s.version,
                "is_loaded": s.is_loaded,
                "slug": s._slug(),
                "triggers": s.triggers
            }
            for s in manager.skills.values()
        ]
    }

@router.get("/skills/{slug}")
async def get_skill(slug: str):
    """Retorna conteúdo completo de uma skill."""
    from app.main import get_skill_manager
    manager = get_skill_manager()
    
    # Busca skill por slug
    target_skill = None
    for s in manager.skills.values():
        if s._slug() == slug:
            target_skill = s
            break
            
    if not target_skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Garante que conteúdo está carregado
    manager.load_skill_content(target_skill)
    
    return {
        "name": target_skill.name,
        "description": target_skill.description,
        "content": target_skill.content,
        "file_path": str(target_skill.file_path),
        "triggers": target_skill.triggers,
        "slug": target_skill._slug()
    }

@router.post("/skills")
async def save_skill(request: SkillRequest):
    """Cria ou atualiza uma skill."""
    from app.main import get_skill_manager
    manager = get_skill_manager()
    
    success = manager.save_skill(request.name, request.content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save skill")
    
    return {"success": True, "message": f"Skill '{request.name}' salva com sucesso."}

@router.delete("/skills/{slug}")
async def delete_skill(slug: str):
    """Exclui uma skill."""
    from app.main import get_skill_manager
    manager = get_skill_manager()
    
    success = manager.delete_skill(slug)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete skill")
    
    return {"success": True, "message": "Skill excluída com sucesso."}

@router.post("/skills/reload")
async def reload_skills_endpoint():
    from app.main import get_skill_manager
    get_skill_manager().reload_skills()
    return {"success": True}

