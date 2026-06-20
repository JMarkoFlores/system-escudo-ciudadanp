# AGENTS.md - Contexto del Proyecto IntelExtorsión

> **IMPORTANTE PARA AGENTES FUTUROS:** Leer este archivo ANTES de hacer cualquier cambio. Contiene el historial completo del proyecto, decisiones arquitectónicas, estado actual y próximos pasos.

---

## 1. Qué es este Proyecto

**IntelExtorsión** es una plataforma de inteligencia policial para la recepción, análisis, correlación y preservación de evidencias digitales relacionadas con denuncias de extorsión.

### Stack Tecnológico
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS
- **Backend Agentes:** FastAPI + LangGraph + GroqCloud (LLM)
- **Backend Web3:** FastAPI + Web3.py + zkSYS Genesis Testnet
- **Smart Contracts:** Solidity 0.8.24 + Hardhat + OpenZeppelin v5
- **Base de Datos:** PostgreSQL 16 + Qdrant (vector DB) + Redis 7
- **Blockchain:** zkSYS Genesis Testnet (Chain ID 5700)
- **Wallet:** Pali Wallet

---

## 2. Historial de Sesiones de Desarrollo

### Sesión Inicial (2026-06-19) - Arquitectura y Validación
- Se diseñó la arquitectura completa de la plataforma
- Se implementaron 5 fases: Agentes Autónomos, Web3, Frontend, Docker, QA
- Se detectaron y corrigieron múltiples bugs críticos
- Se validó Docker Compose, Smart Contracts, Frontend build

### Sesión de Migración (2026-06-19) - OpenAI → GroqCloud
- **Solicitud del usuario:** Migrar TODO el sistema de OpenAI a GroqCloud
- **Problema crítico detectado:** GroqCloud NO tiene API de embeddings
- **Solución implementada:** Se reemplazó `OpenAIEmbeddings` por `FastEmbedLocal` (modelo ONNX `sentence-transformers/all-MiniLM-L6-v2`) que funciona completamente local sin API key
- **Resultado:** 6/9 tests pasan (antes eran 5/9). La búsqueda semántica ahora funciona sin API key.

### Sesión de Corrección (2026-06-19) - Fix Denuncia y Portal Ciudadano
- **Solicitud del usuario:** El portal ciudadano mostraba "Error al registrar denuncia"
- **Problemas corregidos:**
  1. **Bug crítico en prompts:** Los placeholders de tipo (`{bool}`, `{str}`, `{int}`, `{float}`, `{uuid}`) en los ejemplos JSON de `system_prompts.py` rompían el `.format()` de Python al ser interpretados como variables de formato. Se escaparon a `{{bool}}`, `{{str}}`, etc.
  2. **Import roto en agentes:** `intake_agent.py` (y otros 7 agentes) importaban `llm` desde `agent_graph.py`, pero la variable no existía (solo `get_llm()`). Se añadió `llm = get_llm()` para compatibilidad.
  3. **Normalización de riesgo:** El LLM de Groq devuelve `"ALTO"` en mayúsculas, pero el enum `NivelRiesgo` espera `"alto"`. Se añadió `.lower().strip()` en `node_risk` y `node_alert`.
  4. **Parsing JSON robusto:** `_parse_llm_json` mejorado con fallback non-greedy para evitar errores cuando el LLM devuelve texto extra después del JSON.
  5. **Conectividad Frontend→Backend en Docker:** Los rewrites de `next.config.mjs` apuntaban a `localhost:8000`, pero desde dentro del contenedor Docker `localhost` es el propio contenedor. Se cambió a `http://agent-api:8000` y `http://web3-backend:8001` (nombres de servicio Docker).
- **Resultado:** El flujo completo de denuncia (crear + procesar con 8 agentes) ahora funciona. Se generan alertas para riesgo alto/crítico.

