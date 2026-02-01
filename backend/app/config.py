"""
KeaBot Configuration
Gerencia configurações do sistema via variáveis de ambiente.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações do KeaBot Backend."""
    
    # LLM Provider
    llm_provider: Literal["gemini", "openai"] = Field(
        default="gemini",
        description="LLM provider to use"
    )
    
    # API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    
    # Model names
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")
    
    # Safety settings
    keabot_allowed_paths: str = Field(
        default=str(Path(__file__).parent.parent.parent),
        description="Comma-separated list of allowed paths for file operations"
    )
    keabot_safety_mode: Literal["strict", "permissive"] = Field(
        default="strict",
        description="Safety mode: strict requires approval for dangerous ops"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./keabot.db",
        description="Database connection URL"
    )
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def allowed_paths_list(self) -> list[Path]:
        """Retorna lista de paths permitidos como objetos Path."""
        paths = self.keabot_allowed_paths.split(",")
        return [Path(p.strip()).resolve() for p in paths if p.strip()]
    
    def is_path_allowed(self, path: str | Path) -> bool:
        """Verifica se um path está dentro dos paths permitidos."""
        target = Path(path).resolve()
        return any(
            target == allowed or allowed in target.parents
            for allowed in self.allowed_paths_list
        )


# Singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reseta o cache de settings (força reload do .env)."""
    global _settings
    _settings = None
