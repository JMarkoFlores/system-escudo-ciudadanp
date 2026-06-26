import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.web3_service import web3_service
from app.config.settings import settings
import hashlib

denuncias = [
    ("01446b78-76e2-434d-a0aa-c0f11bff7d60", "Me enviaron una foto de mi casa tomada desde la calle con un mensaje que dice: Sabemos donde vives, paga 10,000 soles o te pasamos visita"),
    ("6c069f54-3b7a-4d52-8a1c-b1a7cab71d7c", "Extorsion telefonica con amenaza de secuestro de mi hija del colegio"),
    ("7dc2f86c-2ffd-4be1-8de2-e266a3c39dee", "Amenazas por WhatsApp con foto de mi casa tomada desde la calle"),
    ("76bb7798-d4ea-44fa-8e79-ae8c5281662a", "Extorsion con amenaza de violencia y numero de telefono desconocido"),
]

for did, content in denuncias:
    content_hash = "0x" + hashlib.sha256(content.encode()).hexdigest()
    case_id = int(did.replace("-", "")[:8], 16) % 1000000
    result = web3_service.seal_evidence_by_hash(content_hash, case_id)
    tx = result.get("tx_hash", "N/A")
    block = result.get("block_number", "N/A")
    success = result.get("success", False)
    print(f"{did[:8]} tx={tx[:30]}... block={block} success={success}")
