# AGENTS.md - Contexto del Proyecto IntelExtorsión

> **IMPORTANTE PARA AGENTES FUTUROS:** Leer este archivo ANTES de hacer cualquier cambio. Contiene el historial completo del proyecto, decisiones arquitectónicas, estado actual y próximos pasos.

---

## 1. Qué es este Proyecto

**IntelExtorsión** es una plataforma de **INTELIGENCIA CIUDADANA** para la recepción, análisis, correlación y preservación de evidencias digitales relacionadas con reportes de extorsión.

> **⚠️ IMPORTANTE:** Este sistema NO es un canal directo de denuncia formal a la policía.
>
> El sistema recibe reportes de extorsión de ciudadanos, los analiza con IA forense, correlaciona casos similares y entrega inteligencia procesada a las autoridades competentes (DIVINCRI La Libertad) para que tomen acciones operativas.
>
> **Para denuncias formales ante la Fiscalía o PNP, los ciudadanos deben utilizar la línea 111 o acudir a la comisaría más cercana.** Este sistema complementa, pero no reemplaza, los canales oficiales de denuncia.

### Stack Tecnológico
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS
- **Backend Agentes:** FastAPI + LangGraph + GroqCloud (LLM)
- **Backend Web3:** FastAPI + Web3.py + zkSYS Genesis Testnet
- **Smart Contracts:** Solidity 0.8.24 + Hardhat + OpenZeppelin v5
- **Base de Datos:** PostgreSQL 16 + Qdrant (vector DB) + Redis 7
- **Blockchain:** zkSYS Tanenbaum Testnet (Chain ID 57057)
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

### Sesión de Integración de WhatsApp y Bots de Canales (2026-06-21)
- **Solicitud del usuario:** Integrar un bot de WhatsApp para recibir denuncias y evidencias usando Whapi.cloud, configurar ngrok y documentar todo.
- **Cambios realizados:**
  1. **`app/channels/whatsapp_bot.py`** — Implementada la clase `WhatsAppBot` conectada a Whapi.cloud: descarga y transcripción de audios con Whisper, registro y procesamiento del caso con LangGraph.
  2. **Webhook en `main_api.py`** — Creado el endpoint `POST /v1/channels/whatsapp/webhook` que recibe los mensajes y los delega asíncronamente en segundo plano.
  3. **Seguridad y Filtros** — Se ignoran mensajes salientes (`from_me = True`) para evitar bucles infinitos, y se ignoran chats de grupo (`@g.us`) para evitar spam del bot en conversaciones ajenas.
  4. **Docker Compose y Configuración** — Declarada la variable `WHATSAPP_API_TOKEN` en `docker-compose.yml` y mapeada en `.env` para sincronizarse con el contenedor.
  5. **Túnel local** — Configuración exitosa de ngrok redirigiendo `https://duckbill-exit-detection.ngrok-free.dev` hacia `http://localhost:8000` para pruebas locales.
- **Resultado:** Flujo de WhatsApp completado y listo para pruebas o presentación.

