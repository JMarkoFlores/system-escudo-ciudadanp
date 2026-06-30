# IntelExtorsión

> **Plataforma de Inteligencia Ciudadana contra la Extorsión**
>
> **⚠️ IMPORTANTE:** Este sistema NO es un canal directo de denuncia formal a la policía.
>
> Es una plataforma de **INTELIGENCIA CIUDADANA** que recibe reportes de extorsión, los analiza con IA forense, correlaciona casos similares y entrega inteligencia procesada a las autoridades competentes (DIVINCRI La Libertad) para que tomen acciones operativas.
>
> **Para denuncias formales ante la Fiscalía o PNP, los ciudadanos deben utilizar la línea 111 o acudir a la comisaría más cercana.** Este sistema complementa, pero no reemplaza, los canales oficiales de denuncia.
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

**IntelExtorsión** es una plataforma integral de inteligencia ciudadana diseñada para combatir la extorsión mediante el uso de tecnologías de punta:

- **10 Agentes de IA Autónomos** (Intake, OCR, Speech, NLP, Correlation, OSINT, Risk, Seal, Alert, Respond) que analizan reportes de forma automática.
- **Portal Ciudadano** anónimo y seguro para reportar información vía Web, WhatsApp, Telegram o Discord.
- **Dashboard Policial** en tiempo real con métricas, alertas críticas y gestión de casos.
- **Preservación en Blockchain** (zkSYS Tanenbaum Testnet) para garantizar la inmutabilidad de evidencias.
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
| **zkSYS Tanenbaum** | - | L2 Blockchain (Chain ID 57057) |
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
│  │   :3000      │  │   :3001      │  │  :3001           │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          │  ┌──────────────┴───────────────────┐│
          │  │         DApp Web3 (React)        ││
          │  │              :3002               ││
          │  └──────────────────────────────────┘│
          │                                      │
          └─────────────────┬────────────────────┘
                            │
          ┌─────────────────┴───────────────────┐
          │         FRONTENDS NEXT.JS            │
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

### Flujo de un Reporte

1. **Ciudadano** envía reporte vía Portal Web (o WhatsApp/Telegram/Discord).
2. **Intake Agent** valida que sea extorsión y extrae entidades.
3. **OCR / Speech Agent** procesan archivos adjuntos (imágenes, audios).
4. **NLP Agent** analiza texto, sentimiento, score de amenaza.
5. **Correlation Agent** busca casos similares en la base de datos.
6. **OSINT Agent** enriquece con inteligencia de fuentes abiertas.
7. **Risk Agent** calcula nivel de riesgo (bajo/medio/alto/crítico).
8. **Seal Agent** sella evidencias en blockchain para trazabilidad judicial.
9. **Alert Agent** genera alerta policial si el riesgo es alto/crítico.
10. **Respond Agent** genera código de seguimiento `TRJ-XXXXXXXX` (8 caracteres).
11. **Dashboard** muestra el reporte, métricas y alertas en tiempo real.
12. **Inteligencia procesada** se entrega a las autoridades competentes para operativos.

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
- Construye la imagen del **Frontend Ciudadano** (Node 20 + Next.js standalone)
- Construye la imagen del **Frontend Policial** (Node 20 + Next.js standalone)
- Construye la imagen de la **DApp Web3** (Vite + React)
- Levanta **PostgreSQL**, **Qdrant** y **Redis**
- Configura la red interna entre contenedores

### 4. Verificar Estado de los Servicios

```bash
# Ver contenedores activos
docker compose ps

# Verificar health checks
curl http://localhost:8000/health      # Agent API
curl http://localhost:8001/health      # Web3 Backend
curl http://localhost:3000             # Frontend Ciudadano
curl http://localhost:3001             # Frontend Policial
curl http://localhost:3002             # DApp Web3
```

### 5. Recompilar un Servicio Específico

```bash
# Solo el frontend ciudadano
docker compose build frontend-citizen
docker compose up -d frontend-citizen

# Solo el frontend policial
docker compose build frontend-police
docker compose up -d frontend-police

# Solo el agent-api (útil tras cambios en lógica de agentes)
docker compose build agent-api
docker compose up -d agent-api

# Sin caché (compilación limpia)
docker compose build --no-cache frontend-citizen
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
docker compose logs -f frontend-citizen
docker compose logs -f frontend-police
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
IPFS_JWT=tu_jwt_de_pinata_o_infura
```

> **Nota:** El sistema arranca y funciona **sin** `GROQ_API_KEY`, pero los agentes no procesarán denuncias hasta que configures la API key.

---

## Endpoints y URLs

### Acceso Principal

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend Ciudadano** | http://localhost:3000 | Landing page y portal ciudadano |
| **Portal Ciudadano** | http://localhost:3000/portal | Chat para reportar información |
| **Tracking** | http://localhost:3000/tracking?code=TRJ-XXXXXXXX | Consulta pública de estado |
| **Frontend Policial** | http://localhost:3001 | Login y consola DIVINCRI |
| **Dashboard Policial** | http://localhost:3001/dashboard/policial | Vista general y reportes recientes |
| **Dashboard Analítico** | http://localhost:3001/dashboard/analitico | Métricas, gráficos y heatmap |
| **Centro de Alertas** | http://localhost:3001/dashboard/alertas | Gestión de alertas críticas |
| **Grafos Criminales** | http://localhost:3001/dashboard/grafos | Visualización de redes |
| **DApp Web3** | http://localhost:3002 | Wallet Pali y evidencias blockchain |

