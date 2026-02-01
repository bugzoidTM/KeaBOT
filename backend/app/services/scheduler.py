import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal, Job
from app.config import get_settings

logger = logging.getLogger(__name__)

class SchedulerService:
    """Gerencia agendamento de tarefas usando APScheduler."""
    
    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._started = False
    
    def start(self):
        """Inicia o scheduler."""
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("Scheduler iniciado.")
            
            # Carrega jobs do banco ao iniciar
            # Nota: Em produção, isso deveria aguardar conexão DB ou ser chamado no startup event
    
    def shutdown(self):
        """Para o scheduler."""
        if self._started:
            self._scheduler.shutdown()
            self._started = False
            logger.info("Scheduler parado.")
    
    async def add_job(self, name: str, instruction: str, schedule: str) -> str:
        """Adiciona um novo cron job persistente."""
        job_id = str(uuid4())
        
        # Salva no banco
        async with AsyncSessionLocal() as session:
            db_job = Job(
                id=job_id,
                name=name,
                instruction=instruction,
                schedule=schedule,
                enabled=True
            )
            session.add(db_job)
            await session.commit()
        
        # Adiciona ao scheduler
        self._schedule_job(job_id, name, instruction, schedule)
        
        return job_id

    def _schedule_job(self, job_id: str, name: str, instruction: str, schedule: str):
        """Configura o job no APScheduler."""
        try:
            trigger = CronTrigger.from_crontab(schedule)
            self._scheduler.add_job(
                self._execute_job,
                trigger=trigger,
                id=job_id,
                args=[job_id, instruction],
                name=name,
                replace_existing=True
            )
            logger.info(f"Job agendado: {name} ({schedule})")
        except Exception as e:
            logger.error(f"Erro ao agendar job {name}: {e}")

    async def _execute_job(self, job_id: str, instruction: str):
        """Callback executado pelo scheduler."""
        logger.info(f"Executando Job {job_id}: {instruction}")
        
        # Aqui precisamos instanciar um agente efêmero para executar a tarefa
        from app.agent.core import create_agent
        from app.main import get_skill_manager
        
        # TODO: Implementar execução do agente aqui
        # Por enquanto apenas logamos
        print(f"⏰ [SCHEDULER] Executando: {instruction}")
        
        # Atualiza next_run no banco (opcional, APScheduler controla execução)
        
# Singleton
_scheduler_service: SchedulerService | None = None

def get_scheduler() -> SchedulerService:
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
