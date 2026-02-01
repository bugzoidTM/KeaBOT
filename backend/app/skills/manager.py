"""
KeaBot Skills - Manager
Sistema de carregamento dinâmico de skills via Markdown.
Lazy loading: só injeta conteúdo quando skill é ativada.
"""

import os
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

from app.config import get_settings
from app.tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, get_registry


@dataclass
class Skill:
    """Representa uma skill carregada de um arquivo .md."""
    
    # Metadados do frontmatter
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0"
    
    # Conteúdo
    file_path: Path = None
    content: str = ""  # Corpo do markdown (few-shot examples)
    
    # Estado
    is_loaded: bool = False  # Se o conteúdo completo foi carregado
    
    def to_tool_definition(self) -> ToolDefinition:
        """Converte skill para definição de pseudo-tool."""
        return ToolDefinition(
            name=f"skill_{self._slug()}",
            description=f"[SKILL] {self.description}. Triggers: {', '.join(self.triggers)}",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="A tarefa ou pergunta relacionada a esta skill"
                )
            ]
        )
    
    def _slug(self) -> str:
        """Converte nome para slug."""
        return re.sub(r'[^a-z0-9]+', '_', self.name.lower()).strip('_')
    
    def get_context_injection(self) -> str:
        """Retorna o conteúdo formatado para injeção no contexto."""
        return f"""
=== SKILL ATIVADA: {self.name} ===

{self.content}

=== FIM DA SKILL ===

Use as instruções acima para completar a tarefa do usuário.
"""


class SkillTool(Tool):
    """Wrapper que transforma uma Skill em uma Tool executável."""
    
    def __init__(self, skill: Skill, manager: "SkillManager"):
        self.skill = skill
        self.manager = manager
    
    @property
    def definition(self) -> ToolDefinition:
        return self.skill.to_tool_definition()
    
    async def execute(self, query: str) -> ToolResult:
        """
        Quando a IA 'usa' uma skill, carregamos o conteúdo completo.
        Retorna instruções para o agente seguir.
        """
        # Carrega conteúdo se ainda não carregado
        if not self.skill.is_loaded:
            self.manager.load_skill_content(self.skill)
        
        return ToolResult(
            success=True,
            data={
                "skill_name": self.skill.name,
                "instructions": self.skill.content,
                "message": f"Skill '{self.skill.name}' ativada. Siga as instruções acima para completar a tarefa: {query}"
            }
        )


