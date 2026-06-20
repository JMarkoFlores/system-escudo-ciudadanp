import React, { useState } from 'react';
import { ContractService } from '../services/contractService';

const EvidenceVerifier = ({ provider }) => {
  const [evidenceId, setEvidenceId] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleVerify = async () => {
    if (!evidenceId || !file || !provider) return;
    setLoading(true);

    try {
      const arrayBuffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      const service = new ContractService(provider);
      await service.init();
      const [valid, mensaje] = await service.verifyEvidence(Number(evidenceId), hashHex);
      const ev = await service.getEvidence(Number(evidenceId));

      setResult({
        valid,
        mensaje,
        evidenceId: Number(evidenceId),
        onChainHash: ev.evidenceHash,
        providedHash: hashHex,
        custodian: ev.custodian,
        timestamp: ev.timestamp,
        active: ev.active,
        ipfsCID: ev.ipfsCID,
      });
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Verificar Integridad de Evidencia</h2>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700">Evidence ID</label>
          <input
            type="number"
            value={evidenceId}
            onChange={(e) => setEvidenceId(e.target.value)}
            placeholder="Ej: 42"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Archivo Original</label>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        <button
          onClick={handleVerify}
          disabled={!evidenceId || !file || loading || !provider}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded transition"
        >
          {loading ? 'Verificando...' : 'Verificar Integridad'}
        </button>
      </div>

      {result && !result.error && (
        <div className={`mt-4 p-4 rounded border ${result.valid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <p className={`font-bold ${result.valid ? 'text-green-700' : 'text-red-700'}`}>
            {result.valid ? '✅ INTEGRIDAD VERIFICADA' : '❌ INTEGRIDAD COMPROMETIDA'}
          </p>
          <p className="text-sm mt-1 text-gray-700">{result.mensaje}</p>
          <div className="mt-2 space-y-1 text-xs text-gray-600 font-mono">
            <p>On-chain Hash: {result.onChainHash}</p>
            <p>Provided Hash: {result.providedHash}</p>
            <p>Custodio: {result.custodian}</p>
            <p>Timestamp: {new Date(result.timestamp * 1000).toISOString()}</p>
            <p>Activo: {result.active ? 'Sí' : 'No'}</p>
            <p>IPFS: {result.ipfsCID}</p>
          </div>
        </div>
      )}

      {result?.error && (
        <div className="mt-4 p-4 rounded bg-red-50 border border-red-200">
          <p className="text-red-700">Error: {result.error}</p>
        </div>
      )}
    </div>
  );
};

export default EvidenceVerifier;
