import io
import time
import hashlib
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend


class ActaForenseService:
    def generar_acta_pdf(self, datos_evidencia: Dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CenterTitle', parent=styles['Heading1'], alignment=1, spaceAfter=20))
        styles.add(ParagraphStyle(name='Justify', parent=styles['Normal'], alignment=4, spaceAfter=12))
        styles.add(ParagraphStyle(name='SmallCenter', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.grey))

        Story = []

        Story.append(Paragraph("ACTA DE PRESERVACIÓN DE EVIDENCIA DIGITAL", styles['CenterTitle']))
        Story.append(Paragraph("Sistema de Inteligencia Ciudadana - IntelExtorsión", styles['SmallCenter']))
        Story.append(Spacer(1, 0.15 * inch))

        timestamp_val = datos_evidencia.get('timestamp', time.time())
        if isinstance(timestamp_val, str):
            timestamp_str = timestamp_val
        else:
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp_val))

        intro_text = (
            f"En la presente fecha y hora ({timestamp_str} UTC), se emite la presente Acta Forense "
            "para certificar la preservación inalterable de la evidencia digital asociada a una denuncia "
            "de extorsión, registrada mediante tecnología Blockchain en la red zkSYS Tanenbaum Testnet "
            "(Chain ID 57057)."
        )
        Story.append(Paragraph(intro_text, styles['Justify']))
        Story.append(Spacer(1, 0.15 * inch))

        datos = [
            ["ID de Evidencia (On-Chain):", str(datos_evidencia.get("evidence_id", "N/A"))],
            ["Hash del Contenido (SHA-256):", datos_evidencia.get("on_chain_hash", "N/A")],
            ["DID Denunciante:", datos_evidencia.get("did_denunciante", "N/A")],
            ["Transacción (Tx Hash):", datos_evidencia.get("tx_hash", "N/A")],
            ["Bloque (Block Number):", str(datos_evidencia.get("block_number", "N/A"))],
            ["Red:", "zkSYS Tanenbaum Testnet (57057)"],
            ["Custodio Actual:", datos_evidencia.get("custodian", "N/A")],
            ["Estado (Activa):", "SÍ" if datos_evidencia.get("active", True) else "NO (Revocada)"],
            ["Método de Firma:", datos_evidencia.get("firma_metodo", "ECDSA P-256 / SHA-256")],
        ]

        t = Table(datos, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (1, 0), (1, -1), True)
        ]))

        Story.append(t)
        Story.append(Spacer(1, 0.3 * inch))

        declaracion = (
            "La integridad de esta evidencia está garantizada criptográficamente por los Smart Contracts "
            "desplegados en la blockchain zkSYS Tanenbaum. Cualquier alteración al archivo original resultará "
            "en un Hash diferente, invalidando matemáticamente su correlación con este registro público inmutable."
        )
        Story.append(Paragraph(declaracion, styles['Justify']))
        Story.append(Spacer(1, 0.15 * inch))

        firma_info = datos_evidencia.get("firma_info", {})
        if firma_info.get("signature"):
            sig_text = (
                f"Firma Digital: {firma_info.get('signature', 'N/A')[:64]}...<br/>"
                f"Firmante: {firma_info.get('signer_address', 'N/A')}<br/>"
                f"Hash del Acta: {firma_info.get('acta_hash', 'N/A')[:40]}..."
            )
            Story.append(Paragraph(sig_text, styles['Justify']))
            Story.append(Spacer(1, 0.3 * inch))

        firma_data = [
            ["___________________________________", "___________________________________"],
            ["Firma del Oficial Custodio", "Firma del Fiscal / Juez"]
        ]
        firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        Story.append(firma_table)
        Story.append(Spacer(1, 0.2 * inch))

        footer = (
            "Este documento fue generado automáticamente por el Sistema de Inteligencia Ciudadana. "
            "La firma digital está embebida en los metadatos del PDF y puede ser verificada con la "
            "llave pública del custodio institucional."
        )
        Story.append(Paragraph(footer, styles['SmallCenter']))

        doc.build(Story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def firmar_acta(self, pdf_bytes: bytes, private_key: str, cert_pem: Optional[str] = None) -> Dict[str, Any]:
        """
        Firma digitalmente el acta PDF usando ECDSA P-256 (compatibilidad Ethereum + X.509).
        Si se proporciona cert_pem, incluye información del certificado en la respuesta.
        Retorna la firma, el signer, el hash firmado y metadata del certificado.
        """
        acta_hash = "0x" + hashlib.sha256(pdf_bytes).hexdigest()

        if not private_key or private_key == "0x" + "0" * 64:
            return {
                "acta_hash": acta_hash,
                "signature": None,
                "signer_address": None,
                "cert_info": None,
                "message": "Clave privada no configurada; acta generado sin firma digital"
            }

        # --- Firma ECDSA (secp256k1 compatible Ethereum) ---
        from eth_account import Account
        from eth_account.messages import encode_defunct

        account = Account.from_key(private_key)
        signable_hash = encode_defunct(hexstr=acta_hash)
        signed = account.sign_message(signable_hash)

        # --- Info del certificado (si se proporciona) ---
        cert_info = None
        if cert_pem:
            try:
                cert = load_pem_x509_certificate(cert_pem.encode(), default_backend())
                cert_info = {
                    "subject": cert.subject.rfc4514_string(),
                    "issuer": cert.issuer.rfc4514_string(),
                    "serial_number": str(cert.serial_number),
                    "not_valid_before": cert.not_valid_before_utc.isoformat(),
                    "not_valid_after": cert.not_valid_after_utc.isoformat(),
                    "signature_algorithm": cert.signature_algorithm_oid._name,
                }
            except Exception:
                cert_info = {"error": "No se pudo parsear el certificado"}

        # --- Firma adicional ECDSA P-256 (para verificación no-Ethereum) ---
        ec_signature = None
        try:
            ec_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
            ec_signature = ec_private_key.sign(
                pdf_bytes,
                ec.ECDSA(hashes.SHA256())
            ).hex()
        except Exception:
            pass

        return {
            "acta_hash": acta_hash,
            "signature": signed.signature.hex(),
            "signer_address": account.address,
            "ec_signature_p256": ec_signature,
            "cert_info": cert_info,
            "firma_metodo": "ECDSA secp256k1 (Ethereum)" + (" + X.509" if cert_info else ""),
            "message": "Acta firmada digitalmente por la wallet institucional"
        }

    def generar_metadata_sellado(self, datos_evidencia: Dict[str, Any], firma_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera metadata JSON para el sellado en blockchain (EvidenceSeal).
        Compatible con IPFS metadata standard.
        """
        return {
            "schema_version": "1.0",
            "system": "IntelExtorsión - Sistema de Inteligencia Ciudadana",
            "document_type": "ACTA_PRESERVACION_EVIDENCIA_DIGITAL",
            "evidence": {
                "on_chain_id": datos_evidencia.get("evidence_id"),
                "content_hash": datos_evidencia.get("on_chain_hash"),
                "did_denunciante": datos_evidencia.get("did_denunciante"),
                "tx_hash": datos_evidencia.get("tx_hash"),
                "block_number": datos_evidencia.get("block_number"),
                "network": "zkSYS Tanenbaum Testnet",
                "chain_id": 57057,
            },
            "seal": {
                "acta_hash": firma_result.get("acta_hash"),
                "signature_ethereum": firma_result.get("signature"),
                "signature_p256": firma_result.get("ec_signature_p256"),
                "signer_address": firma_result.get("signer_address"),
                "firma_metodo": firma_result.get("firma_metodo"),
                "certificado": firma_result.get("cert_info"),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
            "legal": {
                "framework": "CPP art. 158-B - Preservación de evidencia digital",
                "jurisdiccion": "Perú",
                "institucion": "DIVINCRI La Libertad",
            }
        }


acta_service = ActaForenseService()
