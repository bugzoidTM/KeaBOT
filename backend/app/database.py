"""
KeaBot Database - SQLite with SQLAlchemy
Persistência de sessões, mensagens e arquivos visitados.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, JSON, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config import get_settings


class Base(DeclarativeBase):
    """Base para todos os modelos."""
    pass


class Session(Base):
    """Sessão de chat do usuário."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # LLM settings for this session
    llm_provider = Column(String(50), default="gemini")
    llm_model = Column(String(100), nullable=True)
    
    # State
    is_active = Column(Boolean, default=True)
    tool_call_count = Column(Integer, default=0)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    visited_files = relationship("VisitedFile", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Mensagem em uma sessão."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    role = Column(String(20), nullable=False)  # user, assistant, tool
    content = Column(Text, nullable=True)
    
    # Tool-specific fields
    tool_calls = Column(JSON, nullable=True)  # For assistant messages with tool calls
    tool_call_id = Column(String(100), nullable=True)  # For tool response messages
    tool_name = Column(String(100), nullable=True)  # For tool response messages
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="messages")


class VisitedFile(Base):
    """Arquivo visitado durante uma sessão."""
    __tablename__ = "visited_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    first_visited_at = Column(DateTime, default=datetime.utcnow)
    visit_count = Column(Integer, default=1)
    
    # Relationships
    session = relationship("Session", back_populates="visited_files")


# Database engine and session
_engine = None
_async_session_maker = None


async def init_db():
    """Inicializa o banco de dados."""
    global _engine, _async_session_maker
    
    settings = get_settings()
    _engine = create_async_engine(settings.database_url, echo=False)
    _async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Retorna uma sessão do banco de dados."""
    global _async_session_maker
    
    if _async_session_maker is None:
        await init_db()
    
    async with _async_session_maker() as session:
        yield session


def get_session_maker():
    """Retorna o session maker para uso direto."""
    return _async_session_maker