### Sesión de Agente Autónomo (2026-06-20) - Fase 1: End-to-End
- **Solicitud del usuario:** Implementar Fase 1 del plan — completar el grafo LangGraph con nodos seal, alert y respond
- **Cambios realizados:**
  1. `agent_schemas.py` — Añadidos campos `seal_tx_hash`, `seal_block`, `seal_status`, `alert_sent`, `tracking_code`, `content_hash`, `zona_detectada`, `cluster_id`
  2. `seal_agent.py` — Nuevo: nodo que llama al Web3 Backend para sellar evidencias en blockchain
  3. `respond_agent.py` — Nuevo: genera código TRJ-XXXX con respuesta al ciudadano
  4. `web3_client.py` — Nuevo: cliente HTTP asíncrono para Web3 Backend (puerto 8001)
  5. `agent_graph.py` — Añadidos nodos `seal` y `respond`; routing condicional post-risk (ALTO/CRÍTICO → seal → alert → respond, BAJO/MEDIO → respond)
  6. `agent_service.py` — Persiste `tracking_code`, `seal_tx_hash`, `seal_block`, `seal_status` en Denuncia
  7. `database.py` — Reparado (estaba corrupto) y añadidas columnas `tracking_code`, `seal_tx_hash`, `seal_block`, `seal_status`, `nivel_riesgo`
  8. `main_api.py` — Nuevo endpoint `POST /v1/dashboard/push` para SSE, y `GET /v1/denuncias/tracking/{tracking_code}`
  9. `settings.py` — Añadido `WEB3_BACKEND_URL` para comunicación entre agentes y Web3 Backend
- **Resultado:** Grafo LangGraph completo con 10 nodos (intake, ocr, speech, nlp, correlation, osint, risk, seal, alert, respond). Flujo end-to-end: denuncia → TRJ-XXXX. Pendiente Fase 2 para sellado real.

### Sesión de Migración a zkSYS (2026-06-20) - Fase 0: zkSYS Genesis Testnet
- **Solicitud del usuario:** Migrar de Rollux Mainnet (Chain ID 570) a zkSYS Genesis Testnet (Chain ID 5700) para desarrollo y demo sin costos reales
- **Cambios realizados:**
  1. `.env.example` — `WEB3_PROVIDER_URL` → `https://rpc.genesis.zksys.io`, `CHAIN_ID` → `5700`, añadidos `EXPLORER_URL`, `FAUCET_URL`, `NETWORK_NAME`
  2. `hardhat.config.js` — Nueva red `zkSYSTestnet` con RPC y chain ID 5700
  3. `config/settings.py` — Defaults actualizados a zkSYS Genesis Testnet
  4. `walletStore.ts` — Migrado de Rollux (570) a zkSYS (5700): nombres, RPC, explorer, DID format
  5. `usePaliWallet.js` (DApp) — Mismo cambio: switchToZkSYS, red, RPC, explorer
  6. `WalletConnect.jsx` — Botón y mensajes actualizados a zkSYS
  7. `docker-compose.yml` — Defaults de red cambiados a zkSYS
  8. `scripts/checkNetwork.js` — Script de verificación de conectividad creado
- **Resultado:** Sistema completo apuntando a zkSYS Genesis Testnet. Toca ejecutar `npx hardhat run scripts/checkNetwork.js --network zkSYSTestnet` para verificar conectividad.

### Sesión de Integración (2026-06-19) - Dashboard Policial y Adjuntos
- **Solicitud del usuario:** 
  1. Dashboard policial no mostraba denuncias registradas.
  2. Botones de adjuntar archivos en portal ciudadano no funcionaban.
- **Problemas corregidos:**
  1. **Endpoint faltante `GET /v1/denuncias`:** La API no tenía endpoint para listar denuncias. El dashboard llamaba `denunciaService.listar()` que hacía `GET /api/agents/denuncias` y recibía 404. Se agregó `GET /v1/denuncias` con filtros por `estado`, `canal`, `limit` y `offset`.
  2. **Endpoints faltantes del dashboard:** `GET /v1/dashboard/metricas` y `GET /v1/alertas` no existían. Se implementaron ambos con queries agregadas a PostgreSQL.
  3. **Adjuntar archivos en portal:** Los botones de Paperclip, Image y Mic no tenían handlers. Se implementó:
     - Inputs file ocultos para cada tipo (documento, imagen, audio)
     - Preview de archivo adjunto con nombre y tipo
     - Envío correcto de `tipo_contenido` (`imagen`/`audio`/`documento`) según el archivo
     - Metadata del archivo incluida en la denuncia
- **Resultado:** 
  - Dashboard policial ahora carga denuncias reales desde PostgreSQL.
  - Métricas del dashboard son dinámicas (total denuncias, hoy, alertas críticas, etc.).
  - Portal ciudadano permite adjuntar imágenes, audios y documentos.