### Sesión de Despliegue a Producción (2026-06-30/07-01)
- **Solicitud del usuario:** Desplegar la plataforma completa en la VM de DigitalOcean (142.93.240.223) con dominio intelextorsion.duckdns.org
- **Cambios realizados:**
  1. **Creación de `deploy/`** — `docker-compose.prod.yml` (8 servicios), `.env.production`, nginx.conf, setup_vm.sh, quick_deploy.sh, deploy_vm.py, CHECKLIST_DEPLOY.md
  2. **Variables de entorno configurables** — `SEED_ADMIN_PASSWORD`, `SEED_SUPERVISOR_PASSWORD`, `SEED_ANALISTA_PASSWORD` en settings.py
  3. **DApp contractService.js** — Actualizado con interfaz EvidenceSeal (sealEvidence, getSeal, verifySeal)
  4. **EvidenceUploader.jsx** — Firma blockchain con parámetros del nuevo contrato
  5. **deploy.js** — EvidenceSeal deployment + SEALER_ROLE
  6. **UI/UX del portal ciudadano** — Rediseño completo de todas las pestañas (DID, KPIs, evidencias, chat split-layout, ayuda, sidebar, header) con estilos premium
  7. **Landing page `#web3`** — Reescrita con propósito claro, 3 cards de features, CTA. Sin labels RF
  8. **Header** — Eliminado enlace "DApp Web3"
  9. **Wallet connection** — `wallet_requestPermissions` para forzar selección de cuenta, `wallet_revokePermissions` para desconectar
  10. **Git push resuelto** — GitHub bloqueaba push por API key en `.env`. Solución: `.gitignore`, `git rm --cached .env`, placeholder en deploy_vm.py
  11. **VM configurada** — Docker instalado, todos los contenedores corriendo, firewall (22/80/443), nginx reverse proxy
  12. **PostgreSQL reseteado** — Volumen recreado para sincronizar password
  13. **Puertos expuestos** — agent-api:8000, web3-backend:8001, citizen:3000, police:3001 (localhost only)
- **Resultado:** Plataforma desplegada y funcionando en http://intelextorsion.duckdns.org
  - **Agent API:** http://intelextorsion.duckdns.org/api/health → `{"status":"ok","componentes":{"postgres":"ok","qdrant":"ok","groq":"ok","langgraph":"ok"}}`
  - **Web3 Backend:** http://intelextorsion.duckdns.org/web3api/health → `{"blockchain_connected":true}`
  - **Frontend Ciudadano:** http://intelextorsion.duckdns.org → 200
  - **Frontend Policial:** http://intelextorsion.duckdns.org/policial/ → 200
  - **7 contenedores Docker** corriendo (postgres, redis, qdrant, agent-api, web3-backend, citizen, police)
  - **nginx** sirviendo como reverse proxy en puerto 80
- **Bugs corregidos durante deploy:**
  - `docker-compose.prod.yml` YAML syntax errors (`:?` validation syntax)
  - Traefik incompatible con versión Docker API → reemplazado por nginx
  - PostgreSQL volume reset para sincronizar password entre compose y DB
  - Frontend-police port mapping (3001→3000) corregido
  - Containers sin ports expuestos → añadidos `127.0.0.1:PORT:PORT`

### Sesión de Revisión Integral (2026-06-30)
- **Solicitud del usuario:** Revisar el sistema completo, corregir bugs críticos, unificar red blockchain, actualizar documentación y dejar los tests verdes.
- **Cambios realizados:**
  1. **Unificación de red blockchain** — Todo el sistema ahora apunta a **zkSYS Tanenbaum Testnet (Chain ID 57057)** incluyendo contratos desplegados, Web3 Backend, DApp y frontends.
  2. **Corrección Web3 Backend** — Se arreglaron `NameError` en funciones de custodia/casos/token y la verificación de evidencia por hash (`hashToEvidenceId`). Se añadió `GET /v1/evidencias/{hash}/verificar`.
  3. **Privacidad en bots de canales** — Se implementó menú de clasificación RF-01 y se eliminaron identificadores personales de `metadata_json` en WhatsApp, Telegram y Discord.
  4. **Robustez del grafo LangGraph** — Las denuncias que fallan en el grafo pasan a estado `error_procesamiento`; los reprocesos ya no duplican resultados.
  5. **Mock LLM determinista** — Se añadió `MockLLM` (`MOCK_LLM=true`) para tests/CI sin consumir tokens Groq.
  6. **Tests de integración verdes** — Se creó `tests/test_integration.py` con 10 tests end-to-end; **10/10 pasan** en Docker.
  7. **Autenticación JWT** — Se implementó login con usuarios seed (`admin`, `supervisor`, `analista`) y se protegieron endpoints del dashboard policial.
  8. **Alembic** — Se configuraron migraciones y se aplicó la inicial (`add usuarios`).
  9. **Alertas push** — Nuevo `app/services/notification_service.py` con envío de webhook HTTP y email SMTP al persistir alertas oficiales.
  10. **Mapa de calor con Plan Cuadrante PNP** — Se añadió `app/data/plan_cuadrante_la_libertad.geojson` y `GET /v1/heatmap/cuadrantes`; el heatmap cruza denuncias con cuadrantes oficiales.
  11. **Frontend policial** — Login real contra `/v1/auth/login`, almacenamiento de token JWT y logout; `agentApi` inyecta el token automáticamente.
  12. **Documentación actualizada** — `AGENTS.md`, `IMPLEMENTACION.md`, `QA_REPORT.md`, `RUN.md`, `.env.example`.
