import React from 'react';
import { usePaliWallet } from './hooks/usePaliWallet';
import WalletConnect from './components/WalletConnect';
import EvidenceUploader from './components/EvidenceUploader';
import EvidenceVerifier from './components/EvidenceVerifier';
import DIDResolver from './components/DIDResolver';

function App() {
  const { provider, isConnected, error } = usePaliWallet();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-slate-900 text-white py-6 shadow-lg">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">IntelExtorsión</h1>
              <p className="text-slate-400 text-sm">Custodia Digital Forense en Blockchain - Syscoin Rollux L2</p>
            </div>
            <div className="text-right text-xs text-slate-400">
              <p>Rollux Mainnet</p>
              <p>Chain ID: 570</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {!window.pali && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <p className="text-yellow-700">
              <strong>Pali Wallet no detectada.</strong> Para usar la DApp, instala la extensión desde{' '}
              <a href="https://paliwallet.com" target="_blank" rel="noreferrer" className="underline font-bold">
                paliwallet.com
              </a>
            </p>
          </div>
        )}

        <WalletConnect />

        {isConnected && (
          <>
            <div className="grid md:grid-cols-2 gap-6">
              <EvidenceUploader provider={provider} />
              <EvidenceVerifier provider={provider} />
            </div>
            <DIDResolver provider={provider} />
          </>
        )}

        {!isConnected && !error && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Conecta tu Pali Wallet para comenzar</p>
            <p className="text-sm mt-2">Registra evidencias, verifica integridad y gestiona identidades descentralizadas</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-6 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm">
          <p>IntelExtorsión Web3 Subsystem v1.0.0</p>
          <p className="mt-1">Powered by Syscoin Rollux L2, Pali Wallet, IPFS & EVM Smart Contracts</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
