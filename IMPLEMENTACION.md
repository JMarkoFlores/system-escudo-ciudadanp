# Plan de Implementación — IntelExtorsión

## Plataforma de Inteligencia Policial para Denuncias de Extorsión

---

## 1. Objetivo del Plan de Implementación

Completar el desarrollo de IntelExtorsión desde su estado actual (arquitectura base funcional: Docker Compose operativo, 6/9 tests pasando, frontend Next.js en build, agentes LangGraph + GroqCloud procesando, embeddings locales con fastembed) hasta un sistema completo, integrado y demostrable que cubra: recepción multicanal de denuncias, análisis con agentes autónomos, sellado blockchain en zkSYS Genesis Testnet, clustering forense e inteligencia para el dashboard DIVINCRI.

El plan organiza 6 fases (0–5) distribuidas entre 5 personas del equipo, detallando objetivos, componentes, entregables y criterios de aceptación de cada fase.

---

## 2. Equipo de Trabajo

| Persona | Rol | Stack principal | Fases principales |
|---------|-----|----------------|-------------------|
| **P1** | Líder técnico / Agentes IA | Python · LangGraph · FastAPI · GroqCloud | Fase 0, Fase 1 |
| **P2** | Blockchain / Smart Contracts | Solidity · Hardhat · Web3.py · zkSYS | Fase 2 |
| **P3** | Frontend / DApp | Next.js · TypeScript · Tailwind · ethers.js | Fase 3 |
| **P4** | Canales externos / Bot | Python · Twilio/360dialog · Telegram · Discord | Fase 4 |
| **P5** | Backend / Infraestructura / QA | PostgreSQL · Docker · Redis · pytest | Fase 5 |

---

## 3. Vista General de Fases

| Fase | Nombre | Duración | Dependencias | Responsable principal |
|------|--------|----------|--------------|----------------------|
| 0 | Migración a zkSYS Genesis Testnet | 1–2 días | Ninguna (bloquea todo lo demás) | **P1** |
| 1 | Agente Autónomo End-to-End | 3–4 días | Fase 0 | **P1** |
| 2 | Smart Contracts + Sellado Real | 3–4 días | Fase 0 | **P2** |
| 3 | Canales Externos (Bot) + DApp Pali Wallet | 4–5 días | Fases 1 y 2 | **P3** |
| 4 | NLP Forense + Clustering | 3–4 días | Fase 1 | **P4** |
| 5 | Integración Final + QA + Demo | 2–3 días | Fases 1–4 | **P5** |

**Duración total estimada:** 16–22 días

### Priorización

| Prioridad | Fases | Descripción |
|-----------|-------|-------------|
| **Crítica** | 0 | Bloquea todas las demás fases |
| **Imprescindible** | 1, 2, 3 | Flujo agente + blockchain + canales |
| **Alta** | 4 | Motor de inteligencia y clustering |
| **Crítica (cierre)** | 5 | Integración, QA y demo |

---

## 4. Fases de Implementación

---

### FASE 0 — Migración a zkSYS Genesis Testnet

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P1** — Líder técnico / Agentes IA |
| **Prioridad** | CRÍTICA — Bloquea todas las demás fases |
| **Duración estimada** | 1–2 días |
| **Dependencias** | Ninguna |
| **Riesgo si no se hace** | Todo el sistema sigue apuntando a Rollux Mainnet; los contratos no se pueden desplegar en testnet; la demo no funciona sin fondos reales |

#### 4.0.1 Objetivo

Migrar la configuración de red de Syscoin Rollux Mainnet (Chain ID 570) a zkSYS Genesis Testnet para desarrollo y demo. Actualizar todos los puntos del sistema que referencian la red anterior.

#### 4.0.2 Problema que resuelve

El sistema actual apunta a `WEB3_PROVIDER_URL=https://rpc.rollux.com` y `CHAIN_ID=570` (Rollux Mainnet). En testnet los contratos se pueden desplegar sin fondos reales, las transacciones son gratuitas y el equipo puede demostrar el sellado blockchain sin riesgo económico.

#### 4.0.3 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `.env.example` | `WEB3_PROVIDER_URL`, `CHAIN_ID`, `EXPLORER_URL` |
| `intel_extorsion_web3_system/hardhat.config.js` | Añadir red `zkSYSTestnet` |
| `intel_extorsion_web3_system/backend/app/config.py` | Chain ID y RPC URL |
| `intel_extorsion_frontend/src/lib/web3Config.ts` | Chain config para Pali Wallet |
| `docker-compose.yml` | Variables de entorno de red |

#### 4.0.4 Configuración zkSYS Genesis Testnet

```
WEB3_PROVIDER_URL=https://rpc.genesis.zksys.io
CHAIN_ID=5700
EXPLORER_URL=https://explorer.genesis.zksys.io
NETWORK_NAME=zkSYS Genesis Testnet
FAUCET_URL=https://faucet.genesis.zksys.io
```

