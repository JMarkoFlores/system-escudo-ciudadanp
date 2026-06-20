# IntelExtorsión - Subsistema de Agentes Autónomos
## Arquitectura Detallada

---

## 1. Visión General

El subsistema de Agentes Autónomos es el cerebro analítico de la plataforma IntelExtorsión. Se encarga de procesar denuncias de extorsión mediante un pipeline de 8 agentes especializados, orquestados por **LangGraph** sobre un estado compartido, utilizando **GPT-5.5** como motor de razonamiento, **PostgreSQL** para persistencia transaccional y **Qdrant** para memoria semántica vectorial.

### Stack Tecnológico Obligatorio
| Componente | Tecnología | Uso |
|-----------|-----------|-----|
| Orquestación | **LangGraph** | Grafo de estados y flujo de agentes |
| LLM | **GPT-5.5** (OpenAI) | Razonamiento, extracción, decisión |
| Base Relacional | **PostgreSQL 16** | Datos transaccionales, memoria conversacional |
| Vector DB | **Qdrant** | Embeddings de casos, búsqueda semántica |
| API | **FastAPI** | Exposición REST del subsistema |

---

## 2. Arquitectura del Grafo (LangGraph)

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
            ┌───────┤   INTAKE    │◄──── Valida y clasifica entrada
            │       │   AGENT     │
            │       └──────┬──────┘
            │              │
            │    ┌─────────┼─────────┐
            │    │         │         │
       NO válido  Imagen   Audio    Texto
            │    │         │         │
            ▼    ▼         ▼         ▼
         [END] ┌────┐   ┌────┐   ┌────┐
               │OCR │   │SPCH│   │NLP │
               └─┬──┘   └─┬──┘   └─┬──┘
                 │        │        │
                 └────────┴────────┘
                          │
                   ┌──────▼──────┐
                   │    NLP      │◄──── Análisis lingüístico integrado
                   │   AGENT     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ CORRELATION │◄──── Matching con historial (Qdrant)
                   │   AGENT     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │    OSINT    │◄──── Enriquecimiento external
                   │   AGENT     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │    RISK     │◄──── Score de riesgo consolidado
                   │   AGENT     │
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
           Bajo/Medio    Alto      Crítico
              │           │           │
              ▼           ▼           ▼
           [END]    ┌────────┐   ┌────────┐
                     │ ALERT  │   │ ALERT  │
                     │ AGENT  │   │ AGENT  │
                     └───┬────┘   └───┬────┘
                         │            │
                         └─────┬──────┘
                               ▼
                             [END]
