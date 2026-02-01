"""
KeaBot Agent - Memory
Gerenciamento de memória de sessão.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Session, Message, VisitedFile, get_session_maker


class SessionMemory:
    """Gerencia a memória de uma sessão de chat."""
    
    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self._messages: list[dict] = []
        self._visited_files: set[str] = set()
    
    @classmethod
    async def create(cls, llm_provider: str = "gemini", llm_model: str | None = None) -> "SessionMemory":
        """Cria uma nova sessão no banco de dados."""
        memory = cls()
        
        session_maker = get_session_maker()
        if session_maker:
            async with session_maker() as db:
                session = Session(
                    id=memory.session_id,
                    llm_provider=llm_provider,
                    llm_model=llm_model
                )
                db.add(session)
                await db.commit()
        
        return memory
    
    @classmethod
    async def load(cls, session_id: str) -> Optional["SessionMemory"]:
        """Carrega uma sessão existente do banco de dados."""
        session_maker = get_session_maker()
        if not session_maker:
            return None
        
        async with session_maker() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            memory = cls(session_id=session_id)
            
            # Carrega mensagens
            msg_result = await db.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.id)
            )
            for msg in msg_result.scalars():
                memory._messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.tool_name
                })
            
            # Carrega arquivos visitados
            files_result = await db.execute(
                select(VisitedFile)
                .where(VisitedFile.session_id == session_id)
            )
            for f in files_result.scalars():
                memory._visited_files.add(f.file_path)
            
            return memory
    
    async def add_message(self, role: str, content: str, **kwargs) -> None:
        """Adiciona uma mensagem à sessão."""
        msg_dict = {"role": role, "content": content, **kwargs}
        self._messages.append(msg_dict)
        
        session_maker = get_session_maker()
        if session_maker:
            async with session_maker() as db:
                message = Message(
                    session_id=self.session_id,
                    role=role,
                    content=content,
                    tool_calls=kwargs.get("tool_calls"),
                    tool_call_id=kwargs.get("tool_call_id"),
                    tool_name=kwargs.get("name")
                )
                db.add(message)
                await db.commit()
    
    async def add_visited_file(self, file_path: str) -> None:
        """Registra um arquivo visitado."""
        self._visited_files.add(file_path)
        
        session_maker = get_session_maker()
        if session_maker:
            async with session_maker() as db:
                # Verifica se já existe
                result = await db.execute(
                    select(VisitedFile).where(
                        VisitedFile.session_id == self.session_id,
                        VisitedFile.file_path == file_path
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    existing.visit_count += 1
                else:
                    db.add(VisitedFile(
                        session_id=self.session_id,
                        file_path=file_path
                    ))
                
                await db.commit()
    
    @property
    def messages(self) -> list[dict]:
        """Retorna todas as mensagens."""
        return self._messages.copy()
    
    @property
    def visited_files(self) -> list[str]:
        """Retorna arquivos visitados."""
        return list(self._visited_files)
    
    def get_context_summary(self, max_messages: int = 20) -> str:
        """Retorna resumo do contexto para o prompt."""
        recent = self._messages[-max_messages:]
        lines = []
        
        for msg in recent:
            role = msg["role"].upper()
            content = msg.get("content", "")[:200]
            lines.append(f"[{role}]: {content}")
        
        return "\n".join(lines)


async def list_sessions(limit: int = 20) -> list[dict]:
    """Lista sessões recentes."""
    session_maker = get_session_maker()
    if not session_maker:
        return []
    
    async with session_maker() as db:
        result = await db.execute(
            select(Session)
            .where(Session.is_active == True)
            .order_by(Session.updated_at.desc())
            .limit(limit)
        )
        
        sessions = []
        for s in result.scalars():
            sessions.append({
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "llm_provider": s.llm_provider,
                "tool_call_count": s.tool_call_count
            })
        
        return sessions
