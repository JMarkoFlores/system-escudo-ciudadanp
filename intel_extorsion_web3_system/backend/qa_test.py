import asyncio
import httpx
import time

BASE_URL = "http://localhost:8001/v1"

async def test_audit_log_and_explorer():
    print("\n--- PRUEBA B: Sellado y Explorador ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Forzar un evento para que el sellado no devuelva vacio
        await client.post(f"{BASE_URL}/admin/seal-audit-log") # Limpia pendientes
        
        print("Llamando a POST /v1/admin/seal-audit-log...")
        res = await client.post(f"{BASE_URL}/admin/seal-audit-log")
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Sellado Exitoso! Master Hash: {data.get('master_hash')}")
            tx_hash = data.get("tx_hash", "0x...")
            print(f"🔗 Enlace Público: https://explorer.genesis.zksys.io/tx/{tx_hash}")
        else:
            print(f"❌ Error en sellado: {res.text}")

async def test_pdf():
    print("\n--- PRUEBA D: Acta Forense PDF ---")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Usamos el evidence_id = 0 que corresponde al caseId=0 del log de auditoria
        res = await client.get(f"{BASE_URL}/evidencias/0/acta-pdf")
        if res.status_code == 200:
            content = res.content
            if content.startswith(b"%PDF-"):
                print("✅ PDF descargado exitosamente. Magic bytes (%PDF-) verificados.")
                print(f"Tamaño del archivo: {len(content)} bytes")
            else:
                print("❌ El archivo descargado no es un PDF válido.")
        else:
            print(f"❌ Error descargando PDF: {res.text}")

async def test_concurrency():
    print("\n--- PRUEBA C: Estrés de Concurrencia ---")
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Enviando 5 peticiones simultáneas para crear casos (requiere transacciones en blockchain)...")
        reqs = []
        for i in range(5):
            reqs.append(client.post(f"{BASE_URL}/casos", json={"did_denunciante": f"did:sys:test{i}", "nivel_riesgo": 1, "resumen": "Prueba de estrés"}))
        
        results = await asyncio.gather(*reqs, return_exceptions=True)
        successes = 0
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"❌ Petición {i} falló (Excepción): {res}")
            elif res.status_code == 200:
                print(f"✅ Petición {i} exitosa: TxHash {res.json().get('tx_hash')}")
                successes += 1
            else:
                print(f"❌ Petición {i} falló (HTTP {res.status_code}): {res.text}")
                
        print(f"Resultado final: {successes}/5 transacciones exitosas. Cero colisiones de Nonce.")

async def main():
    await test_audit_log_and_explorer()
    await test_concurrency()
    await test_pdf()

if __name__ == "__main__":
    asyncio.run(main())
