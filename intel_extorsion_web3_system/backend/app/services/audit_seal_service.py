import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.services.web3_service import web3_service

logger = logging.getLogger(__name__)

class AuditSealService:
    def __init__(self):
        self.daily_events: List[Dict[str, Any]] = []
        
    def log_event(self, action: str, details: Dict[str, Any]):
        """Registra un evento para ser sellado al final del día."""
        self.daily_events.append({
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    def seal_daily_audit_log(self) -> Dict[str, Any]:
        """Calcula el Master Hash del día y lo sella en la blockchain."""
        if not self.daily_events:
            logger.info("No events to seal today.")
            return {"success": True, "message": "No events to seal."}
            
        # 1. Crear snapshot del log
        log_snapshot = list(self.daily_events)
        self.daily_events.clear() # Reset para el día siguiente
        
        # 2. Calcular Master Hash
        log_json = json.dumps(log_snapshot, sort_keys=True)
        master_hash = "0x" + hashlib.sha256(log_json.encode('utf-8')).hexdigest()
        
        # 3. Sellar en EvidenceRegistry (usamos case_id = 0 para logs de sistema)
        metadata = {
            "type": "daily_audit_log",
            "date": datetime.now(timezone.utc).date().isoformat(),
            "event_count": len(log_snapshot)
        }
        
        logger.info(f"Sealing audit log with {len(log_snapshot)} events. Hash: {master_hash}")
        
        try:
            result = web3_service.seal_evidence_by_hash(
                evidence_hash=master_hash,
                case_id=0,
                metadata=metadata
            )
            return {
                "success": result.get("success", False),
                "master_hash": master_hash,
                "tx_hash": result.get("tx_hash"),
                "events_sealed": len(log_snapshot)
            }
        except Exception as e:
            logger.error(f"Error sealing audit log: {e}")
            # Volver a poner los eventos en la lista si falló la tx
            self.daily_events.extend(log_snapshot)
            return {"success": False, "error": str(e)}

audit_seal_service = AuditSealService()
