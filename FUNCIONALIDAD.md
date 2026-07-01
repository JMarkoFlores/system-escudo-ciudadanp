# IntelExtorsión — Manual Completo de Funcionalidad del Sistema

> **Plataforma de Inteligencia Ciudadana** para la recepción, análisis, correlación y preservación de evidencias digitales relacionadas con reportes de extorsión.

---

## Índice

1. [Arquitectura General](#1-arquitectura-general)
2. [Subsistema de Agentes Autónomos (LangGraph)](#2-subsistema-de-agentes-autónomos-langgraph)
3. [API REST — Agent System (Puerto 8000)](#3-api-rest--agent-system-puerto-8000)
4. [API REST — Web3 Backend (Puerto 8001)](#4-api-rest--web3-backend-puerto-8001)
5. [Base de Datos PostgreSQL](#5-base-de-datos-postgresql)
6. [Smart Contracts (zkSYS Tanenbaum Testnet)](#6-smart-contracts-zksys-tanenbaum-testnet)
7. [Frontend Ciudadano (Puerto 3000)](#7-frontend-ciudadano-puerto-3000)
8. [Frontend Policial (Puerto 3001)](#8-frontend-policial-puerto-3001)
9. [DApp Web3 (Puerto 3002)](#9-dapp-web3-puerto-3002)
10. [Bots de Canales de Comunicación](#10-bots-de-canales-de-comunicación)
11. [Servicios del Sistema](#11-servicios-del-sistema)
12. [Autenticación y Seguridad](#12-autenticación-y-seguridad)
13. [Despliegue y Contenedores Docker](#13-despliegue-y-contenedores-docker)
14. [Tests](#14-tests)

---

## 1. Arquitectura General

El sistema está compuesto por **8 contenedores Docker** interconectados:

| Servicio | Puerto | Tecnología | Propósito |
|----------|--------|------------|-----------|
| `postgres` | 5432 | PostgreSQL 16 | Base de datos relacional |
| `qdrant` | 6333 | Qdrant 1.9 | Base de datos vectorial (embeddings) |
| `redis` | 6379 | Redis 7 | Caché y broker |
| `agent-api` | 8000 | FastAPI + LangGraph | 10 agentes autónomos de IA |
| `web3-backend` | 8001 | FastAPI + Web3.py | Integración blockchain |
| `frontend-citizen` | 3000 | Next.js 14 | Portal ciudadano |
| `frontend-police` | 3001 | Next.js 14 | Dashboard policial |
| `dapp` | 3002 | React + Vite | DApp Web3 descentralizada |

Red blockchain: **zkSYS Tanenbaum Testnet** (Chain ID 57057, RPC: `https://rpc-zk.tanenbaum.io`)

---

## 2. Subsistema de Agentes Autónomos (LangGraph)

### 2.1 Flujo del Grafo

El sistema implementa un **grafo de estado (StateGraph)** con 10 nodos que se ejecutan secuencialmente para procesar cada denuncia:

```
Denuncia → intake → [ocr | speech | nlp] → correlation → cluster → osint → risk → [seal → alert → respond | respond] → TRJ-XXXX
```

### 2.2 Nodos del Grafo

| # | Nodo | Agente | Propósito |
|---|------|--------|-----------|
| 1 | `intake` | Intake Agent | Valida y clasifica la denuncia entrante. Determina si es extorsión, extrae entidades iniciales, asigna prioridad. Si la denuncia no es válida, salta a `respond` |
| 2 | `ocr` | OCR Agent | Procesa imágenes/documentos con Tesseract OCR (idioma `spa`). Extrae texto y lo pasa al LLM para estructuración forense |
| 3 | `speech` | Speech Agent | Transcribe audios con Groq Whisper (`whisper-large-v3-turbo`). Analiza emociones e indicadores de amenaza |
| 4 | `nlp` | NLP Agent | Analiza el texto completo (raw + OCR + Speech) para extraer intención, sentimiento, entidades, palabras clave y score de amenaza |
| 5 | `correlation` | Correlation Agent | Busca casos similares en Qdrant usando embeddings. Detecta patrones y redes criminales |
| 6 | `cluster` | Cluster/NER Agent | Ejecuta el motor NER forense (regex + ontología) para extraer entidades criminales: cuentas bancarias, teléfonos, montos, plazos, topónimos, jerga intimidatoria, métodos de violencia |
| 7 | `osint` | OSINT Agent | Enriquece con inteligencia de fuentes abiertas: reportes previos de teléfonos, redes sociales, cuentas bancarias |
| 8 | `risk` | Risk Agent | Consolida todos los resultados previos y calcula nivel de riesgo: BAJO, MEDIO, ALTO, CRÍTICO |
| 9 | `seal` | Seal Agent | Si riesgo es ALTO/CRÍTICO, sella el hash SHA-256 de la evidencia en blockchain (zkSYS Tanenbaum) |
| 10 | `alert` | Alert Agent | Si riesgo es ALTO/CRÍTICO, genera alerta oficial, hace push SSE al dashboard, envía notificaciones webhook/email |
| 11 | `respond` | Respond Agent | Genera código de seguimiento `TRJ-XXXX`, prepara mensaje para el ciudadano |

### 2.3 Routing Condicional

- **Post-intake:** Si la denuncia es inválida → `end` (se archiva). Si tiene imagen/documento → `ocr`. Si tiene audio/video → `speech`. Si es texto puro → `nlp`
- **Post-risk:** Si riesgo es ALTO/CRÍTICO → `seal → alert → respond`. Si es BAJO/MEDIO → `respond` directo
- **Errores:** Si se acumulan 3+ errores, el grafo termina y la denuncia pasa a estado `error_procesamiento`

### 2.4 Mock LLM para Tests

El sistema incluye `MockLLM` (activado con `MOCK_LLM=true` o sin `GROQ_API_KEY`), que devuelve respuestas JSON deterministas predefinidas para cada agente sin consumir tokens de GroqCloud. Útil para CI/CD y desarrollo offline.

### 2.5 LLM Real

Cuando `GROQ_API_KEY` está configurada, usa `ChatGroq` con modelo `llama-3.3-70b-versatile` (temperatura 0.2, max tokens 4096).

### 2.6 Herramientas (LangChain Tools)

| Tool | Nombre | Propósito |
|------|--------|-----------|
| `GuardarResultadoTool` | `guardar_resultado_db` | Persiste resultado de agente en PostgreSQL |
| `BuscarSimilaresTool` | `buscar_casos_similares` | Búsqueda semántica en Qdrant |
| `OCRTool` | `extraer_texto_ocr` | OCR con Tesseract |
| `TranscribirAudioTool` | `transcribir_audio` | STT con Groq Whisper |
| `OSINTLookupTool` | `consultar_osint` | Consulta OSINT externa |
| `EmitirAlertaTool` | `emitir_alerta` | Emite alerta oficial |
| `ConsultarDenunciaTool` | `consultar_denuncia_db` | Consulta denuncia existente |

---

## 3. API REST — Agent System (Puerto 8000)

### 3.1 Health

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check del sistema. Retorna estado de API, PostgreSQL, Qdrant, Groq, LangGraph |

### 3.2 Denuncias

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/v1/denuncias` | No | Crea una denuncia nueva y dispara el grafo LangGraph en background. Devuelve `201 Created` |
| `POST` | `/v1/denuncias/{id}/procesar` | No | Ejecuta el grafo de forma síncrona. Soporta modo `completo` o `selectivo` (lista de agentes) |
| `GET` | `/v1/denuncias` | JWT | Lista denuncias con filtros: `estado`, `canal`, `did_denunciante`, `limit`, `offset` |
| `GET` | `/v1/denuncias/{id}` | JWT | Obtiene detalle de una denuncia con todos los resultados de agentes |
| `GET` | `/v1/denuncias/tracking/{codigo}` | No | Busca denuncia por código TRJ-XXXX (público, para ciudadanos) |
| `GET` | `/v1/denuncias/{id}/resultados` | No | Obtiene resultados de agentes para una denuncia, opcionalmente filtrado por agente |
| `POST` | `/v1/denuncias/{id}/adjuntar` | No | Adjunta archivo de evidencia (multipart). Valida MIME, calcula SHA-256, elimina EXIF, límite 50MB |
| `GET` | `/v1/denuncias/{id}/archivo` | No | Descarga archivo de evidencia (index=0 principal, index>0 adicionales) |
| `GET` | `/v1/denuncias/{id}/archivos` | No | Lista todos los archivos adjuntos a una denuncia |
| `GET` | `/v1/denuncias/{id}/alertas` | No | Lista alertas generadas para una denuncia específica |

### 3.3 Alertas

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/alertas` | JWT | Lista todas las alertas con filtros: `nivel`, `leida`, `limit` |
| `PATCH` | `/v1/alertas/{id}` | JWT | Actualiza alerta: marcarla como leída/atendida, añadir mensaje de resolución, cambiar estado de denuncia relacionada |

### 3.4 Dashboard

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/dashboard/metricas` | JWT | Métricas agregadas: total denuncias, denuncias hoy, alertas críticas, casos resueltos, evidencias registradas |
| `POST` | `/v1/dashboard/push` | No | Endpoint interno para SSE push de agentes al dashboard |

### 3.5 Búsqueda Semántica

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/busqueda/semantica` | No | Búsqueda por lenguaje natural en Qdrant. Parámetros: `q` (query), `limit`, `excluir_denuncia_id` |

### 3.6 Grafos Criminales

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/grafos/criminal` | No | Retorna nodos (clústeres + denuncias) y aristas para visualización de red criminal |

### 3.7 Clústeres

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/clusters` | JWT | Lista clústeres con filtros: `estado`, `zona`, `nivel_alerta` |
| `GET` | `/v1/clusters/{id}` | JWT | Perfil completo de un clúster (banda criminal) |
| `GET` | `/v1/clusters/{id}/denuncias` | JWT | Denuncias anónimas asociadas a un clúster |
| `POST` | `/v1/clusters/recalculate` | JWT | Fuerza recálculo completo de todos los clústeres |

### 3.8 Mapa de Calor (Heatmap)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/v1/heatmap/cuadrantes` | JWT | GeoJSON del Plan Cuadrante PNP La Libertad |
| `GET` | `/v1/heatmap` | JWT | Puntos de calor + polígonos con métricas agregadas por período |

### 3.9 Autenticación

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/v1/auth/login` | No | Login con username/password, retorna JWT + rol |
| `GET` | `/v1/auth/me` | JWT | Información del usuario autenticado |
| `GET` | `/v1/auth/users` | Admin | Lista todos los usuarios |
| `POST` | `/v1/auth/users` | Admin | Crea nuevo usuario |
| `PUT` | `/v1/auth/users/{username}` | Admin | Actualiza usuario existente |
| `DELETE` | `/v1/auth/users/{username}` | Admin | Elimina usuario |

### 3.10 Canales (Webhook)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/v1/channels/whatsapp/webhook` | No | Webhook entrante de Whapi.cloud para recibir mensajes de WhatsApp |

---

## 4. API REST — Web3 Backend (Puerto 8001)

### 4.1 Health

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check con estado de conexión blockchain, bloque actual, dirección del backend |

### 4.2 Evidencias

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/v1/evidencias` | Registra evidencia: recibe archivo, sube a IPFS, calcula SHA-256, registra en EvidenceRegistry |
| `POST` | `/v1/evidencias/seal` | Sella hash de evidencia en blockchain (usado por Seal Agent). Acepta JSON `content_hash` + `case_id` |
| `GET` | `/v1/evidencias/{hash}/verificar` | Verifica si un hash SHA-256 ya fue sellado en blockchain |
| `POST` | `/v1/evidencias/verify` | Verifica integridad de evidencia comparando hash on-chain vs archivo subido |
| `GET` | `/v1/evidencias/{id}/custodia` | Historial de cadena de custodia de una evidencia |
| `POST` | `/v1/evidencias/{id}/transferir` | Transfiere custodia a otra dirección |
| `POST` | `/v1/evidencias/revocar` | Revoca una evidencia (soft-delete) |
| `GET` | `/v1/evidencias/{id}/acta-pdf` | Descarga Acta Forense en PDF |
| `POST` | `/v1/evidencias/{id}/acta-firmada` | Genera Acta PDF, la firma digitalmente (ECDSA P-256), sella el hash del acta en blockchain |

### 4.3 Casos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/v1/casos` | Crea un nuevo caso en CaseManager |
| `POST` | `/v1/casos/vincular` | Vincula evidencia a un caso |
| `GET` | `/v1/casos/{id}` | Obtiene detalle de un caso |
| `POST` | `/v1/casos/{id}/asignar` | Asigna oficial a un caso |
| `POST` | `/v1/casos/{id}/estado` | Cambia estado de un caso (ABIERTO, EN_INVESTIGACION, EVIDENCIA_COMPLETA, RESUELTO, ARCHIVADO) |

### 4.4 DID (Identidad Descentralizada)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/v1/did/{did}` | Resuelve un DID a su documento |
| `GET` | `/v1/did/credential/{hash}/verify` | Verifica una credencial verificable |

### 4.5 Token (NFT Soulbound)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/v1/token/{address}/balance` | Obtiene balance de tokens de una dirección |
| `POST` | `/v1/token/mint` | Mintea un token NFT Soulbound asociado a una evidencia |

### 4.6 Administración / Auditoría

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/v1/admin/seal-audit-log` | Sella manualmente el log de auditoría diario en blockchain |
| `POST` | `/v1/admin/audit/log` | Registra evento en log de auditoría |
| `GET` | `/v1/admin/audit/logs` | Lista eventos pendientes y sellados |

---

## 5. Base de Datos PostgreSQL

### 5.1 Tablas

| Tabla | Propósito | Columnas principales |
|-------|-----------|---------------------|
| `denuncias` | Registro principal de denuncias | `id` (UUID), `canal`, `tipo_contenido`, `contenido_raw`, `url_archivo`, `hash_archivo`, `metadata_json` (JSONB), `nlp_entities_json` (JSONB), `zona_detectada`, `tracking_code`, `seal_tx_hash`, `seal_block`, `seal_status`, `nivel_riesgo` (enum), `estado` (enum), `cluster_id` (FK), `created_at`, `procesado_at` |
| `resultados_agentes` | Resultados de cada agente por denuncia | `id`, `denuncia_id` (FK), `agente`, `resultado_json` (JSONB), `exitoso`, `created_at` |
| `alertas` | Alertas generadas | `id` (UUID), `denuncia_id` (FK), `nivel` (enum), `titulo`, `descripcion`, `recomendacion`, `zona`, `tx_hash`, `leida`, `atendida`, `metadata_json` (JSONB), `created_at` |
| `clusters` | Clústeres (bandas criminales) | `id`, `codigo` (CLU-XXXX), `zona_principal`, `estado` (enum), `nivel_alerta` (enum), `total_denuncias`, `monto_min/max`, `cuentas_detectadas` (JSONB), `jerga_frecuente` (JSONB), `metodos_violencia` (JSONB), `telefonos_detectados` (JSONB) |
| `denuncia_cluster` | Relación M:N denuncia ↔ clúster | `denuncia_id` (FK), `cluster_id` (FK), `score_vinculo`, `vectores_comunes` (JSONB) |
| `usuarios` | Usuarios del dashboard policial | `id` (UUID), `username` (único), `hashed_password`, `nombre_completo`, `rol` (enum: admin/supervisor/analista), `activo` |
| `memoria_conversacional` | Memoria híbrida para agentes | `session_id`, `role`, `content`, `tool_calls` (JSONB) |

### 5.2 Estados de Denuncia

`en_ingesta` → `en_analisis` → `procesado` → `correlacionado` → `riesgo_evaluado` → `alerta_generada` → `en_seguimiento_policial` / `archivado` / `error_procesamiento`

### 5.3 Niveles de Riesgo

`bajo`, `medio`, `alto`, `critico`

### 5.4 Estados de Clúster

`activo`, `inactivo`, `resuelto`

### 5.5 Roles de Usuario

`analista`, `supervisor`, `admin`

---

## 6. Smart Contracts (zkSYS Tanenbaum Testnet)

### 6.1 EvidenceRegistry (`0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb`)

**Propósito:** Registro de cadena de custodia de evidencias digitales.

**Roles:** `REGISTRAR_ROLE`, `AUDITOR_ROLE`, `FORENSIC_ROLE`

**Funciones:**
- `storeEvidence(hash, ipfsCID, didDenunciante, tipoEvidencia, metadataURI)` — Registra nueva evidencia
- `transferCustody(evidenceId, newCustodian, motivo)` — Transfiere custodia
- `linkToCase(evidenceId, caseId)` — Vincula evidencia a caso
- `revokeEvidence(evidenceId, motivo)` — Revoca evidencia
- `verifyEvidence(evidenceId, providedHash)` — Verifica integridad
- `getCustodyHistory(evidenceId)` — Historial de custodia
- `evidenceExists(evidenceId)` — Verifica existencia

**Eventos:** `EvidenceStored`, `CustodyTransferred`, `EvidenceRevoked`, `EvidenceLinkedToCase`

### 6.2 EvidenceSeal (zkSYS Tanenbaum)

**Propósito:** Sellado criptográfico secundario para actas/PDFs.

**Roles:** `SEALER_ROLE`

**Funciones:**
- `seal(evidenceId, sealHash, originalEvidenceHash, metadataURI)` — Sella evidencia
- `verifySeal(sealId, providedSealHash, providedEvidenceHash)` — Verifica sello
- `getSeal(sealId)` — Obtiene sello
- `revokeSeal(sealId, motivo)` — Revoca sello
- `getSealByEvidenceId(evidenceId)` — Obtiene sello por ID de evidencia

**Eventos:** `EvidenceSealed`, `SealRevoked`

### 6.3 CaseManager (`0x3576cb05B2c4094e8f97639892D235044d7476a1`)

**Propósito:** Gestión del ciclo de vida de casos de investigación.

**Roles:** `FISCAL_ROLE`, `POLICE_ROLE`

**Estados:** `ABIERTO`, `EN_INVESTIGACION`, `EVIDENCIA_COMPLETA`, `RESUELTO`, `ARCHIVADO`

**Funciones:**
- `createCase(didDenunciante, nivelRiesgo, resumen, metadataURI)` — Crea caso
- `asignarOficial(caseId, oficial)` — Asigna oficial
- `cambiarEstado(caseId, nuevoEstado, motivo)` — Cambia estado
- `vincularEvidencia(caseId, evidenceId)` — Vincula evidencia
- `getEvidencias(caseId)` — Lista evidencias del caso

**Eventos:** `CasoCreado`, `EstadoCambiado`, `OficialAsignado`, `EvidenciaVinculada`

### 6.4 DIDRegistry (`0x8481c85e54f50C676f0fc37f90848030c3B12bB9`)

**Propósito:** Identidad descentralizada con reputación.

**Roles:** `ISSUER_ROLE`, `VERIFIER_ROLE`

**Funciones:**
- `registerDID(did, controller, publicKeyHex, documentURI, metadata)` — Registra DID
- `updateDIDDocument(did, newDocumentURI, newMetadata)` — Actualiza documento DID
- `deactivateDID(did)` — Desactiva DID
- `issueCredential(credentialHash, issuerDID, subjectDID, credentialType, expiresAt, metadataURI)` — Emite credencial verificable
- `revokeCredential(credentialHash)` — Revoca credencial
- `updateReputation(did, newScore)` — Actualiza reputación (0-10000)
- `verifyCredential(credentialHash)` — Verifica credencial

**Eventos:** `DIDRegistered`, `CredentialIssued`, `ReputationUpdated`

### 6.5 IntelExtorsionToken (IEEV) (`0x622AA147eD0238840ceb215941D5E8CD997896F0`)

**Propósito:** NFT Soulbound (no transferible) por evidencia registrada.

**Roles:** `MINTER_ROLE`, `BURNER_ROLE`

**Funciones:**
- `mintEvidenceToken(to, evidenceId, evidenceHash, ipfsURI)` — Mintea NFT
- `burnEvidenceToken(tokenId)` — Quema token
- `getTokenByEvidenceId(evidenceId)` — Resuelve evidence ID a token ID
- `totalMinted()` — Total minteado

**Eventos:** `EvidenceMinted`, `EvidenceBurned`

---

## 7. Frontend Ciudadano (Puerto 3000)

### 7.1 Páginas

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/` | Landing | Página principal con información del proyecto, propósito (inteligencia ciudadana, NO denuncia formal), features (3 cards), CTA |
| `/portal` | Portal Ciudadano | Formulario de denuncia anónima con campos: tipo de contenido, descripción, adjuntar archivos (imagen, audio, documento) |
| `/tracking` | Seguimiento | Consulta de estado de denuncia mediante código TRJ-XXXX |

### 7.2 Características

- **Bilingüe:** Español / Inglés (selector de idioma)
- **Conexión Web3:** Integración con Pali Wallet (zkSYS Tanenbaum) para DID opcional
- **Tabs:** DID, KPIs, Evidencias, Chat (split layout), Ayuda
- **Sidebar y Header** con diseño responsivo
- **Toast notifications** para feedback al usuario
- **Adjuntar evidencias:** Botones de Paperclip, Image y Mic con inputs file ocultos y preview

### 7.3 Flujo Ciudadano

1. Ciudadano accede al portal
2. Completa formulario de denuncia (texto + adjuntos opcionales)
3. Envía → recibe código `TRJ-XXXX`
4. Puede consultar estado del análisis con ese código
5. Recibe mensaje legible del estado (RF-04) y hash de verificación SHA-256

---

## 8. Frontend Policial (Puerto 3001)

### 8.1 Páginas

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/` | Login | Autenticación JWT con username/password |
| `/dashboard/policial` | Dashboard | Métricas: total denuncias, denuncias hoy, alertas críticas, evidencias registradas |
| `/dashboard/analitico` | Analítico | Dashboard analítico con datos agregados |
| `/dashboard/grafos` | Grafos Criminales | Visualización de redes criminales (grafo de nodos y aristas) |
| `/dashboard/alertas` | Centro de Alertas | Lista de alertas generadas, filtros, marcar como leída/atendida |
| `/dashboard/usuarios` | Gestión de Usuarios | CRUD de usuarios (solo admin) |

### 8.2 Características

- **Autenticación JWT:** Token almacenado en `localStorage.police_token`, inyectado automáticamente en cada request
- **Roles:** admin, supervisor, analista (RBAC)
- **Usuarios seed:** `admin`/`Admin123!`, `supervisor`/`Super123!`, `analista`/`Analista123!`
- **Logout:** Revoca permisos y limpia token
- **Sidebar** con navegación a todas las secciones

---

## 9. DApp Web3 (Puerto 3002)

### 9.1 Componentes

| Componente | Propósito |
|------------|-----------|
| `WalletConnect.jsx` | Conexión con Pali Wallet (zkSYS Tanenbaum). Forza selección de cuenta con `wallet_requestPermissions`, desconecta con `wallet_revokePermissions` |
| `DIDRegister.jsx` | Registro de DID descentralizado en DIDRegistry |
| `DIDResolver.jsx` | Resolución de DID a documento, verificación de credenciales |
| `EvidenceUploader.jsx` | Subida y sellado de evidencias en blockchain (EvidenceSeal) |
| `EvidenceVerifier.jsx` | Verificación de integridad de evidencia on-chain |
| `ForensicReport.jsx` | Generación y descarga de Acta Forense PDF firmada digitalmente |
| `ChannelConnect.jsx` | Conexión de canales (WhatsApp, Telegram, Discord) |

### 9.2 Servicios

| Archivo | Propósito |
|---------|-----------|
| `usePaliWallet.js` | Hook de conexión a Pali Wallet con configuración de red zkSYS Tanenbaum |
| `contractService.js` | Interacción con todos los contratos: EvidenceRegistry, CaseManager, DIDRegistry, Token, EvidenceSeal |

---

## 10. Bots de Canales de Comunicación

### 10.1 WhatsApp (Whapi.cloud)

**Archivo:** `app/channels/whatsapp_bot.py`

**Características:**
- Pasarela Whapi.cloud para enviar/recibir mensajes de WhatsApp
- **Menú de clasificación RF-01:** Al iniciar, pregunta si la amenaza proviene de Particular/Banda criminal o Funcionario público/Policía
- **State machine:** Estados `idle → classifying → waiting_content → processing`
- **Batching temporal:** Agrupa múltiples imágenes/audios enviados en una ventana de 3 segundos como una sola denuncia
- **Transcripción de audios:** Usa Groq Whisper para transcribir notas de voz automáticamente
- **Soporte multi-formato:** Imágenes, audios, videos, documentos
- **Tracking:** Permite consultar estado de denuncia existente con código TRJ-XXXX
- **Privacidad:** Elimina PII (identificadores personales) de `metadata_json` antes de persistir
- **RF-03:** Pregunta opcional de zona geográfica después del registro

**Filtros de seguridad:**
- Ignora mensajes salientes (`from_me = True`) para evitar bucles
- Ignora mensajes de grupos (`@g.us`)
- Ignora stickers, acciones y tipos no soportados

### 10.2 Telegram

**Archivo:** `app/channels/telegram_bot.py`

**Características:**
- Polling-based (no webhook)
- Procesamiento asíncrono de mensajes
- Soporte multi-archivo con batching y timeout
- Flujo: bienvenida → recepción de reporte → procesamiento con LangGraph

### 10.3 Discord

**Archivo:** `app/channels/discord_bot.py`

**Características:**
- Cliente discord.py con intents completos
- Mensajes con embeds estilizados
- Mensaje de bienvenida automático para nuevos miembros

---

## 11. Servicios del Sistema

### 11.1 Motor NER Forense (`app/nlp/ner_engine.py`)

Extrae 10 tipos de entidades criminales usando regex + ontología bootstrap (sin ML):

1. **CUENTA_BANCARIA:** Números de 14-20 dígitos, detecta banco por contexto
2. **YAPE_PLIN:** Números de teléfono asociados a Yape o Plin
3. **TELEFONO_EXTORSIVO:** Formato +51 9xxxxxxxx, 9xxxxxxxx, 01xxxxxxx
4. **MONTO:** Soles (S/ o "soles") con periodicidad
5. **PLAZO:** Horas, días, semanas, meses para pago
6. **TOPONIMO_TRUJILLO:** Zonas/distritos de La Libertad
7. **JERGA_INTIMIDACION:** Términos de jerga extorsiva
8. **METODO_VIOLENCIA:** Métodos de violencia/extorsión
9. **FRECUENCIA_PAGO:** Diario, semanal, mensual
10. **MEDIO_COMUNICACION:** WhatsApp, Telegram, llamada, carta, etc.

### 11.2 Motor de Clustering (`app/nlp/clustering.py`)

**Basado en NetworkX.** Detecta bandas criminales conectando denuncias por vectores compartidos:

- **Umbral mínimo:** 3 denuncias, 2 vectores compartidos
- **Vectores de similitud:**
  - Cuentas bancarias/Yape compartidas (+2)
  - Teléfonos compartidos (+2)
  - Similitud de embeddings coseno > 0.85 (+1)
  - Misma zona + fecha cercana ≤21 días (+1)
  - Montos similares ±20% (+1)
  - Mismo método de violencia (+1)
  - Misma jerga intimidatoria (+1)
- **Perfil de banda:** Zona principal, montos min/max, cuentas, teléfonos, jerga, métodos, tendencia (creciente/decreciente/estable), nivel de alerta

### 11.3 Ontología Forense (`app/nlp/ontology.py`)

Diccionario de aproximadamente 40 entidades incluyendo:
- **Jerga extorsiva:** `"caele", "chapa", "mueve", "arreglo", "cuota", "vacuna", "derecho de piso"`, etc.
- **Métodos de violencia:** `"secuestro", "amenaza de muerte", "atentado", "sicariato"`, etc.
- **Bancos peruanos:** BCP, BBVA, Interbank, Scotiabank, etc.
- **Topónimos de La Libertad:** Trujillo, Florencia de Mora, El Porvenir, La Esperanza, Víctor Larco, Huanchaco, Moche, Salaverry, Laredo

### 11.4 Servicio OCR (`app/services/ocr_service.py`)

- **Motor:** Tesseract OCR (`pytesseract`)
- **Idioma:** Español (`spa`)
- **Confianza:** Calcula confidence scoring con `image_to_data()`
- **Soporta:** JPEG, PNG, WebP, PDF

### 11.5 Servicio STT (`app/services/stt_service.py`)

- **Motor:** Groq Whisper (`whisper-large-v3-turbo`)
- **Idioma:** Español (`es`)
- **Formatos:** MP3, OGG, WAV
- **Límite:** 25MB por archivo, 25 req/min (tier gratuito)

### 11.6 Servicio de Archivos (`app/services/file_service.py`)

- **Validación MIME:** JPEG, PNG, WebP, PDF, MP3, OGG, WAV, MP4, TXT
- **Límite:** 50MB por archivo
- **Hash:** SHA-256 automático
- **Privacidad RF-06:** Elimina metadatos EXIF/ICC/XMP de imágenes (GPS, serial, dispositivo)
- **Almacenamiento:** `/app/uploads/evidencias/`
- **Descarga remota:** `download_from_url()` con soporte HTTP

### 11.7 Cliente Web3 (`app/services/web3_client.py`)

Cliente HTTP asíncrono para comunicación entre Agent System y Web3 Backend:
- `seal_evidence(content_hash, case_id)` — Sella evidencia
- `verify_evidence(content_hash)` — Verifica hash
- `compute_content_hash(text, metadata)` — Calcula SHA-256 como `0x...`

### 11.8 Servicio de Notificaciones (`app/services/notification_service.py`)

Dispara alertas push multicanal cuando se genera una alerta oficial:
- **Webhook HTTP:** POST a URL configurable con payload JSON
- **Email SMTP:** Envío de email HTML a destinatarios configurados (TLS opcional)
- **Nunca falla:** Si las notificaciones fallan, el flujo principal continúa

### 11.9 Servicio de Acta Forense (`web3_backend/app/services/acta_service.py`)

- **PDF:** Genera "Acta de Preservación de Evidencia Digital" en formato A4 con datos on-chain
- **Firma digital:** ECDSA secp256k1 (Ethereum), opcionalmente X.509 y ECDSA P-256
- **Sellado:** El hash del acta se sella en blockchain (EvidenceSeal)
- **Legal:** Compatible con CPP peruano art. 158-B

### 11.10 Servicio de Auditoría (`web3_backend/app/services/audit_seal_service.py`)

- **Buffer en memoria** de eventos de auditoría
- **Sellado diario automático** (cron midnight vía APScheduler)
- **Endpoint manual** para sellado on-demand

### 11.11 Servicio Web3 (`web3_backend/app/services/web3_service.py`)

Singleton que maneja toda la interacción con blockchain:
- Carga dinámica de ABIs desde archivos JSON compilados
- Cache de instancias de contrato
- Envío de transacciones con firma EIP-1559 (gas dinámico)
- **Dev mode:** Si detecta `0x0000...` como address de contrato, responde simuladamente sin transacción real
- Pool de conexiones a RPC

### 11.12 Memoria Híbrida (`app/memory/hybrid_memory.py`)

- **Embeddings:** FastEmbedLocal con modelo `sentence-transformers/all-MiniLM-L6-v2` (384 dims, local, sin API key)
- **Vector DB:** Qdrant (colección `denuncias_embeddings_v2`)
- **Memoria a corto plazo:** PostgreSQL (`memoria_conversacional`)
- **Memoria a largo plazo:** Qdrant para búsqueda semántica de casos similares

---

## 12. Autenticación y Seguridad

### 12.1 JWT

- **Algoritmo:** HS256
- **Expiración:** 480 minutos (8 horas)
- **Claims:** `sub` (username), `rol` (admin/supervisor/analista)
- **Dependencias:** `python-jose[cryptography]`, `passlib[bcrypt]`

### 12.2 Roles (RBAC)

| Rol | Permisos |
|-----|----------|
| `admin` | CRUD de usuarios, acceso total a métricas y alertas |
| `supervisor` | Lectura de denuncias, alertas, clusters |
| `analista` | Lectura de denuncias y resultados |

### 12.3 Privacidad (RF)

| RF | Descripción |
|----|-------------|
| RF-01 | Menú de clasificación en bots: Particular vs Funcionario público |
| RF-04 | Mensajes legibles para el ciudadano al consultar tracking code |
| RF-06 | Eliminación de metadatos EXIF de imágenes subidas |

### 12.4 Seguridad

- **CORS:** Configurable vía `CORS_ALLOWED_ORIGINS` o `CORS_ALLOW_ALL`
- **Contraseñas:** Hasheadas con bcrypt
- **Usuarios seed:** Passwords configurables vía `SEED_ADMIN_PASSWORD`, `SEED_SUPERVISOR_PASSWORD`, `SEED_ANALISTA_PASSWORD`
- **Canales:** Filtros anti-bucle (ignorar mensajes salientes) y anti-spam (ignorar grupos)

---

## 13. Despliegue y Contenedores Docker

### 13.1 Servicios Docker

| Servicio | Imagen Base | Puerto | Dependencias |
|----------|-------------|--------|-------------|
| `postgres` | `postgres:16-alpine` | 5432 | - |
| `qdrant` | `qdrant/qdrant:v1.9.1` | 6333 | - |
| `redis` | `redis:7-alpine` | 6379 | - |
| `agent-api` | `python:3.11-slim` (build) | 8000 | postgres, qdrant, redis |
| `web3-backend` | `python:3.11-slim` (build) | 8001 | postgres |
| `frontend-citizen` | `node:20-alpine` (multi-stage) | 3000 | agent-api |
| `frontend-police` | `node:20-alpine` (multi-stage) | 3001 | agent-api |
| `dapp` | `nginx:alpine` (multi-stage) | 3002 | web3-backend |

### 13.2 Variables de Entorno Clave

```bash
# GROQ (obligatorio para procesamiento real)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# PostgreSQL
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=agent_pass
POSTGRES_DB=intel_extorsion

# Blockchain (zkSYS Tanenbaum)
WEB3_PROVIDER_URL=https://rpc-zk.tanenbaum.io
CHAIN_ID=57057
PRIVATE_KEY=0x...
CONTRACT_EVIDENCE_REGISTRY=0x1A9eB1a4C261AE793e21101a3E5c14003dcF4dEb
CONTRACT_CASE_MANAGER=0x3576cb05B2c4094e8f97639892D235044d7476a1
CONTRACT_DID_REGISTRY=0x8481c85e54f50C676f0fc37f90848030c3B12bB9
CONTRACT_TOKEN=0x622AA147eD0238840ceb215941D5E8CD997896F0

# Canales (opcional)
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
WHATSAPP_API_TOKEN=...

# Notificaciones (opcional)
ALERT_WEBHOOK_URL=...
ALERT_EMAIL_SMTP_HOST=...
```

### 13.3 URL de Acceso (Local)

```
Frontend Ciudadano:     http://localhost:3000
Frontend Policial:      http://localhost:3001
DApp Web3:              http://localhost:3002
Agent API Docs:         http://localhost:8000/docs
Web3 API Docs:          http://localhost:8001/docs
Qdrant Dashboard:       http://localhost:6333/dashboard
```

### 13.4 Comandos Rápidos

```bash
# Levantar todo
docker compose up -d

# Tests de integración
docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit

# Ver logs
docker compose logs -f agent-api
```

---

## 14. Tests

### 14.1 Tests de Integración (10 tests, 10/10 pasan)

Todos los tests se ejecutan con `MOCK_LLM=true` para no consumir tokens de Groq:

| # | Test | Descripción |
|---|------|-------------|
| 1 | `test_health_agent_api` | Verifica `/health` del Agent API |
| 2 | `test_health_web3_backend` | Verifica `/health` del Web3 Backend |
| 3 | `test_crear_denuncia_texto` | Crea denuncia de texto, verifica 201 |
| 4 | `test_procesar_denuncia_y_generar_tracking` | Procesa denuncia, verifica código TRJ- |
| 5 | `test_tracking_por_codigo` | Busca denuncia por tracking code |
| 6 | `test_dashboard_metricas` | Obtiene métricas autenticado |
| 7 | `test_listar_denuncias` | Lista denuncias autenticado |
| 8 | `test_listar_alertas` | Lista alertas autenticado |
| 9 | `test_web3_registrar_y_verificar_evidencia` | Sube archivo y verifica en Web3 |
| 10 | `test_busqueda_semantica` | Búsqueda semántica en Qdrant |

### 14.2 Tests de Smart Contracts

- Ubicación: `intel_extorsion_web3_system/test/test.js`
- Framework: Hardhat
- Ejecución: `npx hardhat test`

---

## Apéndice: Flujo Completo de una Denuncia

1. **Ingreso:** Ciudadano envía reporte por web, WhatsApp, Telegram o Discord
2. **Intake Agent:** Valida que sea una denuncia de extorsión válida
3. **OCR/Speech:** Si hay imágenes o audios, se procesan con Tesseract/Groq Whisper
4. **NLP Agent:** Analiza el texto completo, extrae intención, entidades, score de amenaza
5. **Correlation Agent:** Busca casos similares en Qdrant (embeddings)
6. **Cluster Agent:** Ejecuta NER forense (10 tipos de entidades), detecta zona geográfica
7. **OSINT Agent:** Enriquece con fuentes abiertas (simulado)
8. **Risk Agent:** Calcula nivel de riesgo consolidado
9. **Si es ALTO/CRÍTICO:**
   - **Seal Agent:** Sella hash SHA-256 de la evidencia en zkSYS Tanenbaum
   - **Alert Agent:** Genera alerta, notifica por webhook/email, push SSE al dashboard
10. **Respond Agent:** Genera código TRJ-XXXX y mensaje para el ciudadano
11. **Persistencia:** Resultados guardados en PostgreSQL, embedding en Qdrant, asignación a clúster (NetworkX)
12. **Seguimiento:** Ciudadano consulta con TRJ-XXXX; Policía ve en dashboard; Alertas en centro de alertas

---

*Documento generado el 2026-07-01. Sistema IntelExtorsión v1.0.0*
