from app.tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, register_tool
from app.services.browser import get_browser_service
import asyncio

@register_tool
class VisitPageTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="visit_page",
            description="Visita uma página web e extrai seu conteúdo em texto limpo. Use para ler artigos, documentação ou buscar informações.",
            parameters=[
                ToolParameter(name="url", type="string", description="URL completa da página (incluindo http/https)")
            ]
        )
    
    async def execute(self, url: str) -> ToolResult:
        service = get_browser_service()
        try:
            result = await service.visit_page(url)
            # Retorna JSON string com metadados e conteúdo
            import json
            return ToolResult(success=True, data=json.dumps(result, ensure_ascii=False))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


@register_tool
class ScreenshotTool(Tool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="screenshot",
            description="Tira uma captura de tela da página informada.",
            parameters=[
                ToolParameter(name="url", type="string", description="URL da página")
            ]
        )
    
    async def execute(self, url: str) -> ToolResult:
        service = get_browser_service()
        try:
            # Retorna base64
            base64_img = await service.screenshot(url)
            return ToolResult(success=True, data=f"data:image/jpeg;base64,{base64_img}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
