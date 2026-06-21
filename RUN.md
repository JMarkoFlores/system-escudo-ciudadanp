# IntelExtorsión - Guía de Ejecución

## Iniciar el Sistema

### Modo Docker (Recomendado)

```bash
# Desde la raíz del proyecto
docker compose up -d
```

Servicios disponibles:
- **Frontend:** http://localhost:3000
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

## Acceder al Dashboard

### Dashboard Policial
```
http://localhost:3000/dashboard/policial
```
- Requiere acceso policial
- Muestra KPIs, denuncias recientes, estados

### Dashboard Analítico
```
http://localhost:3000/dashboard/analitico
```
- Gráficos de actividad semanal
- Distribución por canal y riesgo

### Redes Criminales
```
http://localhost:3000/dashboard/grafos
```
- Visualización interactiva de grafos
- Nodos: denunciantes, sospechosos, teléfonos, cuentas

### Centro de Alertas
```
http://localhost:3000/dashboard/alertas
```
- Alertas por nivel: bajo, medio, alto, crítico
- Acciones: marcar leída, atender

---

## Conectar Pali Wallet

1. Instalar extensión Pali Wallet desde https://paliwallet.com
2. Crear o importar una wallet
3. Cambiar red a **Syscoin Rollux Mainnet** (Chain ID 570)
   - Si no aparece, agregar manualmente:
     - RPC: `https://rpc.rollux.com`
     - Chain ID: `570`
     - Símbolo: `SYS`
4. En el frontend, click en "Conectar Pali Wallet"
5. Aprobar la conexión en la extensión

---

## Logs y Monitoreo

```bash
# Ver logs de un servicio
docker logs -f intel_extorsion_agent_api
docker logs -f intel_extorsion_web3_backend
docker logs -f intel_extorsion_frontend

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