class SkillManager:
    """
    Gerencia carregamento e injeção de skills.
    
    Filosofia:
    - Escaneia pasta /skills na inicialização
    - Registra skills como pseudo-tools (só nome + descrição)
    - Carrega conteúdo completo APENAS quando skill é ativada
    """
    
    def __init__(self, skills_dir: str | Path = None):
        if skills_dir is None:
            # Default: backend/skills/
            skills_dir = Path(__file__).parent.parent.parent / "skills"
        
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}
        self._observer: Optional[Observer] = None
    
    def scan_skills(self) -> list[Skill]:
        """Escaneia pasta de skills e carrega metadados (não conteúdo)."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return []
        
        skills = []
        
        for file_path in self.skills_dir.glob("*.md"):
            try:
                skill = self._parse_skill_metadata(file_path)
                if skill:
                    self.skills[skill.name] = skill
                    skills.append(skill)
            except Exception as e:
                print(f"[SkillManager] Erro ao carregar {file_path}: {e}")
        
        print(f"[SkillManager] {len(skills)} skills carregadas: {[s.name for s in skills]}")
        return skills
    
    def _parse_skill_metadata(self, file_path: Path) -> Optional[Skill]:
        """
        Parse do frontmatter YAML de um arquivo .md.
        NÃO carrega o conteúdo completo (lazy loading).
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrai frontmatter YAML
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        if not frontmatter_match:
            # Tenta formato alternativo sem frontmatter
            return Skill(
                name=file_path.stem.replace('_', ' ').title(),
                description=f"Skill from {file_path.name}",
                file_path=file_path,
                is_loaded=False
            )
        
        try:
            metadata = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return None
        
        if not metadata:
            return None
        
        return Skill(
            name=metadata.get('name', file_path.stem.replace('_', ' ').title()),
            description=metadata.get('description', ''),
            triggers=metadata.get('triggers', []),
            author=metadata.get('author', ''),
            version=str(metadata.get('version', '1.0')),
            file_path=file_path,
            is_loaded=False
        )
    
    def load_skill_content(self, skill: Skill) -> str:
        """Carrega o conteúdo completo de uma skill (lazy loading)."""
        if skill.is_loaded:
            return skill.content
        
        if not skill.file_path or not skill.file_path.exists():
            return ""
        
        with open(skill.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove frontmatter, mantém só o corpo
        body_match = re.match(r'^---\s*\n.*?\n---\s*\n(.*)$', content, re.DOTALL)
        if body_match:
            skill.content = body_match.group(1).strip()
        else:
            skill.content = content.strip()
        
        skill.is_loaded = True
        print(f"[SkillManager] Conteúdo carregado: {skill.name} ({len(skill.content)} chars)")
        
        return skill.content
    
    def register_skills_as_tools(self) -> None:
        """Registra todas as skills como pseudo-tools no registry."""
        registry = get_registry()
        
        for skill in self.skills.values():
            tool = SkillTool(skill, self)
            registry.register(tool)
        
        print(f"[SkillManager] {len(self.skills)} skills registradas como tools")
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Busca skill por nome."""
        return self.skills.get(name)
    
    def get_skill_by_trigger(self, text: str) -> Optional[Skill]:
        """Busca skill que match com algum trigger no texto."""
        text_lower = text.lower()
        
        for skill in self.skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in text_lower:
                    return skill
        
        return None
    
    def get_skills_summary(self) -> str:
        """Retorna resumo de skills para o system prompt."""
        if not self.skills:
            return "Nenhuma skill carregada."
        
        lines = ["## Skills Disponíveis\n"]
        
        for skill in self.skills.values():
            triggers = ', '.join(f'`{t}`' for t in skill.triggers[:3])
            lines.append(f"- **{skill.name}**: {skill.description}")
            if triggers:
                lines.append(f"  - Triggers: {triggers}")
        
        lines.append("\nPara usar uma skill, chame-a como uma ferramenta.")
        
        return '\n'.join(lines)
    
    def start_file_watcher(self) -> None:
        """Inicia watcher para hot-reload de skills."""
        if self._observer:
            return
        
        class SkillHandler(FileSystemEventHandler):
            def __init__(self, manager: SkillManager):
                self.manager = manager
            
            def on_created(self, event):
                if event.src_path.endswith('.md'):
                    print(f"[SkillManager] Nova skill detectada: {event.src_path}")
                    self.manager.reload_skills()
            
            def on_modified(self, event):
                if event.src_path.endswith('.md'):
                    print(f"[SkillManager] Skill modificada: {event.src_path}")
                    # Invalida cache
                    for skill in self.manager.skills.values():
                        if str(skill.file_path) == event.src_path:
                            skill.is_loaded = False
            
            def on_deleted(self, event):
                if event.src_path.endswith('.md'):
                    print(f"[SkillManager] Skill removida: {event.src_path}")
                    self.manager.reload_skills()
        
        self._observer = Observer()
        self._observer.schedule(SkillHandler(self), str(self.skills_dir), recursive=False)
        self._observer.start()
        print(f"[SkillManager] File watcher iniciado em {self.skills_dir}")
    
    def stop_file_watcher(self) -> None:
        """Para o watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    def reload_skills(self) -> None:
        """Recarrega todas as skills."""
        self.skills.clear()
        self.scan_skills()
        self.register_skills_as_tools()
    
    def save_skill(self, name: str, content: str) -> bool:
        """
        Salva uma skill em arquivo .md.
        Se já existir, sobrescreve.
        """
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        filename = f"{slug}.md"
        file_path = self.skills_dir / filename
        
        try:
            # Ensure proper markdown formatting if needed
            # For now, trust that 'content' is the full markdown including YAML frontmatter
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[SkillManager] Skill salva: {file_path}")
            # Force reload to pick up changes immediately
            self.reload_skills()
            return True
        except Exception as e:
            print(f"[SkillManager] Erro ao salvar skill {name}: {e}")
            return False

    def delete_skill(self, slug: str) -> bool:
        """Remove o arquivo de uma skill."""
        # Find skill by slug
        target_skill = None
        for s in self.skills.values():
            if s._slug() == slug:
                target_skill = s
                break
        
        if not target_skill or not target_skill.file_path:
            # Try to construct path from slug as fallback
            file_path = self.skills_dir / f"{slug}.md"
            if file_path.exists():
                try:
                    os.remove(file_path)
                    print(f"[SkillManager] Skill excluída por path fallback: {file_path}")
                    self.reload_skills()
                    return True
                except Exception as e:
                    print(f"[SkillManager] Erro ao excluir skill fallback {slug}: {e}")
                    return False
            return False
            
        try:
            os.remove(target_skill.file_path)
            print(f"[SkillManager] Skill excluída: {target_skill.file_path}")
            del self.skills[target_skill.name]
            self.reload_skills()
            return True
        except Exception as e:
            print(f"[SkillManager] Erro ao excluir skill {slug}: {e}")
            return False


# Singleton
_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Retorna instância singleton do SkillManager."""
    global _manager
    if _manager is None:
        _manager = SkillManager()
        _manager.scan_skills()
    return _manager


def init_skills() -> SkillManager:
    """Inicializa o sistema de skills."""
    manager = get_skill_manager()
    manager.register_skills_as_tools()
    manager.start_file_watcher()
    return manager