### APIs

| Servicio | URL | Docs |
|----------|-----|------|
| **Agent System API** | http://localhost:8000 | http://localhost:8000/docs (Swagger UI) |
| **Web3 Backend API** | http://localhost:8001 | http://localhost:8001/docs (Swagger UI) |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | UI de Vector DB |

### Endpoints Clave (Agent API)

```bash
# Crear denuncia (público)
POST /v1/denuncias

# Login policial
POST /v1/auth/login

# Listar denuncias (requiere JWT)
GET /v1/denuncias?estado=recibido&canal=web&limit=50

# Obtener una denuncia (requiere JWT)
GET /v1/denuncias/{denuncia_id}

# Tracking ciudadano (público)
GET /v1/denuncias/tracking/{tracking_code}

# Procesar denuncia manualmente (público, trigger interno)
POST /v1/denuncias/{denuncia_id}/procesar

# Adjuntar evidencia
POST /v1/denuncias/{denuncia_id}/adjuntar

# Búsqueda semántica (requiere JWT)
GET /v1/busqueda/semantica?q=extorsión+telefónica&limit=5

# Métricas del dashboard (requiere JWT)
GET /v1/dashboard/metricas

# Listar alertas (requiere JWT)
GET /v1/alertas

# Heatmap / Plan Cuadrante PNP (requiere JWT)
GET /v1/heatmap
GET /v1/heatmap/cuadrantes
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
│   ├── test_integration.py         # 10 tests end-to-end (10/10 pasan)
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.test.yml         # Orquestación de tests con MOCK_LLM=true
│
├── intel_extorsion_agent_system/   # Subsistema de Agentes Autónomos
│   ├── docker-compose.yml
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # Entry point
│   ├── alembic.ini                 # Migraciones Alembic
│   ├── alembic/
│   ├── deployments/
│   │   └── Dockerfile              # Imagen del Agent API
│   ├── app/
│   │   ├── config/settings.py      # Configuración (GROQ_*, DB, QDRANT, JWT)
│   │   ├── core/agent_graph.py     # Grafo LangGraph + LLM Groq + MockLLM
│   │   ├── api/main_api.py         # Endpoints FastAPI
│   │   ├── api/auth_router.py      # JWT login + require_user
│   │   ├── services/agent_service.py
│   │   ├── services/notification_service.py  # Alertas push
│   │   ├── memory/hybrid_memory.py # FastEmbedLocal + Qdrant
│   │   ├── prompts/system_prompts.py
│   │   ├── data/                   # GeoJSON Plan Cuadrante PNP
│   │   ├── agents/                 # 10 agentes autónomos
│   │   │   ├── intake_agent.py
│   │   │   ├── ocr_agent.py
│   │   │   ├── speech_agent.py
│   │   │   ├── nlp_agent.py
│   │   │   ├── correlation_agent.py
│   │   │   ├── osint_agent.py
│   │   │   ├── risk_agent.py
│   │   │   ├── seal_agent.py
│   │   │   ├── alert_agent.py
│   │   │   └── respond_agent.py
│   │   └── models/
│   │       ├── database.py         # Modelos SQLAlchemy
│   │       └── db_session.py       # Sesiones async
│   └── tests/
│       └── test_agents.py
│
├── intel_extorsion_web3_system/    # Subsistema Web3 / Blockchain
│   ├── hardhat.config.js           # Config Solidity 0.8.24 + Cancun + red Tanenbaum
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
│   └── dapp/                       # DApp React + Pali Wallet
│
├── intel_extorsion_frontend_citizen/   # Frontend Ciudadano Next.js
│   ├── Dockerfile
│   ├── next.config.mjs
│   └── src/app/
│
├── intel_extorsion_frontend_police/    # Frontend Policial Next.js
│   ├── Dockerfile
│   ├── next.config.mjs
│   └── src/app/
│
└── intel_extorsion_frontend/       # Frontend legacy monolítico Next.js
    ├── Dockerfile
    ├── next.config.mjs
    └── src/app/
```

---

## Tests

### Tests de Integración (Docker - recomendado)

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit
```

**Resultados actuales:** 10/10 PASSED
- ✅ test_health_agent_api
- ✅ test_health_web3_backend
- ✅ test_crear_denuncia_texto
- ✅ test_procesar_denuncia_y_generar_tracking
- ✅ test_tracking_por_codigo
- ✅ test_dashboard_metricas
- ✅ test_listar_denuncias
- ✅ test_listar_alertas
- ✅ test_web3_registrar_y_verificar_evidencia
- ✅ test_busqueda_semantica

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
| "Error al registrar reporte" | Verifica `GROQ_API_KEY` en `.env`. Revisa logs: `docker compose logs -f agent-api` |
| Dashboard muestra "No hay reportes" | Verifica que `GET /v1/denuncias` responda: `curl http://localhost:8000/v1/denuncias` |
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

**IntelExtorsión** es un proyecto de inteligencia ciudadana desarrollado con fines de combate a la extorsión mediante tecnologías emergentes.

- **Agentes de IA:** LangGraph + GroqCloud
- **Embeddings:** FastEmbed (ONNX local)
- **Blockchain:** zkSYS Genesis Testnet
- **Frontend:** Next.js 14 + Tailwind CSS

---

*Última actualización: 2026-06-19*
*Versión del sistema: 1.0.0*
