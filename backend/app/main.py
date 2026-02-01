"""
KeaBot Backend - Main Application
FastAPI entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - inicializa recursos."""
    # Startup
    await init_db()
    
    # Import tools to trigger registration
    import app.tools.filesystem  # noqa: F401
    
    print("🦜 KeaBot Backend iniciado!")
    print(f"   Provider: {get_settings().llm_provider}")
    print(f"   Allowed paths: {get_settings().keabot_allowed_paths}")
    
    yield
    
    # Shutdown
    print("🦜 KeaBot Backend encerrado.")


# Create FastAPI app
app = FastAPI(
    title="KeaBot API",
    description="Agente de Automação Local Inteligente",
    version="0.1.0",
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
    return {
        "name": "KeaBot API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
