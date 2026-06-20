"""
Web3 Service - Interacción con Smart Contracts en Syscoin Rollux L2
"""
import json
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path

from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

from app.config.settings import settings

class Web3Service:
    """
    Servicio singleton para interactuar con la blockchain Syscoin Rollux.
    Gestiona conexiones, firmas transaccionales y lecturas de contratos.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        # Rollux usa clique PoA (merge-mined con Bitcoin)
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Cuenta institucional (backend signer)
        if settings.PRIVATE_KEY:
            self.account = Account.from_key(settings.PRIVATE_KEY)
            self.backend_address = self.account.address
        else:
            self.account = None
            self.backend_address = settings.BACKEND_WALLET_ADDRESS
        
        # Cargar ABIs y contratos
        self._load_contracts()
        self._initialized = True
    
    def _load_abi(self, name: str) -> List[Dict[str, Any]]:
        abi_path = Path(__file__).parent / "abis" / f"{name}.json"
        with open(abi_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_contracts(self):
        zero_addr = "0x0000000000000000000000000000000000000000"
        if settings.CONTRACT_EVIDENCE_REGISTRY and settings.CONTRACT_EVIDENCE_REGISTRY != zero_addr:
            self.evidence_registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.CONTRACT_EVIDENCE_REGISTRY),
                abi=self._load_abi("EvidenceRegistry")
            )
        else:
            self.evidence_registry = None
        
        if settings.CONTRACT_CASE_MANAGER and settings.CONTRACT_CASE_MANAGER != zero_addr:
            self.case_manager = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.CONTRACT_CASE_MANAGER),
                abi=self._load_abi("CaseManager")
            )
        else:
            self.case_manager = None
        
        if settings.CONTRACT_DID_REGISTRY and settings.CONTRACT_DID_REGISTRY != zero_addr:
            self.did_registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(settings.CONTRACT_DID_REGISTRY),
                abi=self._load_abi("DIDRegistry")
            )
        else:
            self.did_registry = None
    
    def is_connected(self) -> bool:
        return self.w3.is_connected()
    
    def get_block_number(self) -> int:
        return self.w3.eth.block_number
    
    def _send_transaction(self, tx_function, value: int = 0) -> Dict[str, Any]:
        """Envía una transacción firmada por el backend wallet."""
        if not self.account:
            raise RuntimeError("No backend private key configured")
        
        tx = tx_function.build_transaction({
            "from": self.backend_address,
            "nonce": self.w3.eth.get_transaction_count(self.backend_address),
            "gas": 500000,
            "gasPrice": self.w3.to_wei("0.01", "gwei"),  # Rollux tiene fees ultra bajos
            "chainId": settings.CHAIN_ID,
            "value": value,
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "status": receipt.status,
            "gas_used": receipt.gasUsed,
        }
    
    # ==========================================
    # EvidenceRegistry Methods
    # ==========================================
    
    def store_evidence(
        self,
        file_bytes: bytes,
        ipfs_cid: str,
        did_denunciante: str,
        tipo_evidencia: int,
        metadata_uri: str
    ) -> Dict[str, Any]:
        """
        Registra una evidencia en blockchain:
        1. Calcula SHA-256 del archivo
        2. Almacena en EvidenceRegistry
        3. Devuelve tx_hash y evidence_id
        """
        if not self.evidence_registry:
            raise RuntimeError("EvidenceRegistry contract not configured")
        
        evidence_hash = "0x" + hashlib.sha256(file_bytes).hexdigest()
        
        func = self.evidence_registry.functions.storeEvidence(
            evidence_hash,
            ipfs_cid,
            did_denunciante,
            tipo_evidencia,
            metadata_uri
        )
        
        receipt = self._send_transaction(func)
        
        # Parsear evento EvidenceStored para obtener evidenceId
        logs = self.evidence_registry.events.EvidenceStored().process_receipt(receipt)
        evidence_id = logs[0].args.evidenceId if logs else None
        
        return {
            **receipt,
            "evidence_hash": evidence_hash,
            "evidence_id": evidence_id,
            "ipfs_cid": ipfs_cid,
        }
    
    def seal_evidence_by_hash(
        self,
        evidence_hash: str,
        case_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra evidencia en blockchain usando un hash precalculado.
        En modo desarrollo (sin contrato), retorna respuesta simulada.
        """
        if not self.evidence_registry:
            return {
                "success": True,
                "evidence_id": hash(evidence_hash) % 1000000,
                "evidence_hash": evidence_hash,
                "tx_hash": "0x" + "0" * 64,
                "block_number": self.get_block_number(),
                "status": 1,
                "case_id": case_id,
                "message": "Sellado en modo desarrollo (contrato no desplegado)"
            }

        hash_bytes = Web3.to_bytes(hexstr=evidence_hash) if evidence_hash.startswith("0x") else evidence_hash.encode()
        func = self.evidence_registry.functions.storeEvidence(
            hash_bytes,
            f"case://{case_id}",
            "",
            1,
            json.dumps(metadata or {})
        )

        receipt = self._send_transaction(func)

        logs = self.evidence_registry.events.EvidenceStored().process_receipt(receipt)
        evidence_id = logs[0].args.evidenceId if logs else None

        return {
            **receipt,
            "evidence_hash": evidence_hash,
            "evidence_id": evidence_id,
            "success": receipt["status"] == 1,
            "case_id": case_id,
        }

    def verify_evidence_integrity(self, evidence_id: int, file_bytes: bytes) -> Dict[str, Any]:
        """Verifica si el hash del archivo coincide con el registrado on-chain."""
        if not self.evidence_registry:
            raise RuntimeError("EvidenceRegistry contract not configured")
        
        provided_hash = "0x" + hashlib.sha256(file_bytes).hexdigest()
        valid, mensaje = self.evidence_registry.functions.verifyEvidence(evidence_id, provided_hash).call()
        
        # Obtener datos on-chain
        ev = self.evidence_registry.functions.evidencias(evidence_id).call()
        
        return {
            "evidence_id": evidence_id,
            "valid": valid,
            "mensaje": mensaje,
            "on_chain_hash": ev[1],
            "provided_hash": provided_hash,
            "custodian": ev[4],
            "timestamp": ev[7],
            "active": ev[8],
            "blockchain": "syscoin_rollux",
            "block_number_at_verify": self.get_block_number(),
        }
    
    def get_custody_history(self, evidence_id: int) -> List[Dict[str, Any]]:
        """Obtiene historial de transferencias de custodia."""
        if not self.evidence_registry:
            raise RuntimeError("EvidenceRegistry contract not configured")
        
        history = self.evidence_registry.functions.getCustodyHistory(evidence_id).call()
        return [
            {
                "from": h[0],
                "to": h[1],
                "timestamp": h[2],
                "motivo": h[3]
            }
            for h in history
        ]
    
    def transfer_custody(self, evidence_id: int, new_custodian: str, motivo: str) -> Dict[str, Any]:
        """Transfiere custodia de evidencia a nueva dirección."""
        if not self.evidence_registry:
            raise RuntimeError("EvidenceRegistry contract not configured")
        
        func = self.evidence_registry.functions.transferCustody(evidence_id, new_custodian, motivo)
        return self._send_transaction(func)
    
    # ==========================================
    # CaseManager Methods
    # ==========================================
    
    def create_case(
        self,
        did_denunciante: str,
        nivel_riesgo: int,
        resumen: str,
        metadata_uri: str
    ) -> Dict[str, Any]:
        """Crea un caso de extorsión en blockchain."""
        if not self.case_manager:
            raise RuntimeError("CaseManager contract not configured")
        
        func = self.case_manager.functions.createCase(did_denunciante, nivel_riesgo, resumen, metadata_uri)
        receipt = self._send_transaction(func)
        
        logs = self.case_manager.events.CasoCreado().process_receipt(receipt)
        case_id = logs[0].args.caseId if logs else None
        
        return {**receipt, "case_id": case_id}
    
    def link_evidence_to_case(self, case_id: int, evidence_id: int) -> Dict[str, Any]:
        """Vincula una evidencia registrada a un caso."""
        if not self.case_manager:
            raise RuntimeError("CaseManager contract not configured")
        
        func = self.case_manager.functions.vincularEvidencia(case_id, evidence_id)
        return self._send_transaction(func)
    
    def get_case(self, case_id: int) -> Dict[str, Any]:
        """Obtiene datos de un caso."""
        if not self.case_manager:
            raise RuntimeError("CaseManager contract not configured")
        
        c = self.case_manager.functions.casos(case_id).call()
        return {
            "id": c[0],
            "did_denunciante": c[1],
            "creador": c[2],
            "estado": c[3],
            "nivel_riesgo": c[4],
            "resumen": c[5],
            "created_at": c[6],
            "updated_at": c[7],
            "active": c[8],
            "metadata_uri": c[9],
        }
    
    # ==========================================
    # DID Methods
    # ==========================================
    
    def resolve_did(self, did: str) -> Optional[Dict[str, Any]]:
        """Resuelve un DID a su documento."""
        if not self.did_registry:
            return None
        
        doc = self.did_registry.functions.didDocuments(did).call()
        if not doc or not doc[0]:
            return None
        
        return {
            "did": doc[0],
            "controller": doc[1],
            "public_key": doc[2],
            "document_uri": doc[3],
            "active": doc[4],
            "created_at": doc[5],
            "updated_at": doc[6],
            "reputation_score": doc[7],
            "metadata": doc[8],
        }
    
    def verify_credential(self, credential_hash: str) -> Dict[str, Any]:
        """Verifica validez de una credencial verificable on-chain."""
        if not self.did_registry:
            raise RuntimeError("DIDRegistry contract not configured")
        
        valid, status = self.did_registry.functions.verifyCredential(credential_hash).call()
        return {"valid": valid, "status": status}

# Singleton
web3_service = Web3Service()
