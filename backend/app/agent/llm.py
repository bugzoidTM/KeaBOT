"""
KeaBot Agent - LLM Providers
Integração com Gemini e OpenAI APIs.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Any
import json

from app.config import get_settings
from app.tools.base import ToolRegistry, ToolResult


class LLMProvider(ABC):
    """Classe base abstrata para provedores de LLM."""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> dict:
        """Envia mensagem e retorna resposta."""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> AsyncIterator[dict]:
        """Envia mensagem e retorna stream de respostas."""
        pass


class GeminiProvider(LLMProvider):
    """Provider para Google Gemini API."""
    
    def __init__(self):
        import google.generativeai as genai
        
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.genai = genai
    
    async def chat(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> dict:
        """Envia mensagem para Gemini e retorna resposta."""
        # Configura ferramentas
        gemini_tools = None
        if tools:
            tool_declarations = tools.to_gemini_format()
            if tool_declarations:
                gemini_tools = [{"function_declarations": tool_declarations}]
        
        # Cria modelo
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            tools=gemini_tools
        )
        
        # Converte mensagens para formato Gemini
        gemini_messages = self._convert_messages(messages)
        
        # Inicia chat
        chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        
        # Envia última mensagem
        last_message = gemini_messages[-1] if gemini_messages else {"parts": [{"text": ""}]}
        response = await chat.send_message_async(last_message)
        
        return self._parse_response(response)
    
    async def chat_stream(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> AsyncIterator[dict]:
        """Stream de respostas do Gemini."""
        gemini_tools = None
        if tools:
            tool_declarations = tools.to_gemini_format()
            if tool_declarations:
                gemini_tools = [{"function_declarations": tool_declarations}]
        
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            tools=gemini_tools
        )
        
        gemini_messages = self._convert_messages(messages)
        chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        
        last_message = gemini_messages[-1] if gemini_messages else {"parts": [{"text": ""}]}
        response = await chat.send_message_async(last_message, stream=True)
        
        async for chunk in response:
            yield self._parse_response(chunk)
    
    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Converte mensagens do formato padrão para Gemini."""
        gemini_messages = []
        
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            
            parts = []
            if isinstance(msg.get("content"), str):
                parts.append({"text": msg["content"]})
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if isinstance(part, str):
                        parts.append({"text": part})
                    elif isinstance(part, dict):
                        parts.append(part)
            
            # Handle tool calls
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    parts.append({
                        "function_call": {
                            "name": tc["name"],
                            "args": tc["arguments"]
                        }
                    })
            
            # Handle tool responses
            if msg.get("role") == "tool":
                parts = [{
                    "function_response": {
                        "name": msg.get("name", "unknown"),
                        "response": {"result": msg.get("content", "")}
                    }
                }]
                role = "user"  # Gemini expects tool responses from user role
            
            gemini_messages.append({
                "role": role,
                "parts": parts
            })
        
        return gemini_messages
    
    def _parse_response(self, response) -> dict:
        """Converte resposta do Gemini para formato padrão."""
        result = {
            "content": "",
            "tool_calls": [],
            "finish_reason": None
        }
        
        try:
            # Get candidates
            candidates = getattr(response, 'candidates', [])
            if not candidates:
                # Try direct text access for streaming chunks
                if hasattr(response, 'text'):
                    result["content"] = response.text
                return result
            
            candidate = candidates[0]
            content = candidate.content
            
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    result["content"] += part.text
                
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    result["tool_calls"].append({
                        "id": f"call_{fc.name}",
                        "name": fc.name,
                        "arguments": dict(fc.args) if hasattr(fc.args, 'items') else {}
                    })
            
            # Finish reason
            if hasattr(candidate, 'finish_reason'):
                result["finish_reason"] = str(candidate.finish_reason)
        
        except Exception as e:
            result["content"] = f"[Error parsing response: {e}]"
        
        return result


class OpenAIProvider(LLMProvider):
    """Provider para OpenAI API."""
    
    def __init__(self):
        from openai import AsyncOpenAI
        
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_model
    
    async def chat(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> dict:
        """Envia mensagem para OpenAI e retorna resposta."""
        openai_messages = self._prepare_messages(messages, system_prompt)
        
        kwargs = {
            "model": self.model_name,
            "messages": openai_messages
        }
        
        if tools:
            openai_tools = tools.to_openai_format()
            if openai_tools:
                kwargs["tools"] = openai_tools
        
        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)
    
    async def chat_stream(
        self,
        messages: list[dict],
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None
    ) -> AsyncIterator[dict]:
        """Stream de respostas do OpenAI."""
        openai_messages = self._prepare_messages(messages, system_prompt)
        
        kwargs = {
            "model": self.model_name,
            "messages": openai_messages,
            "stream": True
        }
        
        if tools:
            openai_tools = tools.to_openai_format()
            if openai_tools:
                kwargs["tools"] = openai_tools
        
        async for chunk in await self.client.chat.completions.create(**kwargs):
            yield self._parse_stream_chunk(chunk)
    
    def _prepare_messages(self, messages: list[dict], system_prompt: str | None) -> list[dict]:
        """Prepara mensagens para OpenAI."""
        openai_messages = []
        
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in messages:
            openai_msg = {"role": msg["role"]}
            
            if msg.get("content"):
                openai_msg["content"] = msg["content"]
            
            if msg.get("tool_calls"):
                openai_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]) if isinstance(tc["arguments"], dict) else tc["arguments"]
                        }
                    }
                    for tc in msg["tool_calls"]
                ]
            
            if msg.get("tool_call_id"):
                openai_msg["tool_call_id"] = msg["tool_call_id"]
            
            if msg.get("name"):
                openai_msg["name"] = msg["name"]
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _parse_response(self, response) -> dict:
        """Converte resposta do OpenAI para formato padrão."""
        choice = response.choices[0]
        message = choice.message
        
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "finish_reason": choice.finish_reason
        }
        
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {}
                })
        
        return result
    
    def _parse_stream_chunk(self, chunk) -> dict:
        """Parse streaming chunk."""
        result = {
            "content": "",
            "tool_calls": [],
            "finish_reason": None
        }
        
        if chunk.choices:
            delta = chunk.choices[0].delta
            result["content"] = delta.content or ""
            result["finish_reason"] = chunk.choices[0].finish_reason
        
        return result


def get_provider(provider_name: str | None = None) -> LLMProvider:
    """Factory para criar o provider correto."""
    settings = get_settings()
    name = provider_name or settings.llm_provider
    
    if name == "openai":
        return OpenAIProvider()
    else:
        return GeminiProvider()
