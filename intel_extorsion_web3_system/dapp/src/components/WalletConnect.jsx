import React from 'react';
import { usePaliWallet } from '../hooks/usePaliWallet';
import ContractService from '../services/contractService';

const WalletConnect = () => {
  const { account, isConnected, chainId, error, connect, disconnect, switchToZkSYS } = usePaliWallet();
  const did = account ? ContractService.getDIDFromAddress(account) : null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-bold mb-4 text-gray-800 flex items-center gap-2">
        <span className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 text-sm">C</span>
        Conexión Web3
      </h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span className="flex-1">{error}</span>
          </div>
          {error.includes('zkSYS') && (
            <button
              onClick={switchToZkSYS}
              className="mt-2 w-full bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition"
            >
              Cambiar a zkSYS Tanenbaum Testnet
            </button>
          )}
        </div>
      )}

      {!isConnected ? (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">Conecta tu Pali Wallet V2 para acceder a la custodia forense descentralizada.</p>
          <button
            onClick={connect}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition shadow-sm"
          >
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              Conectar Pali Wallet
            </span>
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 bg-green-500 rounded-full"></span>
            <span className="text-green-700 font-semibold text-sm">Wallet conectada</span>
            {chainId === 57057 && (
              <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-medium">zkSYS Tanenbaum</span>
            )}
          </div>
          <div className="bg-gray-50 rounded-lg p-3 space-y-1.5 text-sm font-mono">
            <p className="text-gray-500 text-xs font-sans uppercase tracking-wide">Cuenta</p>
            <p className="text-gray-900 break-all">{account}</p>
          </div>
          {did && (
            <div className="bg-indigo-50 rounded-lg p-3 space-y-1.5 text-sm font-mono">
              <p className="text-indigo-500 text-xs font-sans uppercase tracking-wide">Tu DID (Identidad Descentralizada)</p>
              <p className="text-indigo-900 break-all">{did}</p>
            </div>
          )}
          <div className="flex gap-2">
            <a
              href={ContractService.getExplorerAddressUrl(account)}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-blue-600 underline hover:text-blue-800"
            >
              Ver en explorer
            </a>
            <button
              onClick={disconnect}
              className="text-xs text-red-600 underline hover:text-red-800 ml-auto"
            >
              Desconectar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default WalletConnect;
