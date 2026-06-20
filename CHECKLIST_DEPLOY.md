# IntelExtorsión - Checklist de Despliegue

## Pre-Despliegue

- [ ] `GROQ_API_KEY` configurada y validada
- [ ] `PRIVATE_KEY` generada y almacenada en vault seguro
- [ ] Smart Contracts compilados (`npx hardhat compile`)
- [ ] Smart Contracts desplegados en Rollux Mainnet/Testnet
- [ ] Direcciones de contratos actualizadas en `.env`
- [ ] `.env` copiado al servidor de producción
- [ ] Docker y Docker Compose instalados en servidor
- [ ] Puertos 3000, 8000, 8001, 5432, 6333, 6379 disponibles o configurados

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
- [ ] Red Rollux (Chain ID 570) configurada en wallet
- [ ] Contratos verificados en Rollux Explorer
- [ ] Backend wallet tiene SYS nativo para gas fees

## Canales

- [ ] Bot de Telegram configurado y corriendo (si aplica)
- [ ] Bot de Discord configurado y corriendo (si aplica)
- [ ] WhatsApp Business API configurada (si aplica)

## Seguridad

- [ ] `PRIVATE_KEY` NO está en repositorio git
- [ ] `GROQ_API_KEY` NO está en repositorio git
- [ ] `.env` está en `.gitignore`
- [ ] Firewall configurado (solo puertos necesarios abiertos)
- [ ] SSL/TLS configurado para dominio público
- [ ] Rate limiting activo en API Gateway

## Post-Despliegue

- [ ] Logs centralizados configurados
- [ ] Monitoreo de contenedores activo
- [ ] Alertas de uptime configuradas
- [ ] Primer flujo de denuncia end-to-end exitoso
- [ ] Primer registro de evidencia en blockchain exitoso
