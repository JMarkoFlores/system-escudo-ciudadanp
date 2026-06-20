"""
Tests básicos del subsistema de agentes
"""
import pytest
from uuid import uuid4

from app.schemas.agent_schemas import AgenteState, CanalEntrada, TipoContenido
from app.agents.intake_agent import IntakeAgent
from app.agents.nlp_agent import NLPAgent
from app.agents.risk_agent import RiskAgent

@pytest.mark.asyncio
async def test_intake_agent_texto_simple():
    agent = IntakeAgent()
    state = AgenteState(
        denuncia_id=uuid4(),
        canal=CanalEntrada.WHATSAPP,
        tipo_contenido=TipoContenido.TEXTO,
        contenido_raw="Me están extorsionando con fotos. Depósitame a la cuenta 123456789 o las publico.",
        metadata={}
    )
    result = await agent.run(state)
    assert "resultado_intake" in result
    # No validamos valores exactos por no tener API key real en tests

@pytest.mark.asyncio
async def test_nlp_agent_consolida_texto():
    agent = NLPAgent()
    state = AgenteState(
        denuncia_id=uuid4(),
        canal=CanalEntrada.TELEGRAM,
        tipo_contenido=TipoContenido.TEXTO,
        contenido_raw="Si no me das 50000 pesos, le digo a tu familia lo que hiciste.",
        metadata={}
    )
    result = await agent.run(state)
    assert "resultado_nlp" in result

@pytest.mark.asyncio
async def test_risk_agent_integracion():
    agent = RiskAgent()
    state = AgenteState(
        denuncia_id=uuid4(),
        canal=CanalEntrada.DISCORD,
        tipo_contenido=TipoContenido.TEXTO,
        contenido_raw="Amenaza de muerte",
        metadata={},
        resultado_intake={"valido": True, "prioridad_inicial": 5},
        resultado_nlp={
            "score_amenaza": 0.95,
            "indicadores_extorsion": ["plazo", "monto", "violencia"],
            "resumen": "Amenaza directa con violencia"
        }
    )
    result = await agent.run(state)
    assert "resultado_riesgo" in result
    assert "nivel_riesgo" in result
