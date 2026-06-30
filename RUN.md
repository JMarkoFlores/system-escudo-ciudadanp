# IntelExtorsión - Guía de Ejecución

## Iniciar el Sistema

### Modo Docker (Recomendado)

```bash
# Desde la raíz del proyecto
docker compose up -d
```

Servicios disponibles:
- **Frontend Ciudadano:** http://localhost:3000
- **Frontend Policial:** http://localhost:3001
- **DApp Web3:** http://localhost:3002
- **Agent System API:** http://localhost:8000/docs
- **Web3 Backend API:** http://localhost:8001/docs
- **PostgreSQL:** localhost:5432
- **Qdrant:** http://localhost:6333/dashboard
- **Redis:** localhost:6379

---

## Detener el Sistema

```bash
# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (datos de BD)
docker compose down -v

# Detener un servicio específico
docker compose stop agent-api
```

---

## Reiniciar el Sistema

```bash
# Reinicio completo
docker compose restart

# Reinicio de un servicio específico
docker compose restart agent-api

# Rebuild + reinicio (después de cambios de código)
docker compose up -d --build
```

---

## Ejecutar Agentes

### Vía API REST

```bash
# Crear una denuncia y ejecutar el grafo automáticamente
curl -X POST http://localhost:8000/v1/denuncias \
  -H "Content-Type: application/json" \
  -d '{
    "canal": "web",
    "tipo_contenido": "texto",
    "contenido_raw": "Me están extorsionando, me piden dinero o publican fotos"
  }'

# Re-procesar una denuncia existente
curl -X POST http://localhost:8000/v1/denuncias/{id}/procesar \
  -H "Content-Type: application/json" \
  -d '{"modo": "completo"}'
```

### Vía Portal Web

1. Abrir http://localhost:3000/portal
2. Seleccionar canal (WhatsApp/Telegram/Discord/Web)
3. Escribir la denuncia en el chat
4. Click en "Enviar"

---

## Iniciar Canales de Denuncia (Bots de Telegram, Discord y WhatsApp)

El sistema de agentes (`agent-api`) levanta e integra automáticamente los canales conversacionales si sus respectivos tokens están configurados en el archivo `.env`.

### 1. Telegram
- El bot de Telegram inicia de forma nativa e integrada en segundo plano dentro de `agent-api`.
- Solo requiere configurar `TELEGRAM_BOT_TOKEN` en el `.env`.

### 2. Discord
- El bot de Discord inicia en segundo plano dentro de `agent-api`.
- Requiere configurar `DISCORD_BOT_TOKEN` en el `.env` y activar los **"Privileged Gateway Intents"** en el Discord Developer Portal (especialmente *Message Content Intent*).

### 3. WhatsApp (Whapi.cloud)
El canal de WhatsApp requiere redirigir las solicitudes webhook de Whapi hacia tu servidor local mediante un túnel como **ngrok**:

1. Configura `WHATSAPP_API_TOKEN` en el `.env`.
2. Inicia tu túnel local exponiendo el puerto `8000`:
   ```bash
   ngrok http 8000
   # O si tienes un dominio reservado:
   ngrok http --url=tu-dominio-reservado.ngrok-free.dev 8000
   ```
3. Copia la URL pública generada (ej. `https://xxxx.ngrok-free.dev`).
4. Ve al dashboard de **Whapi.cloud** y configura la URL del Webhook a:
   `https://xxxx.ngrok-free.dev/v1/channels/whatsapp/webhook`
5. Activa los eventos de **messages** y guarda los cambios.

---

## Iniciar Blockchain Local (Desarrollo)

```bash
cd intel_extorsion_web3_system

# Iniciar nodo local Hardhat
npx hardhat node

# En otra terminal, deploy contratos
npx hardhat run scripts/deploy.js --network localhost
```

---

## Autenticación en el Dashboard Policial

El frontend policial (`http://localhost:3001`) ahora requiere autenticación JWT.

### Usuarios seed (demo)
| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | Admin123! | admin |
| supervisor | Super123! | supervisor |
| analista | Analista123! | analista |

### Login vía API
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"
```

### Acceder a endpoints protegidos
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!" | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/denuncias?limit=5
```

---

## Acceder al Dashboard

### Dashboard Policial
```
http://localhost:3001/dashboard/policial
```
- Requiere login JWT
- Muestra KPIs, denuncias recientes, estados

### Dashboard Analítico
```
http://localhost:3001/dashboard/analitico
```
- Gráficos de actividad semanal
- Distribución por canal y riesgo

### Redes Criminales
```
http://localhost:3001/dashboard/grafos
```
- Visualización interactiva de grafos
- Nodos: denunciantes, sospechosos, teléfonos, cuentas

### Centro de Alertas
```
http://localhost:3001/dashboard/alertas
```
- Alertas por nivel: bajo, medio, alto, crítico
- Acciones: marcar leída, atender

---

## Conectar Pali Wallet

1. Instalar extensión Pali Wallet desde https://paliwallet.com
2. Crear o importar una wallet
3. Cambiar red a **zkSYS Tanenbaum Testnet** (Chain ID 57057)
   - Si no aparece, agregar manualmente:
     - RPC: `https://rpc-zk.tanenbaum.io`
     - Chain ID: `57057`
     - Símbolo: `TSYS`
     - Explorer: `https://explorer-zk.tanenbaum.io`
4. En el frontend, click en "Conectar Pali Wallet"
5. Aprobar la conexión en la extensión

---

## Mapa de Calor / Plan Cuadrante PNP

```bash
# GeoJSON base de cuadrantes (La Libertad)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/heatmap/cuadrantes

# Heatmap con denuncias agregadas por cuadrante
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/v1/heatmap?periodo=30"
```

---

## Notificaciones Push de Alertas

Configura en `.env`:
```bash
ALERT_WEBHOOK_URL=https://tuservidor.com/webhook
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_SMTP_USER=alertas@example.com
ALERT_EMAIL_SMTP_PASSWORD=********
ALERT_EMAIL_FROM=alertas@example.com
ALERT_EMAIL_TO=supervisor@divincri.gob.pe,analista@divincri.gob.pe
```

Cada vez que se persiste una alerta oficial (riesgo alto/crítico), el sistema envía el payload al webhook y un email a los destinatarios configurados.

---

## Tests

```bash
# Tests de integración end-to-end en Docker (usa MOCK_LLM=true)
docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner --build --abort-on-container-exit

# Tests de smart contracts
cd intel_extorsion_web3_system
npx hardhat test
```

**Resultado esperado:** 10/10 tests de integración pasan.

---

## Logs y Monitoreo

```bash
# Ver logs de un servicio
docker logs -f intel_extorsion_agent_api
docker logs -f intel_extorsion_web3_backend
docker logs -f intel_extorsion_frontend_citizen
docker logs -f intel_extorsion_frontend_police
docker logs -f intel_extorsion_dapp

# Ver logs de todos los servicios
docker compose logs -f

# Estado de recursos
docker stats
```

---

## Comandos Útiles

```bash
# Acceder a PostgreSQL
docker exec -it intel_extorsion_postgres psql -U agent_user -d intel_extorsion

# Acceder a Redis CLI
docker exec -it intel_extorsion_redis redis-cli

# Ver colecciones Qdrant
curl http://localhost:6333/collections

# Reiniciar solo la base de datos
docker compose restart postgres

# Limpiar imágenes Docker no usadas
docker image prune -a
```

---

*Guía generada por el equipo de Arquitectura de IntelExtorsión.*
