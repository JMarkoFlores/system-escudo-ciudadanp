import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { ContractService } from '../services/contractService';

const DIDRegister = ({ provider, account, onDIDChange }) => {
  const [status, setStatus] = useState('checking');
  const [didDoc, setDidDoc] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const did = account ? ContractService.getDIDFromAddress(account) : null;

  const checkDID = async () => {
    if (!provider || !did) return;
    setStatus('checking');
    try {
      const service = new ContractService(provider);
      await service.init();
      const result = await service.hasDID(did);
      if (result.registered) {
        setStatus('registered');
        setDidDoc({
          did: result.doc[0],
          controller: result.doc[1],
          publicKey: result.doc[2],
          active: result.doc[4],
          createdAt: Number(result.doc[5]),
        });
      } else {
        setStatus('unregistered');
      }
    } catch {
      setStatus('unregistered');
    }
  };

  useEffect(() => {
    if (account) checkDID();
  }, [account, provider]);

  const handleRegister = async () => {
    if (!provider || !account) return;
    setLoading(true);
    setError(null);
    try {
      const challenge = `IntelExtorsion-DID-Registration\nAddress: ${account}\nNonce: ${Date.now()}\nTimestamp: ${new Date().toISOString()}\n\nAl firmar este mensaje, aceptas crear una Identidad Descentralizada (DID) en zkSYS Tanenbaum Testnet para el sistema de custodia forense IntelExtorsión.`;
      const hexMsg = ethers.hexlify(ethers.toUtf8Bytes(challenge));
      const signature = await provider.request({
        method: 'personal_sign',
        params: [hexMsg, account],
      });

      const service = new ContractService(provider);
      await service.init();
      const result = await service.registerDID(did, account, signature);

      await checkDID();
      if (onDIDChange) onDIDChange(did);
    } catch (err) {
      setError(err.code === 4001 ? 'Registro cancelado por el usuario.' : err.message || 'Error al registrar DID');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'checking') {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="animate-pulse flex items-center gap-3 text-gray-400 text-sm">
          <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
          Verificando identidad descentralizada...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 text-sm">ID</span>
        Identidad Descentralizada (DID)
      </h2>

      {status === 'registered' && didDoc ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center gap-2 text-green-700 font-semibold text-sm">
            <span>✅</span> DID registrado y activo
          </div>
          <p className="text-xs font-mono text-green-800 break-all">{didDoc.did}</p>
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 pt-1">
            <div><span className="font-medium">Controller:</span> <span className="font-mono">{didDoc.controller?.slice(0, 16)}...{didDoc.controller?.slice(-4)}</span></div>
            <div><span className="font-medium">Creado:</span> {new Date(didDoc.createdAt * 1000).toLocaleDateString()}</div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
            <p className="font-medium">No tienes un DID registrado</p>
            <p className="text-xs mt-1">El DID te permite aportar evidencia con trazabilidad judicial siendo seudónimo: identificable ante la DIVINCRI solo si tú lo autorizas.</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-sm font-mono">
            <span className="text-gray-400 text-xs font-sans">Tu DID será:</span>
            <p className="text-gray-700 mt-1 break-all">{did}</p>
          </div>
          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                Firmando y registrando...
              </span>
            ) : (
              'Registrar DID con mi firma digital'
            )}
          </button>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          <div className="text-xs text-gray-400 leading-relaxed">
            <p>Al registrar, firmarás un challenge criptográfico que prueba la posesión de tu clave privada sin revelarla. Tu DID se ancla en zkSYS Tanenbaum como identidad descentralizada según el estándar W3C DID.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DIDRegister;