```javascript
// hardhat.config.js
networks: {
  zkSYSTestnet: {
    url: process.env.WEB3_PROVIDER_URL,
    chainId: parseInt(process.env.CHAIN_ID),
    accounts: [process.env.PRIVATE_KEY],
    gasPrice: "auto"
  }
}
```

#### 4.0.5 Entregables

- `.env.example` actualizado con zkSYS Genesis Testnet
- `hardhat.config.js` con nueva red configurada
- Confirmación de conectividad: `npx hardhat run scripts/checkNetwork.js --network zkSYSTestnet`
- Wallet institucional con fondos del faucet para despliegue

#### 4.0.6 Estado de implementación

**Implementado:** ✅ Sí — Todos los archivos de configuración actualizados a zkSYS Genesis Testnet. Script `checkNetwork.js` creado para verificar conectividad. Pendiente solicitar fondos del faucet para wallet institucional.

#### 4.0.7 Criterios de aceptación

- [x] `curl $WEB3_PROVIDER_URL` responde con JSON-RPC válido
- [x] `ethers.getNetwork()` devuelve Chain ID 5700
- [x] Web3 Backend arranca sin errores de conexión de red
- [ ] P1 tiene fondos de testnet en la wallet institucional (pendiente faucet)

---

### FASE 1 — Agente Autónomo End-to-End

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P1** — Líder técnico / Agentes IA |
| **Prioridad** | IMPRESCINDIBLE — Alta |
| **Duración estimada** | 3–4 días |
| **Dependencias** | Fase 0 completada |
| **Riesgo si no se hace** | El "agente autónomo" es solo una pipeline de funciones; no hay ciclo de razonamiento real ni integración con blockchain ni con canales externos |

#### 4.1.1 Objetivo

Completar el grafo LangGraph para que el agente autónomo ejecute el ciclo completo de forma encadenada: recibe denuncia → clasifica → extrae entidades NLP → evalúa riesgo → decide si sellar en blockchain → emite alerta → responde al usuario. Actualmente el grafo existe pero los nodos `node_seal` y `node_alert` no tienen conexión real con el Web3 Backend ni con los canales de salida.

#### 4.1.2 Problema que resuelve

El agente llama a `node_seal` pero falla silenciosamente porque los smart contracts no están desplegados. Adicionalmente, `node_alert` genera alertas en PostgreSQL pero no las envía a ningún destino externo.

#### 4.1.3 Arquitectura del grafo LangGraph

**Actual:**
```
intake → classify → extract_entities → assess_risk → [FIN]
```

**Objetivo:**
```
intake → classify → extract_entities → assess_risk
    → [if riesgo ALTO/CRÍTICO] → seal_blockchain → emit_alert → respond
    → [if riesgo BAJO/MEDIO]   → store_case → respond
```

#### 4.1.4 Archivos a crear/modificar

| Componente | Acción |
|------------|--------|
| `intel_extorsion_agent_system/app/core/agent_graph.py` | Modificar — añadir nodos `node_seal` y `node_alert` con llamadas reales |
| `intel_extorsion_agent_system/app/agents/seal_agent.py` | Crear — cliente HTTP al Web3 Backend |
| `intel_extorsion_agent_system/app/agents/alert_agent.py` | Crear — emisión de alertas push al dashboard |
| `intel_extorsion_agent_system/app/agents/respond_agent.py` | Crear — generación de código TRJ-XXXX y respuesta al canal |
| `intel_extorsion_agent_system/app/core/state.py` | Modificar — añadir campos `seal_tx_hash`, `alert_sent`, `tracking_code` |
| `intel_extorsion_agent_system/app/services/web3_client.py` | Crear — cliente HTTP interno para Web3 Backend (puerto 8001) |

#### 4.1.5 Lógica de nodos clave

**SealAgent** — Cuando el riesgo es ALTO o CRÍTICO, llama al Web3 Backend para sellar el hash de la evidencia:

```python
async def node_seal(state: AgentState) -> AgentState:
    if state.nivel_riesgo in ["alto", "critico"]:
        response = await web3_client.seal_evidence(
            content_hash=state.content_hash,
            case_id=state.denuncia_id
        )
        state.seal_tx_hash = response["tx_hash"]
        state.seal_block = response["block_number"]
        state.seal_status = "SELLADA" if response["success"] else "PENDIENTE"
    return state
```

**AlertAgent** — Para riesgo ALTO/CRÍTICO, envía alerta push al dashboard:

```python
async def node_alert(state: AgentState) -> AgentState:
    if state.nivel_riesgo in ["alto", "critico"]:
        await alert_service.push_to_dashboard(
            zona=state.zona_detectada,
            cluster_id=state.cluster_id,
            nivel=state.nivel_riesgo,
            tx_hash=state.seal_tx_hash
        )
        state.alert_sent = True
    return state
```

**RespondAgent** — Genera código de seguimiento único:

```python
def generate_tracking_code() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(4))
    return f"TRJ-{suffix}"
```

#### 4.1.6 Entregables

- Grafo LangGraph con ciclo completo (intake → seal → alert → respond)
- `seal_agent.py` y `alert_agent.py` implementados
- Código de seguimiento TRJ-XXXX generado y almacenado en PostgreSQL
- Test `test_crear_denuncia_y_procesar` pasando (actualmente ❌)
- SSE endpoint en Agent API para push al dashboard

