import asyncio
import logging
from typing import Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

class ApprovalService:
    """Gerencia solicitações de aprovação humana."""
    
    def __init__(self):
        # Map: approval_id -> asyncio.Event
        self._pending: Dict[str, asyncio.Event] = {}
        # Map: approval_id -> bool (Approved/Rejected)
        self._results: Dict[str, bool] = {}
        
    def create_request(self) -> str:
        """Cria uma nova solicitação e retorna o ID."""
        req_id = str(uuid4())
        self._pending[req_id] = asyncio.Event()
        return req_id
    
    async def wait_for_approval(self, req_id: str, timeout: int = 300) -> bool:
        """Aguarda aprovação. Retorna True se aprovado, False se rejeitado ou timeout."""
        if req_id not in self._pending:
            return False
            
        event = self._pending[req_id]
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self._results.get(req_id, False)
        except asyncio.TimeoutError:
            logger.warning(f"Approval request {req_id} timed out.")
            return False
        finally:
            self._cleanup(req_id)
            
    def approve(self, req_id: str):
        """Aprova uma solicitação."""
        if req_id in self._pending:
            self._results[req_id] = True
            self._pending[req_id].set()
            
    def reject(self, req_id: str):
        """Rejeita uma solicitação."""
        if req_id in self._pending:
            self._results[req_id] = False
            self._pending[req_id].set()
            
    def _cleanup(self, req_id: str):
        """Limpa recursos."""
        self._pending.pop(req_id, None)
        # Mantém resultado por um tempo se necessário, ou remove
        self._results.pop(req_id, None)

# Singleton
_approval_service: ApprovalService | None = None

def get_approval_service() -> ApprovalService:
    global _approval_service
    if _approval_service is None:
        _approval_service = ApprovalService()
    return _approval_service
