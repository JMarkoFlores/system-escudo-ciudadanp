IntelExtorsión — Plan de Trabajo por Fases
Distribución para 5 personas · zkSYS Genesis Testnet + Agentes Autónomos
Contexto de partida (AGENTS.md): El sistema ya tiene arquitectura base funcional: Docker Compose levanta correctamente, 6/9 tests pasan, frontend Next.js buildea, agentes LangGraph + GroqCloud procesando, embeddings locales con fastembed. Lo pendiente crítico: Smart contracts no desplegados, Pali Wallet sin integrar, canales externos (WhatsApp/Telegram/Discord) sin implementar, zkSYS Genesis Testnet sin configurar, y el agente autónomo sin conexión end-to-end.

Roles del Equipo
Persona
Rol
Stack principal
P1
Líder técnico / Agentes IA
Python · LangGraph · FastAPI · GroqCloud
P2
Blockchain / Smart Contracts
Solidity · Hardhat · Web3.py · zkSYS
P3
Frontend / DApp
Next.js · TypeScript · Tailwind · ethers.js
P4
Canales externos / Bot
Python · Twilio/360dialog · Telegram · Discord
P5
Backend / Infraestructura / QA
PostgreSQL · Docker · Redis · pytest


Vista General de Fases
Fase
Nombre
Duración
Dependencias
0
Migración a zkSYS Genesis Testnet
1–2 días
Ninguna — bloquea todo lo demás
1
Agente Autónomo End-to-End
3–4 días
Fase 0
2
Smart Contracts + Sellado Real
3–4 días
Fase 0
3
Canales Externos (Bot) + DApp Pali Wallet
4–5 días
Fases 1 y 2
4
NLP Forense + Clustering
3–4 días
Fase 1
5
Integración Final + QA + Demo
2–3 días
Fases 1–4

Duración total estimada: 16–22 días

FASE 0 — Migración a zkSYS Genesis Testnet
Atributo
Valor
Prioridad
CRÍTICA — Bloquea todas las demás fases
Duración estimada
1–2 días
Dependencias
Ninguna
Riesgo si no se hace
Todo el sistema sigue apuntando a Rollux Mainnet (Chain ID 570); los contratos no se pueden desplegar en testnet; la demo no funciona sin fondos reales

Objetivo
Migrar la configuración de red de Syscoin Rollux Mainnet (Chain ID 570) a zkSYS Genesis Testnet para desarrollo y demo. Actualizar todos los puntos del sistema que referencian la red anterior.
Problema que resuelve
El AGENTS.md indica WEB3_PROVIDER_URL=https://rpc.rollux.com y CHAIN_ID=570 (Rollux Mainnet). En testnet, los contratos se pueden desplegar sin fondos reales, las transacciones son gratuitas, y el equipo puede demostrar el sellado blockchain sin riesgo económico.
Archivos a modificar
Archivo
Cambio
.env.example
WEB3_PROVIDER_URL, CHAIN_ID, EXPLORER_URL
intel_extorsion_web3_system/hardhat.config.js
Añadir red zkSYSTestnet
intel_extorsion_web3_system/backend/app/config.py
Chain ID y RPC URL
intel_extorsion_frontend/src/lib/web3Config.ts
Chain config para Pali Wallet
docker-compose.yml
Variables de entorno de red

Configuración zkSYS Genesis Testnet
bash
# .env actualizado
WEB3_PROVIDER_URL=https://rpc.genesis.zksys.io
CHAIN_ID=5700
EXPLORER_URL=https://explorer.genesis.zksys.io
NETWORK_NAME=zkSYS Genesis Testnet
FAUCET_URL=https://faucet.genesis.zksys.io
javascript
// hardhat.config.js — añadir red
networks: {
  zkSYSTestnet: {
    url: process.env.WEB3_PROVIDER_URL,
    chainId: parseInt(process.env.CHAIN_ID),
    accounts: [process.env.PRIVATE_KEY],
    gasPrice: "auto"
  }
}
Responsables
P2 (blockchain): configuración Hardhat, verificación RPC, fondos del faucet
P5 (infra): actualización .env, Docker, variables
Entregables
.env.example actualizado con zkSYS Genesis Testnet
hardhat.config.js con nueva red configurada
Confirmación de conectividad: npx hardhat run scripts/checkNetwork.js --network zkSYSTestnet
Wallet institucional con fondos del faucet para despliegue
Criterios de aceptación
curl $WEB3_PROVIDER_URL responde con JSON-RPC válido
ethers.getNetwork() devuelve Chain ID correcto
Web3 Backend arranca sin errores de conexión de red
P2 tiene fondos de testnet en la wallet institucional