#### 4.1.8 Estado de implementación

**Implementado:** ✅ Sí — Grafo LangGraph extendido con nodos `seal`, `alert` (con SSE push) y `respond` (con TRJ-XXXX). Routing condicional por nivel de riesgo. Cliente HTTP `web3_client.py` para Web3 Backend. Endpoint `GET /v1/denuncias/tracking/{tracking_code}`. Base de datos corregida con campos `tracking_code`, `seal_tx_hash`, `seal_block`, `seal_status`.

#### 4.1.9 Criterios de aceptación

- [x] Denuncia de texto libre recibida → procesada por 10 agentes → responde con TRJ-XXXX
- [ ] Denuncia con riesgo ALTO → `seal_tx_hash` no nulo en PostgreSQL (depende de Fase 2)
- [x] Dashboard policial recibe alerta push vía endpoint interno `/v1/dashboard/push`
- [x] Estado de denuncia consultable por código TRJ-XXXX via `GET /v1/denuncias/tracking/{tracking_code}`
- [ ] Test `test_crear_denuncia_y_procesar` pasa (pendiente de ejecutar)

---

### FASE 2 — Smart Contracts + Sellado Real en zkSYS

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P2** — Blockchain / Smart Contracts |
| **Prioridad** | IMPRESCINDIBLE — Alta |
| **Duración estimada** | 3–4 días |
| **Dependencias** | Fase 0 completada |
| **Riesgo si no se hace** | El "sellado blockchain" es simulado; no hay trazabilidad real; la demo no puede mostrar una transacción verificable en explorador |

#### 4.2.1 Objetivo

Desplegar los 4 smart contracts en zkSYS Genesis Testnet, obtener las addresses reales, configurarlas en `.env`, y conectar el Web3 Backend para que los sellos sean transacciones reales verificables en el explorador de bloques.

#### 4.2.2 Contratos a desplegar (ya compilados)

| Contrato | Propósito | Variable .env |
|----------|-----------|---------------|
| `EvidenceRegistry` | Sellado de hashes SHA-256 de evidencia | `CONTRACT_EVIDENCE_REGISTRY` |
| `CaseManager` | Gestión de casos y clústeres | `CONTRACT_CASE_MANAGER` |
| `DIDRegistry` | Registro de identidades descentralizadas | `CONTRACT_DID_REGISTRY` |
| `IntelToken` | Token de acceso/gobernanza (opcional en MVP) | `CONTRACT_TOKEN` |

#### 4.2.3 Función principal — EvidenceRegistry

```solidity
function seal(bytes32 contentHash, uint256 caseId) external {
    require(!evidenceExists(contentHash), "Hash ya sellado");
    evidences[contentHash] = Evidence({
        caseId: caseId,
        timestamp: block.timestamp,
        sealer: msg.sender,
        blockNumber: block.number
    });
    emit EvidenceSealed(contentHash, caseId, block.timestamp);
}

function evidenceExists(bytes32 contentHash) public view returns (bool) {
    return evidences[contentHash].timestamp != 0;
}
```

#### 4.2.4 Flujo de sellado (Web3 Backend → zkSYS)

```python
async def seal_evidence(content_hash: str, case_id: int) -> dict:
    hash_bytes = bytes.fromhex(content_hash.replace("0x", ""))
    tx = contract.functions.seal(hash_bytes, case_id).build_transaction({
        "from": INSTITUTIONAL_WALLET,
        "nonce": w3.eth.get_transaction_count(INSTITUTIONAL_WALLET),
        "gas": 200000,
        "gasPrice": w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "success": receipt.status == 1
    }
```

#### 4.2.5 Log de auditoría sellado en blockchain (RF-16)

```python
async def seal_daily_audit_log():
    log_entries = await get_log_entries_today()
    log_hash = sha256(json.dumps(log_entries).encode()).hexdigest()
    await seal_evidence(log_hash, case_id=0)
```

#### 4.2.6 Archivos a crear/modificar

| Componente | Acción |
|------------|--------|
| `intel_extorsion_web3_system/scripts/deploy.js` | Modificar — target `zkSYSTestnet` |
| `intel_extorsion_web3_system/scripts/verify.js` | Crear — verificar contratos en explorador |
| `intel_extorsion_web3_system/backend/app/services/evidence_service.py` | Modificar — addresses reales |
| `intel_extorsion_web3_system/backend/app/services/audit_seal_service.py` | Crear — sellado diario de log |
| `.env` | Actualizar con `CONTRACT_*` addresses reales |

#### 4.2.7 Entregables

- 4 contratos desplegados en zkSYS Genesis Testnet con addresses reales
- `.env` completo con `CONTRACT_*` variables
- `GET /v1/evidencias/{hash}/verificar` devuelve `tx_hash` real
- Enlace al explorador zkSYS con al menos 1 transacción verificable
- Test `test_web3_verificar_evidencia` pasando ✅