```

---

## 3. Especificación de Agentes

### 3.1 Intake Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Recibir, validar y clasificar denuncias entrantes por canal. Determinar si aplica al ámbito de extorsión. |
| **Entradas** | `canal`, `tipo_contenido`, `contenido_raw`, `metadata` |
| **Salidas** | `IntakeResult` (JSON): válido, categoría, prioridad (1-5), entidades detectadas, notas |
| **Herramientas** | Ninguna externa; usa prompt engineering con GPT-5.5 |
| **Prompt Interno** | `INTAKE_SYSTEM_PROMPT` - instrucciones de validación, minimización de datos, detección de entidades |
| **Memoria** | No requiere memoria a largo plazo; opera sobre el estado actual |
| **Flujo de Decisión** | Si `valido=false`, termina el grafo (`END`). Si es imagen → OCR, si es audio → Speech, si es texto → NLP |
| **Comunicación** | Escribe `resultado_intake` en estado compartido. Decide ruta condicional del grafo |

### 3.2 OCR Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Extraer y estructurar texto de imágenes o documentos adjuntos a la denuncia |
| **Entradas** | `url_archivo`, `hash_archivo`, `tipo_contenido` (imagen/documento) |
| **Salidas** | `OCRResult`: texto_extraido, idioma, confianza, entidades con bbox |
| **Herramientas** | `extraer_texto_ocr` (Tesseract/AWS Textract wrapper) |
| **Prompt Interno** | `OCR_SYSTEM_PROMPT` - validación de OCR, corrección de errores, estructuración forense |
| **Memoria** | Guarda embedding del texto extraído en Qdrant para búsqueda semántica |
| **Flujo de Decisión** | Si no hay archivo o no es imagen/documento, salta este nodo. Siempre continúa a NLP |
| **Comunicación** | Escribe `resultado_ocr` en estado. El NLP Agent consume este resultado |

### 3.3 Speech Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Transcribir audio y analizar características forenses del habla (emoción, fondo, acento) |
| **Entradas** | `url_archivo` (audio/video), `duracion_estimada` |
| **Salidas** | `SpeechResult`: transcripción, idioma, duración, confianza, emoción detectada |
| **Herramientas** | `transcribir_audio` (OpenAI Whisper wrapper) |
| **Prompt Interno** | `SPEECH_SYSTEM_PROMPT` - análisis prosódico, indicadores de amenaza, observaciones forenses |
| **Memoria** | Almacena transcripción en memoria conversacional del caso |
| **Flujo de Decisión** | Salta si no es audio/video. Siempre continúa a NLP |
| **Comunicación** | Escribe `resultado_speech`. NLP lo integra con OCR y texto raw |

### 3.4 NLP Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Análisis lingüístico profundo: intención, sentimiento, entidades, indicadores de extorsión, score de amenaza |
| **Entradas** | `contenido_raw` + `resultado_ocr` + `resultado_speech` (consolidado) |
| **Salidas** | `NLPResult`: intención, sentimiento, entidades, resumen, keywords, indicadores, score_amenaza |
| **Herramientas** | `buscar_casos_similares` (Qdrant) para contextualización previa |
| **Prompt Interno** | `NLP_SYSTEM_PROMPT` - clasificación de intención, cálculo de score de amenaza, resumen ejecutivo |
| **Memoria** | Guarda resumen y keywords en Qdrant como embedding semántico del caso |
| **Flujo de Decisión** | Siempre continúa a Correlation. Si falta texto, registra error pero continúa |
| **Comunicación** | Escribe `resultado_nlp`. Consumido por Correlation, OSINT y Risk |

### 3.5 Correlation Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Detectar relaciones entre el caso actual y denuncias históricas mediante matching de entidades y patrones |
| **Entradas** | `resultado_nlp` (entidades, resumen), acceso a Qdrant para búsqueda semántica |
| **Salidas** | `CorrelationResult`: lista de correlaciones, red_criminal_detectada, modus_operandi_id, score_red |
| **Herramientas** | `buscar_casos_similares` (Qdrant), `consultar_denuncia_db` |
| **Prompt Interno** | `CORRELATION_SYSTEM_PROMPT` - matching difuso, análisis de series, detección de MO |
| **Memoria** | Lee embeddings de Qdrant; no escribe memoria propia (resultado va a PostgreSQL) |
| **Flujo de Decisión** | Siempre continúa a OSINT. Si no hay NLP previo, opera con metadatos limitados |
| **Comunicación** | Escribe `resultado_correlacion`. Consumido por Risk |

### 3.6 OSINT Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Enriquecer la investigación con inteligencia de fuentes abiertas (teléfonos, cuentas, redes) |
| **Entradas** | Entidades extraídas por Intake y NLP (teléfonos, cuentas, aliases) |
| **Salidas** | `OSINTResult`: teléfonos, cuentas, redes sociales, dispositivos, fuentes consultadas, riesgo_osint |
| **Herramientas** | `consultar_osint` (wrapper de APIs externas legítimas) |
| **Prompt Interno** | `OSINT_SYSTEM_PROMPT` - ámbito permitido, restricciones legales, documentación de fuentes |
| **Memoria** | No persistente propia; resultados van a PostgreSQL |
| **Flujo de Decisión** | Siempre continúa a Risk. Puede ser saltado por configuración `OSINT_ENABLED=false` |
| **Comunicación** | Escribe `resultado_osint`. Consumido por Risk |

### 3.7 Risk Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Integrar todos los resultados previos en una evaluación de riesgo unificada con recomendación operativa |
| **Entradas** | `resultado_intake`, `resultado_nlp`, `resultado_correlacion`, `resultado_osint` |
| **Salidas** | `RiskResult`: nivel_riesgo (bajo/medio/alto/crítico), score numérico, factores, recomendación, acción inmediata |
| **Herramientas** | Ninguna externa; razonamiento puro del LLM |
| **Prompt Interno** | `RISK_SYSTEM_PROMPT` - factores de evaluación, niveles definidos, viabilidad de intervención |
| **Memoria** | No requiere memoria externa; opera sobre estado acumulado |
| **Flujo de Decisión** | Si riesgo es ALTO/CRÍTICO, marca `requiere_escalamiento=true`. Siempre continúa a Alert |
| **Comunicación** | Escribe `resultado_riesgo` y actualiza `nivel_riesgo` en estado compartido |

### 3.8 Alert Agent
| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Generar alertas oficiales cuando el riesgo amerite acción inmediata del personal policial |
| **Entradas** | `resultado_riesgo` |
| **Salidas** | `AlertResult`: alerta_generada, alerta_id, canales_notificación, mensaje_corto |
| **Herramientas** | `emitir_alerta` (persiste en PostgreSQL + webhook/email) |
| **Prompt Interno** | `ALERT_SYSTEM_PROMPT` - reglas de emisión, formato para analistas, sugerencia de unidad de reacción |
| **Memoria** | No requiere memoria; operación transaccional |
| **Flujo de Decisión** | Si riesgo < ALTO, genera `alerta_generada=false` y termina. Si es ALTO/CRÍTICO, emite alerta oficial |
| **Comunicación** | Escribe `resultado_alerta`. Es el nodo terminal del grafo (antes del END) |

---

## 4. Diagrama de Flujo de Datos

```
┌──────────────┐
│   CANALES    │ (WhatsApp, Telegram, Discord)
└──────┬───────┘
       │ HTTPS/WebSocket
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                     │
│  POST /v1/denuncias  │  POST /v1/denuncias/{id}/procesar   │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              SERVICIO DE EJECUCIÓN (AgentExecutionService)   │
│  1. Crear Denuncia (PostgreSQL)                              │
│  2. Construir AgenteState                                    │
│  3. Invocar LangGraph                                        │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH - STATE GRAPH                   │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │ INTAKE  │───►│ OCR/SP  │───►│   NLP   │───►│  CORR   │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       │                                          │          │
│       └──────────────────────────────────────────┘          │
│       │                                          ▼          │
│       │                                    ┌─────────┐      │
│       │                                    │  OSINT  │      │
│       │                                    └────┬────┘      │
│       │                                         ▼           │
│       │                                    ┌─────────┐      │
│       │                                    │  RISK   │      │
│       │                                    └────┬────┘      │
│       │                                         ▼           │
│       │                                    ┌─────────┐      │
│       └───────────────────────────────────►│ ALERT   │      │
│                                            └─────────┘      │
│                                                              │
│  Estado compartido: AgenteState (Pydantic)                   │
│  Checkpoint: MemorySaver (persiste en memoria/volumen)       │
└─────────────────────────────────────────────────────────────┘
       │
       ├────────► PostgreSQL (Resultados, Alertas, Métricas)
       │
       ├────────► Qdrant (Embeddings de casos para búsqueda semántica)
       │
       └────────► Webhooks / Email (Alertas críticas)