FASE 1 — Agente Autónomo End-to-End
Atributo
Valor
Prioridad
IMPRESCINDIBLE — Alta
Duración estimada
3–4 días
Dependencias
Fase 0 completada
Riesgo si no se hace
El "agente autónomo" del sistema es solo una pipeline de funciones; no hay ciclo de razonamiento real ni integración con blockchain ni con los canales externos

Objetivo
Completar el grafo LangGraph para que el agente autónomo ejecute el ciclo completo de forma encadenada: recibe denuncia → clasifica → extrae entidades NLP → evalúa riesgo → decide si sellar en blockchain → emite alerta → responde al usuario. Actualmente el grafo existe pero los nodos node_seal y node_alert no tienen conexión real con el Web3 Backend ni con los canales de salida.
Problema que resuelve
Según AGENTS.md, el bug #2 indica "Smart Contracts no desplegados → Web3 Backend devuelve 500". El agente llama a node_seal pero falla silenciosamente. Adicionalmente, node_alert genera alertas en PostgreSQL pero no las envía a ningún destino externo (email, SMS, dashboard push).
Arquitectura del grafo LangGraph (estado actual → objetivo)
text
ACTUAL:
intake → classify → extract_entities → assess_risk → [FIN]

OBJETIVO:
intake → classify → extract_entities → assess_risk
    → [if riesgo ALTO/CRÍTICO] → seal_blockchain → emit_alert → respond
    → [if riesgo BAJO/MEDIO]   → store_case → respond
Archivos a crear/modificar
Componente
Acción
intel_extorsion_agent_system/app/core/agent_graph.py
Modificar — añadir nodos node_seal y node_alert con llamadas reales
intel_extorsion_agent_system/app/agents/seal_agent.py
Crear — cliente HTTP al Web3 Backend
intel_extorsion_agent_system/app/agents/alert_agent.py
Crear — emisión de alertas push al dashboard
intel_extorsion_agent_system/app/agents/respond_agent.py
Crear — generación de código TRJ-XXXX y respuesta al canal
intel_extorsion_agent_system/app/core/state.py
Modificar — añadir campos seal_tx_hash, alert_sent, tracking_code
intel_extorsion_agent_system/app/services/web3_client.py
Crear — cliente HTTP interno para Web3 Backend (puerto 8001)

Nodo SealAgent — lógica
python
# seal_agent.py
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
Nodo AlertAgent — lógica
python
# alert_agent.py
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
Código de seguimiento (RF-04)
python
# respond_agent.py
import secrets, string

def generate_tracking_code() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(4))
    return f"TRJ-{suffix}"
Responsables
P1 (líder/agentes): grafo LangGraph, nodos seal y alert, estado
P5 (backend/infra): servicio web3_client HTTP, SSE para dashboard
Entregables
Grafo LangGraph con ciclo completo (intake → seal → alert → respond)
seal_agent.py y alert_agent.py implementados
Código de seguimiento TRJ-XXXX generado y almacenado en PostgreSQL
Test test_crear_denuncia_y_procesar pasando ✅ (actualmente ❌)
SSE endpoint en Agent API para push al dashboard
Criterios de aceptación
Denuncia de texto libre recibida → procesada por 8 agentes → responde con TRJ-XXXX
Denuncia con riesgo ALTO → seal_tx_hash no nulo en PostgreSQL
Dashboard policial recibe alerta push en < 5 segundos tras procesamiento
Estado de denuncia consultable por código TRJ-XXXX via GET /v1/denuncias/{tracking_code}
Test test_crear_denuncia_y_procesar pasa

