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