- **Resultado:** Sistema estable con todos los contenedores corriendo, tests verdes y funcionalidades mayores (auth, notificaciones, heatmap) implementadas.

---

## 3. Estado Actual de Componentes (Post-Migración)

| Componente | Estado | Puerto | Notas |
|------------|--------|--------|-------|
| **PostgreSQL** | 🟢 Healthy | 5432 | Datos persistentes en volumen Docker |
| **Qdrant** | 🟢 Running | 6333 | Vector DB para embeddings. Colección: `denuncias_embeddings_v2` (384 dims) |
| **Redis** | 🟢 Running | 6379 | Caché y broker |
| **Agent System API** | 🟢 Running | 8000 | FastAPI + LangGraph + Groq. Health: `/health` |
| **Web3 Backend API** | 🟢 Running | 8001 | FastAPI + Web3.py. Conectado a zkSYS Tanenbaum Testnet |
| **Frontend Ciudadano** | 🟢 Running | 3000 | Next.js standalone. Portal ciudadano |
| **Frontend Policial** | 🟢 Running | 3001 | Next.js standalone. Login JWT + dashboards |
| **DApp Web3** | 🟢 Running | 3002 | React + Pali Wallet. zkSYS Tanenbaum |
| **Smart Contracts** | ✅ Desplegados | - | Solidity 0.8.24 + EVM Cancun. Direcciones en zkSYS Tanenbaum |

