import React, { useState } from 'react';
import { ContractService } from '../services/contractService';

const EvidenceVerifier = ({ provider }) => {
  const [evidenceId, setEvidenceId] = useState('');
  const [hashInput, setHashInput] = useState('');
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('file');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleVerify = async () => {
    if (!evidenceId || !provider) return;
    setLoading(true);
    setResult(null);

    try {
      let hashHex;
      if (mode === 'file' && file) {
        hashHex = await ContractService.computeSHA256(file);
      } else if (mode === 'hash' && hashInput) {
        hashHex = hashInput.startsWith('0x') ? hashInput : `0x${hashInput}`;
      } else {
        throw new Error('Selecciona un archivo o ingresa un hash SHA-256');
      }

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
        tipoEvidencia: ContractService.getTipoLabel(ev.tipoEvidencia),
        didDenunciante: ev.didDenunciante,
      });
    } catch (err) {
      setResult({ error: err.message || 'Error al verificar' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 text-sm">V</span>
        Verificar Integridad de Evidencia
      </h2>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Evidence ID</label>
          <input
            type="number"
            value={evidenceId}
            onChange={(e) => setEvidenceId(e.target.value)}
            placeholder="Ej: 1"
            className="w-full rounded-lg border-gray-300 shadow-sm p-2.5 border text-sm"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setMode('file')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${mode === 'file' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}
          >
            Con archivo
          </button>
          <button
            onClick={() => setMode('hash')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${mode === 'hash' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}
          >
            Con hash
          </button>
        </div>

        {mode === 'file' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Archivo original</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hash SHA-256 (0x...)</label>
            <input
              type="text"
              value={hashInput}
              onChange={(e) => setHashInput(e.target.value)}
              placeholder="0x..."
              className="w-full rounded-lg border-gray-300 shadow-sm p-2.5 border text-sm font-mono"
            />
          </div>
        )}

        <button
          onClick={handleVerify}
          disabled={!evidenceId || loading || !provider || (mode === 'file' && !file) || (mode === 'hash' && !hashInput)}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              Verificando en blockchain...
            </span>
          ) : (
            'Verificar Integridad'
          )}
        </button>

        {result && !result.error && (
          <div className={`rounded-xl p-4 border space-y-2 ${
            result.valid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          }`}>
            <div className={`font-bold text-sm flex items-center gap-2 ${
              result.valid ? 'text-green-700' : 'text-red-700'
            }`}>
              <span>{result.valid ? '✅' : '❌'}</span>
              {result.valid ? 'INTEGRIDAD VERIFICADA' : 'INTEGRIDAD COMPROMETIDA'}
            </div>
            <p className="text-xs text-gray-600">{result.mensaje}</p>
            <div className="mt-2 space-y-1 text-xs font-mono bg-white rounded-lg p-3 border">
              <p><span className="text-gray-500">On-chain hash:</span><br/>{result.onChainHash}</p>
              <p><span className="text-gray-500">Provided hash:</span><br/>{result.providedHash}</p>
              <div className="grid grid-cols-2 gap-1 pt-1">
                <p><span className="text-gray-500">Custodio:</span> {result.custodian?.slice(0, 10)}...</p>
                <p><span className="text-gray-500">Tipo:</span> {result.tipoEvidencia}</p>
                <p><span className="text-gray-500">Timestamp:</span> {new Date(result.timestamp * 1000).toLocaleString()}</p>
                <p><span className="text-gray-500">Activo:</span> {result.active ? 'Sí' : 'No'}</p>
              </div>
              {result.didDenunciante && (
                <p><span className="text-gray-500">DID:</span> {result.didDenunciante}</p>
              )}
            </div>
          </div>
        )}

        {result?.error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
            ❌ Error: {result.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceVerifier;