### Sesión de Fase 1 - OCR Real, STT, Upload, Routing Fix, Gap Analysis (2026-06-20)
- **Solicitud del usuario:** Implementar Fase 1 — file upload endpoint, real OCR con Tesseract, real STT con Groq Whisper; luego deep gap analysis vs `requerimientos.md`
- **Problemas detectados y corregidos:**
  1. **`node_risk` no propagaba `nivel_riesgo` al router** — LangGraph congela el estado Pydantic tras cada nodo. `node_risk` mutaba `state.nivel_riesgo` in-place pero eso no se reflejaba en `router_post_risk` que siempre veía `None`. **Fix:** Devolver `nivel_riesgo` y `requiere_escalamiento` en el dict de retorno.
  2. **`node_intake` mismo bug** — Mutaba `saltar_agentes` y `errores` in-place. **Fix:** Devolver en el dict de retorno.
  3. **Web3 Backend sin `/v1/evidencias/seal`** — El `node_seal` llamaba a un endpoint que no existía. **Fix:** Añadido endpoint JSON con soporte dev-mode.
  4. **Zero address en `_load_contracts`** — `web3_service.py` cargaba contratos en `0x0000...` y fallaba. **Fix:** Tratar `0x0000...` como "no configurado" y devolver dev-mode.
  5. **`node_seal` no persistía resultados** — No devolvía campos top-level del state. **Fix:** Devolver `seal_tx_hash`, `seal_block`, `seal_status`, `content_hash` en el dict.
- **Implementaciones nuevas (Fase 1):**
  1. **`POST /v1/denuncias/{denuncia_id}/adjuntar`** — Endpoint multipart para adjuntar evidencias. Valida MIME (jpeg/png/webp/pdf/mp3/ogg/wav/mp4/txt), límite 50MB, almacena en `/app/uploads/evidencias/`, computa SHA-256.
  2. **`app/services/file_service.py`** — `save_upload()` con validación de tipo/tamaño, `download_from_url()` para canales externos.
  3. **`app/services/ocr_service.py`** — OCR real con `pytesseract.image_to_string()` + `image_to_data()` (confidence scoring). Usa modelo `spa` de Tesseract.
  4. **`app/services/stt_service.py`** — STT real con Groq Whisper `whisper-large-v3-turbo`. `transcribe_audio()` soporta archivos locales y remotos.
  5. **`OCRTool` y `TranscribirAudioTool`** — Actualizados para llamar servicios reales en lugar de simulación.
  6. **`node_ocr` y `node_speech`** — Conectados a servicios reales; extraen texto y pasan a LLM para estructuración forense.
  7. **Dependencias nuevas** — `aiofiles==24.1.0`, `groq==0.9.0` en `requirements.txt`.
- **Gap Analysis vs `requerimientos.md` (Profundo):**
  - Identificados 28+ items faltantes en 6 fases
  - Documentados en Sección 7 de `IMPLEMENTACION.md`
  - Recomendada separación del frontend en `frontend-citizen/` y `frontend-police/`
  - Cronograma extendido de 16-22 días a 70-80 días
- **Validación final:** Flujo completo con 9 agentes ejecutado exitosamente:
  ```
  POST /v1/denuncias → intake → ocr → nlp → correlation → osint → risk (ALTO) → seal → alert → respond → tracking TRJ-AFEZ
  ```
  - OCR se ejecutó (texto no extraído por limitación del test image, no por error)
  - Seal devuelve dev-mode `tx_hash: 0x000...` (contratos no deployados)
  - Tracking code funcional en `GET /v1/denuncias/tracking/TRJ-AFEZ`

---

## 3. Estado Actual de Componentes (Post-Migración)

| Componente | Estado | Puerto | Notas |
|------------|--------|--------|-------|
| **PostgreSQL** | 🟢 Healthy | 5432 | Datos persistentes en volumen Docker |
| **Qdrant** | 🟢 Running | 6333 | Vector DB para embeddings. Colección: `denuncias_embeddings_v2` (384 dims) |
| **Redis** | 🟢 Running | 6379 | Caché y broker |
| **Agent System API** | 🟢 Running | 8000 | FastAPI + LangGraph + Groq. Health: `/health` |
| **Web3 Backend API** | 🟢 Running | 8001 | FastAPI + Web3.py. Conectado a zkSYS Genesis Testnet |
| **Frontend Next.js** | 🟢 Running | 3000 | Build standalone. 9 páginas estáticas |
| **Smart Contracts** | ✅ Compilados | - | 25 archivos. Solidity 0.8.24 + EVM Cancun |