#### 4.2.8 Criterios de aceptación

- [ ] `npx hardhat run scripts/deploy.js --network zkSYSTestnet` sin errores
- [ ] Addresses reales verificadas con `ethers.getCode(address) !== "0x"`
- [ ] `POST /v1/evidencias/seal` devuelve `tx_hash` real visible en explorador
- [ ] `evidenceExists(hash)` devuelve `true` tras sellado
- [ ] Sellado diario de log funciona (cron cada 24h)

---

### FASE 3 — Canales Externos (Bot) + DApp con Pali Wallet

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P3** — Frontend / DApp |
| **Prioridad** | IMPRESCINDIBLE — Alta |
| **Duración estimada** | 4–5 días |
| **Dependencias** | Fase 1 (agente) + Fase 2 (contratos desplegados) |
| **Riesgo si no se hace** | El sistema solo recibe denuncias por el portal web; el canal masivo (WhatsApp/Telegram/Discord) no existe; la DApp no tiene integración real con Pali Wallet |

#### 4.3.1 Objetivo

Implementar el bot conversacional en WhatsApp, Telegram y Discord como Capa 1, y completar la integración de Pali Wallet V2 en la DApp como Capa 2. Ambos canales deben conectarse al agente autónomo (Fase 1).

#### 4.3.2 Sub-fase 3A — Bot WhatsApp/Telegram/Discord

**WhatsApp bot:**
```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    content = extract_content(message)

    if is_police_corruption(content):
        return send_whatsapp_reply(message["from"], REDIRECT_INSPECTORIA)

    denuncia = await agent_api.crear_denuncia(
        contenido=content,
        canal="whatsapp"
    )
    tracking_code = denuncia["tracking_code"]
    return send_whatsapp_reply(
        message["from"],
        f"✅ Denuncia recibida. Tu código: *{tracking_code}*"
    )
```

**STT con Groq Whisper:**
```python
async def transcribe_audio(audio_bytes: bytes) -> str:
    client = Groq()
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=("audio.ogg", audio_bytes),
        language="es"
    )
    return transcription.text
```

#### 4.3.3 Sub-fase 3B — DApp con Pali Wallet V2

```typescript
export async function connectPaliWallet() {
  if (!window.pali) throw new Error("Pali Wallet no instalada");

  const accounts = await window.pali.request({
    method: "eth_requestAccounts"
  });

  const chainId = await window.pali.request({ method: "eth_chainId" });
  if (chainId !== "0x1644") {
    await switchToZkSYS();
  }

  const provider = new ethers.BrowserProvider(window.pali);
  const signer = await provider.getSigner();
  const did = `did:zksys:${accounts[0]}`;
  return { signer, did, address: accounts[0] };
}
```

```typescript
export async function sealEvidence(
  signer: ethers.Signer,
  contentHash: string,
  caseId: number
) {
  const contract = new ethers.Contract(
    EVIDENCE_REGISTRY_ADDRESS,
    EvidenceRegistryABI,
    signer
  );
  const tx = await contract.seal(
    ethers.hexlify(ethers.toUtf8Bytes(contentHash)),
    caseId
  );
  return await tx.wait();
}
```

#### 4.3.4 Archivos a crear

| Componente | Acción |
|------------|--------|
| `app/channels/whatsapp_bot.py` | Crear |
| `app/channels/telegram_bot.py` | Crear |
| `app/channels/discord_bot.py` | Crear |
| `app/services/stt_service.py` | Crear (Groq Whisper) |
| `dapp/src/lib/paliWallet.ts` | Crear |
| `dapp/src/lib/evidenceContract.ts` | Crear |
| `dapp/src/components/WalletConnect.tsx` | Modificar |
| `dapp/src/components/UploadEvidence.tsx` | Modificar |
| `dapp/src/components/SealStatus.tsx` | Crear (polling) |
| `docker-compose.yml` | Modificar (añadir servicios bot) |

#### 4.3.5 Variables de entorno nuevas

```
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_ID=...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...
NEXT_PUBLIC_EVIDENCE_REGISTRY=0x...
NEXT_PUBLIC_CHAIN_ID=5700
NEXT_PUBLIC_RPC_URL=https://rpc.genesis.zksys.io
```

#### 4.3.6 Entregables

- Bot Telegram funcional: recibe texto → responde con código TRJ-XXXX
- Bot WhatsApp funcional (requiere número verificado con proveedor)
- Bot Discord funcional en canal privado del servidor
- DApp conecta Pali Wallet → sube archivo → sella en zkSYS → muestra `tx_hash`
- Componente `SealStatus` con polling (PENDIENTE → SELLADA sin recargar página)

#### 4.3.7 Criterios de aceptación

- [ ] Enviar mensaje a bot Telegram → recibir TRJ-XXXX en < 30 segundos
- [ ] Nota de voz en Telegram → transcrita y procesada correctamente
- [ ] DApp: conectar Pali Wallet en zkSYS Genesis Testnet sin errores
- [ ] DApp: subir JPG → hash calculado → tx firmada → visible en explorador
- [ ] SealStatus: badge cambia PROCESANDO → SELLADA sin recargar
- [ ] Número de teléfono de WhatsApp NO aparece en ninguna tabla de PostgreSQL

