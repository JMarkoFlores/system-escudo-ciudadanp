# IntelExtorsión Web3 Subsystem
## Documentación Técnica Completa

---

## 1. Arquitectura Completa Web3

### Visión General
El subsistema Web3 garantiza la **inmutabilidad**, **trazabilidad** y **custodia descentralizada** de evidencias digitales relacionadas con denuncias de extorsión. Se fundamenta en cuatro smart contracts desplegados en **Syscoin Rollux L2** (EVM compatible, merge-mined con Bitcoin, fees ~$0.0001).

### Diagrama de Arquitectura

```
┌───────────────────────────────────────────────────────────────────────┐
│                         CAPA DE PRESENTACIÓN                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    DApp React (Pali Wallet)                      │  │
│  │  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ Conectar │  │ Registrar  │  │   Verificar  │  | Resolver │  │  │
│  │  │ Wallet   │  │ Evidencia  │  │  Integridad  │  |   DID    │  │  │
│  │  └──────────┘  └────────────┘  └──────────────┘  └──────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────────────┘
                              │ HTTPS / JSON-RPC
┌─────────────────────────────▼─────────────────────────────────────────┐
│                      CAPA DE APIs (FastAPI)                            │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Web3 Backend API   │  │ Agent System API │  │  OSINT / NLP     │   │
│  │  (Blockchain)      │  │  (IA/Análisis)   │  │  (Enriquec.)     │   │
│  └────────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────┬─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   IPFS       │    │  PostgreSQL     │    │   Qdrant     │
│ (Evidencias) │    │ (Transaccional) │    │ (Vectores)   │
└──────────────┘    └─────────────────┘    └──────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    CAPA BLOCKCHAIN - Syscoin Rollux L2                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ DIDRegistry     │  │EvidenceReg.  │  │CaseManag.│  │IE Token  │  │
│  │ (Identidad)     │  │ (Custodia)   │  │ (Casos)  │  │(SBT NFT) │  │
│  └─────────────────┘  └──────────────┘  └──────────┘  └──────────┘  │
│                                                                       │
│  ┎─────────────────────────────────────────────────────────────────┒  │
│  ┃ Seguridad: Merge-mined con Bitcoin | EVM | 700+ TPS | 2s block ┃  │
│  ┖─────────────────────────────────────────────────────────────────┚  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Smart Contracts

### 2.1 DIDRegistry.sol
**Propósito:** Registro y gestión de Identidades Descentralizadas (DID) compatibles con `did:ethr`.

| Función | Visibilidad | Descripción |
|---------|-------------|-------------|
| `registerDID` | `external` | Registra un nuevo DID vinculado a una dirección Ethereum |
| `updateDIDDocument` | `external` | Actualiza URI del documento y metadatos (solo controller) |
| `deactivateDID` | `external` | Desactiva un DID (soft delete) |
| `issueCredential` | `external` | Emite una credencial verificable (VC) on-chain |
| `revokeCredential` | `external` | Revoca una credencial emitida |
| `verifyCredential` | `view` | Verifica validez, expiración y revocación |
| `updateReputation` | `external` | Actualiza score de reputación (0-10000) |

### 2.2 EvidenceRegistry.sol
**Propósito:** Registro inmutable de evidencias con hash SHA-256 y trazabilidad de custodia.

| Función | Visibilidad | Descripción |
|---------|-------------|-------------|
| `storeEvidence` | `external` | Registra nueva evidencia. Previene duplicados por hash |
| `transferCustody` | `external` | Transfiere custodia con motivo documentado |
| `linkToCase` | `external` | Vincula evidencia a un caso del CaseManager |
| `revokeEvidence` | `external` | Revocación administrativa (solo admin) |
| `verifyEvidence` | `view` | Comprueba integridad comparando hashes |
| `getCustodyHistory` | `view` | Devuelve array de transferencias |
| `getEvidenciasByCustodian` | `view` | Lista evidencias por dirección custodio |

### 2.3 CaseManager.sol
**Propósito:** Gestión de casos de extorsión con estados, oficiales y evidencias vinculadas.

| Función | Visibilidad | Descripción |
|---------|-------------|-------------|
| `createCase` | `external` | Crea caso con DID denunciante y nivel de riesgo |
| `asignarOficial` | `external` | Asigna oficial investigador (rol FISCAL) |
| `cambiarEstado` | `external` | Transiciona estado con auditoría |
| `vincularEvidencia` | `external` | Vincula evidenceId a caso |
| `archivarCaso` | `external` | Archiva caso (solo FISCAL) |
| `getEstadoHistory` | `view` | Historial de cambios de estado |

### 2.4 IntelExtorsionToken.sol
**Propósito:** NFT Soulbound que representa evidencias certificadas (no transferibles por defecto).

| Función | Visibilidad | Descripción |
|---------|-------------|-------------|
| `mintEvidenceToken` | `external` | Mints SBT vinculado a evidenceId |
| `burnEvidenceToken` | `external` | Quema token (solo BURNER_ROLE) |
| `setTransferable` | `external` | Habilita/deshabilita transferencia (excepcional) |
| `_beforeTokenTransfer` | `internal` | Hook que bloquea transferencias si es soulbound |

---

## 3. Diseño de la DApp

### Stack Frontend
- **Framework:** React 18 + Vite
- **Estilos:** Tailwind CSS
- **Blockchain:** Ethers.js v6
- **Wallet:** Pali Wallet (injecta `window.pali` compatible EIP-1193)

### Componentes Principales
1. **WalletConnect:** Gestiona conexión, desconexión y switch de red a Rollux.
2. **EvidenceUploader:** Drag & drop de archivo → cálculo SHA-256 en browser → firma tx con Pali → registro on-chain.
3. **EvidenceVerifier:** Carga archivo + evidenceId → comparación de hashes on-chain → resultado de integridad.
4. **DIDResolver:** Input de DID → lectura directa del contrato DIDRegistry → visualización de documento.

---

## 4. Integración con Agentes Autónomos

### Flujo de Integración
```
[Agent System]                                    [Web3 Subsystem]
      │                                                    │
      │ 1. Denuncia procesada (Risk Agent detecta         │
      │    riesgo ALTO/CRITICO)                            │
      │───────────────────────────────────────────────────►│
      │    POST /v1/evidencias                             │
      │    { file, did_denunciante, tipo_evidencia }       │
      │                                                    │
      │ 2. Web3 Backend:                                   │
      │    - Calcula SHA-256                               │
      │    - Sube a IPFS                                   │
      │    - Tx: EvidenceRegistry.storeEvidence()          │
      │    - Tx: CaseManager.createCase()                  │
      │    - Tx: CaseManager.vincularEvidencia()           │
      │◄───────────────────────────────────────────────────│
      │    Response: { evidence_id, case_id, tx_hash }     │
      │                                                    │
      │ 3. Alert Agent incluye en alerta oficial:          │
      │    - tx_hash                                       │
      │    - block_number                                  │
      │    - evidence_id on-chain                          │
      │    - IPFS CID                                      │