### URLs de Acceso
```
Frontend Principal:     http://localhost:3000
Dashboard Policial:     http://localhost:3000/dashboard/policial
Dashboard Analítico:    http://localhost:3000/dashboard/analitico
Grafos Criminales:      http://localhost:3000/dashboard/grafos
Centro de Alertas:      http://localhost:3000/dashboard/alertas
Portal Ciudadano:       http://localhost:3000/portal
Agent API Docs:         http://localhost:8000/docs
Web3 API Docs:          http://localhost:8001/docs
Qdrant Dashboard:       http://localhost:6333/dashboard
```

---

## 4. Decisiones Arquitectónicas Clave

### 4.1 Migración a GroqCloud (vs OpenAI)
- **Motivo:** Solicitud explícita del usuario. Reduce costos.
- **LLM:** `llama-3.3-70b-versatile` via `ChatGroq` (langchain-groq==0.1.10)
- **Embeddings:** `FastEmbedLocal` (wrapper de `fastembed`) con modelo `sentence-transformers/all-MiniLM-L6-v2`
  - **Ventaja:** Sin API key, local, ultraligero (~50MB vs 2GB de torch)
  - **Dimensión:** 384 (antes era 1536 con OpenAI)
  - **Colección Qdrant:** Renombrada a `denuncias_embeddings_v2` para evitar conflicto de dimensiones

### 4.2 Smart Contracts - OpenZeppelin v5
- Se tuvieron que corregir múltiples breaking changes de OZ v5:
  - `security/ReentrancyGuard` → `utils/ReentrancyGuard`
  - `Counters` eliminado → reemplazado por `uint256` nativo
  - `_exists()` eliminado → `_ownerOf() != address(0)`
  - `_beforeTokenTransfer` → `_update()` + `_increaseBalance()`
  - `evidenceExists()` añadido como helper público
- Solidity actualizado a `0.8.24` con `evmVersion: cancun`

### 4.3 Frontend
- `next.config.ts` no era soportado → convertido a `next.config.mjs`
- `output: 'standalone'` para Docker multi-stage
- `tailwindcss-animate` añadido por dependencia faltante
- `ToastProvider` separado como Client Component (Server Component no soportaba Toaster)

### 4.4 Docker
- `docker-compose.yml` consolidado en raíz (antes paths relativos `../` fallaban)
- Agent API usa `python:3.11-slim` con tesseract-ocr, ffmpeg, build-essential
- Frontend usa `node:20-alpine` multi-stage con standalone output
- Web3 Backend usa `python:3.11-slim`

---

## 5. Estructura de Directorios

```
System-Escudo-Ciudadano/
├── docker-compose.yml              # Orquestación consolidada (VALIDADA)
├── .env.example                    # Variables de entorno (GROQ_* no OPENAI_*)
├── AGENTS.md                       # ESTE ARCHIVO
├── MIGRATION_REPORT.md             # Informe detallado de migración OpenAI→Groq
├── QA_REPORT.md                    # Informe de auditoría QA
├── API_KEYS_GUIDE.md               # Guía de obtención de API Keys
├── INSTALL.md                      # Guía de instalación paso a paso
├── RUN.md                          # Guía de ejecución y troubleshooting
├── CHECKLIST_DEPLOY.md             # Checklist de despliegue a producción
├── tests/
│   └── test_integration.py         # 9 tests end-to-end (6 pasan, 3 esperados)
│
├── intel_extorsion_agent_system/   # Subsistema de Agentes (MIGRADO A GROQ)
│   ├── docker-compose.yml
│   ├── requirements.txt            # langchain-groq==0.1.10, fastembed
│   ├── main.py
│   ├── deployments/Dockerfile
│   ├── app/
│   │   ├── config/settings.py      # GROQ_*, QDRANT_DIMENSION=384
│   │   ├── core/agent_graph.py     # ChatGroq con lazy loading
│   │   ├── api/main_api.py         # Health check "groq"
│   │   ├── memory/hybrid_memory.py # FastEmbedLocal (sin API key)
│   │   ├── agents/                 # 8 agentes autónomos
│   │   └── ...
│   └── docs/ARCHITECTURE.md
│
├── intel_extorsion_web3_system/    # Subsistema Web3
│   ├── hardhat.config.js           # Solidity 0.8.24, evm: cancun
│   ├── contracts/                  # 4 contratos (EvidenceRegistry, CaseManager, DIDRegistry, Token)
│   ├── scripts/deploy.js
│   ├── test/test.js
│   ├── backend/                    # FastAPI + Web3.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   └── dapp/                       # DApp React separada
│
└── intel_extorsion_frontend/       # Frontend Next.js
    ├── Dockerfile                  # Multi-stage standalone
    ├── next.config.mjs
    ├── package.json
    └── src/app/                    # Landing, Portal, Dashboards
```

