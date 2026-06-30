from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState
from app.services import web3_client

async def node_seal(state: AgenteState) -> Dict[str, Any]:
    if "seal" in state.saltar_agentes:
        return {"resultado_seal": None}

    if state.nivel_riesgo and state.nivel_riesgo.value not in ["alto", "critico"]:
        return {
            "resultado_seal": {
                "sellado": False,
                "motivo": f"Riesgo {state.nivel_riesgo.value} no requiere sellado blockchain"
            }
        }

    content_hash = state.content_hash
    if not content_hash and state.contenido_raw:
        content_hash = web3_client.compute_content_hash(
            state.contenido_raw,
            state.metadata
        )

    if not content_hash:
        return {
            "resultado_seal": {
                "sellado": False,
                "error": "No hay contenido para generar hash"
            }
        }

    case_id = int(str(state.denuncia_id).replace("-", "")[:8], 16) % 1000000

    response = await web3_client.seal_evidence(
        content_hash=content_hash,
        case_id=case_id
    )

    tx_hash = response.get("tx_hash")
    block_number = response.get("block_number")
    success = response.get("success", False)
    seal_status = "sellado" if success else "pendiente"

    return {
        "resultado_seal": {
            "sellado": success,
            "tx_hash": tx_hash,
            "block_number": block_number,
            "red": "zkSYS Tanenbaum Testnet",
            "content_hash": content_hash,
            "case_id": case_id
        },
        "seal_tx_hash": tx_hash,
        "seal_block": block_number,
        "seal_status": seal_status,
        "content_hash": content_hash
    }
