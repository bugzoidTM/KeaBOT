"""
KeaBot Backend - Main Application
FastAPI entry point with Skills System.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db
from app.config import get_settings


# Global skill manager reference
_skill_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - inicializa recursos."""
    global _skill_manager
    
    # Startup
    await init_db()
    
    # Import tools to trigger registration
    import app.tools.filesystem  # noqa: F401
    import app.tools.browser     # noqa: F401
    import app.tools.youtube     # noqa: F401
    
    # Initialize Skills System
    from app.skills import init_skills
    _skill_manager = init_skills()
    
    # Initialize Scheduler
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    scheduler.start()
    
    settings = get_settings()
    print("[KeaBot] Backend iniciado!")
    print(f"   Provider: {settings.llm_provider}")
    print(f"   Allowed paths: {settings.keabot_allowed_paths}")
    print(f"   Skills loaded: {len(_skill_manager.skills)}")
    print(f"   Scheduler active: True")
    
    yield
    
    # Shutdown
    if _skill_manager:
        _skill_manager.stop_file_watcher()
    
    scheduler.shutdown()
    print("[KeaBot] Backend encerrado.")


# Create FastAPI app
app = FastAPI(
    title="KeaBot API",
    description="Agente de Automação Local Inteligente com Skills Dinâmicas",
    version="0.2.0",
    lifespan=lifespan
)

# CORS - permite frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    global _skill_manager
    
    skills_count = len(_skill_manager.skills) if _skill_manager else 0
    skills_names = list(_skill_manager.skills.keys()) if _skill_manager else []
    
    return {
        "name": "KeaBot API",
        "version": "0.2.0",
        "status": "running",
        "skills_loaded": skills_count,
        "skills": skills_names,
        "docs": "/docs"
    }


@app.get("/api/skills")
async def list_skills():
    """Lista todas as skills disponíveis."""
    global _skill_manager
    
    if not _skill_manager:
        return {"skills": []}
    
    skills = []
    for skill in _skill_manager.skills.values():
        skills.append({
            "name": skill.name,
            "description": skill.description,
            "triggers": skill.triggers,
            "author": skill.author,
            "version": skill.version,
            "is_loaded": skill.is_loaded
        })
    
    return {"skills": skills}


@app.post("/api/skills/reload")
async def reload_skills():
    """Recarrega todas as skills."""
    global _skill_manager
    
    if not _skill_manager:
        return {"success": False, "error": "Skill manager not initialized"}
    
    _skill_manager.reload_skills()
    
    return {
        "success": True,
        "skills_loaded": len(_skill_manager.skills),
        "skills": list(_skill_manager.skills.keys())
    }


def get_skill_manager():
    """Retorna o skill manager global."""
    global _skill_manager
    return _skill_manager


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