FASE 2 — Smart Contracts + Sellado Real en zkSYS
Atributo
Valor
Prioridad
IMPRESCINDIBLE — Alta
Duración estimada
3–4 días
Dependencias
Fase 0 completada
Riesgo si no se hace
El "sellado blockchain" es simulado; no hay trazabilidad real; la demo ante el jurado no puede mostrar una transacción verificable en explorador

Objetivo
Desplegar los 4 smart contracts en zkSYS Genesis Testnet, obtener las addresses reales, configurarlas en .env, y conectar el Web3 Backend para que los sellos sean transacciones reales verificables en el explorador de bloques.
Contratos a desplegar (ya compilados según AGENTS.md)
Contrato
Propósito
Variable .env
EvidenceRegistry
Sellado de hashes SHA-256 de evidencia
CONTRACT_EVIDENCE_REGISTRY
CaseManager
Gestión de casos y clústeres
CONTRACT_CASE_MANAGER
DIDRegistry
Registro de identidades descentralizadas
CONTRACT_DID_REGISTRY
IntelToken
Token de acceso/gobernanza (opcional en MVP)
CONTRACT_TOKEN

Función principal — EvidenceRegistry
text
// EvidenceRegistry.sol
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
Flujo de sellado (Web3 Backend → zkSYS)
python
# evidence_service.py
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
Log de auditoría sellado en blockchain (RF-16)
python
# Cron cada 24h
async def seal_daily_audit_log():
    log_entries = await get_log_entries_today()
    log_hash = sha256(json.dumps(log_entries).encode()).hexdigest()
    await seal_evidence(log_hash, case_id=0)  # case_id=0 = audit log
Archivos a crear/modificar
Componente
Acción
intel_extorsion_web3_system/scripts/deploy.js
Modificar — target zkSYSTestnet
intel_extorsion_web3_system/scripts/verify.js
Crear — verificar contratos en explorador
intel_extorsion_web3_system/backend/app/services/evidence_service.py
Modificar — addresses reales
intel_extorsion_web3_system/backend/app/services/audit_seal_service.py
Crear — sellado diario de log
.env
Actualizar con CONTRACT_* addresses reales

Responsables
P2 (blockchain): deploy, verificación, ABI sync, scripts
P5 (infra): actualización .env, test test_web3_verificar_evidencia
Entregables
4 contratos desplegados en zkSYS Genesis Testnet con addresses reales
.env completo con CONTRACT_* variables
GET /v1/evidencias/{hash}/verificar devuelve tx_hash real
Enlace al explorador zkSYS con al menos 1 transacción verificable
Test test_web3_verificar_evidencia pasando ✅
Criterios de aceptación
npx hardhat run scripts/deploy.js --network zkSYSTestnet sin errores
Addresses reales verificadas con ethers.getCode(address) !== "0x"
POST /v1/evidencias/seal devuelve tx_hash real visible en explorador
evidenceExists(hash) devuelve true tras sellado
Sellado diario de log funciona (cron cada 24h)

FASE 3 — Canales Externos (Bot) + DApp con Pali Wallet
Atributo
Valor
Prioridad
IMPRESCINDIBLE — Alta
Duración estimada
4–5 días
Dependencias
Fase 1 (agente) + Fase 2 (contratos desplegados)
Riesgo si no se hace
El sistema solo recibe denuncias por el portal web; el canal masivo (WhatsApp/Telegram/Discord) no existe; la DApp no tiene integración real con Pali Wallet

Objetivo
Implementar el bot conversacional en WhatsApp, Telegram y Discord como Capa 1, y completar la integración de Pali Wallet V2 en la DApp como Capa 2. Ambos canales deben conectarse al agente autónomo (Fase 1).
Sub-fase 3A — Bot WhatsApp/Telegram/Discord (P4)
python
# app/channels/whatsapp_bot.py
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    content = extract_content(message)  # texto, imagen OCR, audio STT

    # Clasificación inicial RF-01
    if is_police_corruption(content):
        return send_whatsapp_reply(message["from"], REDIRECT_INSPECTORIA)

    # Enviar al agente SIN guardar el número de teléfono (RNF-01)
    denuncia = await agent_api.crear_denuncia(
        contenido=content,
        canal="whatsapp"
        # NUNCA incluir message["from"]
    )
    tracking_code = denuncia["tracking_code"]
    return send_whatsapp_reply(
        message["from"],
        f"✅ Denuncia recibida. Tu código: *{tracking_code}*\n"
        f"Consúltalo escribiendo: estado {tracking_code}"
    )
