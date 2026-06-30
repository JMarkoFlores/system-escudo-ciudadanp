import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import ContractService from '../services/contractService';

const ForensicReport = ({
  fileMeta,
  imageDims,
  hash,
  evidenceId,
  blockNumber,
  txHash,
  sealTxHash,
  sealBlockNumber,
  sealId,
  did,
  tipo,
}) => {
  const [generating, setGenerating] = useState(false);

  const tipoEvidencia = ContractService.getTipoLabel ? ContractService.getTipoLabel(tipo) : tipo;

  const handleDownloadPDF = async () => {
    setGenerating(true);
    try {
      const doc = new jsPDF({ format: 'a4', unit: 'mm' });
      const pageW = 210;
      const margin = 20;
      const contentW = pageW - 2 * margin;
      let y = margin;

      const title = (text, size = 16, bold = true) => {
        doc.setFont('helvetica', bold ? 'bold' : 'normal');
        doc.setFontSize(size);
        doc.text(text, pageW / 2, y, { align: 'center' });
        y += size * 0.5 + 2;
      };
      const subtitle = (text) => {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(text, margin, y);
        y += 5;
        doc.setTextColor(0);
      };
      const line = (label, value) => {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        const labW = doc.getTextWidth(label + ': ');
        doc.text(label + ': ', margin, y);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        const remainingW = contentW - labW;
        const lines = doc.splitTextToSize(String(value || '—'), remainingW);
        doc.text(lines, margin + labW, y);
        y += 4 * lines.length;
      };
      const section = (label) => {
        doc.setFillColor(240, 240, 245);
        doc.rect(margin, y - 1, contentW, 6, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(60);
        doc.text(label, margin + 2, y + 3);
        y += 8;
        doc.setTextColor(0);
      };

      // ── HEADER ──
      doc.setFillColor(30, 27, 75);
      doc.rect(0, 0, pageW, 35, 'F');
      doc.setTextColor(255);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.text('ACTA DE CUSTODIA FORENSE DIGITAL', pageW / 2, 15, { align: 'center' });
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.text('IntelExtorsión — Sistema de Custodia Forense en Blockchain', pageW / 2, 23, { align: 'center' });
      doc.setFontSize(7);
      doc.setTextColor(180);
      doc.text('zkSYS Tanenbaum Testnet (Chain ID 57057)', pageW / 2, 30, { align: 'center' });
      doc.setTextColor(0);

      y = 42;

      // ── INFO DEL DOCUMENTO ──
      section('INFORMACIÓN DEL DOCUMENTO');
      line('Versión acta', '2.0');
      line('Fecha de emisión', new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
      line('Emitido por', 'IntelExtorsión Web3 DApp v2.0.0');
      line('Estándar', 'W3C DID Core 1.0 / SHA-256 (FIPS 180-4)');
      line('Marco legal', 'Artículo 158-B CPP Peruano — Evidencia Digital Trazable');

      // ── ARCHIVO ──
      section('DATOS DEL ARCHIVO');
      line('Nombre del archivo', fileMeta?.fileName);
      line('Tamaño', fileMeta?.fileSizeFormatted);
      line('Tipo MIME', fileMeta?.mimeType);
      if (imageDims) {
        line('Dimensiones', `${imageDims.width} × ${imageDims.height} px`);
      }
      line('Última modificación', fileMeta?.lastModified);

      // ── CAPTURA FORENSE ──
      section('CAPTURA FORENSE (RF-06)');
      line('Hash SHA-256', hash);
      line('Timestamp de captura', fileMeta?.captureTimestamp);
      line('Método de hash', 'SHA-256 via Web Crypto API (procesamiento cliente)');
      line('Metadatos EXIF/GPS', 'Eliminados automáticamente — privacidad preservada');
      line('Metadatos de identidad', 'No recolectados');
      line('Tipo de evidencia', tipoEvidencia);

      // ── REGISTRO BLOCKCHAIN ──
      if (txHash) {
        section('REGISTRO EN BLOCKCHAIN (RF-07)');
        line('Evidence ID', String(evidenceId ?? '—'));
        line('Transacción (Tx Hash)', txHash);
        line('Número de bloque', String(blockNumber ?? '—'));
        line('Red', 'zkSYS Tanenbaum Testnet');
        line('Chain ID', '57057');
        line('Explorador', ContractService.getExplorerTxUrl(txHash));
      }

      // ── SELLADO ──
      if (sealTxHash) {
        section('SELLADO DE INTEGRIDAD (EvidenceSeal)');
        line('Seal ID', String(sealId ?? '—'));
        line('Transacción de sellado', sealTxHash);
        line('Bloque de sellado', String(sealBlockNumber ?? '—'));
        line('Explorador', ContractService.getExplorerTxUrl(sealTxHash));
      }

      // ── IDENTIDAD ──
      section('IDENTIDAD DEL APORTANTE');
      line('DID (Identidad Descentralizada)', did || 'No especificado');
      line('Método de autenticación', 'Firma criptográfica con Pali Wallet V2');
      line('Tipo de identidad', 'Seudónimo — identificable ante DIVINCRI solo con autorización explícita');
      line('Estándar DID', 'W3C DID Core 1.0');

      // ── CADENA DE CUSTODIA ──
      section('CADENA DE CUSTODIA');
      line('Origen', 'Aportante vía DApp Web3 (Pali Wallet)');
      line('Hash calculado', 'Antes de cualquier procesamiento (stream binario original)');
      line('Almacenamiento', 'Hash en blockchain — archivo cifrado en almacenamiento seguro');
      line('Verificación', 'Pública en explorador de bloques — cualquier fiscal/juez/perito');

      // ── VALIDACIÓN OFFLINE ──
      section('VALIDACIÓN OFFLINE (Respaldo Secundario)');
      line('Método', 'Este PDF contiene todos los datos forenses necesarios');
      line('Verificación', 'Comparar el hash SHA-256 del archivo original con el registrado');
      line('Blockchain', 'Si la red no está accesible, el acta PDF es evidencia válida');
      line('Recomendación', 'Conservar este PDF junto con el archivo original para peritaje');

      // ── FIRMA DIGITAL ──
      y += 2;
      doc.setDrawColor(150);
      doc.line(margin, y, pageW - margin, y);
      y += 8;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(100);
      doc.text('FIRMA DIGITAL DEL SISTEMA', pageW / 2, y, { align: 'center' });
      y += 6;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7);
      doc.setTextColor(150);
      doc.text('Documento generado automáticamente por IntelExtorsión Web3 DApp', pageW / 2, y, { align: 'center' });
      y += 4;
      doc.text(`Hash del acta: ${hash ? hash.substring(0, 20) + '...' : 'N/A'}`, pageW / 2, y, { align: 'center' });
      y += 4;
      doc.text('La firma digital del servidor con certificado oficial estará disponible en producción.', pageW / 2, y, { align: 'center' });

      // ── FOOTER ──
      doc.setFontSize(6);
      doc.setTextColor(180);
      doc.text('IntelExtorsión — Inteligencia Ciudadana contra la Extorsión', pageW / 2, 290, { align: 'center' });
      doc.text('Esta DApp no reemplaza los canales oficiales de denuncia (Línea 111, comisaría).', pageW / 2, 294, { align: 'center' });
      doc.text(`Generado: ${new Date().toISOString()} | Página 1 de 1`, pageW / 2, 298, { align: 'center' });

      doc.save(`acta-custodia-forense-${evidenceId || Date.now()}.pdf`);
    } catch (err) {
      console.error('Error generating PDF:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadJSON = () => {
    const forensicData = {
      actaVersion: '2.0',
      titulo: 'ACTA DE CUSTODIA FORENSE DIGITAL',
      sistema: 'IntelExtorsión - Custodia Forense en Blockchain',
      red: 'zkSYS Tanenbaum Testnet (Chain ID 57057)',
      marcoLegal: 'Artículo 158-B CPP Peruano — Evidencia Digital Trazable',
      fechaEmision: new Date().toISOString(),
      archivo: {
        nombre: fileMeta?.fileName || '—',
        tamano: fileMeta?.fileSizeFormatted || '—',
        mimeType: fileMeta?.mimeType || '—',
        dimensiones: imageDims ? `${imageDims.width}x${imageDims.height}px` : 'N/A',
        ultimaModificacion: fileMeta?.lastModified || '—',
      },
      capturaForense: {
        hashSHA256: hash || '—',
        timestampUTC: fileMeta?.captureTimestamp || new Date().toISOString(),
        metodoHash: 'SHA-256 via Web Crypto API (cliente)',
        exifEliminado: true,
        metadatosIdentidad: 'No recolectados',
        tipoEvidencia,
      },
      registroBlockchain: txHash ? {
        evidenceId: evidenceId ?? '—',
        txHash,
        blockNumber: blockNumber || '—',
        red: 'zkSYS Tanenbaum Testnet',
        chainId: 57057,
        explorador: ContractService.getExplorerTxUrl(txHash),
      } : null,
      selladoBlockchain: sealTxHash ? {
        sealId: sealId ?? '—',
        txHashSeal: sealTxHash,
        blockNumberSeal: sealBlockNumber || '—',
        exploradorSeal: ContractService.getExplorerTxUrl(sealTxHash),
      } : null,
      identidadAportante: {
        did: did || 'No especificado',
        metodoAutenticacion: 'Firma criptográfica con Pali Wallet V2',
        tipoIdentidad: 'Seudónimo — identificable ante DIVINCRI solo con autorización explícita',
        estandarDID: 'W3C DID Core 1.0',
      },
      cadenaDeCustodia: {
        origen: 'Aportante vía DApp Web3 (Pali Wallet)',
        hashCalculado: 'Antes de cualquier procesamiento (stream binario original)',
        almacenamiento: 'Hash en blockchain — archivo cifrado en almacenamiento seguro',
        verificacion: 'Pública en explorador de bloques',
      },
      validacionOffline: {
        metodo: 'Este documento contiene todos los datos forenses necesarios',
        verificacion: 'Comparar el hash SHA-256 del archivo original con el registrado',
        recomendacion: 'Conservar este documento junto con el archivo original para peritaje',
      },
    };

    const blob = new Blob([JSON.stringify(forensicData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `acta-forense-${evidenceId || 'pendiente'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
        <span>📋</span>
        Acta de Custodia Forense Digital
      </h3>
      <p className="text-xs text-gray-500">
        Documento con los datos forenses completos compatibles con el artículo 158-B del CPP peruano (Evidencia Digital Trazable). Incluye hash SHA-256, timestamp UTC, DID del aportante, número de bloque y datos de sellado en zkSYS Tanenbaum.
      </p>

      <div className="bg-white rounded-lg p-3 text-xs space-y-2 border border-gray-100">
        <p className="font-semibold text-gray-700">📄 Datos del archivo</p>
        <div className="grid grid-cols-2 gap-1">
          <p><span className="text-gray-400">Nombre:</span> {fileMeta?.fileName || '—'}</p>
          <p><span className="text-gray-400">Tamaño:</span> {fileMeta?.fileSizeFormatted || '—'}</p>
          <p><span className="text-gray-400">Tipo MIME:</span> {fileMeta?.mimeType || '—'}</p>
          {imageDims && <p><span className="text-gray-400">Dimensiones:</span> {imageDims.width}×{imageDims.height}px</p>}
        </div>

        <p className="font-semibold text-gray-700 pt-1">🔐 Captura forense</p>
        <div className="grid grid-cols-1 gap-1">
          <p><span className="text-gray-400">Hash SHA-256:</span> <span className="font-mono text-xs break-all">{hash || '—'}</span></p>
          <p><span className="text-gray-400">Timestamp UTC:</span> {fileMeta?.captureTimestamp || '—'}</p>
          <p><span className="text-gray-400">EXIF/GPS eliminado:</span> Sí</p>
          <p><span className="text-gray-400">Tipo:</span> {tipoEvidencia}</p>
        </div>

        {txHash && (
          <>
            <p className="font-semibold text-gray-700 pt-1">⛓️ Blockchain</p>
            <div className="grid grid-cols-2 gap-1">
              <p><span className="text-gray-400">Evidence ID:</span> {evidenceId ?? '—'}</p>
              <p><span className="text-gray-400">Bloque:</span> {blockNumber || '—'}</p>
              <p className="col-span-2"><span className="text-gray-400">Red:</span> zkSYS Tanenbaum (Chain ID 57057)</p>
              <p className="col-span-2">
                <span className="text-gray-400">Tx:</span>{' '}
                <a href={ContractService.getExplorerTxUrl(txHash)} target="_blank" rel="noreferrer" className="text-blue-600 underline">Ver en explorer</a>
              </p>
            </div>
          </>
        )}

        {sealTxHash && (
          <>
            <p className="font-semibold text-gray-700 pt-1">🔒 Sellado (EvidenceSeal)</p>
            <div className="grid grid-cols-2 gap-1">
              <p><span className="text-gray-400">Seal ID:</span> {sealId ?? '—'}</p>
              <p><span className="text-gray-400">Bloque seal:</span> {sealBlockNumber ?? '—'}</p>
              <p className="col-span-2">
                <a href={ContractService.getExplorerTxUrl(sealTxHash)} target="_blank" rel="noreferrer" className="text-blue-600 underline">Ver seal en explorer</a>
              </p>
            </div>
          </>
        )}

        <p className="font-semibold text-gray-700 pt-1">👤 Identidad del aportante</p>
        <p><span className="text-gray-400">DID:</span> <span className="font-mono text-xs">{did || 'No especificado'}</span></p>
        <p><span className="text-gray-400">Tipo:</span> Seudónimo — solo identificable ante DIVINCRI con autorización explícita</p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleDownloadPDF}
          disabled={generating}
          className="flex-1 bg-gray-800 hover:bg-gray-900 disabled:bg-gray-400 text-white text-sm font-semibold py-2.5 px-4 rounded-lg transition"
        >
          {generating ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              Generando PDF...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
              Descargar Acta PDF
            </span>
          )}
        </button>
        <button
          onClick={handleDownloadJSON}
          className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
          title="Descargar datos forenses en formato JSON"
        >
          JSON
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center">
        PDF generado con todos los datos forenses. La firma digital del servidor con certificado oficial se integrará en producción (Fase 2).
      </p>
    </div>
  );
};

export default ForensicReport;