```

### Punto de Unión
El **Web3 Backend API** expone `POST /v1/evidencias` que es consumido por el `AgentExecutionService` del subsistema de agentes cuando se requiere custodia blockchain.

---

## 5. Flujo de Autenticación

### Autenticación Descentralizada (DID)
```
Usuario / Denunciante
        │
        ▼
┌─────────────────┐
│   Pali Wallet   │──► Firma mensaje con clave privada
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DID Registry   │──► did:ethr:rollux:<address>
│  (on-chain)     │    Documento DID almacenado
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DApp / API   │──► Verifica firma contra DID document
└─────────────────┘
```

### Credenciales Verificables (VC)
1. **Emisor:** Fiscalía/Entidad con `ISSUER_ROLE` emite VC on-chain (`issueCredential`).
2. **Sujeto:** Denunciante u Oficial almacena referencia al hash de la VC.
3. **Verificación:** Cualquier parte puede llamar `verifyCredential(hash)` → recibe `(bool, string)`.

---

## 6. Flujo de Firma Digital

### Firma de Evidencia (Custodia)
```
1. Backend Wallet (institucional) recibe resultado del agente
2. Calcula SHA-256 del contenido de evidencia
3. Prepara transacción: EvidenceRegistry.storeEvidence(hash, ipfsCID, ...)
4. Firma con eth_account / AWS KMS / HSM
5. Envía raw transaction a Rollux RPC
6. Espera receipt y parsea evento EvidenceStored
7. Almacena tx_hash, block_number, evidence_id en PostgreSQL
```

### Firma de Custodia Transferida
```
1. Custodio actual (oficial) inicia transferencia en DApp
2. Pali Wallet firma transacción: transferCustody(evidenceId, newCustodian, motivo)
3. Contrato valida que msg.sender == custodian actual
4. Se emite evento CustodyTransferred
5. Historial queda inmutable en custodyHistory mapping
```

---

## 7. Flujo de Almacenamiento de Evidencias

### Pipeline Completo
```
[Archivo Original] (WhatsApp, Telegram, Discord)
        │
        ▼
[Hash SHA-256] ───────────────────┐
        │                          │
        ▼                          │
[IPFS Network]                    │
   CID: QmXyZ...                  │
        │                         │
        ▼                         │
[Smart Contract]                  │
EvidenceRegistry                  │
.storeEvidence(                   │
  hash = 0xabc..., ◄──────────────┘
  ipfsCID = "QmXyZ...",
  didDenunciante = "did:ethr:...",
  tipoEvidencia = 2,
  metadataURI = "https://..."
)
        │
        ▼
