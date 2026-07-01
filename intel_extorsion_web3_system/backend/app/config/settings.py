"""
IntelExtorsión Web3 Backend - Configuración
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "IntelExtorsion-Web3-Backend"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
    # Blockchain (zkSYS Tanenbaum Testnet para desarrollo/demo)
    WEB3_PROVIDER_URL: str = "https://rpc-zk.tanenbaum.io"
    CHAIN_ID: int = 57057
    
    # Cuenta institucional (backend signer)
    # EN PRODUCCION: usar AWS KMS / HashiCorp Vault / HSM
    PRIVATE_KEY: str = ""
    BACKEND_WALLET_ADDRESS: Optional[str] = None
    
    # Contract addresses (después del deploy)
    CONTRACT_DID_REGISTRY: Optional[str] = None
    CONTRACT_EVIDENCE_REGISTRY: Optional[str] = None
    CONTRACT_CASE_MANAGER: Optional[str] = None
    CONTRACT_TOKEN: Optional[str] = None
    CONTRACT_EVIDENCE_SEAL: Optional[str] = None
    CONTRACT_IDENTITY_REVEAL: Optional[str] = None
    
    # IPFS
    IPFS_API_URL: str = "https://api.pinata.cloud"
    IPFS_JWT: str = ""
    
    # Certificado X.509 para firma de actas (PEM)
    # EN PRODUCCION: usar certificado emitido por CA autorizada
    X509_CERT_PEM: Optional[str] = None
    X509_KEY_PEM: Optional[str] = None
    
    # Agent System Integration
    AGENT_SYSTEM_API_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
