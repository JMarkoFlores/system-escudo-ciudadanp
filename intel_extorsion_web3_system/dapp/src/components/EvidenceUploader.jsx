import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { ContractService } from '../services/contractService';
import { ethers } from 'ethers';

const EvidenceUploader = ({ provider }) => {
  const [file, setFile] = useState(null);
  const [did, setDid] = useState('');
  const [tipo, setTipo] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    setFile(acceptedFiles[0]);
    setResult(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, maxFiles: 1 });

  const handleUpload = async () => {
    if (!file || !provider) return;
    setLoading(true);

    try {
      // Leer archivo y calcular hash
      const arrayBuffer = await file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      const hashBuffer = await crypto.subtle.digest('SHA-256', bytes);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      // Subir a IPFS via backend (simulado para demo)
      const ipfsCID = `Qm${hashHex.slice(2, 18)}`; // Simulado

      // Interactuar con contrato
      const service = new ContractService(provider);
      await service.init();
      const res = await service.storeEvidence(hashHex, ipfsCID, did, Number(tipo), '');

      setResult({
        success: true,
        evidenceId: res.evidenceId,
        txHash: res.txHash,
        blockNumber: res.blockNumber,
        hash: hashHex,
        ipfsCID,
      });
    } catch (err) {
      setResult({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Registrar Evidencia en Blockchain</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-green-600 font-semibold">{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
        ) : (
          <p className="text-gray-500">
            {isDragActive ? 'Suelta el archivo aquí' : 'Arrastra un archivo o haz clic para seleccionar'}
          </p>
        )}
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700">DID del Denunciante (opcional)</label>
          <input
            type="text"
            value={did}
            onChange={(e) => setDid(e.target.value)}
            placeholder="did:ethr:rollux:0x..."
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Tipo de Evidencia</label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          >
            <option value={1}>Texto</option>
            <option value={2}>Imagen</option>
            <option value={3}>Audio</option>
            <option value={4}>Video</option>
            <option value={5}>Documento</option>
          </select>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || loading || !provider}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition"
        >
          {loading ? 'Registrando en Rollux...' : 'Registrar en Blockchain'}
        </button>
      </div>

      {result && (
        <div className={`mt-4 p-4 rounded ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          {result.success ? (
            <div className="space-y-1 text-sm">
              <p className="text-green-700 font-bold">✅ Evidencia registrada exitosamente</p>
              <p><span className="font-semibold">Evidence ID:</span> {result.evidenceId}</p>
              <p><span className="font-semibold">Tx Hash:</span> <a href={`https://explorer.rollux.com/tx/${result.txHash}`} target="_blank" rel="noreferrer" className="text-blue-600 underline">{result.txHash.slice(0, 20)}...</a></p>
              <p><span className="font-semibold">Bloque:</span> {result.blockNumber}</p>
              <p><span className="font-semibold">SHA-256:</span> <span className="font-mono text-xs">{result.hash}</span></p>
              <p><span className="font-semibold">IPFS CID:</span> {result.ipfsCID}</p>
            </div>
          ) : (
            <p className="text-red-700">❌ Error: {result.error}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceUploader;