```

---

## 5. Modelo de Datos (PostgreSQL)

### Tablas Principales

#### `denuncias`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID | PK, generado automáticamente |
| `canal` | VARCHAR(50) | Origen: whatsapp, telegram, discord |
| `id_externo` | VARCHAR(255) | ID del mensaje en plataforma externa |
| `did_denunciante` | VARCHAR(255) | Identidad descentralizada (opcional) |
| `estado` | ENUM | recibido → en_analisis → procesado → ... → alerta_generada |
| `tipo_contenido` | ENUM | texto, imagen, audio, video, documento |
| `contenido_raw` | TEXT | Texto original o transcripción previa |
| `url_archivo` | VARCHAR(512) | Ruta al archivo en almacenamiento |
| `hash_archivo` | VARCHAR(64) | SHA-256 del archivo para integridad |
| `metadata_json` | JSONB | Metadatos flexibles |
| `created_at` | TIMESTAMPTZ | Timestamp de creación |
| `procesado_at` | TIMESTAMPTZ | Timestamp de fin de procesamiento |

#### `resultados_agentes`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID | PK |
| `denuncia_id` | UUID | FK → denuncias |
| `agente` | VARCHAR(50) | Nombre del agente |
| `resultado_json` | JSONB | Payload estructurado del resultado |
| `tokens_consumidos` | INT | Métrica de uso de LLM |
| `tiempo_ms` | INT | Latencia del agente |
| `exitoso` | BOOLEAN | Si la ejecución fue exitosa |
| `error_msg` | TEXT | Mensaje de error si aplica |
| `created_at` | TIMESTAMPTZ | Timestamp |

#### `alertas`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID | PK |
| `denuncia_id` | UUID | FK |
| `nivel` | ENUM | bajo, medio, alto, critico |
| `titulo` | VARCHAR(255) | Título de alerta |
| `descripcion` | TEXT | Descripción detallada |
| `recomendacion` | TEXT | Recomendación operativa |
| `leida` / `atendida` | BOOLEAN | Estado de gestión |
| `atendida_por` | VARCHAR(255) | Usuario/entidad que atendió |

#### `memoria_conversacional`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID | PK |
| `session_id` | VARCHAR(255) | ID de sesión (denuncia_id) |
| `role` | VARCHAR(50) | system, user, assistant, tool |
| `content` | TEXT | Contenido del mensaje |
| `tool_calls` | JSONB | Llamadas a herramientas |

---

## 6. Memoria Híbrida (PostgreSQL + Qdrant)

### Corto Plazo (Conversacional)
- **Almacenamiento**: PostgreSQL (`memoria_conversacional`)
- **Uso**: Últimos 20 mensajes de interacción con el LLM por sesión
- **Recuperación**: SQL ordenado por timestamp

### Largo Plazo (Semántica)
- **Almacenamiento**: Qdrant (vectores de 1536 dimensiones)
- **Modelo de embeddings**: `text-embedding-3-large` (OpenAI)
- **Uso**: Búsqueda de casos similares por similitud coseno
- **Actualización**: Después de cada ejecución exitosa del NLP Agent

### Flujo de Contexto
```
Usuario/Llm
    │
    ▼
