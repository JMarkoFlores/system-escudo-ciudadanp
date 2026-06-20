# IntelExtorsión - Guía de API Keys y Secretos

## Resumen

Este documento lista **TODAS** las API Keys, tokens y secretos necesarios para ejecutar IntelExtorsión en producción.

> **ADVERTENCIA:** Ninguna API Key es opcional para producción. Las marcadas como "Opcional" solo funcionan en modo desarrollo/demo.

---

## 1. GroqCloud API Key

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `GROQ_API_KEY` |
| **Propósito** | Alimenta los 8 agentes autónomos (Intake, OCR, Speech, NLP, Correlation, OSINT, Risk, Alert) |
| **Obligatoria** | **SÍ** |
| **URL oficial** | https://console.groq.com/keys |
| **Pasos para obtenerla** | 1. Crear cuenta en GroqCloud<br>2. Ir a API Keys<br>3. Click "Create API Key"<br>4. Copiar el valor (empieza con `gsk_`) |
| **Costo estimado** | Gratis hasta ciertos límites, luego ~$0.005-$0.01 por denuncia |
| **Modelo recomendado** | `llama-3.3-70b-versatile` |
| **Ejemplo** | `GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| **Nota embeddings** | Los embeddings ahora son locales (sentence-transformers/all-MiniLM-L6-v2). No requieren API key. |

---

## 2. Syscoin Rollux (Blockchain)

### 2.1 Private Key (Backend Wallet)

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `PRIVATE_KEY` |
| **Propósito** | Firma transacciones en la blockchain (registro de evidencias, casos, custodia) |
| **Obligatoria** | **SÍ** (para funcionalidad Web3) |
| **URL oficial** | https://paliwallet.com / https://rollux.com |
| **Pasos para obtenerla** | 1. Instalar Pali Wallet<br>2. Crear nueva wallet<br>3. Exportar private key (0x...)<br>4. **EN PRODUCCIÓN:** usar AWS KMS o HSM |
| **Advertencia** | **NUNCA** compartir esta clave. Usar vault en producción. |
| **Ejemplo** | `PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef` |

### 2.2 RPC URL

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `WEB3_PROVIDER_URL` |
| **Propósito** | Conexión al nodo RPC de Syscoin Rollux |
| **Obligatoria** | **SÍ** (para funcionalidad Web3) |
| **URL Mainnet** | `https://rpc.rollux.com` |
| **URL Testnet** | `https://rpc-testnet.rollux.com` |
| **Ejemplo** | `WEB3_PROVIDER_URL=https://rpc.rollux.com` |

### 2.3 Contract Addresses (post-deploy)

| Nombre variable | Propósito | Obligatoria |
|-----------------|-----------|-------------|
| `CONTRACT_EVIDENCE_REGISTRY` | Dirección del contrato EvidenceRegistry | SÍ |
| `CONTRACT_CASE_MANAGER` | Dirección del contrato CaseManager | SÍ |
| `CONTRACT_DID_REGISTRY` | Dirección del contrato DIDRegistry | SÍ |
| `CONTRACT_TOKEN` | Dirección del contrato IntelExtorsionToken | SÍ |

**Cómo obtener:** Después de ejecutar `npx hardhat run scripts/deploy.js --network rollux`, las direcciones se guardan en `deployments/addresses.json`.

---

## 3. IPFS (Pinata)

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `IPFS_JWT` |
| **Propósito** | Almacenar archivos de evidencia en IPFS de forma permanente |
| **Obligatoria** | Opcional (sin ella usa hashes simulados para desarrollo) |
| **URL oficial** | https://pinata.cloud |
| **Pasos para obtenerla** | 1. Crear cuenta en Pinata<br>2. Ir a API Keys<br>3. Generar JWT de acceso |
| **Ejemplo** | `IPFS_JWT=eyJhbGciOiJIUzI1NiIs...` |

---

## 4. Infraestructura Base

### 4.1 PostgreSQL

| Nombre variable | Valor por defecto | Descripción |
|-----------------|-------------------|-------------|
| `POSTGRES_USER` | `agent_user` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `agent_pass` | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `intel_extorsion` | Nombre de la base de datos |

### 4.2 Qdrant

| Nombre variable | Valor por defecto | Descripción |
|-----------------|-------------------|-------------|
| `QDRANT_HOST` | `localhost` | Host del servidor Qdrant |
| `QDRANT_PORT` | `6333` | Puerto de Qdrant |

### 4.3 Redis

| Nombre variable | Valor por defecto | Descripción |
|-----------------|-------------------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | URL de conexión Redis |

---

## 5. Canales de Denuncia (Bots)

### 5.1 WhatsApp Business API

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `WHATSAPP_API_TOKEN` |
| **Propósito** | Autenticación con WhatsApp Business API |
| **Obligatoria** | Sí (para canal WhatsApp) |
| **URL oficial** | https://business.facebook.com/products/whatsapp-business-platform |
| **Pasos** | 1. Crear cuenta Business Manager<br>2. Registrar número de teléfono<br>3. Obtener Permanent Access Token |

### 5.2 Telegram Bot

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `TELEGRAM_BOT_TOKEN` |
| **Propósito** | Autenticación del bot de Telegram |
| **Obligatoria** | Sí (para canal Telegram) |
| **URL oficial** | https://core.telegram.org/bots |
| **Pasos** | 1. Hablar con @BotFather en Telegram<br>2. Enviar `/newbot`<br>3. Copiar el token provisto |
| **Ejemplo** | `TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |

### 5.3 Discord Bot

| Atributo | Valor |
|----------|-------|
| **Nombre variable** | `DISCORD_BOT_TOKEN` |
| **Propósito** | Autenticación del bot de Discord |
| **Obligatoria** | Sí (para canal Discord) |
| **URL oficial** | https://discord.com/developers/applications |
| **Pasos** | 1. Crear aplicación en Discord Developer Portal<br>2. Ir a Bot > Add Bot<br>3. Copiar el token |
| **Ejemplo** | `DISCORD_BOT_TOKEN=MTAxMjM0NTY3ODkw.abcdef.ghijklmnop` |

---

## 6. Pali Wallet (Frontend)

| Atributo | Valor |
|----------|-------|
| **Requisito** | Extensión de navegador |
| **URL oficial** | https://paliwallet.com |
| **Pasos** | 1. Instalar extensión Chrome/Firefox<br>2. Crear o importar wallet<br>3. Cambiar red a Syscoin Rollux (Chain ID 570) |
| **Nota** | No requiere API Key. La wallet es del usuario final. |

---

## Checklist de Configuración

```
[ ] GROQ_API_KEY configurada
[ ] PRIVATE_KEY generada y segura
[ ] Smart Contracts desplegados en Rollux
[ ] CONTRACT_* addresses configuradas
[ ] IPFS_JWT obtenido (opcional para dev)
[ ] PostgreSQL corriendo
[ ] Qdrant corriendo
[ ] Redis corriendo
[ ] TELEGRAM_BOT_TOKEN obtenido (si se usa Telegram)
[ ] DISCORD_BOT_TOKEN obtenido (si se usa Discord)
[ ] WHATSAPP_API_TOKEN obtenido (si se usa WhatsApp)
[ ] Pali Wallet instalada en navegador de prueba
```

---

*Documento generado por el equipo de Arquitectura de IntelExtorsión.*