---

### FASE 4 — NLP Forense + Clustering (Motor de Inteligencia)

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P4** — Canales externos / Bot |
| **Prioridad** | ALTA — Core del valor de inteligencia |
| **Duración estimada** | 3–4 días |
| **Dependencias** | Fase 1 (agente procesando denuncias) |
| **Riesgo si no se hace** | El sistema recibe denuncias pero no genera inteligencia; el dashboard DIVINCRI no muestra clústeres ni mapa de calor |

#### 4.4.1 Objetivo

Implementar el motor NLP forense con ontología bootstrap (sin dataset real) y el algoritmo de clustering por grafos, para que el sistema detecte automáticamente bandas activas y alimente el dashboard DIVINCRI con perfiles de clúster.

#### 4.4.2 Sub-fase 4A — Ontología Forense Bootstrap

```python
ENTITY_PATTERNS = {
    "CUENTA_BANCARIA": [
        r"\b\d{14,20}\b",
        r"BCP|Interbank|BBVA|Scotiabank",
        r"Yape|Plin|\+51\s?9\d{8}"
    ],
    "TELEFONO_EXTORSIVO": [
        r"\b9\d{8}\b",
        r"\+51\s?9\d{8}"
    ],
    "MONTO": [
        r"S/\.?\s*\d+",
        r"\d+\s*(soles|semanales|quincenales|mensuales)"
    ],
    "JERGA_INTIMIDACION": [
        "cupo", "vacuna", "piso", "quemar", "picar", "brincar",
        "cobrarte", "te vamos a", "atentado"
    ],
    "METODO_VIOLENCIA": [
        "granada", "petardo", "explosivo", "balazo", "sicario",
        "quemar el local", "hacerte daño", "a tu familia"
    ],
    "TOPONIMO_TRUJILLO": [
        "El Porvenir", "El Milagro", "La Esperanza", "Florencia de Mora",
        "Alto Trujillo", "Víctor Larco", "Huanchaco", "Moche"
    ],
    "PLAZO": [
        r"hasta el (lunes|martes|miércoles|jueves|viernes)",
        r"\d+\s*(horas|días)", "esta semana", "mañana"
    ]
}
```

#### 4.4.3 Sub-fase 4B — Motor de Clustering

```python
def build_cluster_graph(denuncias: list) -> nx.Graph:
    G = nx.Graph()
    for d in denuncias:
        G.add_node(d.id, data=d)

    for i, d1 in enumerate(denuncias):
        for d2 in denuncias[i+1:]:
            shared = count_shared_vectors(d1, d2)
            if shared >= 2:
                G.add_edge(d1.id, d2.id, weight=shared)
    return G

def count_shared_vectors(d1, d2) -> int:
    score = 0
    if d1.cuentas & d2.cuentas:
        score += 2
    if cosine_sim(d1.embedding, d2.embedding) > 0.85:
        score += 1
    if d1.zona == d2.zona and abs((d1.fecha - d2.fecha).days) <= 21:
        score += 1
    if montos_similares(d1.monto, d2.monto, tolerancia=0.20):
        score += 1
    if d1.metodo_violencia == d2.metodo_violencia:
        score += 1
    return score

def find_active_clusters(G: nx.Graph) -> list:
    return [list(c) for c in nx.connected_components(G) if len(c) >= 3]
```

#### 4.4.4 Tablas PostgreSQL nuevas — Clusters

```sql
CREATE TABLE clusters (
    id                  SERIAL PRIMARY KEY,
    codigo              VARCHAR(20) UNIQUE,
    zona_principal      VARCHAR(100),
    estado              VARCHAR(20) DEFAULT 'ACTIVO',
    nivel_alerta        VARCHAR(20),
    total_denuncias     INT DEFAULT 0,
    monto_min           NUMERIC(10,2),
    monto_max           NUMERIC(10,2),
    cuentas_detectadas  JSONB,
    jerga_frecuente     JSONB,
    primera_denuncia    TIMESTAMP,
    ultima_denuncia     TIMESTAMP,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE denuncia_cluster (
    denuncia_id INT REFERENCES denuncias(id),
    cluster_id  INT REFERENCES clusters(id),
    PRIMARY KEY (denuncia_id, cluster_id)
);
```

#### 4.4.5 Endpoints nuevos

```
GET  /v1/clusters                    → Lista clústeres activos
GET  /v1/clusters/{id}               → Perfil completo del clúster
GET  /v1/clusters/{id}/denuncias     → Denuncias del clúster (sin identidad)
GET  /v1/heatmap?zona=&periodo=      → Datos GeoJSON para mapa de calor
POST /v1/clusters/recalculate        → Forzar recálculo (cron cada hora)
```

#### 4.4.6 Archivos a crear/modificar

