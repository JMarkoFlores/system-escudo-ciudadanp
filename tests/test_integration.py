"""
Tests de integración end-to-end del sistema IntelExtorsión.

Ejecutar:
    docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

O directamente dentro del contenedor agent-api con pytest:
    pytest tests/test_integration.py -v
"""
import os
import time
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://agent-api:8000")
WEB3_API_URL = os.getenv("WEB3_API_URL", "http://web3-backend:8001")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(timeout=60.0) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    r = await client.post(
        f"{AGENT_API_URL}/v1/auth/login",
        data={"username": "admin", "password": "Admin123!"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Health & infraestructura
# ---------------------------------------------------------------------------
async def test_health_agent_api(client):
    r = await client.get(f"{AGENT_API_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["componentes"]["api"] == "ok"


async def test_health_web3_backend(client):
    r = await client.get(f"{WEB3_API_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["blockchain_connected"] is True


# ---------------------------------------------------------------------------
# Flujo ciudadano completo
# ---------------------------------------------------------------------------
async def test_crear_denuncia_texto(client):
    payload = {
        "canal": "web",
        "tipo_contenido": "texto",
        "contenido_raw": (
            "Me contactaron por WhatsApp desde el numero 999888777. "
            "Dicen que tienen a mi familiar secuestrado y piden 5000 soles de rescate. "
            "Amenazan con matarlo si llamo a la policia. No tengo familiares en esa zona."
        ),
        "metadata": {"user_agent": "pytest"},
    }
    r = await client.post(f"{AGENT_API_URL}/v1/denuncias", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "id" in data
    assert data["estado"] == "en_ingesta"
    assert data["tipo_contenido"] == "texto"


@pytest.mark.skipif(not GROQ_API_KEY, reason="Requiere GROQ_API_KEY")
async def test_procesar_denuncia_y_generar_tracking(client):
    # Crear denuncia
    payload = {
        "canal": "web",
        "tipo_contenido": "texto",
        "contenido_raw": (
            "Me contactaron por WhatsApp desde el numero 999888777. "
            "Dicen que tienen a mi familiar secuestrado y piden 5000 soles de rescate. "
            "Amenazan con matarlo si llamo a la policia. No tengo familiares en esa zona."
        ),
        "metadata": {},
    }
    r = await client.post(f"{AGENT_API_URL}/v1/denuncias", json=payload)
    denuncia_id = r.json()["id"]

    # Procesar síncrono
    r = await client.post(f"{AGENT_API_URL}/v1/denuncias/{denuncia_id}/procesar")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["estado_final"] in ("procesado", "riesgo_evaluado", "alerta_generada")
    assert data["tiempo_total_ms"] > 0
    assert data["resultados"]
    assert data["resultados"]["intake"]["valido"] is True


@pytest.mark.skipif(not GROQ_API_KEY, reason="Requiere GROQ_API_KEY")
async def test_tracking_por_codigo(client):
    payload = {
        "canal": "web",
        "tipo_contenido": "texto",
        "contenido_raw": (
            "Llamada extorsiva del numero 111222333 pidiendo depositar 2000 soles "
            "a una cuenta para no secuestrar a mi hermano."
        ),
        "metadata": {},
    }
    r = await client.post(f"{AGENT_API_URL}/v1/denuncias", json=payload)
    denuncia_id = r.json()["id"]

    r = await client.post(f"{AGENT_API_URL}/v1/denuncias/{denuncia_id}/procesar")
    data = r.json()
    tracking_code = None
    respond = data["resultados"].get("respond", {})
    tracking_code = respond.get("tracking_code")

    assert tracking_code and tracking_code.startswith("TRJ-")

    r = await client.get(f"{AGENT_API_URL}/v1/denuncias/tracking/{tracking_code}")
    assert r.status_code == 200, r.text
    denuncia = r.json()
    assert denuncia["tracking_code"] == tracking_code
    assert denuncia["estado"] == data["estado_final"]


# ---------------------------------------------------------------------------
# Dashboard policial
# ---------------------------------------------------------------------------
async def test_dashboard_metricas(client, auth_headers):
    r = await client.get(f"{AGENT_API_URL}/v1/dashboard/metricas", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "total_denuncias" in data
    assert "alertas_criticas" in data


async def test_listar_denuncias(client, auth_headers):
    r = await client.get(f"{AGENT_API_URL}/v1/denuncias", params={"limit": 5}, headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


async def test_listar_alertas(client, auth_headers):
    r = await client.get(f"{AGENT_API_URL}/v1/alertas", params={"limit": 5}, headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Web3 / Blockchain
# ---------------------------------------------------------------------------
async def test_web3_registrar_y_verificar_evidencia(client):
    tmp = Path("/tmp/test_evidence_integration.txt")
    tmp.write_text(f"evidencia de prueba {uuid.uuid4()}")

    r = await client.post(
        f"{WEB3_API_URL}/v1/evidencias",
        data={
            "did_denunciante": "did:web:intel.test:user1",
            "nivel_riesgo": "2",
            "metadata_uri": "ipfs://QmTest",
            "tipo_evidencia": "3",
        },
        files={"file": ("test.txt", tmp.open("rb"), "text/plain")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert data["tx_hash"].startswith("0x")
    evidence_hash = data["evidence_hash"]

    # Verificar on-chain
    for _ in range(10):
        r = await client.get(f"{WEB3_API_URL}/v1/evidencias/{evidence_hash}/verificar")
        if r.status_code == 200 and r.json()["exists"]:
            break
        time.sleep(2)
    else:
        pytest.fail("No se pudo verificar la evidencia on-chain")

    verify = r.json()
    assert verify["exists"] is True
    assert verify["evidence_id"] > 0
    assert verify["blockchain"] == "zksys_tanenbaum"


# ---------------------------------------------------------------------------
# Memoria semántica
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not GROQ_API_KEY, reason="Requiere GROQ_API_KEY")
async def test_busqueda_semantica(client):
    # Asegurar al menos un documento en memoria
    payload = {
        "canal": "web",
        "tipo_contenido": "texto",
        "contenido_raw": (
            "Secuestro virtual por WhatsApp pidiendo 5000 soles al numero 999888777"
        ),
        "metadata": {},
    }
    r = await client.post(f"{AGENT_API_URL}/v1/denuncias", json=payload)
    denuncia_id = r.json()["id"]
    await client.post(f"{AGENT_API_URL}/v1/denuncias/{denuncia_id}/procesar")

    # La búsqueda semántica puede tardar en indexar
    for _ in range(10):
        r = await client.get(
            f"{AGENT_API_URL}/v1/busqueda/semantica",
            params={"q": "secuestro virtual whatsapp", "limit": 5},
        )
        if r.status_code == 200 and r.json():
            break
        time.sleep(2)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "resultados" in data
        assert isinstance(data["resultados"], list)
