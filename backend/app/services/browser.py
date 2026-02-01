import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class BrowserService:
    """Service singleton para gerenciar instância do Playwright."""
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Inicia o Playwright e o Browser."""
        async with self._lock:
            if not self._playwright:
                logger.info("Iniciando Playwright...")
                self._playwright = await async_playwright().start()
            
            if not self._browser:
                logger.info("Iniciando Chromium...")
                self._browser = await self._playwright.chromium.launch(headless=True)
    
    async def stop(self):
        """Para o Playwright."""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
                
    async def _get_page(self) -> Page:
        """Cria uma nova página (tab)."""
        if not self._browser:
            await self.start()
        
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        return await context.new_page()

    async def visit_page(self, url: str) -> dict:
        """Visita uma URL e extrai o conteúdo principal."""
        page = await self._get_page()
        try:
            logger.info(f"Visitando: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Extrai título
            title = await page.title()
            
            # Extrai conteúdo (simplificado)
            content = await page.content()
            clean_text = self._extract_main_content(content)
            
            return {
                "title": title,
                "content": clean_text[:20000], # Limite seguro para contexto
                "url": url
            }
        except Exception as e:
            logger.error(f"Erro ao visitar {url}: {e}")
            raise
        finally:
            await page.context.close()

    async def screenshot(self, url: str) -> str:
        """Tira screenshot de uma URL e retorna base64."""
        page = await self._get_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            screenshot_bytes = await page.screenshot(type="jpeg", quality=70)
            
            import base64
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        finally:
            await page.context.close()

    def _extract_main_content(self, html: str) -> str:
        """Limpa HTML e retorna apenas texto relevante."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove scripts, styles, etc
        for script in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            script.decompose()
            
        # Pega texto
        text = soup.get_text(separator='\n')
        
        # Limpa linhas em branco excessivas
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)

# Singleton
_service: BrowserService | None = None

def get_browser_service() -> BrowserService:
    global _service
    if _service is None:
        _service = BrowserService()
    return _service