[Evento: EvidenceStored]
evidenceId = 42
        │
        ▼
[PostgreSQL] ──► denuncias.hash_archivo = 0xabc...
         denuncias.url_archivo = ipfs://QmXyZ...
```

### Estrategia de Almacenamiento Híbrida
| Capa | Tecnología | Datos Almacenados |
|------|-----------|-------------------|
| Hot Storage | PostgreSQL + S3/MinIO | Metadatos, textos, archivos accesibles |
| Warm Storage | IPFS + Pinata | Archivos originales con CID permanente |
| Cold / Immutable | Syscoin Rollux L2 | Hashes, timestamps, custodia, estados |

---

## 8. Flujo de Verificación de Integridad

### Proceso de Verificación
```
[Usuario/Autoridad Judicial] ──► DApp Verificador
        │
        ▼
┌─────────────────────────────┐
│ 1. Selecciona Evidence ID   │
│ 2. Sube archivo original    │
│ 3. Frontend calcula SHA-256 │
│    en browser (crypto API)  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ EvidenceRegistry.verify     │
│ (evidenceId, providedHash)  │
│     view function call       │
└─────────────┬───────────────┘
              │
              ▼
        ┌─────┴─────┐
        ▼           ▼
   [VALID]      [INVALID]
   Hash ==      Hash !=
   On-chain     On-chain
        │           │
        ▼           ▼
   ✅ Verde      ❌ Rojo
   Integridad    ALTERADA
   verificada
```

### Verificación Off-Chain (API Backend)
El endpoint `POST /v1/evidencias/verify` permite verificación masiva sin requerir wallet del verificador, usando el backend institucional como lector público.

---

## 9. Pruebas

### Unitarias (Hardhat)
```bash
cd intel_extorsion_web3_system
npm install
npx hardhat test
```

**Cobertura:**
- DIDRegistry: registro, actualización, credenciales, revocación
- EvidenceRegistry: store, transfer, verify, duplicados, revocación
- CaseManager: create, assign, link, state transitions
- IntelExtorsionToken: mint, soulbound restriction, burn

### Integración (Python)
```bash
cd backend
pytest tests/ -v
```

---

## 10. Despliegue en Producción

### Paso 1: Preparar Wallet Institucional
- Generar dirección dedicada (cold storage recomendado)
- Obtener SYS nativo en Rollux Mainnet (faucet o bridge desde Syscoin NEVM)
- Configurar `PRIVATE_KEY` en `.env` (usar AWS Secrets Manager / HashiCorp Vault)

### Paso 2: Deploy Contratos
```bash
export PRIVATE_KEY=0x...
npx hardhat run scripts/deploy.js --network rollux
```

### Paso 3: Verificar en Explorer
```bash
npx hardhat verify --network rollux <CONTRACT_ADDRESS> [constructor args]
```

### Paso 4: Configurar Roles
- Asignar `REGISTRAR_ROLE` en EvidenceRegistry al backend wallet
- Asignar `POLICE_ROLE` y `FISCAL_ROLE` en CaseManager a wallets operativas
- Asignar `MINTER_ROLE` en Token al backend wallet

### Paso 5: Levantar Infraestructura
```bash
docker-compose up -d --build
```

### Paso 6: DNS + SSL
- Apuntar dominio a servidor de producción
- Configurar Cloudflare / certbot para SSL
- Habilitar WAF rules para protección de APIs

---

## 11. Seguridad en Producción

| Capa | Medida |
|------|--------|
| Claves | AWS KMS / Azure Key Vault / HSM. Nunca en reposo plano |
| Smart Contracts | ReentrancyGuard, AccessControl, validaciones de input |
| API | Rate limiting, JWT auth para endpoints sensibles |
| DApp | CSP headers, XSS protection, input sanitization |
| Blockchain | Multi-sig para admin roles, timelock en cambios críticos |
| IPFS | Pinning en múltiples nodos, gateway privada |

---

## 12. Stack Tecnológico Completo

| Componente | Tecnología |
|-----------|-----------|
| L1 Security | Bitcoin (merge-mined) |
| L2 Execution | Syscoin Rollux (EVM, Chain ID 570) |
| Smart Contracts | Solidity 0.8.20, OpenZeppelin |
| Framework SC | Hardhat |
| Wallet | Pali Wallet (browser extension) |
| Frontend | React 18, Vite, Tailwind CSS, Ethers.js v6 |
| Backend | Python 3.11, FastAPI, Web3.py, eth-account |
| Storage | IPFS (Pinata), PostgreSQL |
| DevOps | Docker, Docker Compose, Nginx |

---

*Documento técnico del subsistema Web3 de IntelExtorsión. Listo para implementación en producción.*
