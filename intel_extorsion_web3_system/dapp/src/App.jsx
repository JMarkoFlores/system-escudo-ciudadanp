import React, { useState } from 'react';
import { usePaliWallet } from './hooks/usePaliWallet';
import WalletConnect from './components/WalletConnect';
import DIDRegister from './components/DIDRegister';
import DIDResolver from './components/DIDResolver';
import EvidenceUploader from './components/EvidenceUploader';
import EvidenceVerifier from './components/EvidenceVerifier';
import ChannelConnect from './components/ChannelConnect';
import RevealAuthorization from './components/RevealAuthorization';

function App() {
  const { provider, isConnected, account, error } = usePaliWallet();
  const [activeSection, setActiveSection] = useState('identidad');

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-slate-900 text-white shadow-lg">
        <div className="max-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-blue-500 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-lg">
                IE
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">IntelExtorsión</h1>
                <p className="text-slate-400 text-xs">Custodia Digital Forense Descentralizada</p>
              </div>
            </div>
            <div className="text-right text-xs text-slate-500">
              <p className="font-mono text-emerald-400">zkSYS Tanenbaum Testnet</p>
              <p className="font-mono">Chain ID: 57057</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="bg-gradient-to-r from-indigo-900 via-slate-900 to-purple-900 text-white">
        <div className="max-5xl mx-auto px-4 py-10">
          <div className="max-w-3xl">
            <span className="inline-block bg-emerald-500/20 text-emerald-300 text-xs font-semibold px-3 py-1 rounded-full mb-3">
              🛡️ Inteligencia Ciudadana contra la Extorsión
            </span>
            <h2 className="text-3xl font-bold leading-tight mb-3">
              Aporta Evidencia con Trazabilidad Judicial
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Esta DApp es el canal para ciudadanos que desean contribuir evidencia digital con <strong className="text-white">trazabilidad judicial</strong> usando una <strong className="text-white">Identidad Descentralizada (DID)</strong> que te permite ser <strong className="text-emerald-300">seudónimo</strong> —identificable ante la DIVINCRI La Libertad solo si tú lo autorizas— sin exposición de tu identidad civil en el sistema.
            </p>
            <div className="flex flex-wrap gap-3 mt-4">
              <span className="bg-white/10 text-xs px-3 py-1.5 rounded-lg">🔗 Hash SHA-256 forense</span>
              <span className="bg-white/10 text-xs px-3 py-1.5 rounded-lg">⛓️ Sellado en zkSYS Tanenbaum</span>
              <span className="bg-white/10 text-xs px-3 py-1.5 rounded-lg">🆔 DID W3C estándar</span>
              <span className="bg-white/10 text-xs px-3 py-1.5 rounded-lg">📋 Acta compatible CPP</span>
            </div>
          </div>
        </div>
      </div>

      {/* No Pali Wallet Warning */}
      {!window.pali && (
        <div className="max-5xl mx-auto px-4 mt-6">
          <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
            <p className="text-amber-800 text-sm">
              <strong>⚠️ Pali Wallet V2 no detectada.</strong> Para usar la DApp necesitas la extensión{' '}
              <a href="https://paliwallet.com" target="_blank" rel="noreferrer" className="underline font-bold text-amber-900">
                Pali Wallet
              </a>
              . Instálala, crea una wallet y conecta la red <strong>zkSYS Tanenbaum Testnet</strong>.
            </p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-5xl mx-auto px-4 py-6">
        <WalletConnect />

        {!isConnected && !error && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-10 text-center">
            <div className="text-5xl mb-4">🛡️</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Conecta tu Pali Wallet para comenzar</h3>
            <p className="text-gray-500 text-sm max-w-lg mx-auto leading-relaxed">
              La DApp de IntelExtorsión te permite registrar evidencias digitales con custodia forense en la blockchain de zkSYS Tanenbaum. 
              Tus archivos se hashean con SHA-256, se sellan en un smart contract y se genera un acta digital compatible con el Código Procesal Penal peruano.
            </p>
            <div className="mt-6 grid grid-cols-3 gap-4 max-w-md mx-auto text-xs text-gray-400">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-lg mb-1">🔐</p>
                <p className="font-medium text-gray-600">Hash SHA-256</p>
                <p>Huella digital del archivo</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-lg mb-1">⛓️</p>
                <p className="font-medium text-gray-600">Sellado</p>
                <p>En smart contract</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-lg mb-1">📋</p>
                <p className="font-medium text-gray-600">Acta</p>
                <p>Con trazabilidad judicial</p>
              </div>
            </div>
          </div>
        )}

        {isConnected && (
          <div className="space-y-6">
            {/* Navigation Tabs */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex gap-1">
              {[
                { id: 'identidad', label: '1. Identidad Descentralizada', icon: '🆔' },
                { id: 'evidencia', label: '2. Custodia de Evidencia', icon: '🔒' },
                { id: 'autorizacion', label: '3. Autorización de Revelación', icon: '🔐' },
                { id: 'canales', label: '4. Otros Canales', icon: '📡' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id)}
                  className={`flex-1 py-2.5 px-3 rounded-lg text-sm font-medium transition ${
                    activeSection === tab.id
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-1.5">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Section 1: Identity */}
            {activeSection === 'identidad' && (
              <div>
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm text-blue-800">
                  <p className="font-semibold mb-1">📌 ¿Qué es un DID?</p>
                  <p className="text-xs leading-relaxed">
                    Un <strong>Identificador Descentralizado (DID)</strong> es tu identidad seudónima en el sistema. 
                    No almacenamos nombre, DNI, teléfono ni correo. Solo tu dirección de wallet firma un challenge criptográfico 
                    que prueba que eres el dueño de esa identidad. Este DID se ancla en zkSYS Tanenbaum y es el único 
                    identificador que usamos. Tú controlas cuándo y ante quién revelas tu identidad civil.
                  </p>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <DIDRegister provider={provider} account={account} />
                  <DIDResolver provider={provider} account={account} />
                </div>
              </div>
            )}

            {/* Section 2: Evidence */}
            {activeSection === 'evidencia' && (
              <div>
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6 text-sm text-emerald-800">
                  <p className="font-semibold mb-1">📌 Flujo de custodia forense</p>
                  <ol className="text-xs leading-relaxed list-decimal pl-4 space-y-1">
                    <li><strong>Captura forense:</strong> Se calcula el hash SHA-256 del archivo original ANTES de cualquier procesamiento</li>
                    <li><strong>Timestamp UTC:</strong> Se registra la fecha/hora exacta de recepción en el servidor</li>
                    <li><strong>Metadata técnica:</strong> Tipo MIME, tamaño, dimensiones (si aplica) — sin EXIF ni GPS</li>
                    <li><strong>Sellado primario:</strong> El hash se registra en el smart contract EvidenceRegistry</li>
                    <li><strong>Sellado secundario:</strong> El hash se sella en EvidenceSeal con evento público en blockchain</li>
                    <li><strong>Acta forense:</strong> Se genera un documento con todos los datos para verificación judicial</li>
                  </ol>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <EvidenceUploader provider={provider} account={account} />
                  <EvidenceVerifier provider={provider} />
                </div>
              </div>
            )}

            {/* Section 3: Identity Reveal Authorization */}
            {activeSection === 'autorizacion' && (
              <div>
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6 text-sm text-orange-800">
                  <p className="font-semibold mb-1">📌 Control total de tu identidad</p>
                  <ol className="text-xs leading-relaxed list-decimal pl-4 space-y-1">
                    <li><strong>Solicitud:</strong> La DIVINCRI solicita vincular tu DID con tu identidad civil para un caso</li>
                    <li><strong>Notificación:</strong> Recibes una solicitud con el motivo y detalles del caso</li>
                    <li><strong>Decisión:</strong> Tú decides si autorizas, rechazas o ignoras la solicitud</li>
                    <li><strong>Revocación:</strong> Puedes revocar tu autorización en cualquier momento antes de que se ejecute</li>
                    <li><strong>Trazabilidad:</strong> Cada acción queda registrada en blockchain de forma inmutable</li>
                  </ol>
                </div>
                <RevealAuthorization provider={provider} account={account} />
              </div>
            )}

            {/* Section 4: Channels */}
            {activeSection === 'canales' && (
              <ChannelConnect />
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 mt-12">
        <div className="max-5xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="text-white font-semibold mb-2">IntelExtorsión</h4>
              <p className="text-xs leading-relaxed">
                Plataforma de inteligencia ciudadana para la recepción, análisis y preservación de evidencias digitales relacionadas con extorsión.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-2">Red</h4>
              <p className="text-xs font-mono">zkSYS Tanenbaum Testnet</p>
              <p className="text-xs font-mono">Chain ID: 57057</p>
              <a href="https://explorer-zk.tanenbaum.io" target="_blank" rel="noreferrer" className="text-xs text-blue-400 underline">Explorador de bloques</a>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-2">Canales</h4>
              <div className="text-xs space-y-1">
                <p>💬 WhatsApp: +51 999 999 999</p>
                <p>✈️ Telegram: @IntelExtorsionBot</p>
                <p>🎮 Discord: intel-extorsion</p>
              </div>
            </div>
          </div>
          <div className="border-t border-slate-800 mt-6 pt-4 text-center text-xs">
            <p>Web3 Custodia Forense v2.0.0 — Powered by zkSYS Tanenbaum, Pali Wallet V2 & Smart Contracts</p>
            <p className="mt-1 text-slate-600">Esta DApp no reemplaza los canales oficiales de denuncia (Línea 111, comisaría).</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