---

## 6. Configuración Actual (.env)

**Variables MÍNIMAS requeridas para funcionar:**

```bash
# GROQCLOUD (OBLIGATORIO para agentes)
GROQ_API_KEY=gsk_tu_clave_aqui
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
GROQ_MAX_TOKENS=4096

# INFRAESTRUCTURA (defaults funcionan en local)
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=agent_pass
POSTGRES_DB=intel_extorsion

# WEB3 (OBLIGATORIO para funcionalidad blockchain)
WEB3_PROVIDER_URL=https://rpc.genesis.zksys.io
CHAIN_ID=5700
PRIVATE_KEY=0x...                          # Wallet institucional
CONTRACT_EVIDENCE_REGISTRY=0x...           # Obtener tras deploy
CONTRACT_CASE_MANAGER=0x...
CONTRACT_DID_REGISTRY=0x...
CONTRACT_TOKEN=0x...
```

**Nota:** El sistema arranca y funciona SIN `GROQ_API_KEY` (lazy loading), pero los agentes no procesarán denuncias hasta que se configure.

---

## 7. Bugs y Problemas Conocidos

| # | Problema | Severidad | Workaround / Solución |
|---|----------|-----------|----------------------|
| 1 | ~~`test_crear_denuncia_y_procesar` falla con `KeyError` en prompt formatting~~ | **RESUELTO** | ✅ Corregido: Se escaparon placeholders JSON (`{{bool}}`, `{{str}}`, etc.) en `system_prompts.py`. Se normalizó `nivel_riesgo` a minúsculas. Se reparó import `llm` en `agent_graph.py`. |
| 2 | Smart Contracts no desplegados | **MEDIA** | Requieren deploy en zkSYS Genesis Testnet. Sin addresses reales, Web3 Backend devuelve dev-mode en `/v1/evidencias/seal`. `node_seal` funciona con `tx_hash: 0x000...`. La arquitectura está lista. |
| 3 | `asyncpg` requiere compilador C en Windows | **BAJA** | Solo afecta desarrollo local en Windows. En Docker Linux funciona perfectamente. |
| 4 | Descarga de modelo fastembed en primer arranque | **BAJA** | En contenedores sin internet, precargar el modelo en el Dockerfile. |
| 5 | Frontend no tiene axios/lucide-react types instalados | **BAJA** | Errores LSP pero no afectan build/runtime. `npm run build` funciona. |
| 6 | Rate limits de GroqCloud (TPM) | **BAJA** | El modelo `llama-3.3-70b-versatile` tiene límite de 12k tokens/minuto. En flujos con muchos agentes puede dar 429. Esperar unos segundos y reintentar. |

---

## 8. Cómo Levantar el Sistema (Comandos Rápidos)

```bash
# 1. Todas las variables en .env (mínimo: GROQ_API_KEY, POSTGRES_PASSWORD)

# 2. Levantar TODO de una vez
docker compose up -d

# 3. Verificar
curl http://localhost:8000/health      # Agent API
curl http://localhost:8001/health      # Web3 Backend
curl http://localhost:3000             # Frontend

# 4. Ver logs
docker compose logs -f agent-api
docker compose logs -f web3-backend
docker compose logs -f frontend
```

---

## 9. Tests

```bash
# Tests de integración (desde host con Python 3.13+)
pytest tests/test_integration.py -v

# Tests de smart contracts
cd intel_extorsion_web3_system
npx hardhat test

# Tests unitarios agentes
cd intel_extorsion_agent_system
pytest tests/test_agents.py -v
```

**Resultados actuales:** 6/9 PASSED
- ✅ test_health_checks
- ✅ test_busqueda_semantica (mejoró tras migración a embeddings locales)
- ✅ test_web3_did_resolver
- ✅ test_postgresql_conectividad
- ✅ test_qdrant_conectividad
- ✅ test_redis_conectividad
- ❌ test_crear_denuncia_y_procesar (bug de parsing JSON en prompts)
- ❌ test_web3_verificar_evidencia (contratos no desplegados)
- ❌ test_frontend_carga (frontend no ejecutado durante pytest)

---

## 10. Próximos Pasos Pendientes (Priorizados)