python
# app/services/stt_service.py — Groq Whisper (coherente con stack actual)
async def transcribe_audio(audio_bytes: bytes) -> str:
    client = Groq()
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=("audio.ogg", audio_bytes),
        language="es"
    )
    return transcription.text
Sub-fase 3B — DApp con Pali Wallet V2 (P3)
typescript
// dapp/src/lib/paliWallet.ts
export async function connectPaliWallet() {
  if (!window.pali) throw new Error("Pali Wallet no instalada");

  const accounts = await window.pali.request({
    method: "eth_requestAccounts"
  });

  const chainId = await window.pali.request({ method: "eth_chainId" });
  if (chainId !== "0x1644") {  // 5700 decimal — verificar Chain ID oficial zkSYS
    await switchToZkSYS();
  }

  const provider = new ethers.BrowserProvider(window.pali);
  const signer = await provider.getSigner();
  const did = `did:zksys:${accounts[0]}`;
  return { signer, did, address: accounts[0] };
}

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
Archivos a crear
Componente
Persona
Acción
app/channels/whatsapp_bot.py
P4
Crear
app/channels/telegram_bot.py
P4
Crear
app/channels/discord_bot.py
P4
Crear
app/services/stt_service.py
P4
Crear (Groq Whisper)
dapp/src/lib/paliWallet.ts
P3
Crear
dapp/src/lib/evidenceContract.ts
P3
Crear
dapp/src/components/WalletConnect.tsx
P3
Modificar
dapp/src/components/UploadEvidence.tsx
P3
Modificar
dapp/src/components/SealStatus.tsx
P3
Crear (polling)
docker-compose.yml
P5
Modificar (añadir servicios bot)

Variables de entorno nuevas
bash
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_ID=...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...
NEXT_PUBLIC_EVIDENCE_REGISTRY=0x...
NEXT_PUBLIC_CHAIN_ID=5700
NEXT_PUBLIC_RPC_URL=https://rpc.genesis.zksys.io
Responsables
P4: bots WhatsApp, Telegram, Discord, STT service
P3: DApp Pali Wallet V2, sellado desde frontend, SealStatus component
Entregables
Bot Telegram funcional: recibe texto → responde con código TRJ-XXXX
Bot WhatsApp funcional (requiere número verificado con proveedor)
Bot Discord funcional en canal privado del servidor
DApp conecta Pali Wallet → sube archivo → sella en zkSYS → muestra tx_hash
Componente SealStatus con polling (PENDIENTE → SELLADA sin recargar página)
Criterios de aceptación
Enviar mensaje a bot Telegram → recibir TRJ-XXXX en < 30 segundos
Nota de voz en Telegram → transcrita y procesada correctamente
DApp: conectar Pali Wallet en zkSYS Genesis Testnet sin errores
DApp: subir JPG → hash calculado → tx firmada → visible en explorador
SealStatus: badge cambia PROCESANDO → SELLADA sin recargar
Número de teléfono de WhatsApp NO aparece en ninguna tabla de PostgreSQL

FASE 4 — NLP Forense + Clustering (Motor de Inteligencia)
Atributo
Valor
Prioridad
ALTA — Core del valor de inteligencia
Duración estimada
3–4 días
Dependencias
Fase 1 (agente procesando denuncias)
Riesgo si no se hace
El sistema recibe denuncias pero no genera inteligencia; el dashboard DIVINCRI no muestra clústeres ni mapa de calor; el diferenciador frente a la Central 111 desaparece

