'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { denunciaService } from '@/services/api';
import {
  ShieldAlert,
  Search,
  ArrowLeft,
  Calendar,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Cpu,
  Lock,
  MessageSquare,
  FileText,
  HelpCircle,
  Clock,
} from 'lucide-react';

interface AgentResult {
  agente: string;
  exitoso?: boolean;
  valido?: boolean;
  nivel_riesgo?: string;
  score_amenaza?: number;
  score_numerico?: number;
  sellado?: boolean;
  tx_hash?: string;
  block_number?: number;
  alerta_generada?: boolean;
  mensaje_ciudadano?: string;
  texto_extraido?: string;
  transcripcion?: string;
  resumen?: string;
  [key: string]: any;
}

interface DenunciaData {
  id: string;
  canal: string;
  estado: string;
  tipo_contenido: string;
  created_at: string;
  resultados: AgentResult[];
  tracking_code: string;
  nivel_riesgo: string | null;
  seal_tx_hash: string | null;
  seal_block: number | null;
  seal_status: string | null;
}

export default function TrackingPage() {
  return (
    <React.Suspense fallback={
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    }>
      <TrackingContent />
    </React.Suspense>
  );
}

function TrackingContent() {
  const searchParams = useSearchParams();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [denuncia, setDenuncia] = useState<DenunciaData | null>(null);

  // Cargar código desde URL si existe
  useEffect(() => {
    const codeParam = searchParams.get('code');
    if (codeParam) {
      setCode(codeParam);
      buscarDenuncia(codeParam);
    }
  }, [searchParams]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return;
    buscarDenuncia(code.trim());
  };

  const buscarDenuncia = async (trackingCode: string) => {
    setLoading(true);
    setError(null);
    setDenuncia(null);
    try {
      const response = await denunciaService.obtenerPorTracking(trackingCode.toUpperCase().trim());
      setDenuncia(response.data as unknown as DenunciaData);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'No se pudo encontrar el código de seguimiento especificado. Verifica que sea correcto.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Mapear agentes para la línea de tiempo
  const agentesDisponibles = [
    { key: 'intake', name: 'Intake Agent', desc: 'Validación de estructura y pertinencia forense' },
    { key: 'ocr', name: 'OCR Agent', desc: 'Extracción de textos en imágenes o documentos' },
    { key: 'speech', name: 'Speech Agent', desc: 'Transcripción y análisis acústico con Groq Whisper' },
    { key: 'nlp', name: 'NLP Agent', desc: 'Análisis de intenciones, resúmenes y score de amenaza' },
    { key: 'osint', name: 'OSINT Agent', desc: 'Correlación de números de teléfono, cuentas y redes sociales' },
    { key: 'correlation', name: 'Correlation Agent', desc: 'Análisis predictivo de patrones y modus operandi' },
    { key: 'risk', name: 'Risk Agent', desc: 'Cálculo del nivel de riesgo policial' },
    { key: 'seal', name: 'Seal Agent', desc: 'Custodia digital y sellado en la blockchain zkSYS' },
    { key: 'alert', name: 'Alert Agent', desc: 'Notificación y escalamiento a dependencias policiales' },
    { key: 'respond', name: 'Respond Agent', desc: 'Generación de código TRJ y respuesta al ciudadano' },
  ];

  const getAgentStatus = (agentKey: string) => {
    if (!denuncia) return 'pending';
    
    // El agente de speech/ocr solo corre si el contenido coincide
    if (agentKey === 'ocr' && denuncia.tipo_contenido !== 'imagen' && denuncia.tipo_contenido !== 'documento' && denuncia.tipo_contenido !== 'mixto') {
      return 'skipped';
    }
    if (agentKey === 'speech' && denuncia.tipo_contenido !== 'audio' && denuncia.tipo_contenido !== 'mixto') {
      return 'skipped';
    }

    const resultado = denuncia.resultados?.find(r => r.agente === agentKey);
    if (resultado) {
      return resultado.exitoso !== false ? 'success' : 'failed';
    }
    
    // Si la denuncia ya está procesada y el agente no está en los resultados, significa que fue omitido
    if (denuncia.estado === 'procesado' || denuncia.estado === 'riesgo_evaluado' || denuncia.estado === 'alerta_generada') {
      return 'skipped';
    }

    return 'pending';
  };

  const getAgentResultData = (agentKey: string) => {
    return denuncia?.resultados.find(r => r.agente === agentKey);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/" className="text-slate-400 hover:text-white transition">
              <ArrowLeft size={20} />
            </Link>
            <ShieldAlert className="text-blue-500" size={24} />
            <span className="font-bold text-lg tracking-tight">Rastreo de Denuncia</span>
          </div>
          <Link href="/portal" className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition">
            Portal Ciudadano
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">
        {/* Search Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
          <h2 className="text-xl font-bold mb-2 flex items-center">
            <Search className="mr-2 text-blue-500" size={20} /> Consulta tu código
          </h2>
          <p className="text-slate-400 text-sm mb-4">
            Ingresa el código en formato <span className="font-mono text-blue-400">TRJ-XXXX</span> provisto por el bot de Telegram o el Portal para verificar su estado de análisis y preservación.
          </p>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Ej: TRJ-AFEZ"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm font-mono focus:border-blue-500 outline-none uppercase tracking-widest text-center text-blue-400"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-semibold px-6 py-3 rounded-xl transition flex items-center justify-center min-w-[120px]"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-white" />
              ) : (
                'Consultar'
              )}
            </button>
          </form>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-8 flex items-start space-x-3">
            <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={20} />
            <span className="text-red-200 text-sm">{error}</span>
          </div>
        )}

        {/* Results */}
        {denuncia && (
          <div className="space-y-8 animate-fadeIn">
            {/* General Info Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl grid md:grid-cols-3 gap-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-600" />
              <div>
                <span className="text-xs text-slate-500 block mb-1">Código de Seguimiento</span>
                <span className="font-mono text-xl font-bold tracking-widest text-blue-400">{denuncia.tracking_code}</span>
              </div>
              <div>
                <span className="text-xs text-slate-500 block mb-1">Fecha de Registro</span>
                <div className="flex items-center text-slate-300 font-medium">
                  <Calendar size={14} className="mr-1.5 text-slate-400" />
                  {new Date(denuncia.created_at).toLocaleDateString([], { day: 'numeric', month: 'long', year: 'numeric' })}
                </div>
              </div>
              <div>
                <span className="text-xs text-slate-500 block mb-1">Canal de Entrada</span>
                <div className="capitalize text-slate-300 font-medium">
                  {denuncia.canal}
                </div>
              </div>
            </div>

            {/* Blockchain Seal Info */}
            {denuncia.seal_tx_hash && (
              <div className="bg-blue-950/20 border border-blue-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl pointer-events-none" />
                <h3 className="text-lg font-bold mb-4 flex items-center text-blue-400">
                  <Lock className="mr-2 text-blue-400 animate-pulse" size={20} /> Preservación Blockchain Activa (Custodia Web3)
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-3">
                    <div className="flex justify-between border-b border-slate-800 pb-2">
                      <span className="text-slate-400">Nivel de Riesgo Evaluado:</span>
                      <span className={`font-semibold capitalize px-2 py-0.5 rounded text-xs ${
                        denuncia.nivel_riesgo === 'critico' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        denuncia.nivel_riesgo === 'alto' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        denuncia.nivel_riesgo === 'medio' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        'bg-green-500/20 text-green-400 border border-green-500/30'
                      }`}>
                        {denuncia.nivel_riesgo}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-slate-800 pb-2">
                      <span className="text-slate-400">Bloque de Registro:</span>
                      <span className="font-mono text-slate-200">{denuncia.seal_block || 'Pendiente'}</span>
                    </div>
                    <div className="flex justify-between pb-2">
                      <span className="text-slate-400">Estado del Sellado:</span>
                      <span className="text-green-400 font-semibold">{denuncia.seal_status || 'Completado'}</span>
                    </div>
                  </div>
                  <div className="space-y-2 flex flex-col justify-end">
                    <span className="text-slate-400 text-xs block">Hash de Transacción (SHA-256 zkSYS):</span>
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 font-mono text-[11px] text-blue-300 break-all select-all flex items-center justify-between">
                      <span>{denuncia.seal_tx_hash}</span>
                    </div>
                    <a
                      href={`${process.env.NEXT_PUBLIC_EXPLORER_URL || 'https://explorer-zk.tanenbaum.io'}/tx/${denuncia.seal_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg transition mt-2 cursor-pointer"
                    >
                      Ver en Explorador zkSYS <ExternalLink size={12} className="ml-1.5" />
                    </a>
                  </div>
                </div>
              </div>
            )}

            {/* AI Agent Timeline */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <h3 className="text-lg font-bold mb-6 flex items-center">
                <Cpu className="mr-2 text-indigo-500" size={20} /> Proceso de Análisis de Inteligencia
              </h3>
              <div className="relative border-l border-slate-800 ml-4 space-y-8 pb-4">
                {agentesDisponibles.map((ag) => {
                  const status = getAgentStatus(ag.key);
                  const resultData = getAgentResultData(ag.key);

                  return (
                    <div key={ag.key} className="relative pl-8 group">
                      {/* Circle indicator */}
                      <span className={`absolute -left-[13px] top-1 flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-bold transition ${
                        status === 'success' ? 'bg-green-950 border-green-500 text-green-400 shadow-[0_0_8px_rgba(34,197,94,0.3)]' :
                        status === 'failed' ? 'bg-red-950 border-red-500 text-red-400' :
                        status === 'skipped' ? 'bg-slate-900 border-slate-800 text-slate-500' :
                        'bg-slate-950 border-slate-800 text-slate-600 animate-pulse'
                      }`}>
                        {status === 'success' ? <CheckCircle2 size={12} /> : 
                         status === 'failed' ? '!' : 
                         status === 'skipped' ? '—' : '•'}
                      </span>

                      {/* Content */}
                      <div>
                        <div className="flex flex-col md:flex-row md:items-center justify-between">
                          <h4 className={`font-semibold text-sm ${
                            status === 'success' ? 'text-white' :
                            status === 'skipped' ? 'text-slate-500' :
                            'text-slate-400'
                          }`}>
                            {ag.name}
                          </h4>
                          <span className={`text-[10px] uppercase font-semibold tracking-wider md:ml-2 mt-1 md:mt-0 px-2 py-0.5 rounded ${
                            status === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                            status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                            status === 'skipped' ? 'bg-slate-950 text-slate-600' :
                            'bg-slate-950 text-slate-500 border border-slate-800 animate-pulse'
                          }`}>
                            {status === 'success' ? 'Ejecutado' : 
                             status === 'failed' ? 'Fallo' : 
                             status === 'skipped' ? 'Omitido' : 'Pendiente'}
                          </span>
                        </div>
                        <p className="text-slate-500 text-xs mt-0.5">{ag.desc}</p>

                        {/* Extra analysis output from agents to citizen (safe data) */}
                        {status === 'success' && resultData && (
                          <div className="mt-2.5 bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-xs text-slate-300 font-mono space-y-2">
                            {ag.key === 'intake' && (
                              <div>
                                <span className="text-slate-500">Pertinencia:</span> {resultData.valido ? '✓ Válida como denuncia' : '❌ Inválida'}
                                {resultData.categoria_preliminar && (
                                  <div className="mt-1"><span className="text-slate-500">Categoría:</span> <span className="text-blue-400 capitalize">{resultData.categoria_preliminar}</span></div>
                                )}
                              </div>
                            )}
                            {ag.key === 'nlp' && (
                              <div className="space-y-1">
                                <div><span className="text-slate-500">Sentimiento:</span> <span className="text-orange-400">{resultData.sentimiento}</span></div>
                                <div><span className="text-slate-500">Resumen forense:</span> <p className="text-slate-300 mt-1 leading-relaxed font-sans">{resultData.resumen}</p></div>
                              </div>
                            )}
                            {ag.key === 'ocr' && resultData.texto_extraido && (
                              <div>
                                <span className="text-slate-500">Texto detectado en evidencia:</span>
                                <p className="text-slate-400 mt-1 line-clamp-2 italic">"{resultData.texto_extraido}"</p>
                              </div>
                            )}
                            {ag.key === 'speech' && resultData.transcripcion && (
                              <div>
                                <span className="text-slate-500">Transcripción de voz:</span>
                                <p className="text-slate-400 mt-1 line-clamp-2 italic">"{resultData.transcripcion}"</p>
                              </div>
                            )}
                            {ag.key === 'risk' && (
                              <div>
                                <span className="text-slate-500">Evaluación:</span> Nivel <span className="text-red-400 font-bold capitalize">{resultData.nivel_riesgo}</span>
                                {resultData.recomendacion_operativa && (
                                  <div className="mt-1 font-sans text-slate-300"><span className="text-slate-500 font-mono">Acción:</span> {resultData.recomendacion_operativa}</div>
                                )}
                              </div>
                            )}
                            {ag.key === 'respond' && resultData.mensaje_ciudadano && (
                              <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-lg p-2.5 mt-1">
                                <span className="text-indigo-400 font-semibold flex items-center mb-1"><MessageSquare size={12} className="mr-1.5" /> Mensaje Oficial al Denunciante:</span>
                                <p className="text-slate-200 font-sans leading-relaxed text-sm whitespace-pre-wrap">{resultData.mensaje_ciudadano}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Official Respond Card if complete */}
            {denuncia.estado === 'procesado' && (
              <div className="bg-gradient-to-r from-emerald-950/25 to-teal-950/25 border border-emerald-500/20 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />
                <h3 className="text-lg font-bold mb-2 flex items-center text-emerald-400">
                  <CheckCircle2 className="mr-2 text-emerald-400" size={20} /> Análisis Finalizado
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-4">
                  El sistema de agentes autónomos ha completado el análisis forense y el registro legal de la evidencia. Tu código de seguimiento e identidad digital (DID) resguardan tus derechos y la veracidad del proceso.
                </p>
              </div>
            )}

            {/* CASO RESUELTO */}
            {denuncia.estado === 'archivado' && (
              <div className="bg-gradient-to-r from-green-950/40 to-emerald-950/40 border border-green-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full blur-2xl pointer-events-none" />
                <h3 className="text-lg font-bold mb-2 flex items-center text-green-400">
                  <CheckCircle2 className="mr-2 text-green-400" size={20} /> Caso Resuelto
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  La Policía Nacional ha atendido y resuelto tu denuncia. El caso ha sido archivado con éxito. Agradecemos tu colaboración ciudadana.
                </p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 bg-slate-950 text-center">
        <p className="text-xs text-slate-600">
          IntelExtorsión. Custodia y preservación de denuncias ciudadanas. Encriptación Web3 zkSYS Tanenbaum Testnet.
        </p>
      </footer>
    </div>
  );
}