1. ~~**Obtener GROQ_API_KEY** y validar procesamiento completo de denuncias~~ ✅ RESUELTO (Flujo completo validado)
2. ~~**Corregir bug de parsing** en `AGENT_PROMPTS` (`system_prompts.py`)~~ ✅ RESUELTO
3. ~~**Migrar a zkSYS Genesis Testnet** — Fase 0 completada~~ ✅ RESUELTO
4. ~~**Implementar Fase 1: Agente Autónomo End-to-End** — Grafo LangGraph completo~~ ✅ RESUELTO
5. ~~**Implementar subida de archivos y OCR/STT real** — Fase 1 completada~~ ✅ RESUELTO
6. ~~**Fix routing del grafo (node_risk, node_intake, node_seal)** — Bugs críticos corregidos~~ ✅ RESUELTO
7. **Desplegar Smart Contracts** en zkSYS Genesis Testnet y obtener addresses reales
8. **Completar .env** con CONTRACT_* addresses y PRIVATE_KEY
9. **Integración Pali Wallet** en frontend para funcionalidad Web3 completa
10. **Canales externos:** Implementar bots de WhatsApp/Telegram/Discord
11. **Precargar modelo fastembed** en Dockerfile para evitar descarga en primer arranque
12. **Implementar Fase 2** (Acta Forense PDF, cobertura API de contratos, gas dinámico) — ver Section 7 en `IMPLEMENTACION.md`
13. **Separar frontend** en `frontend-citizen/` y `frontend-police/` (recomendado para Phase 3)

---

## 11. Documentos Relacionados

| Documento | Propósito |
|-----------|-----------|
| `MIGRATION_REPORT.md` | Detalle completo de migración OpenAI→Groq |
| `QA_REPORT.md` | Auditoría QA con hallazgos y correcciones |
| `API_KEYS_GUIDE.md` | Cómo obtener cada API key |
| `INSTALL.md` | Instalación paso a paso |
| `RUN.md` | Ejecución, monitoreo, troubleshooting |
| `CHECKLIST_DEPLOY.md` | Checklist para despliegue a producción |

---

## 12. Notas para Agentes Futuros

- **NO volver a usar OpenAI** en este proyecto. El usuario especificó GroqCloud obligatoriamente.
- **NO aumentar `QDRANT_DIMENSION`** a 1536. Está en 384 por el modelo fastembed.
- **NO usar `langchain-openai`** ni `openai` package. Ya fueron eliminados.
- **Si se actualiza `langchain-core`**, verificar compatibilidad con `langchain-groq==0.1.10`. Si hay conflicto, buscar versión compatible de langchain-groq.
- **Smart Contracts:** Si se modifica Solidity, usar `0.8.24` y `evmVersion: cancun`. Verificar compatibilidad con OpenZeppelin v5.
- **Docker builds:** Si el build es lento, revisar caché. `docker compose build --no-cache` solo si es necesario.
- **Red actual:** zkSYS Genesis Testnet (Chain ID 5700). NO cambiar a Rollux a menos que se solicite explícitamente. El RPC es `https://rpc.genesis.zksys.io`.
- **Verificación de conectividad:** Usar `npx hardhat run scripts/checkNetwork.js --network zkSYSTestnet` después de configurar `.env`.
- **OCR real con Tesseract:** El contenedor `agent-api` tiene `tesseract-ocr` y `tesseract-ocr-spa` instalados. El servicio `app/services/ocr_service.py` usa `pytesseract.image_to_string()` con lang=`spa`. Si no se extrae texto, revisar que la imagen tenga texto legible y que el idioma `spa` esté instalado.
- **STT real con Groq Whisper:** `app/services/stt_service.py` usa `groq.audio.transcriptions.create()` con modelo `whisper-large-v3-turbo`. Requiere `GROQ_API_KEY`. Límite: 25MB por archivo, 25 req/min en tier gratuito.
- **File upload:** Endpoint `POST /v1/denuncias/{id}/adjuntar`. Acepta multipart file. Validación por MIME. Almacena en `/app/uploads/evidencias/`. Calcula SHA-256. Max 50MB.
- **Routing del grafo LangGraph:** `node_risk` y `node_intake` deben devolver TODOS los cambios de estado en el dict de retorno. NO mutar `state.*` in-place porque LangGraph congela el estado Pydantic tras cada nodo.
- **Smart Contracts:** Si `_load_contracts` detecta `0x0000...` como address, trata el contrato como "no configurado" y devuelve modo dev. El endpoint `/v1/evidencias/seal` en Web3 Backend no requiere contratos deployados para responder.

---

*Última actualización: 2026-06-20*
*Contexto generado tras sesión de integración Fase 1 (OCR real, STT, File Upload)*
