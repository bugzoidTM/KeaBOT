"""
KeaBot Tool - YouTube
Extrai informações e transcrições de vídeos do YouTube.
"""

import re
import asyncio
from typing import Optional, Any
from app.tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, register_tool
from app.config import get_settings

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from googleapiclient.discovery import build
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

@register_tool
class YouTubeTool(Tool):
    """Ferramenta para interagir com YouTube."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="youtube",
            description="Obtém transcrição e metadados de um vídeo do YouTube. Tenta obter legendas, mas retorna metadados se não houver.",
            parameters=[
                ToolParameter(
                    name="url", 
                    type="string", 
                    description="URL do vídeo do YouTube (ex: https://www.youtube.com/watch?v=...)"
                ),
                ToolParameter(
                     name="video_id",
                     type="string",
                     description="ID do vídeo (opcional, se URL não for fornecida)",
                     required=False
                )
            ]
        )

    async def execute(self, url: Optional[str] = None, video_id: Optional[str] = None, **kwargs) -> ToolResult:
        if not HAS_DEPS:
            return ToolResult(
                success=False, 
                error="Bibliotecas 'google-api-python-client' e 'youtube-transcript-api' não instaladas."
            )

        if not video_id and url:
            video_id = self._extract_video_id(url)
        
        if not video_id:
            return ToolResult(success=False, error="Forneça uma URL ou video_id válido.")

        result_data = {
            "video_id": video_id,
            "transcript_found": False,
            "transcript_full": None,
            "metadata": {}
        }
        errors = []

        # 1. Try Transcript
        try:
            # Tries to get Portuguese or English
            transcript_list = await asyncio.to_thread(
                YouTubeTranscriptApi.get_transcript, video_id, languages=['pt', 'en']
            )
            full_text = " ".join([entry['text'] for entry in transcript_list])
            result_data["transcript_full"] = full_text
            result_data["transcript_found"] = True
            result_data["transcript_preview"] = full_text[:500] + "..."
        except Exception as e:
            errors.append(f"Transcript error: {str(e)}")
            result_data["transcript_error"] = str(e)

        # 2. Get Metadata
        try:
            settings = get_settings()
            api_key = getattr(settings, 'youtube_api_key', None) or settings.gemini_api_key
            
            if api_key:
                youtube = build('youtube', 'v3', developerKey=api_key)
                request = youtube.videos().list(
                    part="snippet,statistics",
                    id=video_id
                )
                response = await asyncio.to_thread(request.execute)
                
                if response.get('items'):
                    item = response['items'][0]
                    result_data["metadata"] = {
                        "title": item['snippet']['title'],
                        "channel": item['snippet']['channelTitle'],
                        "description": item['snippet'].get('description', '')[:500] + "...",
                        "views": item['statistics'].get('viewCount'),
                        "likes": item['statistics'].get('likeCount')
                    }
            else:
                errors.append("No API Key for metadata")
        except Exception as e:
            errors.append(f"Metadata error: {str(e)}")

        # Check success: at least one of them worked?
        # If we have title OR transcript, it's a success.
        if result_data["transcript_found"] or result_data.get("metadata"):
            return ToolResult(success=True, data=result_data)
        
        return ToolResult(
            success=False, 
            error=f"Não foi possível extrair dados do vídeo. Erros: {'; '.join(errors)}"
        )

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extrai ID do vídeo de URLs comuns."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
