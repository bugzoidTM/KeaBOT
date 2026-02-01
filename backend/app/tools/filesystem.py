"""
KeaBot Tools - Filesystem (ContextNavigator)
Ferramentas para navegação inteligente do sistema de arquivos.
"The GTA Trick" - Nunca lê arquivos inteiros, navega sob demanda.
"""

import os
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.tools.base import (
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    register_tool,
)


def check_path_allowed(path: str | Path) -> tuple[bool, str]:
    """Verifica se o path é permitido. Retorna (allowed, error_message)."""
    settings = get_settings()
    resolved = Path(path).resolve()
    
    if not settings.is_path_allowed(resolved):
        allowed = ", ".join(str(p) for p in settings.allowed_paths_list)
        return False, f"Path not allowed. Allowed paths: {allowed}"
    
    return True, ""


@register_tool
class ListDirectoryTool(Tool):
    """Lista arquivos e pastas em um diretório."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_directory",
            description=(
                "Lista arquivos e subpastas em um diretório. "
                "Use esta ferramenta PRIMEIRO para entender a estrutura do projeto. "
                "Retorna nome, tipo (file/dir), e tamanho."
            ),
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Caminho do diretório a listar (absoluto ou relativo ao projeto)"
                ),
                ToolParameter(
                    name="depth",
                    type="integer",
                    description="Profundidade da listagem (1 = apenas o diretório, 2 = inclui subpastas)",
                    required=False,
                    default=1
                ),
                ToolParameter(
                    name="pattern",
                    type="string",
                    description="Filtro glob opcional (ex: '*.py', '*.md')",
                    required=False,
                    default=None
                )
            ]
        )
    
    async def execute(self, path: str, depth: int = 1, pattern: str | None = None) -> ToolResult:
        # Verifica permissão
        allowed, error = check_path_allowed(path)
        if not allowed:
            return ToolResult(success=False, error=error)
        
        target = Path(path).resolve()
        
        if not target.exists():
            return ToolResult(success=False, error=f"Path does not exist: {path}")
        
        if not target.is_dir():
            return ToolResult(success=False, error=f"Path is not a directory: {path}")
        
        try:
            items = []
            self._list_recursive(target, target, depth, pattern, items)
            
            return ToolResult(
                success=True,
                data={
                    "path": str(target),
                    "total_items": len(items),
                    "items": items
                }
            )
        except PermissionError:
            return ToolResult(success=False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _list_recursive(
        self,
        base: Path,
        current: Path,
        depth: int,
        pattern: str | None,
        items: list,
        current_depth: int = 1
    ) -> None:
        """Lista recursivamente até a profundidade especificada."""
        if current_depth > depth:
            return
        
        try:
            entries = sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        
        for entry in entries:
            # Ignora arquivos ocultos e diretórios especiais
            if entry.name.startswith('.') and entry.name not in ['.env', '.env.local']:
                continue
            
            # Aplica filtro de pattern
            if pattern and entry.is_file() and not entry.match(pattern):
                continue
            
            relative = entry.relative_to(base)
            
            item = {
                "name": entry.name,
                "path": str(relative),
                "type": "dir" if entry.is_dir() else "file"
            }
            
            if entry.is_file():
                item["size"] = entry.stat().st_size
                item["size_human"] = self._human_size(entry.stat().st_size)
            elif entry.is_dir():
                try:
                    item["children_count"] = len(list(entry.iterdir()))
                except PermissionError:
                    item["children_count"] = "?"
            
            items.append(item)
            
            # Recursão para subdiretórios
            if entry.is_dir() and current_depth < depth:
                if entry.name not in ['node_modules', '__pycache__', '.git', 'venv', '.venv']:
                    self._list_recursive(base, entry, depth, pattern, items, current_depth + 1)
    
    @staticmethod
    def _human_size(size: int) -> str:
        """Converte bytes para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@register_tool
