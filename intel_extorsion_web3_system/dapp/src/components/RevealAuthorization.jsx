import React, { useState, useEffect, useCallback } from 'react';
import { ContractService } from '../services/contractService';

const REVEAL_STATES = {
  0: { label: 'Pendiente', color: 'amber', icon: '⏳' },
  1: { label: 'Autorizada', color: 'green', icon: '✅' },
  2: { label: 'Revelada', color: 'blue', icon: '🔓' },
  3: { label: 'Rechazada', color: 'red', icon: '❌' },
  4: { label: 'Expirada', color: 'gray', icon: '⏰' },
};

const RevealAuthorization = ({ provider, account }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  const did = account ? ContractService.getDIDFromAddress(account) : null;

  const fetchRequests = useCallback(async () => {
    if (!provider || !did) return;
    setLoading(true);
    setError(null);

    try {
      const service = new ContractService(provider);
      await service.init();

      const requestIds = await service.getRevealRequestsByCitizen(did);
      const requestData = [];

      for (const id of requestIds) {
        try {
          const req = await service.getRevealRequest(id);
          requestData.push(req);
        } catch (err) {
          console.error(`Error fetching request ${id}:`, err);
        }
      }

      setRequests(requestData.sort((a, b) => b.timestamp - a.timestamp));
    } catch (err) {
      setError(err.message || 'Error al cargar solicitudes');
    } finally {
      setLoading(false);
    }
  }, [provider, did]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleAuthorize = async (requestId) => {
    if (!provider) return;
    setProcessingId(requestId);
    setError(null);
    setSuccess(null);

    try {
      const service = new ContractService(provider);
      await service.init();
      await service.authorizeReveal(requestId);
      setSuccess(`Solicitud #${requestId} autorizada exitosamente. La DIVINCRI ahora puede vincular tu DID con tu identidad para este caso.`);
      await fetchRequests();
    } catch (err) {
      if (err.code === 4001) {
        setError('Autorización cancelada por el usuario.');
      } else {
        setError(err.message || 'Error al autorizar');
      }
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (requestId) => {
    if (!provider) return;
    setProcessingId(requestId);
    setError(null);
    setSuccess(null);

    try {
      const service = new ContractService(provider);
      await service.init();
      await service.rejectReveal(requestId, 'Rechazado por el ciudadano');
      setSuccess(`Solicitud #${requestId} rechazada. Tu identidad permanecerá seudónima para este caso.`);
      await fetchRequests();
    } catch (err) {
      if (err.code === 4001) {
        setError('Rechazo cancelado por el usuario.');
      } else {
        setError(err.message || 'Error al rechazar');
      }
    } finally {
      setProcessingId(null);
    }
  };

  const handleRevoke = async (requestId) => {
    if (!provider) return;
    setProcessingId(requestId);
    setError(null);
    setSuccess(null);

    try {
      const service = new ContractService(provider);
      await service.init();
      await service.revokeAuthorization(requestId);
      setSuccess(`Autorización #${requestId} revocada. La DIVINCRI ya no puede vincular tu identidad para este caso.`);
      await fetchRequests();
    } catch (err) {
      if (err.code === 4001) {
        setError('Revocación cancelada por el usuario.');
      } else {
        setError(err.message || 'Error al revocar');
      }
    } finally {
      setProcessingId(null);
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '—';
    return new Date(timestamp * 1000).toLocaleString('es-PE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeRemaining = (expiresAt) => {
    if (!expiresAt) return '';
    const now = Math.floor(Date.now() / 1000);
    const diff = expiresAt - now;
    if (diff <= 0) return 'Expirada';
    const days = Math.floor(diff / 86400);
    const hours = Math.floor((diff % 86400) / 3600);
    if (days > 0) return `${days}d ${hours}h restantes`;
    return `${hours}h restantes`;
  };

  if (!did) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="text-center text-gray-500 text-sm">
          Conecta tu Pali Wallet para ver las solicitudes de revelación de identidad.
        </div>
      </div>
    );
  }

  const pendingRequests = requests.filter(r => r.state === 0);
  const otherRequests = requests.filter(r => r.state !== 0);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600 text-sm">🔐</span>
        Autorizaciones de Revelación de Identidad
      </h2>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm text-blue-800">
        <p className="font-semibold mb-1">📌 ¿Qué es esto?</p>
        <p className="text-xs leading-relaxed">
          La DIVINCRI puede solicitar vincular tu DID (seudónimo) con tu identidad civil para un caso específico.
          <strong> Tú decides si autorizas o rechazas.</strong> Sin tu autorización explícita, nadie puede vincular tu
          identidad seudónima con tu verdadera identidad.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-700">
          ❌ {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-sm text-green-700">
          ✅ {success}
        </div>
      )}

      {loading && (
        <div className="text-center py-8 text-gray-400">
          <svg className="animate-spin h-6 w-6 mx-auto mb-2" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Cargando solicitudes...
        </div>
      )}

      {!loading && requests.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-3">🛡️</div>
          <p className="font-medium">No tienes solicitudes de revelación</p>
          <p className="text-xs mt-1 text-gray-400">
            Cuando la DIVINCRI necesite vincular tu DID con tu identidad para un caso, recibirás una solicitud aquí.
          </p>
        </div>
      )}

      {pendingRequests.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
            Solicitudes Pendientes ({pendingRequests.length})
          </h3>
          <div className="space-y-4">
            {pendingRequests.map((req) => (
              <div key={req.id} className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-mono text-amber-700">Solicitud #{req.id}</span>
                    <p className="text-sm font-semibold text-gray-800 mt-1">{req.motivoRevelacion}</p>
                  </div>
                  <span className="text-xs text-amber-600 font-medium">
                    {getTimeRemaining(req.expiresAt)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Caso:</span>
                    <span className="ml-1 font-mono">{req.caseId}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Solicitado:</span>
                    <span className="ml-1">{formatDate(req.timestamp)}</span>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-3 text-xs text-gray-600 border border-amber-200">
                  <p className="font-medium text-amber-800 mb-1">⚠️ Importante</p>
                  <p>
                    Si autorizas, la DIVINCRI podrá vincular tu DID <code className="font-mono text-[10px]">{did?.slice(0, 20)}...</code> 
                    {' '}con tu identidad civil para el caso <strong>{req.caseId}</strong>.
                    Esta acción queda registrada en blockchain de forma permanente.
                  </p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleAuthorize(req.id)}
                    disabled={processingId === req.id}
                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
                  >
                    {processingId === req.id ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Firmando...
                      </span>
                    ) : (
                      '✅ Autorizar'
                    )}
                  </button>
                  <button
                    onClick={() => handleReject(req.id)}
                    disabled={processingId === req.id}
                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition text-sm"
                  >
                    ❌ Rechazar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {otherRequests.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Historial</h3>
          <div className="space-y-3">
            {otherRequests.map((req) => {
              const stateInfo = REVEAL_STATES[req.state] || REVEAL_STATES[4];
              return (
                <div key={req.id} className={`bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>{stateInfo.icon}</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full bg-${stateInfo.color}-100 text-${stateInfo.color}-700`}>
                        {stateInfo.label}
                      </span>
                      <span className="text-xs font-mono text-gray-500">#{req.id}</span>
                    </div>
                    <span className="text-xs text-gray-400">{formatDate(req.timestamp)}</span>
                  </div>

                  <p className="text-sm text-gray-700">{req.motivoRevelacion}</p>

                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                    <div>
                      <span>Caso:</span>
                      <span className="ml-1 font-mono">{req.caseId}</span>
                    </div>
                    <div>
                      <span>Expira:</span>
                      <span className="ml-1">{formatDate(req.expiresAt)}</span>
                    </div>
                  </div>

                  {req.state === 1 && (
                    <button
                      onClick={() => handleRevoke(req.id)}
                      disabled={processingId === req.id}
                      className="w-full mt-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition text-xs"
                    >
                      {processingId === req.id ? 'Procesando...' : '🔄 Revocar Autorización'}
                    </button>
                  )}

                  {req.state === 2 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-xs text-blue-700">
                      🔓 Identidad revelada el {formatDate(req.revealedAt)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default RevealAuthorization;