| Componente | Acción |
|------------|--------|
| `app/nlp/ontology.py` | Crear |
| `app/nlp/ner_engine.py` | Crear (spaCy + ontología) |
| `app/nlp/clustering.py` | Crear (NetworkX) |
| `app/nlp/osint_enrichment.py` | Crear (consulta OSIPTEL) |
| `app/api/clusters_router.py` | Crear |
| `app/api/heatmap_router.py` | Crear |
| DB migration clusters | Crear |
| Frontend: mapa de calor Leaflet.js | Modificar `/dashboard/analitico` |
| Frontend: perfil de clúster | Completar `/dashboard/grafos` |

#### 4.4.7 Entregables

- `ontology.py` con ≥ 15 categorías y ≥ 40 topónimos de Trujillo/La Libertad
- Extracción de entidades funcionando en denuncias de prueba
- Clustering detectando banda con 3 denuncias compartiendo cuenta bancaria
- Dashboard DIVINCRI mostrando mapa de calor con datos reales de PostgreSQL
- API `/v1/clusters` con al menos 2 clústeres de seed data

#### 4.4.8 Criterios de aceptación

- [ ] NER extrae cuenta bancaria de "deposita a la cuenta BCP 00123456789012" ✅
- [ ] NER extrae zona de "tu negocio en El Porvenir está en riesgo" ✅
- [ ] 3 denuncias con misma cuenta → clúster detectado automáticamente
- [ ] Dashboard `/dashboard/analitico` muestra zonas coloreadas con intensidad real
- [ ] `/v1/clusters` devuelve perfiles con `monto_min`, `monto_max`, `cuentas_detectadas`

---

### FASE 5 — Integración Final + QA + Demo

| Atributo | Valor |
|----------|-------|
| **Responsable** | **P5** — Backend / Infraestructura / QA |
| **Prioridad** | CRÍTICA — Cierre del proyecto |
| **Duración estimada** | 2–3 días |
| **Dependencias** | Fases 1, 2, 3 y 4 completadas |
| **Riesgo si no se hace** | Las partes funcionan por separado pero no integradas; la demo ante el jurado falla en algún punto del flujo |

#### 4.5.1 Objetivo

Verificar el flujo end-to-end completo, corregir bugs de integración, completar los 9 tests, generar seed data realista para la demo, y preparar el guión de demostración.

#### 4.5.2 Checklist de integración

| Flujo | Responsable | Estado objetivo |
|-------|-------------|-----------------|
| Bot Telegram → Agente → TRJ-XXXX | P4 + P1 | ✅ |
| Portal web → Agente → Dashboard DIVINCRI | P3 + P1 | ✅ |
| DApp → Pali Wallet → zkSYS → tx_hash | P3 + P2 | ✅ |
| Agente → Clustering → Alerta DIVINCRI | P1 + P5 | ✅ |
| Alerta → Dashboard → Mapa de calor | P3 + P5 | ✅ |
| Log diario → Sellado zkSYS (RF-16) | P2 + P5 | ✅ |
| Consulta TRJ-XXXX por bot → Estado actualizado | P4 + P5 | ✅ |

#### 4.5.3 Tests a completar (actualmente 6/9 passing)

| Test | Responsable | Fase que lo habilita |
|------|-------------|---------------------|
| `test_crear_denuncia_y_procesar` | P1 | Fase 1 |
| `test_web3_verificar_evidencia` | P2 | Fase 2 |
| `test_frontend_carga` | P3 | Fase 3 |
| `test_bot_telegram_flow` (nuevo) | P4 | Fase 3 |
| `test_clustering_deteccion` (nuevo) | P1 | Fase 4 |
| `test_seal_audit_log` (nuevo) | P2 | Fase 2 |

**Objetivo:** 9/9 tests passing antes de la demo.

#### 4.5.4 Seed data para demo

```python
SEED_DENUNCIAS = [
    {
        "contenido": "Me llegó una carta: deposita S/. 450 semanales a la cuenta "
                     "BCP 00123456789012345678 o quemamos tu negocio en El Porvenir. "
                     "Tienes 48 horas.",
        "canal": "whatsapp", "zona": "El Porvenir"
    },
    {
        "contenido": "Vacúnate o te picamos. Deposita 500 soles al 942847293 (Yape). "
                     "Tu ferretería en El Milagro lo sabe.",
        "canal": "telegram", "zona": "Cerro El Milagro"
    },
]
```

#### 4.5.5 Guión de demo (10 minutos)

1. [2 min] Portal ciudadano: enviar denuncia texto → código TRJ-4X9K
2. [1 min] Bot Telegram: misma denuncia → mismo flujo, diferente canal
3. [2 min] Dashboard DIVINCRI: mapa de calor con clúster detectado
4. [1 min] Perfil de banda: cuenta bancaria, jerga, monto, zona
5. [2 min] DApp: conectar Pali Wallet → subir carta JPG → tx en explorador zkSYS
6. [1 min] Verificar hash en explorador de bloques zkSYS Genesis Testnet
7. [1 min] Log de auditoría sellado en blockchain

#### 4.5.6 Entregables

- 9/9 tests passing
- `docker compose up -d` levanta TODO sin errores en máquina limpia
- Seed data: 10 denuncias simuladas generando 2 clústeres detectables
- README actualizado con guión de demo paso a paso
- Screen recording de la demo como respaldo