┌─────────────────┐
│  HybridMemory   │
│                 │
│  ┌───────────┐  │    ┌─────────────┐
│  │  Corto    │  │───►│ PostgreSQL  │
│  │  Plazo    │  │    │ (SQL)       │
│  └───────────┘  │    └─────────────┘
│                 │
│  ┌───────────┐  │    ┌─────────────┐
│  │  Largo    │  │───►│   Qdrant    │
│  │  Plazo    │  │    │ (Vector)    │
│  └───────────┘  │    └─────────────┘
└─────────────────┘
```

---

## 7. APIs REST

### Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Health check del sistema |
| `POST` | `/v1/denuncias` | Crear denuncia y lanzar grafo en background |
| `POST` | `/v1/denuncias/{id}/procesar` | Ejecutar grafo síncrono sobre denuncia existente |
| `GET` | `/v1/denuncias/{id}` | Obtener denuncia con resultados |
| `GET` | `/v1/denuncias/{id}/resultados` | Listar resultados por agente |
| `GET` | `/v1/denuncias/{id}/alertas` | Listar alertas generadas |
| `GET` | `/v1/busqueda/semantica?q=...` | Búsqueda vectorial de casos similares |

---

## 8. Esquema de Carpetas

```
intel_extorsion_agent_system/
├── app/
│   ├── __init__.py
│   ├── agents/              # (Extensión futura: clases de agente personalizados)
│   ├── api/
│   │   ├── __init__.py
│   │   └── main_api.py      # FastAPI app y endpoints
│   ├── config/
│   │   └── settings.py      # Pydantic Settings (.env)
│   ├── core/
│   │   ├── __init__.py
│   │   └── agent_graph.py   # Definición del grafo LangGraph
│   ├── memory/
│   │   ├── __init__.py
│   │   └── hybrid_memory.py # PostgreSQL + Qdrant
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py      # SQLAlchemy models
│   │   └── db_session.py    # Async session manager
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system_prompts.py # Prompts de los 8 agentes
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── agent_schemas.py  # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── agent_service.py  # Lógica de ejecución del grafo
│   └── tools/
│       ├── __init__.py
│       └── shared_tools.py   # LangChain Tools
├── deployments/
│   └── Dockerfile
├── tests/
├── docs/
│   └── ARCHITECTURE.md       # Este documento
├── docker-compose.yml
├── main.py                   # Entry point Uvicorn
└── requirements.txt
```

---

## 9. Instrucciones de Despliegue

### Desarrollo Local

```bash
# 1. Clonar y entrar al directorio
cd intel_extorsion_agent_system

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (crear .env)
cp .env.example .env
# Editar .env con GROQ_API_KEY, etc.

# 5. Levantar infraestructura
docker-compose up -d postgres qdrant redis

# 6. Iniciar API
python main.py
# Accesible en http://localhost:8000/docs
```

### Producción (Docker Compose completo)

```bash
docker-compose up -d --build
```

---

## 10. Consideraciones de Seguridad

1. **OpenAI API Key**: Almacenar en HashiCorp Vault o AWS Secrets Manager; nunca en repositorio.
2. **Datos PII**: Los prompts están diseñados para minimizar la exposición de datos personales innecesarios.
3. **OSINT**: El OSINT Agent opera solo sobre fuentes públicas legítimas; se documenta toda fuente consultada.
4. **Blockchain (Integración futura)**: El hash de evidencias puede registrarse on-chain sin exponer contenido raw.
5. **Rate Limiting**: Implementado a nivel de API Gateway (Kong/AWS API Gateway).

---

*Documento generado para el equipo de desarrollo de IntelExtorsión. Arquitectura lista para implementación.*
