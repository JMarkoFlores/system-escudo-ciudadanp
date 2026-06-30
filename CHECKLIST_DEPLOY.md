# IntelExtorsión - Checklist de Despliegue

## Pre-Despliegue

- [ ] `GROQ_API_KEY` configurada y validada
- [ ] `PRIVATE_KEY` generada y almacenada en vault seguro
- [ ] `JWT_SECRET_KEY` generada (mínimo 32 caracteres) y almacenada en vault seguro
- [ ] Smart Contracts compilados (`npx hardhat compile`)
- [ ] Smart Contracts desplegados en zkSYS Tanenbaum Testnet (Chain ID 57057)
- [ ] Direcciones de contratos actualizadas en `.env`
- [ ] `WEB3_PROVIDER_URL` apunta a `https://rpc-zk.tanenbaum.io`
- [ ] `.env` copiado al servidor de producción
- [ ] Docker y Docker Compose instalados en servidor
- [ ] Puertos 3000, 3001, 3002, 8000, 8001, 5432, 6333, 6379 disponibles o configurados

## Infraestructura

- [ ] PostgreSQL 16+ corriendo
- [ ] Qdrant 1.9+ corriendo
- [ ] Redis 7+ corriendo
- [ ] Volúmenes Docker persistentes configurados
- [ ] Backups de PostgreSQL configurados

## Aplicación

- [ ] `docker compose build` exitoso (sin errores)
- [ ] `docker compose up -d` exitoso
- [ ] Todos los contenedores en estado `Up` o `Healthy`
- [ ] Agent System API responde en `:8000/health`
- [ ] Web3 Backend API responde en `:8001/health`
- [ ] Frontend accesible en `:3000`

## Web3

- [ ] Pali Wallet detectada en navegador
- [ ] Red zkSYS Tanenbaum Testnet (Chain ID 57057) configurada en wallet
- [ ] Contratos verificados en zkSYS Tanenbaum Explorer
- [ ] Backend wallet tiene TSYS nativo para gas fees

## Canales

- [ ] Bot de Telegram configurado y corriendo (si aplica)
- [ ] Bot de Discord configurado y corriendo (si aplica)
- [ ] WhatsApp Business API configurada (si aplica)

## Seguridad

- [ ] `PRIVATE_KEY` NO está en repositorio git
- [ ] `GROQ_API_KEY` NO está en repositorio git
- [ ] `JWT_SECRET_KEY` NO está en repositorio git
- [ ] `.env` está en `.gitignore`
- [ ] Firewall configurado (solo puertos necesarios abiertos)
- [ ] SSL/TLS configurado para dominio público
- [ ] Rate limiting activo en API Gateway
- [ ] Contraseñas de usuarios seed cambiadas en producción

## Notificaciones y Heatmap

- [ ] `ALERT_EMAIL_SMTP_*` configurado o deshabilitado si no aplica
- [ ] `ALERT_WEBHOOK_URL` configurado o deshabilitado si no aplica
- [ ] GeoJSON oficial del Plan Cuadrante PNP cargado en `app/data/plan_cuadrante_la_libertad.geojson`

## Tests y QA

- [ ] `docker compose build` exitoso (sin errores)
- [ ] `docker compose -f docker-compose.yml -f docker-compose.test.yml up test-runner` pasa 10/10 tests
- [ ] Tests de smart contracts (`npx hardhat test`) pasan

## Post-Despliegue

- [ ] Logs centralizados configurados
- [ ] Monitoreo de contenedores activo
- [ ] Alertas de uptime configuradas
- [ ] Primer flujo de denuncia end-to-end exitoso
- [ ] Primer registro de evidencia en blockchain exitoso
- [ ] Primer login en dashboard policial exitoso
- [ ] Primer envío de alerta push exitoso (si aplica)
