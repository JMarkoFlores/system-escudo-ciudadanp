# AGENTS.md - Contexto del Proyecto IntelExtorsión

> **IMPORTANTE PARA AGENTES FUTUROS:** Leer este archivo ANTES de hacer cualquier cambio. Contiene el historial completo del proyecto, decisiones arquitectónicas, estado actual y próximos pasos.

---

## 1. Qué es este Proyecto

**IntelExtorsión** es una plataforma de inteligencia policial para la recepción, análisis, correlación y preservación de evidencias digitales relacionadas con denuncias de extorsión.

### Stack Tecnológico
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS
- **Backend Agentes:** FastAPI + LangGraph + GroqCloud (LLM)
- **Backend Web3:** FastAPI + Web3.py + Syscoin Rollux L2
- **Smart Contracts:** Solidity 0.8.24 + Hardhat + OpenZeppelin v5
- **Base de Datos:** PostgreSQL 16 + Qdrant (vector DB) + Redis 7
- **Blockchain:** Syscoin Rollux (Chain ID 570)
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

---

## 3. Estado Actual de Componentes (Post-Migración)

| Componente | Estado | Puerto | Notas |
|------------|--------|--------|-------|
| **PostgreSQL** | 🟢 Healthy | 5432 | Datos persistentes en volumen Docker |
| **Qdrant** | 🟢 Running | 6333 | Vector DB para embeddings. Colección: `denuncias_embeddings_v2` (384 dims) |
| **Redis** | 🟢 Running | 6379 | Caché y broker |
| **Agent System API** | 🟢 Running | 8000 | FastAPI + LangGraph + Groq. Health: `/health` |
| **Web3 Backend API** | 🟢 Running | 8001 | FastAPI + Web3.py. Conectado a Rollux RPC |
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
WEB3_PROVIDER_URL=https://rpc.rollux.com
CHAIN_ID=570
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
| 2 | Smart Contracts no desplegados | **MEDIA** | Requieren deploy en Rollux Testnet/Mainnet. Sin addresses reales, Web3 Backend devuelve 500 en endpoints de contrato. La arquitectura está lista. |
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

1. **Obtener GROQ_API_KEY** y validar procesamiento completo de denuncias
2. ~~**Corregir bug de parsing** en `AGENT_PROMPTS` (`system_prompts.py`)~~ ✅ RESUELTO
3. **Desplegar Smart Contracts** en Rollux Testnet y obtener addresses reales
4. **Completar .env** con CONTRACT_* addresses y PRIVATE_KEY
5. **Integración Pali Wallet** en frontend para funcionalidad Web3 completa
6. **Canales externos:** Implementar bots de WhatsApp/Telegram/Discord
7. **STT (Speech-to-Text):** Definir estrategia (OpenAI API Whisper, Groq Whisper, o local)
8. **Precargar modelo fastembed** en Dockerfile para evitar descarga en primer arranque

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

---

*Última actualización: 2026-06-19*
*Contexto generado tras sesión de corrección de bugs en portal ciudadano y flujo de denuncias*
