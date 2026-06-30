# Resumen de Revisión Integral - IntelExtorsión

**Fecha de revisión:** 2026-06-30  
**Objetivo:** Auditar el sistema completo para garantizar una buena experiencia de usuario, detectar fallos, inconsistencias e incoherencias, y definir el plan de corrección.  
**Base:** `requerimientos.md`, `AGENTS.md`, `IMPLEMENTACION.md`, `FASE4_NLP_CLUSTERING_REPORT.md`, `HANDOFF_P3.md`, `RUN.md`, `INSTALL.md`, `CHECKLIST_DEPLOY.md`, `MANUAL_DENUNCIA.md`.

---

## 1. Estado General

El sistema está **operativo en Docker** con 8 contenedores corriendo:

| Servicio | Puerto | Estado |
|----------|--------|--------|
| Frontend Ciudadano | 3000 | Up |
| Frontend Policial | 3001 | Up |
| DApp Web3 | 3002 | Up |
| Agent API | 8000 | Healthy |
| Web3 Backend | 8001 | Healthy, conectado a blockchain |
| PostgreSQL | 5432 | Healthy |
| Qdrant | 6333 | Up |
| Redis | 6379 | Up |

Los flujos principales funcionan (crear denuncia → procesar con agentes → clustering → tracking code). Sin embargo, se detectaron **problemas críticos de consistencia, privacidad y bugs de integración** que deben corregirse antes de considerar el sistema "completo y bien hecho".

---

## 2. Hallazgos Críticos

### 2.1 Crisis de red blockchain
El proyecto no tiene una única red oficial:

| Fuente | Red declarada | Chain ID | RPC |
|--------|--------------|----------|-----|
| `.env.example` raíz | zkSYS Genesis Testnet | 5700 | `rpc.genesis.zksys.io` |
| `docker-compose.yml` (web3-backend) | zkSYS Genesis Testnet | 5700 | `rpc.genesis.zksys.io` |
| `docker-compose.yml` (frontends) | zkSYS Tanenbaum Testnet | 57057 | `rpc-zk.tanenbaum.io` |
| `intel_extorsion_web3_system/hardhat.config.js` | zkSYS Tanenbaum Testnet | 57057 | `rpc-zk.tanenbaum.io` |
| `intel_extorsion_web3_system/backend/app/config/settings.py` | zkSYS Genesis Testnet | 5700 | `rpc.genesis.zksys.io` |
| `intel_extorsion_frontend_citizen/src/stores/walletStore.ts` | zkSYS Tanenbaum Testnet | 57057 | `rpc-zk.tanenbaum.io` |
| `intel_extorsion_frontend_police/src/stores/walletStore.ts` | zkSYS Tanenbaum Testnet | 57057 | `rpc-zk.tanenbaum.io` |
| `intel_extorsion_web3_system/dapp/...` | zkSYS Genesis Testnet / Rollux | 5700 / 570 | `rpc.genesis.zksys.io` / `rpc.rollux.com` |
| `RUN.md`, `INSTALL.md`, `CHECKLIST_DEPLOY.md`, `MANUAL_DENUNCIA.md` | Syscoin Rollux Mainnet | 570 | `rpc.rollux.com` |

**Decisión tomada:** La red oficial del sistema es **zkSYS Tanenbaum Testnet (Chain ID 57057)** porque:
- Los contratos están desplegados y verificados en esa red.
- El Web3 Backend real está conectado a esa red (`block_number: ~2806`).
- Los frontends citizen/police ya están configurados para 57057.

Se unificará toda la codebase a esta red.

### 2.2 Bugs críticos en Web3 Backend
- `web3_service.py`: 6 funciones llaman `_send_transaction(func)` sin definir `func` (`transfer_custody`, `revoke_evidence`, `link_evidence_to_case`, `assign_officer`, `change_case_status`, `mint_achievement`).
- `verify_evidence_integrity` devuelve `on_chain_hash` como `bytes`, pero el schema espera `str`.
- Falta `GET /v1/evidencias/{hash}/verificar`; el agente llama a un endpoint 404.
- `hardhat.config.js` configura Etherscan con red `rollux` y explorer `explorer.rollux.com` para chain 57057.

### 2.3 Violaciones de privacidad y RF-01
- Los bots de WhatsApp, Telegram y Discord almacenan identificadores del denunciante en `metadata_json` (número, user_id, nombre, chat_id).
- **RF-01 no está implementado**: no hay menú de clasificación de dos niveles ni redirección a Inspectoría/Fiscalía para denuncias contra funcionarios públicos o policías.

### 2.4 Alertas distorsionadas
- El `Alert Agent` no devuelve el campo `nivel`, por lo que `_persistir_alerta` guarda todas las alertas como `medio`.

### 2.5 Problemas de frontend
- `tracking/page.tsx` usa `http://localhost:8000` hardcodeado.
- La DApp no recibe variables `VITE_*` en build (Dockerfile sin `ARG`/`ENV`).
- Explorer en tracking apunta a `explorer.genesis.zksys.io` en lugar de Tanenbaum.
- Login policial es simulado.

### 2.6 Infraestructura y documentación
- No hay migraciones Alembic; se usa `Base.metadata.create_all()`.
- Redis y PostgreSQL expuestos sin autenticación fuerte.
- Los `.md` de guía (`RUN.md`, `INSTALL.md`, etc.) están desactualizados (Rollux 570, un solo frontend).
- `AGENTS.md` no refleja el estado post-Fase 4 ni los frontends separados.

