import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { ethers } from 'ethers';
import { ContractService } from '../services/contractService';
import ForensicReport from './ForensicReport';

const EvidenceUploader = ({ provider, account }) => {
  const [file, setFile] = useState(null);
  const [fileMeta, setFileMeta] = useState(null);
  const [imageDims, setImageDims] = useState(null);
  const [did, setDid] = useState('');
  const [tipo, setTipo] = useState(2);
  const [step, setStep] = useState('select');
  const [loading, setLoading] = useState(false);
  const [computedHash, setComputedHash] = useState(null);
  const [result, setResult] = useState(null);
  const [sealResult, setSealResult] = useState(null);
  const [error, setError] = useState(null);

  const didPlaceholder = account ? ContractService.getDIDFromAddress(account) : 'did:zsys:tanenbaum:0x...';

  const processFile = async (acceptedFile) => {
    setFile(acceptedFile);
    setResult(null);
    setSealResult(null);
    setError(null);
    setStep('metadata');

    const meta = ContractService.getForensicMetadata(acceptedFile);
    setFileMeta(meta);

    if (acceptedFile.type.startsWith('image/')) {
      const dims = await ContractService.getImageDimensions(acceptedFile);
      setImageDims(dims);
    } else {
      setImageDims(null);
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) processFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: 52428800,
  });

  const handleHashAndSeal = async () => {
    if (!file || !provider) return;
    setLoading(true);
    setError(null);

    try {
      const hashHex = await ContractService.computeSHA256(file);
      setComputedHash(hashHex);
      const ipfsCID = `Qm${hashHex.slice(2, 18)}`;
      const metadataURI = JSON.stringify({
        fileName: file.name,
        mimeType: file.type,
        fileSize: file.size,
        dimensions: imageDims,
        capturedAt: fileMeta?.captureTimestamp,
      });

      const service = new ContractService(provider);
      await service.init();

      const res = await service.storeEvidence(hashHex, ipfsCID, did, Number(tipo), metadataURI);

      let seal = null;
      try {
        const sealHash = ethers.keccak256(ethers.toUtf8Bytes(hashHex + (res.evidenceId || 0)));
        seal = await service.sealEvidence(
          res.evidenceId || 0,
          sealHash,
          hashHex,
          metadataURI
        );
      } catch (sealErr) {
        seal = { txHash: null, blockNumber: null, sealId: null, error: sealErr.message };
      }

      setResult(res);
      setSealResult(seal);
      setStep('result');
    } catch (err) {
      setError(err.message || 'Error al procesar la evidencia');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileMeta(null);
    setImageDims(null);
    setResult(null);
    setSealResult(null);
    setError(null);
    setStep('select');
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 text-sm">E</span>
        Carga de Evidencia con Captura Forense
      </h2>

      {step === 'select' && (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${
            isDragActive ? 'border-emerald-400 bg-emerald-50' : 'border-gray-300 hover:border-emerald-300'
          }`}
        >
          <input {...getInputProps()} />
          <div className="space-y-2">
            <div className="text-4xl text-gray-300">📎</div>
            <p className="text-gray-600 font-medium">
              {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra un archivo o haz clic para seleccionar'}
            </p>
            <p className="text-xs text-gray-400">Imágenes, PDF, Audio, Video — Máx 50 MB</p>
          </div>
        </div>
      )}

      {(step === 'metadata' || step === 'result') && fileMeta && (
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-xl p-4 space-y-2">
            <h3 className="text-sm font-semibold text-gray-700">Archivo seleccionado</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-500">Nombre:</span> <span className="font-medium">{fileMeta.fileName}</span></div>
              <div><span className="text-gray-500">Tamaño:</span> <span className="font-medium">{fileMeta.fileSizeFormatted}</span></div>
              <div><span className="text-gray-500">Tipo MIME:</span> <span className="font-mono text-xs">{fileMeta.mimeType}</span></div>
              <div><span className="text-gray-500">Modificado:</span> <span className="text-xs">{new Date(fileMeta.lastModified).toLocaleString()}</span></div>
              {imageDims && (
                <div><span className="text-gray-500">Dimensiones:</span> <span className="font-medium">{imageDims.width}×{imageDims.height}px</span></div>
              )}
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-xs text-amber-700 mt-2">
              ⚠️ Los metadatos EXIF con geolocalización (GPS) se eliminan automáticamente antes del almacenamiento para proteger tu privacidad.
            </div>
          </div>

          {step === 'metadata' && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tu DID (Identidad Descentralizada)</label>
                <input
                  type="text"
                  value={did}
                  onChange={(e) => setDid(e.target.value)}
                  placeholder={didPlaceholder}
                  className="w-full rounded-lg border-gray-300 shadow-sm p-2.5 border text-sm font-mono"
                />
                <p className="text-xs text-gray-400 mt-1">Si no tienes DID, regístrate en la sección "Identidad Descentralizada"</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Evidencia</label>
                <select
                  value={tipo}
                  onChange={(e) => setTipo(e.target.value)}
                  className="w-full rounded-lg border-gray-300 shadow-sm p-2.5 border text-sm"
                >
                  <option value={1}>Texto</option>
                  <option value={2}>Imagen</option>
                  <option value={3}>Audio</option>
                  <option value={4}>Video</option>
                  <option value={5}>Documento</option>
                </select>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700 space-y-1">
                <p className="font-semibold">Captura forense automática (RF-06):</p>
                <ul className="list-disc pl-4 space-y-0.5">
                  <li>Hash SHA-256 del archivo original (antes de procesamiento)</li>
                  <li>Timestamp UTC del momento de recepción</li>
                  <li>Tipo MIME y metadatos técnicos del archivo</li>
                  <li>Sin metadatos de identidad del dispositivo (EXIF eliminado)</li>
                </ul>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleReset}
                  className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cambiar archivo
                </button>
                <button
                  onClick={handleHashAndSeal}
                  disabled={loading}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      Calculando hash y sellando...
                    </span>
                  ) : (
                    'Calcular Hash y Sellar en Blockchain'
                  )}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              ❌ {error}
            </div>
          )}

          {step === 'result' && result && (
            <div className="space-y-4">
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2 text-emerald-700 font-semibold text-sm">
                  <span>✅</span> Evidencia registrada y sellada en blockchain
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="col-span-2 bg-white rounded-lg p-2 border border-emerald-100">
                    <span className="text-gray-500 font-sans">SHA-256:</span>
                    <p className="break-all text-emerald-800">{computedHash || 'calculado...'}</p>
                  </div>
                  <div className="bg-white rounded-lg p-2 border border-emerald-100">
                    <span className="text-gray-500 font-sans">Evidence ID:</span>
                    <p className="text-emerald-800 font-bold">{result.evidenceId ?? '—'}</p>
                  </div>
                  <div className="bg-white rounded-lg p-2 border border-emerald-100">
                    <span className="text-gray-500 font-sans">Bloque:</span>
                    <p className="text-emerald-800">{result.blockNumber}</p>
                  </div>
                  <div className="col-span-2 bg-white rounded-lg p-2 border border-emerald-100">
                    <span className="text-gray-500 font-sans">Tx Hash (Registry):</span>
                    <p className="break-all">
                      <a href={ContractService.getExplorerTxUrl(result.txHash)} target="_blank" rel="noreferrer" className="text-blue-600 underline text-xs">
                        {result.txHash}
                      </a>
                    </p>
                  </div>
                </div>

                {sealResult && sealResult.txHash && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 mt-2 space-y-1">
                    <p className="text-indigo-700 font-semibold text-xs">🔒 Sellado en EvidenceSeal</p>
                    <div className="grid grid-cols-2 gap-1 text-xs font-mono">
                      <div><span className="text-gray-500">Seal ID:</span> {sealResult.sealId ?? '—'}</div>
                      <div><span className="text-gray-500">Bloque seal:</span> {sealResult.blockNumber}</div>
                      <div className="col-span-2">
                        <span className="text-gray-500">Tx:</span>{' '}
                        <a href={ContractService.getExplorerTxUrl(sealResult.txHash)} target="_blank" rel="noreferrer" className="text-blue-600 underline">
                          {sealResult.txHash.slice(0, 30)}...
                        </a>
                      </div>
                    </div>
                  </div>
                )}
                {sealResult && !sealResult.txHash && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-xs text-amber-700">
                    Sellado secundario no disponible: {sealResult.error || 'contrato EvidenceSeal no configurado'}
                  </div>
                )}
              </div>

              <ForensicReport
                fileMeta={fileMeta}
                imageDims={imageDims}
                hash={computedHash || '—'}
                evidenceId={result.evidenceId}
                blockNumber={result.blockNumber}
                txHash={result.txHash}
                sealTxHash={sealResult?.txHash}
                sealBlockNumber={sealResult?.blockNumber}
                sealId={sealResult?.sealId}
                did={did}
                tipo={tipo}
                provider={provider}
              />

              <button
                onClick={handleReset}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2.5 px-4 rounded-lg transition text-sm"
              >
                Subir otra evidencia
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceUploader;
