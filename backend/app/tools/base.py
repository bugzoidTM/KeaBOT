"""
KeaBot Tools - Base Classes
Define a estrutura base para todas as ferramentas do agente.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar
from pydantic import BaseModel, Field
import json


class ToolParameter(BaseModel):
    """Define um parâmetro de ferramenta."""
    name: str
    type: str  # "string", "integer", "boolean", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


class ToolDefinition(BaseModel):
    """Definição de uma ferramenta para a LLM."""
    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    
    def to_gemini_format(self) -> dict:
        """Converte para formato de function declaration do Gemini."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type.upper(),
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": required
            }
        }
    
    def to_openai_format(self) -> dict:
        """Converte para formato de function do OpenAI."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolResult(BaseModel):
    """Resultado da execução de uma ferramenta."""
    success: bool
    data: Any = None
    error: str | None = None
    
    def to_observation(self) -> str:
        """Converte resultado para texto de observação."""
        if self.success:
            if isinstance(self.data, (dict, list)):
                return json.dumps(self.data, indent=2, ensure_ascii=False)
            return str(self.data)
        return f"[ERROR] {self.error}"


class Tool(ABC):
    """Classe base abstrata para todas as ferramentas."""
    
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Retorna a definição da ferramenta."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Executa a ferramenta com os parâmetros fornecidos."""
        pass
    
    @property
    def name(self) -> str:
        return self.definition.name
    
    @property
    def description(self) -> str:
        return self.definition.description


class ToolRegistry:
    """Registro de todas as ferramentas disponíveis."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Registra uma ferramenta."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Tool | None:
        """Retorna uma ferramenta pelo nome."""
        return self._tools.get(name)
    
    def get_all(self) -> list[Tool]:
        """Retorna todas as ferramentas registradas."""
        return list(self._tools.values())
    
    def get_definitions(self) -> list[ToolDefinition]:
        """Retorna definições de todas as ferramentas."""
        return [tool.definition for tool in self._tools.values()]
    
    def to_gemini_format(self) -> list[dict]:
        """Retorna todas as ferramentas no formato Gemini."""
        return [tool.definition.to_gemini_format() for tool in self._tools.values()]
    
    def to_openai_format(self) -> list[dict]:
        """Retorna todas as ferramentas no formato OpenAI."""
        return [tool.definition.to_openai_format() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Executa uma ferramenta pelo nome."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )


# Singleton global registry
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Retorna o registro global de ferramentas."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


# Decorator for easy tool creation
T = TypeVar('T', bound=Tool)


def register_tool(tool_class: type[T]) -> type[T]:
    """Decorator para registrar uma ferramenta automaticamente."""
    registry = get_registry()
    registry.register(tool_class())
    return tool_class