Objetivo
Implementar el motor NLP forense con ontología bootstrap (sin dataset real) y el algoritmo de clustering por grafos, para que el sistema detecte automáticamente bandas activas y alimente el dashboard DIVINCRI con perfiles de clúster.
Sub-fase 4A — Ontología Forense Bootstrap (P1)
python
# app/nlp/ontology.py — sin datos reales de víctimas
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
        "Alto Trujillo", "Víctor Larco", "Huanchaco", "Moche",
        "cerro El Toro", "cerro El Milagro", "cerro San Cosme"
        # +35 topónimos de La Libertad
    ],
    "PLAZO": [
        r"hasta el (lunes|martes|miércoles|jueves|viernes)",
        r"\d+\s*(horas|días)",
        "esta semana", "mañana"
    ]
}
Sub-fase 4B — Motor de Clustering (P1 + P5)
python
# app/nlp/clustering.py
import networkx as nx

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
        score += 2                            # vector fuerte: misma cuenta
    if cosine_sim(d1.embedding, d2.embedding) > 0.85:
        score += 1                            # similitud textual
    if d1.zona == d2.zona and abs((d1.fecha - d2.fecha).days) <= 21:
        score += 1                            # misma zona en 21 días
    if montos_similares(d1.monto, d2.monto, tolerancia=0.20):
        score += 1                            # monto similar ±20%
    if d1.metodo_violencia == d2.metodo_violencia:
        score += 1                            # mismo método
    return score

def find_active_clusters(G: nx.Graph) -> list:
    # Componente con ≥ 3 nodos = banda activa
    return [list(c) for c in nx.connected_components(G) if len(c) >= 3]
