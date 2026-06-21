import io
import time
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

class ActaForenseService:
    def generar_acta_pdf(self, datos_evidencia: Dict[str, Any]) -> bytes:
        """
        Genera un Acta de Preservación de Evidencia Digital en PDF.
        Retorna los bytes del PDF.
        """
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
        
        Story = []
        
        # Título
        Story.append(Paragraph("ACTA DE PRESERVACIÓN DE EVIDENCIA DIGITAL", styles['CenterTitle']))
        Story.append(Spacer(1, 0.2 * inch))
        
        # Introducción
        timestamp_val = datos_evidencia.get('timestamp', time.time())
        if isinstance(timestamp_val, str):
            timestamp_str = timestamp_val
        else:
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_val))
            
        intro_text = (
            f"En la presente fecha y hora ({timestamp_str}), se emite la presente Acta Forense "
            "para certificar la preservación inalterable de la evidencia digital asociada a una denuncia "
            "de extorsión, registrada mediante tecnología Blockchain en la red zkSYS (Tanenbaum)."
        )
        Story.append(Paragraph(intro_text, styles['Justify']))
        Story.append(Spacer(1, 0.2 * inch))
        
        # Datos Técnicos (Tabla)
        datos = [
            ["ID de Evidencia (On-Chain):", str(datos_evidencia.get("evidence_id", "N/A"))],
            ["Hash del Contenido (SHA-256):", datos_evidencia.get("on_chain_hash", "N/A")],
            ["DID Denunciante:", datos_evidencia.get("did_denunciante", "N/A")],
            ["Transacción (Tx Hash):", datos_evidencia.get("tx_hash", "N/A")],
            ["Bloque (Block Number):", str(datos_evidencia.get("block_number", "N/A"))],
            ["Custodio Actual:", datos_evidencia.get("custodian", "N/A")],
            ["Estado (Activa):", "SÍ" if datos_evidencia.get("active", True) else "NO (Revocada)"]
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
        Story.append(Spacer(1, 0.4 * inch))
        
        # Declaración Jurada
        declaracion = (
            "La integridad de esta evidencia está garantizada criptográficamente por los Smart Contracts "
            "desplegados en la blockchain. Cualquier alteración al archivo original resultará en un Hash "
            "diferente, invalidando matemáticamente su correlación con este registro público inmutable."
        )
        Story.append(Paragraph(declaracion, styles['Justify']))
        Story.append(Spacer(1, 1 * inch))
        
        # Firmas
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
        
        # Generar
        doc.build(Story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

acta_service = ActaForenseService()