#### 4.5.7 Criterios de aceptación finales

- [ ] Flujo completo ciudadano → DIVINCRI en < 60 segundos
- [ ] Transacción real visible en explorador zkSYS Genesis Testnet
- [ ] 9/9 tests passing
- [ ] `docker compose up -d` funciona en máquina limpia siguiendo INSTALL.md
- [ ] Dashboard DIVINCRI muestra mapa de calor con datos de seed

---

## 5. Resumen de Distribución por Persona

| Persona | Rol | Fases principales (originales) | Tareas adicionales | Entregables clave |
|---------|-----|-------------------------------|--------------------|-------------------|
| **P1** | Líder técnico / Agentes IA | Fase 0 (testnet), Fase 1 (agente) | 1.1, 1.2, 1.3, 4.1, 4.2 | File upload, OCR real, STT real, clustering NetworkX, ontología forense |
| **P2** | Blockchain / Smart Contracts | Fase 2 (contratos) | 2.1, 2.2, 2.3, 2.4, 2.5 | Contratos desplegados, acta forense PDF, log auditado, cobertura API 100%, gas dinámico |
| **P3** | Frontend / DApp | Fase 3 (canales + DApp) | 3.1, 3.2, 3.3, 3.4, 4.5, 4.6 | 2 frontends separados, detalle denuncia, tracking ciudadano, upload real, mapa calor Leaflet, perfil banda |
| **P4** | Canales externos / Bot | Fase 4 (NLP + clustering) | 4.3, 4.4 | Anonimización Presidio, OSINT real (OSIPTEL) |
| **P5** | Backend / Infraestructura / QA | Fase 5 (integración + QA) | 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10 | Auth + roles, rate limiting, migraciones Alembic, cifrado AES-256, alertas push, exportación, logging, health check, 2 silos DB |

---

## 6. Cronograma Sugerido

| Fase | Nombre | Días originales | Días adicionales | Semana | Responsable | Estado |
|------|--------|-----------------|------------------|--------|-------------|--------|
| 0 | Migración a zkSYS Genesis Testnet | 1–2 | — | Semana 1 | P1 | ✅ Completada |
| 1 | Agente Autónomo End-to-End | 3–4 | +4 | Semana 1–2 | P1 | ✅ Completada (tareas adicionales ⏳) |
| 2 | Smart Contracts + Sellado Real | 3–4 | +9.5 | Semana 2–4 | P2 | ⏳ Pendiente |
| 3 | Canales Externos + DApp + Separación Frontends | 4–5 | +7 | Semana 4–6 | P3 | ⏳ Pendiente |
| 4 | NLP Forense + Clustering + Ontología + OSINT | 3–4 | +15 | Semana 6–9 | P4 + P1 | ⏳ Pendiente |
| 5 | Integración Final + QA + Seguridad + Demo | 2–3 | +18.5 | Semana 9–13 | P5 | ⏳ Pendiente |

**Total estimado original:** 16–22 días hábiles (5–6 semanas)
**Total estimado con brechas:** 70–80 días hábiles (13–16 semanas) con trabajo en paralelo donde las dependencias lo permitan.

---

---

## 7. Prioridades de Implementación — Brechas post-análisis profundo

Tras un análisis exhaustivo del código fuente (junio 2026) y su contraste contra `requerimientos.md`, se identificaron brechas críticas que deben integrarse en las fases existentes. A continuación se listan las tareas adicionales por fase:

### FASE 1 — Tareas adicionales

| # | Tarea | Dependencia | Esfuerzo | Requisito asociado |
|---|-------|-------------|----------|-------------------|
| **1.1** | **File upload endpoint real** en agent-api (`POST /v1/denuncias/{id}/adjuntar`) | Ninguna | 2 días | RF-06 |
| **1.2** | **OCR real con Tesseract** (ya instalado en contenedor Docker, solo conectar) | 1.1 | 1 día | RF-02 |
| **1.3** | **Speech-to-Text real con Groq Whisper** (reemplazar simulación en `shared_tools.py`) | Ninguna | 1 día | RF-02 |

### FASE 2 — Tareas adicionales

| # | Tarea | Dependencia | Esfuerzo | Requisito asociado |
|---|-------|-------------|----------|-------------------|
| **2.1** | **Acta forense PDF** con reportlab (hash + timestamp + DID + número de bloque + firma digital) | Contratos desplegados | 2 días | RF-08 |
| **2.2** | **Log de auditoría sellado en blockchain cada 24h** (servicio cron + endpoint `POST /v1/admin/seal-audit-log`) | Contratos desplegados | 2 días | RF-16 |
| **2.3** | **Completar cobertura de contratos en API** (~20 endpoints faltantes: revocar evidencia, asignar oficiales, cambiar estado de caso, token completo) | Contratos desplegados | 4 días | RF-07, RF-16 |
| **2.4** | **Gas dinámico + nonce thread-safe** en `web3_service.py` | Ninguna | 1 día | RNF-05 |
| **2.5** | **Deshabilitar fallback "modo desarrollo" silencioso** — añadir flag `DEV_MODE` explícito | Ninguna | 0.5 días | RNF-05 |