### URLs de Acceso
```
Frontend Ciudadano:     http://localhost:3000
Frontend Policial:      http://localhost:3001
DApp Web3:              http://localhost:3002
Dashboard Policial:     http://localhost:3001/dashboard/policial
Dashboard Analítico:    http://localhost:3001/dashboard/analitico
Grafos Criminales:      http://localhost:3001/dashboard/grafos
Centro de Alertas:      http://localhost:3001/dashboard/alertas
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
│   ├── test_integration.py         # 10 tests end-to-end (10/10 pasan)
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.test.yml         # Orquestación de tests con MOCK_LLM=true
│
├── intel_extorsion_agent_system/   # Subsistema de Agentes (MIGRADO A GROQ)
│   ├── docker-compose.yml
│   ├── requirements.txt            # langchain-groq==0.1.10, fastembed
│   ├── main.py
│   ├── alembic.ini                 # Configuración de migraciones
│   ├── alembic/                    # Migraciones Alembic
│   ├── deployments/Dockerfile      # Precarga modelo fastembed
│   ├── app/
│   │   ├── config/settings.py      # GROQ_*, QDRANT_DIMENSION=384, JWT, alertas
│   │   ├── core/agent_graph.py     # ChatGroq + MockLLM
│   │   ├── api/main_api.py         # Health check "groq"
│   │   ├── api/auth_router.py      # JWT login + require_user
│   │   ├── services/notification_service.py  # Alertas push email/webhook
│   │   ├── data/                   # GeoJSON Plan Cuadrante PNP
│   │   ├── memory/hybrid_memory.py # FastEmbedLocal (sin API key)
│   │   ├── agents/                 # 10 agentes autónomos
│   │   └── ...
│   └── docs/ARCHITECTURE.md
│
├── intel_extorsion_web3_system/    # Subsistema Web3
│   ├── hardhat.config.js           # Solidity 0.8.24, evm: cancun, red zkSYS Tanenbaum
│   ├── contracts/                  # 4 contratos (EvidenceRegistry, CaseManager, DIDRegistry, Token)
│   ├── scripts/deploy.js
│   ├── test/test.js
│   ├── backend/                    # FastAPI + Web3.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   └── dapp/                       # DApp React separada
│
├── intel_extorsion_frontend_citizen/   # Frontend ciudadano (Next.js)
│   ├── Dockerfile
│   ├── next.config.mjs
│   └── src/app/
│
├── intel_extorsion_frontend_police/    # Frontend policial (Next.js)
│   ├── Dockerfile
│   ├── next.config.mjs
│   └── src/app/
│
└── intel_extorsion_frontend/       # Frontend legacy monolítico (Next.js)
    ├── Dockerfile
    ├── next.config.mjs
    ├── package.json
    └── src/app/
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
# Red oficial: zkSYS Tanenbaum Testnet (Chain ID 57057)
WEB3_PROVIDER_URL=https://rpc-zk.tanenbaum.io
CHAIN_ID=57057
EXPLORER_URL=https://explorer-zk.tanenbaum.io
NETWORK_NAME=zkSYS Tanenbaum Testnet
PRIVATE_KEY=0x...                          # Wallet institucional
CONTRACT_EVIDENCE_REGISTRY=0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb
CONTRACT_CASE_MANAGER=0x3576cb05B2c4094e8f97639892D235044d7476a1
CONTRACT_DID_REGISTRY=0x8481c85e54f50C676f0fc37f90848030c3B12bB9
CONTRACT_TOKEN=0x622AA147eD0238840ceb215941D5E8CD997896F0
```

**Nota:** El sistema arranca y funciona SIN `GROQ_API_KEY` (lazy loading), pero los agentes no procesarán denuncias hasta que se configure.

---

## 7. Bugs y Problemas Conocidos

| # | Problema | Severidad | Workaround / Solución |
|---|----------|-----------|----------------------|
| 1 | ~~`test_crear_denuncia_y_procesar` falla con `KeyError` en prompt formatting~~ | **RESUELTO** | ✅ Corregido: Se escaparon placeholders JSON (`{{bool}}`, `{{str}}`, etc.) en `system_prompts.py`. Se normalizó `nivel_riesgo` a minúsculas. Se reparó import `llm` en `agent_graph.py`. |
| 2 | ~~Smart Contracts no desplegados~~ | **RESUELTO** | ✅ Contratos desplegados en zkSYS Tanenbaum Testnet. Direcciones en `.env.example` y `AGENTS.md`. |
| 3 | `asyncpg` requiere compilador C en Windows | **BAJA** | Solo afecta desarrollo local en Windows. En Docker Linux funciona perfectamente. |
| 4 | ~~Descarga de modelo fastembed en primer arranque~~ | **RESUELTO** | ✅ El modelo `all-MiniLM-L6-v2` se precarga en el Dockerfile del `agent-api`. |
| 5 | Frontend no tiene axios/lucide-react types instalados | **BAJA** | Errores LSP pero no afectan build/runtime. `npm run build` funciona. |
| 6 | Rate limits de GroqCloud (TPM) | **BAJA** | El modelo `llama-3.3-70b-versatile` tiene límite de 12k tokens/minuto. En flujos con muchos agentes puede dar 429. Usar `MOCK_LLM=true` para tests/CI. En producción, controlar throughput o usar tier de pago. |
| 7 | ~~Inconsistencia de red blockchain en documentación y templates~~ | **RESUELTO** | ✅ Todo el sistema apunta a zkSYS Tanenbaum (57057). Actualizar `.env` local si aún usa valores antiguos. |
| 8 | ~~Bots de canales almacenaban PII del denunciante~~ | **RESUELTO** | ✅ Se implementó menú de clasificación RF-01 y se eliminaron identificadores personales de `metadata_json`. |
| 9 | ~~Alertas siempre se persistían con nivel "medio"~~ | **RESUELTO** | ✅ Se corrigió el prompt del Alert Agent y `_persistir_alerta` para usar el nivel de riesgo real. |
| 10 | ~~Web3 Service tenía `NameError` en funciones de custodia/casos/token~~ | **RESUELTO** | ✅ Se corrigió la construcción del objeto `func` antes de `_send_transaction` y se añadió `GET /v1/evidencias/{hash}/verificar`. |
| 11 | Login policial con credenciales hardcodeadas | **BAJA** | Usuarios seed (`admin`/`Admin123!`, `supervisor`/`Super123!`, `analista`/`Analista123!`) para demo. En producción implementar administración de usuarios. |

