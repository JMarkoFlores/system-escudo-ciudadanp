import React, { useState } from 'react';
import { ContractService } from '../services/contractService';

const DIDResolver = ({ provider }) => {
  const [did, setDid] = useState('');
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
      if (!document) {
        setError('DID no encontrado o inactivo');
      } else {
        setDoc(document);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Resolver DID</h2>

      <div className="flex space-x-2">
        <input
          type="text"
          value={did}
          onChange={(e) => setDid(e.target.value)}
          placeholder="did:ethr:rollux:0x..."
          className="flex-1 rounded-md border-gray-300 shadow-sm p-2 border"
        />
        <button
          onClick={handleResolve}
          disabled={loading || !provider}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded"
        >
          {loading ? '...' : 'Resolver'}
        </button>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {doc && (
        <div className="mt-4 bg-gray-50 rounded p-4 text-sm space-y-2">
          <p><span className="font-bold">DID:</span> {doc.did}</p>
          <p><span className="font-bold">Controller:</span> {doc.controller}</p>
          <p><span className="font-bold">Pública Key:</span> {doc.publicKey || 'N/A'}</p>
          <p><span className="font-bold">Documento URI:</span> <a href={doc.documentURI} target="_blank" rel="noreferrer" className="text-blue-600 underline">{doc.documentURI}</a></p>
          <p><span className="font-bold">Activo:</span> {doc.active ? 'Sí' : 'No'}</p>
          <p><span className="font-bold">Creado:</span> {new Date(doc.createdAt * 1000).toLocaleString()}</p>
          <p><span className="font-bold">Reputación:</span> {doc.reputationScore}/10000</p>
          <p><span className="font-bold">Metadata:</span> {doc.metadata}</p>
        </div>
      )}
    </div>
  );
};

export default DIDResolver;
