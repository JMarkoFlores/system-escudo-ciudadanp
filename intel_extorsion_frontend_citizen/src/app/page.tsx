import Link from 'next/link';
import {
  Shield,
  MessageCircle,
  Lock,
  BrainCircuit,
  BarChart3,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Navbar */}
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="text-blue-500" size={28} />
            <span className="font-bold text-xl tracking-tight">IntelExtorsión</span>
          </div>
          <div className="hidden md:flex items-center space-x-8 text-sm text-slate-300">
            <a href="#features" className="hover:text-white transition">Características</a>
            <a href="#canales" className="hover:text-white transition">Canales</a>
            <a href="#web3" className="hover:text-white transition">Web3</a>
            <Link href="/tracking" className="hover:text-white transition">Rastrear Código</Link>
            <Link href="/portal" className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md font-medium transition">
              Portal Ciudadano
            </Link>
            <a href="http://localhost:3001" className="text-slate-300 hover:text-white transition">
              Acceso Policial
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold mb-6 border border-blue-500/20">
                <Shield size={14} className="mr-2" /> Plataforma de Inteligencia Policial
              </div>
              <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6">
                Combatiendo la <span className="text-blue-500">extorsión</span> con tecnología de punta
              </h1>
              <p className="text-lg text-slate-400 mb-8 leading-relaxed">
                IntelExtorsión integra agentes autónomos de IA, procesamiento NLP, OCR, análisis de audio y blockchain Web3 para la recepción, correlación y preservación de evidencias digitales.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/portal" className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold transition">
                  Realizar Denuncia <ChevronRight size={18} className="ml-2" />
                </Link>
                <Link href="/tracking" className="inline-flex items-center justify-center border border-slate-600 hover:border-slate-400 text-slate-300 hover:text-white px-6 py-3 rounded-lg font-semibold transition">
                  Rastrear Denuncia
                </Link>
              </div>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500/20 blur-3xl rounded-full" />
              <div className="relative bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-2xl">
                <div className="flex items-center space-x-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <div className="space-y-3 text-sm font-mono">
                  <div className="text-green-400">$ intel-extorsion analyze --channel whatsapp</div>
                  <div className="text-slate-400">{'>'} Intake Agent: Denuncia válida detectada</div>
                  <div className="text-slate-400">{'>'} NLP Agent: Score amenaza = 0.92</div>
                  <div className="text-slate-400">{'>'} Risk Agent: Nivel CRÍTICO</div>
                  <div className="text-blue-400">{'>'} Evidence hash stored on Rollux L2</div>
                  <div className="text-slate-400">{'>'} Alert emitted to dashboard</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Arquitectura Inteligente</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Ocho agentes autónomos trabajan en conjunto para analizar, correlacionar y preservar cada evidencia.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: BrainCircuit, title: 'Agentes Autónomos', desc: 'Intake, OCR, Speech, NLP, Correlation, OSINT, Risk y Alert Agent con LangGraph y GPT-5.5.' },
              { icon: BarChart3, title: 'Análisis Predictivo', desc: 'Correlación de patrones, detección de redes criminales y scoring de riesgo en tiempo real.' },
              { icon: Lock, title: 'Custodia Blockchain', desc: 'Evidencias inmutables en Syscoin Rollux L2 con hash SHA-256, DID y tokens soulbound.' },
            ].map((f) => (
              <div key={f.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-blue-500/50 transition">
                <f.icon className="text-blue-500 mb-4" size={32} />
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Canales */}
      <section id="canales" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Canales de Denuncia</h2>
            <p className="text-slate-400">Reporta por el canal que más te convenga. Todos convergen en una misma plataforma inteligente.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: MessageCircle, name: 'WhatsApp', color: 'text-green-500', desc: 'Envía mensajes, audios, imágenes o documentos directamente a nuestro bot oficial.' },
              { icon: MessageCircle, name: 'Telegram', color: 'text-sky-500', desc: 'Denuncia de forma anónima o identificada mediante nuestro bot de Telegram.' },
              { icon: MessageCircle, name: 'Discord', color: 'text-indigo-500', desc: 'Canal seguro para comunidades y grupos de apoyo con atención especializada.' },
            ].map((c) => (
              <div key={c.name} className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 text-center hover:bg-slate-800 transition">
                <c.icon className={`mx-auto mb-4 ${c.color}`} size={40} />
                <h3 className="text-xl font-bold mb-2">{c.name}</h3>
                <p className="text-slate-400 text-sm">{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Web3 */}
      <section id="web3" className="py-20 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-4">Identidad Descentralizada</h2>
              <p className="text-slate-400 mb-6">
                Conecta tu Pali Wallet para generar un DID (Identidad Descentralizada) que protege tu privacidad mientras garantiza la autenticidad de tu denuncia.
              </p>
              <ul className="space-y-3 text-sm text-slate-300">
                <li className="flex items-start"><Shield size={16} className="text-blue-500 mr-2 mt-1 shrink-0" /> Denuncias anónimas verificables</li>
                <li className="flex items-start"><Lock size={16} className="text-blue-500 mr-2 mt-1 shrink-0" /> Cadena de custodia digital inmutable</li>
                <li className="flex items-start"><BarChart3 size={16} className="text-blue-500 mr-2 mt-1 shrink-0" /> Trazabilidad completa en Syscoin Rollux L2</li>
              </ul>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-800">
                <span className="text-sm text-slate-400">Wallet conectada</span>
                <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded">Pali Wallet</span>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">DID</span><span className="text-slate-300 font-mono">did:ethr:rollux:0x7a...3f</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Red</span><span className="text-slate-300">Syscoin Rollux (570)</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Evidencias</span><span className="text-slate-300">3 registradas</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-2 mb-4 md:mb-0">
            <ShieldAlert className="text-blue-500" size={20} />
            <span className="font-bold text-lg">IntelExtorsión</span>
          </div>
          <p className="text-slate-500 text-sm">
            Plataforma de inteligencia policial. Tecnología de punta contra la extorsión.
          </p>
        </div>
      </footer>
    </div>
  );
}