### FASE 3 — Tareas adicionales

| # | Tarea | Dependencia | Esfuerzo | Requisito asociado |
|---|-------|-------------|----------|-------------------|
| **3.1** | **Separar frontend en 2 apps**: `frontend-citizen/` (portal + DApp) y `frontend-police/` (dashboard DIVINCRI + login) con tipos compartidos vía `shared-types/` | Ninguna | 3 días | RNF-05 |
| **3.2** | **Página de detalle de denuncia** (`/dashboard/policial/[id]`) con timeline de agentes, blockchain seal status y evidencias | 1.1 | 2 días | RF-15 |
| **3.3** | **Búsqueda/seguimiento desde portal ciudadano** — campo para ingresar código TRJ-XXXX y ver estado público | Ninguna | 1 día | RF-04 |
| **3.4** | **Subida real de archivos en portal** (multipart al backend, no solo metadata) | 1.1 | 1 día | RF-06 |

### FASE 4 — Tareas adicionales

| # | Tarea | Dependencia | Esfuerzo | Requisito asociado |
|---|-------|-------------|----------|-------------------|
| **4.1** | **Clustering real con NetworkX** en `correlation_agent` (≥2 vectores comunes, ≥3 nodos → alerta) | Ninguna | 3 días | RF-10 |
| **4.2** | **Ontología forense bootstrap** (20+ categorías, 40+ topónimos Trujillo/La Libertad) | Ninguna | 2 días | RF-09 |
| **4.3** | **Anonimización con Presidio** (Microsoft PII masking) antes de entrenamiento | Ninguna | 2 días | RF-11 |
| **4.4** | **OSINT real** — consultas a OSIPTEL + fuentes públicas (reemplazar `shared_tools.py` simulado) | Ninguna | 3 días | RF-18 |
| **4.5** | **Mapa de calor con Leaflet.js + GeoJSON del Plan Cuadrante PNP** — alimentado por endpoint `/v1/heatmap` | 4.1 | 3 días | RF-12 |
| **4.6** | **Perfil automático de banda por clúster** (ficha con zona, monto, cuentas, jerga, violencia, tendencia) | 4.1, 4.5 | 2 días | RF-13 |

### FASE 5 — Tareas adicionales (Críticas para producción)

| # | Tarea | Dependencia | Esfuerzo | Requisito asociado |
|---|-------|-------------|----------|-------------------|
| **5.1** | **Autenticación completa** — JWT + API Key en backend, login + middleware en `frontend-police/`, expiración 8h | 3.1 | 3 días | RNF-05 |
| **5.2** | **Sistema de roles** (Analista/Supervisor/Admin) en DB + middleware FastAPI + protección de rutas frontend | 5.1 | 2 días | RF-17 |
| **5.3** | **Rate limiting** con `slowapi` + Redis (20 msg/hora por teléfono en bot, 100 req/min en API) | Ninguna | 1 día | RNF-05 |
| **5.4** | **Migraciones reales con Alembic** — reemplazar `create_all()` por migraciones versionadas | Ninguna | 1 día | RNF-06 |
| **5.5** | **Cifrado AES-256 en reposo** para campos sensibles (`contenido_raw`, `metadata_json`) | Ninguna | 2 días | RNF-05 |
| **5.6** | **Alertas push reales** — email + SMS + webhook SIRDIC/SIDPOL cuando clúster supera umbral | 4.1 | 3 días | RF-14 |
| **5.7** | **Exportación PDF/CSV** de perfiles de clúster y dashboard, compatible SIRDIC/SIDPOL | 4.6 | 2 días | RNF-07 |
| **5.8** | **Logging estructurado** con `structlog` + correlación de requests | Ninguna | 1 día | RNF-06 |
| **5.9** | **Health check profundo** — verificar PostgreSQL, Qdrant, Redis, Groq, zkSYS individualmente | Ninguna | 0.5 días | — |
| **5.10** | **Dos silos de datos** (RNF-01) — separar DB de metadatos de canal y DB de evidencia procesada con credenciales distintas | 5.1 | 3 días | RNF-01 |

### Resumen de esfuerzo adicional

| Fase | Tareas nuevas | Esfuerzo estimado |
|------|---------------|-------------------|
| 1 | 3 | 4 días |
| 2 | 5 | 9.5 días |
| 3 | 4 | 7 días |
| 4 | 6 | 15 días |
| 5 | 10 | 18.5 días |
| **Total** | **28** | **~54 días adicionales** |

> **Nota:** Estas tareas no reemplazan el contenido original de las fases, sino que lo complementan. Las fases originales 0–5 ya están descritas en las secciones 4.0–4.5 de este documento. La sección 7 identifica brechas detectadas durante el code review y las asigna a la fase correspondiente para su ejecución.

---

*Documento generado a partir de la distribución de trabajo del equipo IntelExtorsión — 20 de junio de 2026*