---

## 3. Plan de Corrección (Priorizado)

### Fase A - Unificación blockchain (crítico)
1. Unificar red oficial a **zkSYS Tanenbaum Testnet (57057, `rpc-zk.tanenbaum.io`, `explorer-zk.tanenbaum.io`)**.
2. Actualizar `.env.example`, `docker-compose.yml`, `AGENTS.md`, `RUN.md`, `INSTALL.md`, `CHECKLIST_DEPLOY.md`, `MANUAL_DENUNCIA.md`.
3. Actualizar `web3 backend settings.py`, `agent system seal_agent.py`, `hardhat.config.js`.
4. Actualizar DApp (`usePaliWallet.js`, `contractService.js`, `Dockerfile`, `.env.example`).
5. Actualizar frontends citizen/police `.env.example`.
6. Actualizar frontend legacy `walletStore.ts`.

### Fase B - Corrección bugs Web3
1. Corregir `NameError` en `web3_service.py`.
2. Convertir `on_chain_hash` a hex en `verify_evidence_integrity`.
3. Implementar `GET /v1/evidencias/{hash}/verificar`.
4. Corregir `web3_client.py` del agente para usar verify correcto.
5. Corregir `hardhat.config.js` customChains.

### Fase C - Privacidad y RF-01
1. Implementar menú de clasificación en WhatsApp, Telegram y Discord.
2. Redirigir denuncias contra funcionarios/policías sin persistir en DB de evidencia.
3. Eliminar PII de `metadata_json`; usar solo `session_id` anónimo/hash.

### Fase D - Agentes
1. Corregir `respond_agent.py` para código de 8 caracteres y mensaje neutral.
2. Actualizar prompt del `Alert Agent` para devolver `nivel`.
3. Propagar `nivel_riesgo` real en `_persistir_alerta`.
4. Robustecer manejo de errores del LLM en `main_api.py`.
5. Restringir CORS a orígenes conocidos.

### Fase E - Frontend
1. Usar `agentApi` en `tracking/page.tsx`.
2. Unificar explorer a Tanenbaum.
3. Pasar `VITE_*` y `NEXT_PUBLIC_*` como build args en Docker.

### Fase F - Tests y documentación
1. Crear `tests/test_integration.py` actualizado.
2. Corregir test de DIDRegistry en Hardhat.
3. Actualizar `AGENTS.md` con estado post-revisión.
4. Actualizar `CHECKLIST_DEPLOY.md` con red y puertos correctos.

### Fase G - Funcionalidades mayores (post-revisión)
1. Implementar autenticación JWT en dashboard policial.
2. Configurar Alembic para migraciones.
3. Implementar alertas push (webhook/email).
4. Integrar mapa de calor con GeoJSON Plan Cuadrante PNP.

---

## 4. Criterios de Aceptación Final

- [x] Toda la codebase apunta a **zkSYS Tanenbaum Testnet (57057)**.
- [x] Web3 Backend endpoints críticos funcionan sin `NameError` ni `ValidationError`.
- [x] Los canales no almacenan PII y redirigen denuncias contra funcionarios/policías.
- [x] Las alertas se persisten con el nivel de riesgo real.
- [x] El frontend citizen consulta tracking correctamente y apunta al explorer correcto.
- [x] `docker compose up -d` levanta todo sin errores.
- [x] Tests de integración pasan (**10/10**).
- [x] Autenticación JWT funcional en frontend policial.
- [x] Mapa de calor con Plan Cuadrante PNP disponible.
- [x] Notificaciones push de alertas implementadas (webhook/email).
- [ ] Documentación restante (`RUN.md`, `INSTALL.md`, `CHECKLIST_DEPLOY.md`, `MANUAL_DENUNCIA.md`) pendiente de actualización.

---

## 5. Resumen de Cambios Aplicados (2026-06-30)

| Área | Cambio |
|------|--------|
| Blockchain | Unificación total a zkSYS Tanenbaum Testnet (57057). Contratos reales desplegados. |
| Web3 Backend | Fix `NameError`, verificación por hash, endpoint `/v1/evidencias/{hash}/verificar`. |
| Canales | RF-01 implementado; PII eliminado de WhatsApp, Telegram y Discord. |
| Agentes | `MockLLM`, manejo de errores, tracking code de 8 caracteres, alertas con nivel real. |
| Auth | JWT en Agent API; login/logout real en frontend policial. |
| BD | Alembic configurado; tabla `usuarios` con roles seed. |
| Notificaciones | Servicio de alertas push con webhook HTTP y email SMTP. |
| Heatmap | GeoJSON `plan_cuadrante_la_libertad.geojson` + endpoint `/v1/heatmap/cuadrantes`. |
| Tests | `tests/test_integration.py` con 10 tests end-to-end, todos verdes en Docker. |
| Docs | Actualizados `AGENTS.md`, `.env.example`, `RESUMEN_REVISION.md`. |

---

*Documento vivo. Pendiente: actualizar `RUN.md`, `INSTALL.md`, `CHECKLIST_DEPLOY.md`, `MANUAL_DENUNCIA.md` y `QA_REPORT.md` con el estado post-revisión.*