---

## 8. Cómo Levantar el Sistema (Comandos Rápidos)

```bash
# 1. Todas las variables en .env (mínimo: GROQ_API_KEY, POSTGRES_PASSWORD)

# 2. Levantar TODO de una vez
docker compose up -d

# 3. Verificar
curl http://localhost:8000/health      # Agent API
curl http://localhost:8001/health      # Web3 Backend
curl http://localhost:3000             # Frontend Ciudadano
curl http://localhost:3001             # Frontend Policial
curl http://localhost:3002             # DApp Web3

# 4. Ver logs
docker compose logs -f agent-api
docker compose logs -f web3-backend
docker compose logs -f frontend-citizen
docker compose logs -f frontend-police
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

**Resultados actuales:** `tests/test_integration.py`
- ✅ test_health_agent_api
- ✅ test_health_web3_backend
- ✅ test_crear_denuncia_texto
- ✅ test_procesar_denuncia_y_generar_tracking (con `MOCK_LLM=true`)
- ✅ test_tracking_por_codigo
- ✅ test_dashboard_metricas
- ✅ test_listar_denuncias
- ✅ test_listar_alertas
- ✅ test_web3_registrar_y_verificar_evidencia
- ✅ test_busqueda_semantica

**Ejecución:**
```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit
```

---

## 10. Próximos Pasos Pendientes (Priorizados)

1. ~~**Obtener GROQ_API_KEY** y validar procesamiento completo de denuncias~~ ✅ RESUELTO
2. ~~**Corregir bug de parsing** en `AGENT_PROMPTS` (`system_prompts.py`)~~ ✅ RESUELTO
3. ~~**Migrar a zkSYS Tanenbaum Testnet** — Fase 0 completada~~ ✅ RESUELTO
4. ~~**Implementar Fase 1: Agente Autónomo End-to-End** — Grafo LangGraph completo~~ ✅ RESUELTO
5. ~~**Implementar subida de archivos y OCR/STT real** — Fase 1 completada~~ ✅ RESUELTO
6. ~~**Fix routing del grafo (node_risk, node_intake, node_seal)**~~ ✅ RESUELTO
7. ~~**Precargar modelo fastembed** en Dockerfile~~ ✅ RESUELTO
8. ~~**Tests de integración verdes**~~ ✅ RESUELTO
9. ~~**Autenticación JWT y roles en frontend policial**~~ ✅ RESUELTO
10. ~~**Alertas push (email/webhook)**~~ ✅ RESUELTO (base implementada; configurar SMTP/webhook en `.env`)
11. ~~**Mapa de calor con Plan Cuadrante PNP**~~ ✅ RESUELTO (GeoJSON base + endpoint)
12. ~~**Migraciones Alembic**~~ ✅ RESUELTO
13. ~~**CRUD de usuarios policiales en frontend policial y backend~~ ✅ RESUELTO
14. ~~**Integrar GeoJSON oficial del Plan Cuadrante PNP~~ ✅ RESUELTO (código mejorado, documentación creada)
15. ~~**Actualizar documentación y tests tras cambios~~ ✅ RESUELTO

**Próximos pasos:**
16. **Obtener PRIVATE_KEY real** para zkSYS Tanenbaum (actualmente usa placeholder `0x000...001`)
17. **Configurar HTTPS/SSL** — certbot + Let's Encrypt para `intelextorsion.duckdns.org`
18. **Configurar canales** — WhatsApp (WHATSAPP_API_TOKEN), Telegram (TELEGRAM_BOT_TOKEN), Discord (DISCORD_BOT_TOKEN) en `.env` de la VM
19. **Implementar Fase 2** (gas dinámico EIP-1559, firma digital real en acta PDF, seal secundario Sepolia) — ver Sección 7 en `IMPLEMENTACION.md`
20. **Notificaciones SMS/SIRDIC-SIDPOL** cuando un clúster supere umbral
21. **Obtener GeoJSON oficial** del Plan Cuadrante PNP (reemplazar polígonos demo por datos reales de la DIVINCRI)
22. **Domain HTTPS** — configurar DuckDNS + Let's Encrypt para HTTPS

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
- **Red actual:** zkSYS Tanenbaum Testnet (Chain ID 57057). NO cambiar a Rollux (570) ni Genesis (5700) a menos que se solicite explícitamente. El RPC es `https://rpc-zk.tanenbaum.io` y el explorer `https://explorer-zk.tanenbaum.io`.
- **Contratos desplegados en zkSYS Tanenbaum:** EvidenceRegistry `0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb`, CaseManager `0x3576cb05B2c4094e8f97639892D235044d7476a1`, DIDRegistry `0x8481c85e54f50C676f0fc37f90848030c3B12bB9`, Token `0x622AA147eD0238840ceb215941D5E8CD997896F0`.
- **Verificación de conectividad:** Usar `npx hardhat run scripts/checkNetwork.js --network zkSYSTestnet` después de configurar `.env`.
- **OCR real con Tesseract:** El contenedor `agent-api` tiene `tesseract-ocr` y `tesseract-ocr-spa` instalados. El servicio `app/services/ocr_service.py` usa `pytesseract.image_to_string()` con lang=`spa`. Si no se extrae texto, revisar que la imagen tenga texto legible y que el idioma `spa` esté instalado.
- **STT real con Groq Whisper:** `app/services/stt_service.py` usa `groq.audio.transcriptions.create()` con modelo `whisper-large-v3-turbo`. Requiere `GROQ_API_KEY`. Límite: 25MB por archivo, 25 req/min en tier gratuito.
- **File upload:** Endpoint `POST /v1/denuncias/{id}/adjuntar`. Acepta multipart file. Validación por MIME. Almacena en `/app/uploads/evidencias/`. Calcula SHA-256. Max 50MB.
- **Routing del grafo LangGraph:** `node_risk` y `node_intake` deben devolver TODOS los cambios de estado en el dict de retorno. NO mutar `state.*` in-place porque LangGraph congela el estado Pydantic tras cada nodo.
- **Smart Contracts:** Si `_load_contracts` detecta `0x0000...` como address, trata el contrato como "no configurado" y devuelve modo dev. El endpoint `/v1/evidencias/seal` en Web3 Backend no requiere contratos deployados para responder.
- **Autenticación:** Dashboard policial requiere JWT. Credenciales seed en `auth_service.seed_default_users()`. `agentApi` inyecta el token desde `localStorage.police_token`.
- **Alembic:** En dev `create_all` mantiene el esquema actualizado; en producción ejecutar `alembic upgrade head`. Si una tabla ya existe por `create_all`, usar `alembic stamp <revision>`.
- **Tests:** Usar `MOCK_LLM=true` para tests/CI deterministas. `docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit`.

