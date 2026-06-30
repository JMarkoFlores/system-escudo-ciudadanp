import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.services.web3_service import web3_service

logger = logging.getLogger(__name__)

class AuditSealService:
    def __init__(self, log_path: str = "/app/logs/audit_log.json"):
        self.log_path = log_path
        self.daily_events: List[Dict[str, Any]] = []
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.daily_events = data.get("pending_events", [])
            except Exception as exc:
                logger.warning(f"No se pudo cargar audit log desde disco: {exc}")
                self.daily_events = []

    def _save_to_disk(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump({"pending_events": self.daily_events, "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        except Exception as exc:
            logger.error(f"No se pudo guardar audit log en disco: {exc}")

    def log_event(self, action: str, details: Dict[str, Any]):
        """Registra un evento para ser sellado al final del día."""
        event = {
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.daily_events.append(event)
        self._save_to_disk()
        logger.info(f"Audit event logged: {action}")

    def get_events(self) -> List[Dict[str, Any]]:
        return list(self.daily_events)

    def seal_daily_audit_log(self) -> Dict[str, Any]:
        """Calcula el Master Hash del día y lo sella en la blockchain."""
        if not self.daily_events:
            logger.info("No events to seal today.")
            return {"success": True, "message": "No events to seal."}

        # 1. Crear snapshot del log
        log_snapshot = list(self.daily_events)
        self.daily_events.clear()
        self._save_to_disk()

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
            sealed_event = {
                "action": "daily_audit_log_sealed",
                "details": {
                    "master_hash": master_hash,
                    "tx_hash": result.get("tx_hash"),
                    "block_number": result.get("block_number"),
                    "evidence_id": result.get("evidence_id"),
                    "events_sealed": len(log_snapshot),
                    "date": metadata["date"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            # Guardar el registro del sello en disco
            self._append_sealed_log(sealed_event)
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
            self._save_to_disk()
            return {"success": False, "error": str(e)}

    def _append_sealed_log(self, event: Dict[str, Any]):
        sealed_path = self.log_path.replace(".json", "_sealed.json")
        sealed_logs = []
        if os.path.exists(sealed_path):
            try:
                with open(sealed_path, "r", encoding="utf-8") as f:
                    sealed_logs = json.load(f)
            except Exception:
                pass
        sealed_logs.append(event)
        try:
            with open(sealed_path, "w", encoding="utf-8") as f:
                json.dump(sealed_logs, f, indent=2)
        except Exception as exc:
            logger.error(f"No se pudo guardar sealed audit log: {exc}")

    def get_sealed_logs(self) -> List[Dict[str, Any]]:
        sealed_path = self.log_path.replace(".json", "_sealed.json")
        if os.path.exists(sealed_path):
            try:
                with open(sealed_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

audit_seal_service = AuditSealService()
