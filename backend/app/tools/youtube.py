"""
KeaBot Tool - YouTube (Bionic Ear Edition)
Extrai informações, transcrições e analisa áudio de vídeos do YouTube.
"""

import os
import re
import asyncio
import logging
from typing import Optional
from pathlib import Path
import tempfile
import time

from app.tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, register_tool
from app.config import get_settings

# Logger setup
logger = logging.getLogger(__name__)

# Conditional imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False

try:
    from googleapiclient.discovery import build
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False

try:
    import yt_dlp
    import imageio_ffmpeg
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


@register_tool
class YouTubeTool(Tool):
    """Ferramenta avançada para YouTube com suporte a transcrição e análise de áudio."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="youtube",
            description="Analisa vídeos do YouTube. Obtém metadados, tenta ler transcrição (legendas) e, se falhar, baixa e 'ouve' o áudio do vídeo (usando Gemini Flash) para gerar um resumo com timestamps.",
            parameters=[
                ToolParameter(
                    name="url", 
                    type="string", 
                    description="URL do vídeo do YouTube."
                ),
                ToolParameter(
                     name="force_listen",
                     type="boolean",
                     description="Se verdadeiro, força o download e análise do áudio mesmo se houver transcrição (Lento!).",
                     required=False,
                     default=False
                )
            ]
        )

    async def execute(self, url: str, force_listen: bool = False, **kwargs) -> ToolResult:
        """Executa a análise do vídeo."""
        if not (HAS_TRANSCRIPT_API and HAS_GOOGLE_API and HAS_YTDLP and HAS_GENAI):
            return ToolResult(success=False, error="Dependências ausentes. Verifique se google-genai, yt-dlp, etc. estão instalados.")

        video_id = self._extract_video_id(url)
        if not video_id:
            return ToolResult(success=False, error="URL inválida. Não foi possível extrair o ID do vídeo.")

        settings = get_settings()
        api_key = getattr(settings, 'youtube_api_key', None) or settings.gemini_api_key
        
        result_data = {
            "video_id": video_id,
            "url": url,
            "title": None,
            "metadata": {},
            "source": "unknown",
            "content": ""
        }

        # 1. Get Metadata (Fastest)
        try:
            metadata = await self._get_metadata(video_id, api_key)
            result_data["metadata"] = metadata
            result_data["title"] = metadata.get("title")
        except Exception as e:
            logger.error(f"Metadata error: {e}")

        # 2. Try Transcript (Fast & Accurate if available)
        if not force_listen:
            try:
                transcript_text = await self._get_transcript(video_id)
                if transcript_text:
                    result_data["source"] = "transcript"
                    result_data["content"] = transcript_text
                    return ToolResult(success=True, data=result_data)
            except Exception as e:
                logger.warning(f"Transcript failed: {e}. Falling back to audio analysis...")

        # 3. Fallback: Listen to Video (Slow, requires Gemini)
        if settings.llm_provider != "gemini" or not settings.gemini_api_key:
             return ToolResult(success=True, data={**result_data, "error": "Transcrição indisponível e 'Audio Analysis' requer provider Gemini configurado."})

        try:
            logger.info(f"Iniciando análise de áudio para {video_id} com Gemini...")
            audio_summary = await self._listen_to_video(url, settings.gemini_api_key)
            result_data["source"] = "audio_analysis"
            result_data["content"] = audio_summary
            return ToolResult(success=True, data=result_data)
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return ToolResult(success=False, error=f"Falha ao analisar áudio: {str(e)}")


    async def _get_metadata(self, video_id: str, api_key: str | None) -> dict:
        """Busca metadados via YouTube Data API."""
        if not api_key:
            return {}
            
        def _fetch():
            youtube = build('youtube', 'v3', developerKey=api_key)
            request = youtube.videos().list(part="snippet,statistics", id=video_id)
            return request.execute()

        response = await asyncio.to_thread(_fetch)
        if not response.get('items'):
            return {}
            
        item = response['items'][0]
        return {
            "title": item['snippet']['title'],
            "channel": item['snippet']['channelTitle'],
            "description": item['snippet'].get('description', ''),
            "views": item['statistics'].get('viewCount'),
            "duration": item['snippet'].get('duration') # Useful for Gemini context
        }

    async def _get_transcript(self, video_id: str) -> str | None:
        """Busca transcrição via youtube-transcript-api."""
        def _fetch():
            return YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en', 'en-US'])
            
        transcript_list = await asyncio.to_thread(_fetch)
        # Formata com timestamps simples
        text_parts = []
        last_time = -30
        for entry in transcript_list:
            start = entry['start']
            text = entry['text']
            if start - last_time >= 30:
                minutes = int(start // 60)
                seconds = int(start % 60)
                text_parts.append(f"\n[{minutes:02d}:{seconds:02d}] {text}")
                last_time = start
            else:
                text_parts.append(text)
                
        return " ".join(text_parts)

    async def _listen_to_video(self, url: str, api_key: str) -> str:
        """Baixa áudio e envia para Gemini via google-genai SDK."""
        
        # Configure Client
        client = genai.Client(api_key=api_key)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 1. Download Audio
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            ydl_opts = {
                'format': 'bestaudio/best',
                'ffmpeg_location': ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'outtmpl': str(temp_path / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }
            
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            logger.info("Baixando áudio com yt-dlp...")
            await asyncio.to_thread(_download)
            
            audio_file = next(temp_path.glob("*.mp3"), None)
            if not audio_file:
                raise FileNotFoundError("Falha ao baixar arquivo de áudio")

            logger.info(f"Áudio baixado: {audio_file.name} ({audio_file.stat().st_size / 1024 / 1024:.2f} MB)")

            # 2. Upload to Gemini using new SDK
            def _process_with_gemini():
                # Upload
                # The new SDK handles upload differently. We use client.files.upload
                logger.info("Enviando arquivo para Gemini...")
                file_ref = client.files.upload(path=str(audio_file))
                
                # Check state (waiting for processing if needed, though for audio usually fast)
                while file_ref.state.name == "PROCESSING":
                     time.sleep(2)
                     file_ref = client.files.get(name=file_ref.name)
                
                if file_ref.state.name == "FAILED":
                    raise ValueError(f"File upload failed: {file_ref.error.message}")

                logger.info("Arquivo processado. Gerando conteúdo...")
                
                prompt = """
                Ouça este áudio do vídeo do YouTube.
                Gere uma transcrição detalhada e um resumo estruturado dos pontos principais.
                IMPORTANTE: 
                - Identifique os falantes se possível.
                - Use timestamps [MM:SS] para citar momentos chave.
                - Capture o tom e a intenção do conteúdo.
                """
                
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=[file_ref, prompt]
                )
                
                # Clean up (delete file from Gemini storage)
                # Note: New SDK might auto-cleanup or we should do it manually?
                # Usually good practice strictly speaking, but for now we let it be or delete if method exists
                # client.files.delete(name=file_ref.name) # If supported
                
                return response.text

            return await asyncio.to_thread(_process_with_gemini)

    def _extract_video_id(self, url: str) -> Optional[str]:
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