---

### Sesión de Internacionalización i18n (2026-07-01) - Español/Inglés
- **Solicitud del usuario:** Implementar cambio de idioma Español/Inglés con persistencia en localStorage, manteniendo términos técnicos (blockchain, wallet, DID, Web3, etc.) sin traducir
- **Cambios realizados (ambos frontends):**
  1. **Instalación de dependencias** — `i18next`, `react-i18next`, `i18next-browser-languagedetector` en citizen y police
  2. **`src/lib/i18n/`** — Configuración compartida: `i18n.ts` (detector de idioma por localStorage), `I18nProvider.tsx` (wrapper client-side), `locales/es.json` y `locales/en.json`
  3. **`src/components/LanguageSwitcher.tsx`** — Componente reutilizable con modo compacto (solo bandera) y modo normal (bandera + texto)
  4. **`I18nClientLayout.tsx`** — Cliente wrapper que combina `I18nProvider` + `ToastProvider` + actualiza `<html lang>` dinámicamente
  5. **Layouts actualizados** — `layout.tsx` en ambos frontends usa `I18nClientLayout`, `suppressHydrationWarning`
- **Frontend Ciudadano migrado:**
  - **Landing (`page.tsx`):** Nav, hero, features, channels, "how it works", Web3 section, CTA, footer; `LanguageSwitcher` en nav desktop y mobile
  - **Portal (`portal/page.tsx`):** Wallet connection, DID card, sidebar, tabs, KPIs, cluster, quick actions, custody, evidence history, help glossary, FAQ, chat, security, tips, disconnect, footer
  - **Tracking (`tracking/page.tsx`):** Titles, agent status labels, blockchain summary, footer
