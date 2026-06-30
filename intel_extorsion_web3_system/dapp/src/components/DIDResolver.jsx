import React, { useState } from 'react';
import { ContractService } from '../services/contractService';

const DIDResolver = ({ provider, account }) => {
  const [did, setDid] = useState(account ? ContractService.getDIDFromAddress(account) : '');
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleResolve = async () => {
    if (!did || !provider) return;
    setLoading(true);
    setError(null);
    setDoc(null);

    try {
      const service = new ContractService(provider);
      await service.init();
      const document = await service.resolveDID(did);
      if (!document || !document.active) {
        setError('DID no encontrado o inactivo en zkSYS Tanenbaum');
      } else {
        setDoc(document);
      }
    } catch (err) {
      setError(err.message || 'Error al resolver DID');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center text-violet-600 text-sm">R</span>
        Resolver DID en zkSYS Tanenbaum
      </h2>

      <div className="flex gap-2">
        <input
          type="text"
          value={did}
          onChange={(e) => setDid(e.target.value)}
          placeholder="did:zsys:tanenbaum:0x..."
          className="flex-1 rounded-lg border-gray-300 shadow-sm p-2.5 border text-sm font-mono"
        />
        <button
          onClick={handleResolve}
          disabled={loading || !provider}
          className="bg-violet-600 hover:bg-violet-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
        >
          {loading ? (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          ) : 'Resolver'}
        </button>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {doc && (
        <div className="mt-4 bg-gray-50 rounded-xl p-4 text-sm space-y-2 border border-gray-200">
          <div className="grid grid-cols-2 gap-2">
            <div className="col-span-2">
              <span className="text-gray-500 text-xs uppercase tracking-wide">DID</span>
              <p className="font-mono text-xs break-all">{doc.did}</p>
            </div>
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Controller</span>
              <p className="font-mono text-xs">{doc.controller?.slice(0, 16)}...{doc.controller?.slice(-4)}</p>
            </div>
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Activo</span>
              <p className={doc.active ? 'text-green-600 font-bold' : 'text-red-600'}>{doc.active ? 'Sí' : 'No'}</p>
            </div>
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Creado</span>
              <p className="text-xs">{new Date(doc.createdAt * 1000).toLocaleString()}</p>
            </div>
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Reputación</span>
              <p className="text-xs">{doc.reputationScore}/100</p>
            </div>
          </div>
          {doc.publicKey && (
            <div className="pt-1">
              <span className="text-gray-500 text-xs uppercase tracking-wide">Clave pública</span>
              <p className="font-mono text-xs break-all">{doc.publicKey}</p>
            </div>
          )}
          {doc.metadata && (
            <div>
              <span className="text-gray-500 text-xs uppercase tracking-wide">Metadata</span>
              <p className="text-xs break-all">{doc.metadata}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DIDResolver;
