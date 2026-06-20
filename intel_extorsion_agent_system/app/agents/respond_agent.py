import secrets
import string
from typing import Dict, Any
from app.schemas.agent_schemas import AgenteState

def generate_tracking_code() -> str:
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(4))
    return f"TRJ-{suffix}"

async def node_respond(state: AgenteState) -> Dict[str, Any]:
    tracking_code = generate_tracking_code()

    if state.nivel_riesgo and state.nivel_riesgo.value in ["alto", "critico"]:
        mensaje = (
            f"✅ Denuncia registrada con código {tracking_code}. "
            f"Tu caso ha sido escalado a nuestra unidad de inteligencia. "
            f"Un oficial se comunicará contigo a la brevedad."
        )
    else:
        mensaje = (
            f"✅ Denuncia registrada con código {tracking_code}. "
            f"Puedes dar seguimiento usando este código. "
            f"Te contactaremos si necesitamos más información."
        )

    return {
        "resultado_respond": {
            "tracking_code": tracking_code,
            "mensaje_ciudadano": mensaje,
            "enviado": True
        },
        "tracking_code": tracking_code
    }