Tabla PostgreSQL nueva — Clusters
sql
CREATE TABLE clusters (
    id                  SERIAL PRIMARY KEY,
    codigo              VARCHAR(20) UNIQUE,       -- C-2026-041
    zona_principal      VARCHAR(100),
    estado              VARCHAR(20) DEFAULT 'ACTIVO',
    nivel_alerta        VARCHAR(20),              -- EMERGENTE|ALTO|CRITICO
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
Endpoints nuevos
text
GET  /v1/clusters                    → Lista clústeres activos
GET  /v1/clusters/{id}               → Perfil completo del clúster
GET  /v1/clusters/{id}/denuncias     → Denuncias del clúster (sin identidad)
GET  /v1/heatmap?zona=&periodo=      → Datos GeoJSON para mapa de calor
POST /v1/clusters/recalculate        → Forzar recálculo (cron cada hora)
Archivos a crear/modificar
Componente
Persona
Acción
app/nlp/ontology.py
P1
Crear
app/nlp/ner_engine.py
P1
Crear (spaCy + ontología)
app/nlp/clustering.py
P1
Crear (NetworkX)
app/nlp/osint_enrichment.py
P1
Crear (consulta OSIPTEL)
app/api/clusters_router.py
P5
Crear
app/api/heatmap_router.py
P5
Crear
DB migration clusters
P5
Crear
Frontend: mapa de calor Leaflet.js
P3
Modificar /dashboard/analitico
Frontend: perfil de clúster
P3
Completar /dashboard/grafos

Responsables
P1: ontología, NER engine, algoritmo clustering, OSINT enrichment
P5: endpoints REST, migración DB, cron recálculo cada hora
P3: mapa de calor Leaflet.js, perfil de clúster en dashboard
Entregables
ontology.py con ≥ 15 categorías y ≥ 40 topónimos de Trujillo/La Libertad
Extracción de entidades funcionando en denuncias de prueba
Clustering detectando banda con 3 denuncias compartiendo cuenta bancaria
Dashboard DIVINCRI mostrando mapa de calor con datos reales de PostgreSQL
API /v1/clusters con al menos 2 clústeres de seed data
Criterios de aceptación
NER extrae cuenta bancaria de "deposita a la cuenta BCP 00123456789012" ✅
NER extrae zona de "tu negocio en El Porvenir está en riesgo" ✅
3 denuncias con misma cuenta → clúster detectado automáticamente
Dashboard /dashboard/analitico muestra zonas coloreadas con intensidad real
/v1/clusters devuelve perfiles con monto_min, monto_max, cuentas_detectadas

FASE 5 — Integración Final + QA + Demo
Atributo
Valor
Prioridad
CRÍTICA — Cierre del proyecto
Duración estimada
2–3 días
Dependencias
Fases 1, 2, 3 y 4 completadas
Riesgo si no se hace
Las partes funcionan por separado pero no integradas; la demo ante el jurado falla en algún punto del flujo

Objetivo
Verificar el flujo end-to-end completo, corregir bugs de integración, completar los 9 tests, generar seed data realista para la demo, y preparar el guión de demostración.
Checklist de integración
Flujo
Responsable
Estado objetivo
Bot Telegram → Agente → TRJ-XXXX
P4 + P1
✅
Portal web → Agente → Dashboard DIVINCRI
P3 + P1
✅
DApp → Pali Wallet → zkSYS → tx_hash
P3 + P2
✅
Agente → Clustering → Alerta DIVINCRI
P1 + P5
✅
Alerta → Dashboard → Mapa de calor
P3 + P5
✅
Log diario → Sellado zkSYS (RF-16)
P2 + P5
✅
Consulta TRJ-XXXX por bot → Estado actualizado
P4 + P5
✅

Tests a completar (actualmente 6/9 passing)
Test
Responsable
Fase que lo habilita
test_crear_denuncia_y_procesar
P1
Fase 1
test_web3_verificar_evidencia
P2
Fase 2
test_frontend_carga
P3
Fase 3
test_bot_telegram_flow (nuevo)
P4
Fase 3
test_clustering_deteccion (nuevo)
P1
Fase 4
test_seal_audit_log (nuevo)
P2
Fase 2

Objetivo: 9/9 tests passing antes de la demo.
Seed data para demo
python
# tests/seed_demo.py
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
    # +8 denuncias que forman 2 clústeres detectables
]
Guión de demo (10 minutos)
text
1. [2 min] Portal ciudadano: enviar denuncia texto → código TRJ-4X9K
2. [1 min] Bot Telegram: misma denuncia → mismo flujo, diferente canal
3. [2 min] Dashboard DIVINCRI: mapa de calor con clúster detectado
4. [1 min] Perfil de banda: cuenta bancaria, jerga, monto, zona
5. [2 min] DApp: conectar Pali Wallet → subir carta JPG → tx en explorador zkSYS
6. [1 min] Verificar hash en explorador de bloques zkSYS Genesis Testnet
7. [1 min] Log de auditoría sellado en blockchain
Responsables
P5: tests 9/9, seed data, Docker final desde cero
P1: integración agente completo, revisión prompts finales
P2: verificación contratos en explorador, guión demo blockchain
P3: revisión UI/UX final, ajustes responsive
P4: prueba bots en canales reales (Telegram, Discord)
Entregables
9/9 tests passing
docker compose up -d levanta TODO sin errores en máquina limpia
Seed data: 10 denuncias simuladas generando 2 clústeres detectables
README actualizado con guión de demo paso a paso
Screen recording de la demo como respaldo
Criterios de aceptación finales
Flujo completo ciudadano → DIVINCRI en < 60 segundos
Transacción real visible en explorador zkSYS Genesis Testnet
9/9 tests passing
docker compose up -d funciona en máquina limpia siguiendo INSTALL.md
Dashboard DIVINCRI muestra mapa de calor con datos de seed

Resumen de Distribución por Persona
Persona
Fases principales
Fases de apoyo
Entregables clave
P1 — Líder/Agentes
Fase 1, Fase 4 (NLP)
Fase 5
Grafo LangGraph completo, ontología, clustering
P2 — Blockchain
Fase 0, Fase 2
Fase 5
Contratos en zkSYS, sellado real, log auditado
P3 — Frontend/DApp
Fase 3B (Pali Wallet)
Fase 4 (mapa), Fase 5
DApp completa, mapa de calor
P4 — Bot/Canales
Fase 3A (bots)
Fase 5
WhatsApp + Telegram + Discord + STT
P5 — Backend/QA
Fase 0, Fase 5
Fases 1, 2, 4
Endpoints, DB migrations, 9/9 tests


IntelExtorsión — Plan de trabajo v1.0 · 20 jun 2026

