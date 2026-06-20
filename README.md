# IntelExtorsión

> **Plataforma de Inteligencia Policial contra la Extorsión**
>
> Recepción, análisis, correlación y preservación de evidencias digitales mediante agentes de IA autónomos y blockchain.

---

## Tabla de Contenidos

1. [Descripción](#descripción)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Arquitectura](#arquitectura)
4. [Requisitos Previos](#requisitos-previos)
5. [Instalación y Compilación con Docker](#instalación-y-compilación-con-docker)
6. [Variables de Entorno](#variables-de-entorno)
7. [Endpoints y URLs](#endpoints-y-urls)
8. [Estructura del Proyecto](#estructura-del-proyecto)
9. [Tests](#tests)
10. [Documentación](#documentación)
11. [Troubleshooting](#troubleshooting)

---

## Descripción

**IntelExtorsión** es una plataforma integral de inteligencia policial diseñada para combatir la extorsión mediante el uso de tecnologías de punta:

- **8 Agentes de IA Autónomos** (Intake, OCR, Speech, NLP, Correlation, OSINT, Risk, Alert) que analizan denuncias de forma automática.
- **Portal Ciudadano** anónimo y seguro para registrar denuncias vía Web, WhatsApp, Telegram o Discord.
- **Dashboard Policial** en tiempo real con métricas, alertas críticas y gestión de casos.
- **Preservación en Blockchain** (Syscoin Rollux L2) para garantizar la inmutabilidad de evidencias.
- **Búsqueda Semántica** con embeddings vectoriales para detectar patrones y redes criminales.

---

## Stack Tecnológico

### Frontend
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Next.js** | 14.2.4 | Framework React con App Router |
| **TypeScript** | 5.x | Tipado estático |
| **Tailwind CSS** | 3.x | Estilos utilitarios |
| **Lucide React** | Latest | Iconografía |
| **Axios** | Latest | Cliente HTTP |
| **React Hot Toast** | Latest | Notificaciones |
| **date-fns** | Latest | Formateo de fechas |
| **Recharts** | Latest | Gráficos analíticos |

### Backend - Sistema de Agentes
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Python** | 3.11 | Lenguaje principal |
| **FastAPI** | Latest | API REST async |
| **LangGraph** | Latest | Orquestación de agentes |
| **LangChain-Groq** | 0.1.10 | Integración con LLM Groq |
| **GroqCloud** | - | LLM `llama-3.3-70b-versatile` |
| **FastEmbed** | Latest | Embeddings locales (ONNX) |
| **SQLAlchemy** | 2.x | ORM async para PostgreSQL |
| **AsyncPG** | Latest | Driver PostgreSQL async |

### Backend - Web3 / Blockchain
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Python** | 3.11 | Backend Web3 |
| **FastAPI** | Latest | API REST |
| **Web3.py** | 6.x | Interacción con EVM |
| **Syscoin Rollux** | - | L2 Blockchain (Chain ID 570) |
| **Hardhat** | 2.x | Framework Smart Contracts |
| **Solidity** | 0.8.24 | Lenguaje de contratos |
| **OpenZeppelin** | v5 | Librería de seguridad |

### Infraestructura
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **PostgreSQL** | 16 | Base de datos relacional |
| **Qdrant** | 1.9.1 | Base de datos vectorial |
| **Redis** | 7 | Caché y broker |
| **Docker** | 24+ | Contenerización |
| **Docker Compose** | 2.24+ | Orquestación |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     CIUDADANO / ANALISTA                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Portal Web │  │   Dashboard  │  │  Dashboard       │  │
│  │  (Next.js)   │  │   Policial   │  │  Analítico       │  │
│  │   :3000      │  │   :3000      │  │  :3000           │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          └─────────────────┴───────────────────┘
                            │
          ┌─────────────────┴───────────────────┐
          │         FRONTEND NEXT.JS             │
          │      (Standalone Output)             │
          └─────────────────┬───────────────────┘
                            │
          ┌─────────────────┼───────────────────┐
          │                 │                   │
┌─────────▼─────────┐ ┌─────▼──────┐  ┌────────▼────────┐
│  AGENT SYSTEM API │ │  WEB3 API  │  │   Qdrant        │
│   (FastAPI)       │ │ (FastAPI)  │  │   (Vector DB)   │
│    :8000          │ │   :8001    │  │    :6333        │
│                   │ │            │  │                 │
│  • Intake Agent   │ │ • Web3.py  │  │ • Embeddings    │
│  • OCR Agent      │ │ • IPFS     │  │   (384 dims)    │
│  • Speech Agent   │ │ • Rollux   │  │ • Similaridad   │
│  • NLP Agent      │ └────────────┘  └─────────────────┘
│  • Correlation    │         │
│  • OSINT          │         │
│  • Risk           │         │
│  • Alert          │         │
└─────────┬─────────┘         │
          │                   │
┌─────────▼───────────────────▼─────────┐
│           POSTGRESQL + REDIS          │
│       :5432           :6379           │
│  • Denuncias      • Caché             │
│  • Resultados     • Sesiones          │
│  • Alertas                            │
│  • Métricas                           │
└───────────────────────────────────────┘
```

### Flujo de una Denuncia

1. **Ciudadano** envía denuncia vía Portal Web (o WhatsApp/Telegram/Discord en futuras versiones).
2. **Intake Agent** valida que sea extorsión y extrae entidades.
3. **OCR / Speech Agent** procesan archivos adjuntos (imágenes, audios).
4. **NLP Agent** analiza texto, sentimiento, score de amenaza.
5. **Correlation Agent** busca casos similares en la base de datos.
6. **OSINT Agent** enriquece con inteligencia de fuentes abiertas.
7. **Risk Agent** calcula nivel de riesgo (bajo/medio/alto/crítico).
8. **Alert Agent** genera alerta policial si el riesgo es alto/crítico.
9. **Dashboard** muestra la denuncia, métricas y alertas en tiempo real.

---

## Requisitos Previos

- **Docker Desktop** o **Docker Engine** 24.0+
- **Docker Compose** 2.24+
- **Git** (para clonar el repositorio)
- **4 GB RAM** mínimo (recomendado 8 GB)
- **10 GB espacio libre** en disco
- **API Key de GroqCloud** (obligatorio para que los agentes procesen denuncias)

---

## Instalación y Compilación con Docker

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd System-Escudo-Ciudadano
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales (ver sección [Variables de Entorno](#variables-de-entorno)).

### 3. Compilar y Levantar Todos los Servicios

```bash
# Compilar imágenes y levantar en segundo plano
docker compose up -d --build
```

Este comando:
- Construye la imagen del **Agent API** (Python 3.11 + dependencias ML)
- Construye la imagen del **Web3 Backend** (Python 3.11 + Web3.py)
- Construye la imagen del **Frontend** (Node 20 + Next.js standalone)
- Levanta **PostgreSQL**, **Qdrant** y **Redis**
- Configura la red interna entre contenedores

### 4. Verificar Estado de los Servicios

```bash
# Ver contenedores activos
docker compose ps

# Verificar health checks
curl http://localhost:8000/health      # Agent API
curl http://localhost:8001/health      # Web3 Backend
curl http://localhost:3000             # Frontend
```

### 5. Recompilar un Servicio Específico

```bash
# Solo el frontend (útil tras cambios en UI)
docker compose build frontend
docker compose up -d frontend

# Solo el agent-api (útil tras cambios en lógica de agentes)
docker compose build agent-api
docker compose up -d agent-api

# Sin caché (compilación limpia)
docker compose build --no-cache frontend
```

### 6. Detener el Sistema

```bash
# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ borra datos de PostgreSQL/Qdrant)
docker compose down -v
```

### 7. Ver Logs

```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f agent-api
docker compose logs -f frontend
docker compose logs -f postgres
```

---

## Variables de Entorno

### Mínimas Requeridas

```bash
# GROQCLOUD (OBLIGATORIO para que los agentes procesen denuncias)
GROQ_API_KEY=gsk_tu_clave_aqui
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.2
GROQ_MAX_TOKENS=4096

# POSTGRESQL
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=agent_pass
POSTGRES_DB=intel_extorsion
```

### Opcionales (Web3 / Blockchain)

```bash
# WEB3 (OBLIGATORIO solo para funcionalidad blockchain)
WEB3_PROVIDER_URL=https://rpc.rollux.com
CHAIN_ID=570
PRIVATE_KEY=0x...                          # Wallet institucional
CONTRACT_EVIDENCE_REGISTRY=0x...           # Obtener tras deploy
CONTRACT_CASE_MANAGER=0x...
CONTRACT_DID_REGISTRY=0x...
CONTRACT_TOKEN=0x...
IPFS_JWT=tu_jwt_de_pinata_o_infura
```

> **Nota:** El sistema arranca y funciona **sin** `GROQ_API_KEY`, pero los agentes no procesarán denuncias hasta que configures la API key.

---

## Endpoints y URLs

### Acceso Principal

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Landing page y portal ciudadano |
| **Portal Ciudadano** | http://localhost:3000/portal | Chat para realizar denuncias |
| **Dashboard Policial** | http://localhost:3000/dashboard/policial | Vista general y denuncias recientes |
| **Dashboard Analítico** | http://localhost:3000/dashboard/analitico | Métricas y gráficos |
| **Centro de Alertas** | http://localhost:3000/dashboard/alertas | Gestión de alertas críticas |
| **Grafos Criminales** | http://localhost:3000/dashboard/grafos | Visualización de redes |

### APIs

| Servicio | URL | Docs |
|----------|-----|------|
| **Agent System API** | http://localhost:8000 | http://localhost:8000/docs (Swagger UI) |
| **Web3 Backend API** | http://localhost:8001 | http://localhost:8001/docs (Swagger UI) |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | UI de Vector DB |

### Endpoints Clave (Agent API)

```bash
# Crear denuncia
POST /v1/denuncias

# Listar denuncias
GET /v1/denuncias?estado=recibido&canal=web&limit=50

# Obtener una denuncia
GET /v1/denuncias/{denuncia_id}

# Procesar denuncia manualmente
POST /v1/denuncias/{denuncia_id}/procesar

# Búsqueda semántica
GET /v1/busqueda/semantica?q=extorsión+telefónica&limit=5

# Métricas del dashboard
GET /v1/dashboard/metricas

# Listar alertas
GET /v1/alertas
```

---

## Estructura del Proyecto

```
System-Escudo-Ciudadano/
│
├── docker-compose.yml              # Orquestación Docker consolidada
├── .env.example                    # Variables de entorno de ejemplo
├── .env                            # Variables locales (NO versionar)
│
├── AGENTS.md                       # Contexto completo para agentes de IA
├── README.md                       # Este archivo
├── MANUAL_DENUNCIA.md              # Guía para ciudadanos
├── MIGRATION_REPORT.md             # Informe OpenAI → GroqCloud
├── QA_REPORT.md                    # Auditoría de calidad
├── API_KEYS_GUIDE.md               # Cómo obtener API keys
├── INSTALL.md                      # Guía de instalación detallada
├── RUN.md                          # Ejecución y troubleshooting
├── CHECKLIST_DEPLOY.md             # Checklist de despliegue
│
├── tests/
│   └── test_integration.py         # Tests end-to-end
│
├── intel_extorsion_agent_system/   # Subsistema de Agentes Autónomos
│   ├── docker-compose.yml
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # Entry point
│   ├── deployments/
│   │   └── Dockerfile              # Imagen del Agent API
│   ├── app/
│   │   ├── config/settings.py      # Configuración (GROQ_*, DB, QDRANT)
│   │   ├── core/agent_graph.py     # Grafo LangGraph + LLM Groq
│   │   ├── api/main_api.py         # Endpoints FastAPI
│   │   ├── services/agent_service.py
│   │   ├── memory/hybrid_memory.py # FastEmbedLocal + Qdrant
│   │   ├── prompts/system_prompts.py
│   │   ├── agents/                 # 8 agentes autónomos
│   │   │   ├── intake_agent.py
│   │   │   ├── ocr_agent.py
│   │   │   ├── speech_agent.py
│   │   │   ├── nlp_agent.py
│   │   │   ├── correlation_agent.py
│   │   │   ├── osint_agent.py
│   │   │   ├── risk_agent.py
│   │   │   └── alert_agent.py
│   │   └── models/
│   │       ├── database.py         # Modelos SQLAlchemy
│   │       └── db_session.py       # Sesiones async
│   └── tests/
│       └── test_agents.py
│
├── intel_extorsion_web3_system/    # Subsistema Web3 / Blockchain
│   ├── hardhat.config.js           # Config Solidity 0.8.24 + Cancun
│   ├── contracts/                  # Smart Contracts
│   │   ├── EvidenceRegistry.sol
│   │   ├── CaseManager.sol
│   │   ├── DIDRegistry.sol
│   │   └── Token.sol
│   ├── scripts/deploy.js
│   ├── test/test.js                # Tests Hardhat
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/                    # FastAPI Web3
│   └── dapp/                       # DApp React (futuro)
│
└── intel_extorsion_frontend/       # Frontend Next.js
    ├── Dockerfile                  # Multi-stage (builder + runner)
    ├── next.config.mjs             # Standalone output + rewrites
    ├── package.json
    ├── tailwind.config.ts
    └── src/
        ├── app/
        │   ├── page.tsx            # Landing
        │   ├── portal/page.tsx     # Portal ciudadano
        │   ├── dashboard/
        │   │   ├── policial/page.tsx
        │   │   ├── analitico/page.tsx
        │   │   ├── alertas/page.tsx
        │   │   └── grafos/page.tsx
        │   └── layout.tsx
        ├── services/api.ts         # Clientes axios
        ├── stores/
        │   ├── appStore.ts         # Estado global (Zustand)
        │   └── walletStore.ts      # Estado wallet
        └── types/
            └── index.ts            # Tipos TypeScript
```

---

## Tests

### Tests de Integración (desde el host)

```bash
# Requiere Python 3.11+ y pytest
pip install pytest aiohttp
pytest tests/test_integration.py -v
```

**Resultados actuales:** 6/9 PASSED
- ✅ test_health_checks
- ✅ test_busqueda_semantica
- ✅ test_web3_did_resolver
- ✅ test_postgresql_conectividad
- ✅ test_qdrant_conectividad
- ✅ test_redis_conectividad
- ❌ test_crear_denuncia_y_procesar (requiere GROQ_API_KEY válida)
- ❌ test_web3_verificar_evidencia (requiere contratos desplegados)
- ❌ test_frontend_carga (frontend no ejecutado durante pytest)

### Tests de Smart Contracts

```bash
cd intel_extorsion_web3_system
npm install
npx hardhat test
```

### Tests Unitarios de Agentes

```bash
cd intel_extorsion_agent_system
pip install -r requirements.txt
pytest tests/test_agents.py -v
```

---

## Documentación

| Documento | Propósito |
|-----------|-----------|
| `AGENTS.md` | Contexto técnico completo para agentes de IA |
| `MANUAL_DENUNCIA.md` | Guía paso a paso para ciudadanos |
| `MIGRATION_REPORT.md` | Detalle de migración OpenAI → GroqCloud |
| `QA_REPORT.md` | Auditoría de calidad y hallazgos |
| `API_KEYS_GUIDE.md` | Cómo obtener cada API key |
| `INSTALL.md` | Instalación paso a paso |
| `RUN.md` | Ejecución, monitoreo y troubleshooting avanzado |
| `CHECKLIST_DEPLOY.md` | Checklist para despliegue a producción |

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "Error al registrar denuncia" | Verifica `GROQ_API_KEY` en `.env`. Revisa logs: `docker compose logs -f agent-api` |
| Dashboard muestra "No hay denuncias" | Verifica que `GET /v1/denuncias` responda: `curl http://localhost:8000/v1/denuncias` |
| Botones adjuntar no funcionan | Recompila frontend: `docker compose build frontend && docker compose up -d frontend` |
| Build de frontend lento | Es normal (2-3 minutos). Usa cache: evita `--no-cache` |
| Rate limit 429 (Groq) | El modelo tiene límite de 12k tokens/min. Espera 10s y reintenta |
| PostgreSQL no conecta | Verifica `POSTGRES_PASSWORD` en `.env`. Puerto 5432 libre? |
| Contenedores no arrancan | Verifica Docker Desktop ejecutándose. Revisa RAM disponible |

---

## Estado del Proyecto

| Componente | Estado |
|------------|--------|
| PostgreSQL | 🟢 Healthy |
| Qdrant | 🟢 Running |
| Redis | 🟢 Running |
| Agent System API | 🟢 Running |
| Web3 Backend API | 🟢 Running |
| Frontend Next.js | 🟢 Running |
| Smart Contracts | ✅ Compilados (pendiente deploy) |

---

## Créditos

**IntelExtorsión** es un proyecto de inteligencia policial desarrollado con fines de combate a la extorsión mediante tecnologías emergentes.

- **Agentes de IA:** LangGraph + GroqCloud
- **Embeddings:** FastEmbed (ONNX local)
- **Blockchain:** Syscoin Rollux L2
- **Frontend:** Next.js 14 + Tailwind CSS

---

*Última actualización: 2026-06-19*
*Versión del sistema: 1.0.0*
