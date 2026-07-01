import Link from 'next/link';
import {
  Shield,
  MessageCircle,
  Lock,
  BrainCircuit,
  BarChart3,
  ChevronRight,
  ShieldAlert,
  Wallet,
  FileText,
  MessageSquare,
  Phone,
  Send,
  ArrowRight,
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
                  <div className="text-blue-400">{'>'} Evidence hash sealed on zkSYS Tanenbaum</div>
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
              { icon: Lock, title: 'Custodia Blockchain', desc: 'Evidencias inmutables en zkSYS Tanenbaum Testnet con hash SHA-256, DID y tokens soulbound.' },
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

      {/* Canales de Denuncia */}
      <section id="canales" className="py-24 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-purple-500/3 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-bold mb-6 border border-blue-500/20 uppercase tracking-wider">
              <MessageCircle size={14} className="mr-2" /> Canales de Denuncia
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4">Reporta de Forma Anónima</h2>
            <p className="text-slate-400 max-w-3xl mx-auto leading-relaxed">
              Usa <strong className="text-white">WhatsApp, Telegram o Discord</strong> para enviar tu denuncia de extorsión. 
              El bot te guía paso a paso y genera un <strong className="text-white">código de seguimiento</strong> sin recopilar ningún dato personal.
            </p>
          </div>

          {/* Why no wallet explanation */}
          <div className="bg-gradient-to-r from-slate-900 to-blue-950/20 border border-blue-500/15 rounded-2xl p-8 max-w-3xl mx-auto mb-12">
            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Lock className="text-blue-400" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-bold mb-2">¿Por qué no se usa wallet aquí?</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Los canales de WhatsApp, Telegram y Discord son <strong className="text-white">canal de denuncia anónima</strong>: 
                  el ciudadano no necesita conectar wallet ni crear identidad. El sistema recibe el reporte, lo procesa con IA forense y genera un código de seguimiento (ej. <code className="bg-slate-800 px-1.5 py-0.5 rounded text-blue-300">TRJ-4X9K</code>). 
                  La <strong className="text-white">DApp Web3</strong> (sección inferior) es para quien desee custodiar evidencia con trazabilidad judicial y firma blockchain — eso sí requiere Pali Wallet.
                </p>
              </div>
            </div>
          </div>

          {/* Channel Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {[
              { 
                icon: MessageSquare, 
                title: 'WhatsApp', 
                desc: 'Envía un mensaje directo al bot de WhatsApp. Acepta texto, imágenes de cartas extorsivas y notas de voz.',
                action: 'Abrir WhatsApp',
                href: 'https://wa.me/51902455346?text=Start',
                color: 'from-green-500/15 to-green-500/5',
                borderColor: 'border-green-500/20 hover:border-green-500/40',
                iconColor: 'text-green-400',
                available: true,
              },
              { 
                icon: Send, 
                title: 'Telegram', 
                desc: 'Busca el bot en Telegram y envía tu denuncia. Soporta texto, audios y documentos. Respuestas inmediatas.',
                action: 'Abrir Telegram',
                href: 'https://t.me/intelextorsion_bot',
                color: 'from-sky-500/15 to-sky-500/5',
                borderColor: 'border-sky-500/20 hover:border-sky-500/40',
                iconColor: 'text-sky-400',
                available: true,
              },
              { 
                icon: MessageCircle, 
                title: 'Discord', 
                desc: 'Únete al servidor y usa el canal de denuncias. Ideal para reportes con múltiples archivos adjuntos.',
                action: 'Unirse a Discord',
                href: 'https://discord.gg/4DQ27gaYW',
                color: 'from-indigo-500/15 to-indigo-500/5',
                borderColor: 'border-indigo-500/20 hover:border-indigo-500/40',
                iconColor: 'text-indigo-400',
                available: true,
              },
            ].map((f) => (
              <div key={f.title} className={`bg-gradient-to-br from-slate-900 to-slate-900/80 border ${f.borderColor} rounded-2xl p-6 transition-all duration-300 hover:shadow-xl group relative overflow-hidden`}>
                <div className={`absolute -top-16 -right-16 w-32 h-32 bg-gradient-to-br ${f.color} rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />
                <div className="relative z-10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} border ${f.borderColor} flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-300 mb-4`}>
                    <f.icon className={f.iconColor} size={24} />
                  </div>
                  <h3 className="text-lg font-bold mb-2 group-hover:text-white transition">{f.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-4">{f.desc}</p>
                  {f.available ? (
                    <a 
                      href={f.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white px-4 py-2 rounded-lg font-bold text-sm transition-all duration-300"
                    >
                      <span>{f.action}</span>
                      <ArrowRight size={14} />
                    </a>
                  ) : (
                    <span className="inline-flex items-center space-x-2 bg-slate-800 text-slate-500 px-4 py-2 rounded-lg text-sm cursor-not-allowed">
                      <span>Próximamente</span>
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* How it works */}
          <div className="bg-gradient-to-r from-slate-900 to-slate-900/80 border border-slate-700/50 rounded-2xl p-8 max-w-3xl mx-auto">
            <h3 className="text-lg font-bold mb-4 text-center">Cómo funciona</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              {[
                { step: '1', title: 'Envía tu reporte', desc: 'Escribe, envía una foto o un audio con los detalles de la extorsión.' },
                { step: '2', title: 'Recibe tu código', desc: 'El bot genera un código único TRJ-XXXX para dar seguimiento anónimo.' },
                { step: '3', title: 'Consulta el estado', desc: 'Envía tu código cuando quieras saber qué está pasando con tu caso.' },
              ].map((s) => (
                <div key={s.step} className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center mb-3">{s.step}</div>
                  <h4 className="font-semibold text-sm mb-1">{s.title}</h4>
                  <p className="text-slate-400 text-xs leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Web3 */}
      <section id="web3" className="py-24 relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-blue-500/3 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-teal-500/10 text-teal-400 text-xs font-bold mb-6 border border-teal-500/20 uppercase tracking-wider">
              <Lock size={14} className="mr-2" /> DApp Web3
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4">Custodia Forense Descentralizada</h2>
            <p className="text-slate-400 max-w-3xl mx-auto leading-relaxed">
              Tu canal para aportar evidencia con <strong className="text-white">trazabilidad judicial</strong>, usando una{' '}
              <strong className="text-white">Identidad Descentralizada (DID)</strong> que te permite ser{' '}
              <strong className="text-emerald-300">seudónimo</strong> — identificable ante la DIVINCRI La Libertad solo si tú lo autorizas, sin exposición de tu identidad civil.
            </p>
          </div>

          {/* Features Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {[
              { 
                icon: Wallet, 
                title: 'Identidad Descentralizada', 
                desc: 'Conecta tu Pali Wallet V2 y firma un challenge criptográfico para generar tu DID. No se recopilan nombre, DNI ni correo.',
                color: 'from-purple-500/15 to-purple-500/5',
                borderColor: 'border-purple-500/20 hover:border-purple-500/40',
                iconColor: 'text-purple-400',
              },
              { 
                icon: Lock, 
                title: 'Sellado en Blockchain', 
                desc: 'Sube tu archivo. Se captura hash SHA-256, timestamp UTC, tipo MIME y metadatos técnicos. El hash se sella en la blockchain zkSYS.',
                color: 'from-emerald-500/15 to-emerald-500/5',
                borderColor: 'border-emerald-500/20 hover:border-emerald-500/40',
                iconColor: 'text-emerald-400',
              },
              { 
                icon: FileText, 
                title: 'Acta Forense PDF', 
                desc: 'Descarga el acta digital compatible con el artículo 158-B del CPP peruano: hash, timestamp, DID, bloque y firma del sistema.',
                color: 'from-blue-500/15 to-blue-500/5',
                borderColor: 'border-blue-500/20 hover:border-blue-500/40',
                iconColor: 'text-blue-400',
              },
            ].map((f) => (
              <div key={f.title} className={`bg-gradient-to-br from-slate-900 to-slate-900/80 border ${f.borderColor} rounded-2xl p-6 transition-all duration-300 hover:shadow-xl group relative overflow-hidden`}>
                <div className={`absolute -top-16 -right-16 w-32 h-32 bg-gradient-to-br ${f.color} rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />
                <div className="relative z-10">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} border ${f.borderColor} flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-300 mb-4`}>
                    <f.icon className={f.iconColor} size={24} />
                  </div>
                  <h3 className="text-lg font-bold mb-2 group-hover:text-white transition">{f.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-gradient-to-r from-slate-900 to-teal-950/20 border border-teal-500/15 rounded-2xl p-8 max-w-2xl mx-auto text-center">
            <div className="flex items-center justify-center space-x-2 mb-3">
              <ShieldAlert className="text-teal-400" size={20} />
              <span className="text-sm font-bold text-teal-300">Listo para comenzar</span>
            </div>
            <p className="text-slate-400 text-sm mb-5 leading-relaxed">
              Conecta tu wallet desde el Portal Ciudadano para acceder a la custodia forense descentralizada con trazabilidad judicial completa.
            </p>
            <Link 
              href="/portal"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white px-6 py-3 rounded-xl font-bold text-sm transition-all duration-300 shadow-lg hover:shadow-[0_4px_20px_rgba(13,148,136,0.3)]"
            >
              <span>Abrir Portal Ciudadano</span>
              <ChevronRight size={16} />
            </Link>
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
