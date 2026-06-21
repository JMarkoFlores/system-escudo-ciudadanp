# 🚀 Handoff para Persona 3 (Frontend / DApp)

¡Hola equipo de Frontend (P3)! La fase 2 de Blockchain (P2) ha concluido con éxito. El backend Web3 ya está 100% operativo en la Testnet de zkSYS (Tanenbaum) y listo para ser consumido por la DApp y los canales externos.

Aquí tienes toda la información y artefactos que necesitas para tu desarrollo.

## 🔗 1. Configuración de Red (zkSYS Tanenbaum Testnet)

Para configurar la **Pali Wallet** y el provider de `ethers.js` en tu frontend, utiliza los siguientes parámetros:

- **Nombre de la Red:** zkSYS Tanenbaum Testnet
- **RPC URL:** `https://rpc-zk.tanenbaum.io`
- **Chain ID:** `57057`
- **Símbolo:** `tSYS`
- **Explorador:** `https://explorer-zk.tanenbaum.io`

Asegúrate de configurar estas variables en el `.env` de la carpeta `intel_extorsion_frontend`:
```env
NEXT_PUBLIC_RPC_URL=https://rpc-zk.tanenbaum.io
NEXT_PUBLIC_CHAIN_ID=57057
NEXT_PUBLIC_EXPLORER_URL=https://explorer-zk.tanenbaum.io
```

## 📜 2. Direcciones de los Smart Contracts

Los contratos ya fueron desplegados y verificados exitosamente. Agrega las siguientes direcciones a tu `.env` del Frontend:

```env
NEXT_PUBLIC_CONTRACT_DID_REGISTRY=0xbCC2969860098c922B7844A540F3525CF2eA09c3
NEXT_PUBLIC_CONTRACT_EVIDENCE_REGISTRY=0x9dAe55D2e43fD55Fb83C46Ca6aF8cA7614BE03C8
NEXT_PUBLIC_CONTRACT_CASE_MANAGER=0xA1210591a7e16E6720229DA6a9C598F1499854C5
NEXT_PUBLIC_CONTRACT_TOKEN=0x350e898a2166949717a6c1E000301d9F4dF66B65
```

## 🛠️ 3. ABIs Consolidados

Para instanciar los contratos en `ethers.js`, vas a necesitar los ABIs (Application Binary Interfaces). 
Ya los hemos extraído, actualizado (soportan OpenZeppelin v5 y Solidity 0.8.24) y limpiado para ti.

Puedes copiarlos desde la siguiente ruta hacia el frontend (`src/lib/abis` o similar):
📂 **Ubicación en el repositorio:** `intel_extorsion_web3_system/backend/app/services/abis/`
- `CaseManager.json`
- `DIDRegistry.json`
- `EvidenceRegistry.json`
- `IntelExtorsionToken.json`

## ⚙️ 4. Endpoints y Novedades del Backend Web3

El contenedor de `web3-backend` ya está robustecido con concurrencia (evita colisiones de *Nonce*) y preparado para escalar. Algunos endpoints clave que puedes utilizar desde el dashboard policial o la DApp:

- **Sellado directo de evidencia:** `POST /v1/evidencias/seal`
- **Creación de Casos en Blockchain:** El Agent API invoca internamente la creación del caso cuando el nivel de riesgo es ALTO/CRITICO.
- **Acta Forense PDF:** `GET /v1/evidencias/{evidence_id}/acta-pdf` 
  - Retorna un archivo Binario con Content-Type `application/pdf`. Contiene hash, bloque, timestamp, did y resumen del caso. Ideal para mostrar un botón "Descargar Acta" en el Frontend de Policía.
- **Log de Auditoría (Cron):** El log se sella automáticamente en blockchain cada 24 horas.

## ✅ Tus objetivos principales (Fase 3):

Según el `IMPLEMENTACION.md`, tu trabajo en la Fase 3 se centrará en:
1. **Separar/Estructurar el Frontend:** `frontend-citizen` (portal) vs `frontend-police` (dashboard).
2. **Integrar Pali Wallet:** Permitir al ciudadano firmar transacciones directamente.
3. **Canales Externos:** Colaborar con P4 (opcional/cruzado) para los bots de WhatsApp/Telegram.
4. **Subida Real:** Habilitar el multipart upload desde el Frontend hacia el Agent API.
5. **UI de Estado Blockchain:** Componentes de polling o SSE para ver cuándo una denuncia pasa de `PROCESANDO` a `SELLADA`.

¡Mucho éxito en la Fase 3! Si hay un error de conexión Web3, asegúrate de que el contenedor backend tiene la variable `WEB3_PROVIDER_URL` apuntando a `https://rpc-zk.tanenbaum.io`.
