import React from 'react';
import { usePaliWallet } from '../hooks/usePaliWallet';

const WalletConnect = () => {
  const { account, isConnected, error, connect, disconnect, switchToRollux } = usePaliWallet();

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Conexión Web3</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
          {error.includes('Rollux') && (
            <button 
              onClick={switchToRollux}
              className="ml-2 underline font-semibold"
            >
              Cambiar a Rollux
            </button>
          )}
        </div>
      )}

      {!isConnected ? (
        <button
          onClick={connect}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition"
        >
          Conectar Pali Wallet
        </button>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-green-700 font-semibold">Conectado</span>
          </div>
          <p className="text-sm text-gray-600 font-mono break-all">
            <span className="font-bold">Cuenta:</span> {account}
          </p>
          <button
            onClick={disconnect}
            className="text-red-600 hover:text-red-800 text-sm underline"
          >
            Desconectar
          </button>
        </div>
      )}
    </div>
  );
};

export default WalletConnect;