class GrepSearchTool(Tool):
    """Busca texto em arquivos usando regex."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="grep_search",
            description=(
                "Busca por um termo ou regex dentro de arquivos. "
                "Use para encontrar onde algo é definido ou usado. "
                "Retorna linhas que contêm o termo com contexto."
            ),
            parameters=[
                ToolParameter(
                    name="term",
                    type="string",
                    description="Termo ou regex para buscar"
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="Diretório ou arquivo onde buscar"
                ),
                ToolParameter(
                    name="file_pattern",
                    type="string",
                    description="Filtro de arquivos (ex: '*.py', '*.ts')",
                    required=False,
                    default="*"
                ),
                ToolParameter(
                    name="case_sensitive",
                    type="boolean",
                    description="Se a busca é case-sensitive",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Número máximo de resultados",
                    required=False,
                    default=20
                )
            ]
        )
    
    async def execute(
        self,
        term: str,
        path: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_results: int = 20
    ) -> ToolResult:
        # Verifica permissão
        allowed, error = check_path_allowed(path)
        if not allowed:
            return ToolResult(success=False, error=error)
        
        target = Path(path).resolve()
        
        if not target.exists():
            return ToolResult(success=False, error=f"Path does not exist: {path}")
        
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(term, flags)
        except re.error as e:
            return ToolResult(success=False, error=f"Invalid regex: {e}")
        
        results = []
        files_searched = 0
        
        try:
            if target.is_file():
                files = [target]
            else:
                files = list(target.rglob(file_pattern))
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Ignora binários e arquivos grandes
                if file_path.stat().st_size > 1_000_000:  # 1MB
                    continue
                
                # Ignora diretórios problemáticos
                if any(p in file_path.parts for p in ['node_modules', '__pycache__', '.git', 'venv']):
                    continue
                
                files_searched += 1
                matches = self._search_file(file_path, pattern, target)
                results.extend(matches)
                
                if len(results) >= max_results:
                    results = results[:max_results]
                    break
            
            return ToolResult(
                success=True,
                data={
                    "term": term,
                    "files_searched": files_searched,
                    "total_matches": len(results),
                    "matches": results
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _search_file(self, file_path: Path, pattern: re.Pattern, base: Path) -> list[dict]:
        """Busca em um arquivo e retorna matches com contexto."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return matches
        
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                matches.append({
                    "file": str(file_path.relative_to(base)),
                    "line_number": i,
                    "content": line.rstrip()[:200],  # Limita tamanho
                    "context_before": lines[max(0, i-2):i-1][0].rstrip()[:100] if i > 1 else None,
                    "context_after": lines[i:i+1][0].rstrip()[:100] if i < len(lines) else None
                })
        
        return matches


@register_tool
class ReadFileChunkTool(Tool):
    """Lê apenas um trecho específico de um arquivo."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file_chunk",
            description=(
                "Lê apenas linhas específicas de um arquivo. "
                "SEMPRE use esta ferramenta em vez de ler o arquivo inteiro. "
                "Use list_directory e grep_search primeiro para saber O QUE ler."
            ),
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Caminho do arquivo"
                ),
                ToolParameter(
                    name="start_line",
                    type="integer",
                    description="Linha inicial (1-indexed)",
                    required=False,
                    default=1
                ),
                ToolParameter(
                    name="end_line",
                    type="integer",
                    description="Linha final (inclusive). Se não especificado, lê 50 linhas.",
                    required=False,
                    default=None
                )
            ]
        )
    
    async def execute(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None
    ) -> ToolResult:
        # Verifica permissão
        allowed, error = check_path_allowed(path)
        if not allowed:
            return ToolResult(success=False, error=error)
        
        target = Path(path).resolve()
        
        if not target.exists():
            return ToolResult(success=False, error=f"File does not exist: {path}")
        
        if not target.is_file():
            return ToolResult(success=False, error=f"Path is not a file: {path}")
        
        # Limita leitura a 100 linhas por vez
        if end_line is None:
            end_line = start_line + 49  # 50 linhas
        
        if end_line - start_line > 100:
            end_line = start_line + 99
        
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            chunk = lines[start_idx:end_idx]
            
            # Formata com números de linha
            numbered_lines = []
            for i, line in enumerate(chunk, start=start_line):
                numbered_lines.append(f"{i:4d} | {line.rstrip()}")
            
            return ToolResult(
                success=True,
                data={
                    "file": str(target),
                    "total_lines": total_lines,
                    "showing": f"{start_line}-{min(end_line, total_lines)}",
                    "content": "\n".join(numbered_lines)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


@register_tool
class FileStatsTool(Tool):
    """Retorna metadados de um arquivo."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_stats",
            description=(
                "Retorna informações sobre um arquivo: tamanho, data de modificação, "
                "número de linhas. Use para decidir se vale a pena ler o arquivo."
            ),
            parameters=[
                ToolParameter(
                    name="path",
                    type="string",
                    description="Caminho do arquivo"
                )
            ]
        )
    
    async def execute(self, path: str) -> ToolResult:
        # Verifica permissão  
        allowed, error = check_path_allowed(path)
        if not allowed:
            return ToolResult(success=False, error=error)
        
        target = Path(path).resolve()
        
        if not target.exists():
            return ToolResult(success=False, error=f"Path does not exist: {path}")
        
        try:
            stat_info = target.stat()
            
            data = {
                "path": str(target),
                "name": target.name,
                "type": "directory" if target.is_dir() else "file",
                "size_bytes": stat_info.st_size,
                "size_human": self._human_size(stat_info.st_size),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            }
            
            # Conta linhas para arquivos de texto
            if target.is_file() and stat_info.st_size < 1_000_000:
                try:
                    with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                        data["line_count"] = sum(1 for _ in f)
                except Exception:
                    data["line_count"] = None
            
            # Detecta extensão
            data["extension"] = target.suffix.lower() if target.suffix else None
            
            return ToolResult(success=True, data=data)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    @staticmethod
    def _human_size(size: int) -> str:
        """Converte bytes para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
