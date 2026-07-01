from typing import Dict, Any, List
import json
import hashlib
from app.schemas.agent_schemas import AgenteState
from app.services import web3_client


def _collect_evidence_hashes(state: AgenteState) -> List[Dict[str, Any]]:
    """
    Recopila TODOS los hashes de evidencia de la denuncia:
    1. Hash del texto contenido_raw
    2. Hash del archivo principal (hash_archivo)
    3. Hashes de archivos adicionales (metadata_json['archivos_adicionales'])
    Retorna lista de {hash, tipo, filename}
    """
    evidences = []

    # 1. Hash del contenido de texto
    if state.contenido_raw:
        text_hash = web3_client.compute_content_hash(
            state.contenido_raw, state.metadata
        )
        evidences.append({
            "hash": text_hash,
            "tipo": "texto",
            "filename": "contenido_denuncia.txt",
        })

    # 2. Archivo principal
    if state.hash_archivo:
        evidences.append({
            "hash": state.hash_archivo,
            "tipo": state.tipo_contenido or "archivo",
            "filename": "evidencia_principal",
        })

    # 3. Archivos adicionales del metadata_json
    archivos_adicionales = (state.metadata or {}).get("archivos_adicionales", [])
    for archivo in archivos_adicionales:
        sha = archivo.get("sha256")
        if sha:
            evidences.append({
                "hash": sha,
                "tipo": archivo.get("tipo", "archivo"),
                "filename": archivo.get("filename", "evidencia_adjunta"),
            })

    return evidences


async def node_seal(state: AgenteState) -> Dict[str, Any]:
    if "seal" in state.saltar_agentes:
        return {"resultado_seal": None}

    if state.nivel_riesgo and state.nivel_riesgo.value not in ["alto", "critico"]:
        return {
            "resultado_seal": {
                "sellado": False,
                "total_evidencias": 0,
                "sellados_exitosos": 0,
                "motivo": f"Riesgo {state.nivel_riesgo.value} no requiere sellado blockchain"
            }
        }

    evidences = _collect_evidence_hashes(state)

    if not evidences:
        return {
            "resultado_seal": {
                "sellado": False,
                "total_evidencias": 0,
                "sellados_exitosos": 0,
                "error": "No hay evidencias para sellar"
            }
        }

    case_id = int(str(state.denuncia_id).replace("-", "")[:8], 16) % 1000000

    seal_results: List[Dict[str, Any]] = []
    first_tx_hash = None
    first_block = None

    for ev in evidences:
        response = await web3_client.seal_evidence(
            content_hash=ev["hash"],
            case_id=case_id
        )
        tx_hash = response.get("tx_hash")
        block_number = response.get("block_number")
        success = response.get("success", False)

        seal_entry = {
            "hash": ev["hash"],
            "tipo": ev["tipo"],
            "filename": ev["filename"],
            "tx_hash": tx_hash,
            "block_number": block_number,
            "success": success,
            "red": "zkSYS Tanenbaum Testnet",
        }
        seal_results.append(seal_entry)

        if success and first_tx_hash is None:
            first_tx_hash = tx_hash
            first_block = block_number

    sellados_exitosos = sum(1 for s in seal_results if s["success"])

    return {
        "resultado_seal": {
            "sellado": sellados_exitosos > 0,
            "total_evidencias": len(evidences),
            "sellados_exitosos": sellados_exitosos,
            "case_id": case_id,
            "seal_results": seal_results,
            "red": "zkSYS Tanenbaum Testnet",
        },
        "seal_tx_hash": first_tx_hash,
        "seal_block": first_block,
        "seal_status": "sellado" if sellados_exitosos > 0 else "pendiente",
        "content_hash": evidences[0]["hash"] if evidences else None,
    }