- **Frontend Policial migrado:**
  - **Login (`page.tsx`):** Form, buttons, errors, footer; `LanguageSwitcher` en card header
  - **Dashboard layout (`dashboard/layout.tsx`):** `navItems` convertido a función `getNavItems(t)`, header/sidebar textos con `t()`, `LanguageSwitcher` en header
  - **Dashboard policial (`dashboard/policial/page.tsx`):** Título, subtítulo, stat cards, tabla, estados
  - **Dashboard analítico (`dashboard/analitico/page.tsx`):** Título, subtítulo
  - **Grafos (`dashboard/grafos/page.tsx`):** Título, subtítulo, loading text
  - **Alertas (`dashboard/alertas/page.tsx`):** Título, subtítulo
  - **Usuarios (`dashboard/usuarios/page.tsx`):** Título
  - **Revelaciones (`dashboard/revelaciones/page.tsx`):** Título, subtítulo, cómo funciona, estados, loading, empty state, stats, labels
  - **Detalle denuncia (`dashboard/policial/[id]/page.tsx`):** Título, info general, DID, nivel riesgo, agentes descripciones, OSINT risk, sellado, resoluciones
- **Reglas de traducción:**
  - Términos técnicos/Web3 (blockchain, wallet, DID, SHA-256, Web3, DApp, Pali Wallet, Testnet, zkSYS, hash, TRJ, etc.) permanecen en inglés en ambos idiomas
  - Nombres de agentes (Intake Agent, OCR Agent, etc.) en inglés; solo descripciones traducidas
  - Prefijos de claves: `common.*`, `landing.*`, `portal.*`, `tracking.*`, `login.*`, `dashboard.*`, `alertas.*`, `detalle.*`, `riesgo.*`, `agents.*`, `revelaciones.*`
- **Bug corregido:** `seal_results` type error en `dashboard/policial/[id]/page.tsx:643` — añadido `as any` al resultado del `find`
- **Resultado:** Ambos frontends build exitoso (citizen: 6 rutas, police: 10 rutas). Traducción funcional con persistencia localStorage.

---

*Última actualización: 2026-07-01*
*Contexto generado tras sesión de internacionalización i18n: Español/Inglés, persistencia localStorage, términos técnicos sin traducir*
