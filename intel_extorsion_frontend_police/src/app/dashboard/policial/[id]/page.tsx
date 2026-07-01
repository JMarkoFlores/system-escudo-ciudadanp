'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { denunciaService, alertaService } from '@/services/api';
import { Denuncia } from '@/types';
import {
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
  User,
  ShieldCheck,
  FileAudio,
  Image as ImageIcon,
  Play,
  RotateCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

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

export default function DetalleDenunciaPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [denuncia, setDenuncia] = useState<Denuncia | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const [archivos, setArchivos] = useState<Array<{index: number; path: string; filename: string; tipo: string; principal: boolean; existe?: boolean; mime?: string}>>([]);
  const [archivoActivo, setArchivoActivo] = useState(0);
  const [alertasDenuncia, setAlertasDenuncia] = useState<any[]>([]);

  const fetchDenuncia = async () => {
    try {
      const { data } = await denunciaService.obtener(id);
      setDenuncia(data);
      // Cargar archivos adicionales
      try {
        const archRes = await denunciaService.listarArchivos(id);
        setArchivos(archRes.data.archivos || []);
      } catch {
        setArchivos([]);
      }
      // Cargar alertas
      try {
        const alertRes = await alertaService.obtenerPorDenuncia(id);
        setAlertasDenuncia(alertRes.data.alertas || []);
      } catch {
        setAlertasDenuncia([]);
      }
    } catch (e: any) {
      toast.error('Error al cargar los detalles de la denuncia');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchDenuncia();
    }
  }, [id]);

  const handleReprocesar = async () => {
    setProcessing(true);
    try {
      await denunciaService.procesar(id, 'completo');
      toast.success('Análisis de agentes reiniciado con éxito');
      fetchDenuncia();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error al procesar la denuncia');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
        <p className="text-slate-500 text-sm">Cargando expediente forense...</p>
      </div>
    );
  }

  if (!denuncia) {
    return (
      <div className="bg-white border rounded-xl p-8 text-center max-w-lg mx-auto mt-12 shadow-sm">
        <AlertTriangle className="text-red-500 mx-auto mb-4" size={48} />
        <h2 className="text-xl font-bold text-slate-800 mb-2">Expediente no encontrado</h2>
        <p className="text-slate-500 mb-6 text-sm">
          La denuncia solicitada no existe o no pudo ser recuperada del sistema.
        </p>
        <Link
          href="/dashboard/policial"
          className="inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition text-sm"
        >
          <ArrowLeft size={16} className="mr-2" /> Volver al listado
        </Link>
      </div>
    );
  }

  // Agentes que se muestran en el acordeón
  const agentes = [
    { key: 'intake', name: 'Intake Agent', desc: 'Validación forense e ingesta' },
    { key: 'ocr', name: 'OCR Agent', desc: 'Extracción de textos en capturas de pantalla o imágenes' },
    { key: 'speech', name: 'Speech Agent', desc: 'Transcripción Whisper de notas de voz/audios de extorsión' },
    { key: 'nlp', name: 'NLP Agent', desc: 'Clasificación de intenciones, resúmenes y score de amenaza' },
    { key: 'osint', name: 'OSINT Agent', desc: 'Correlación de teléfonos, cuentas y redes sociales' },
    { key: 'correlation', name: 'Correlation Agent', desc: 'Detección de patrones y modus operandi criminal' },
    { key: 'risk', name: 'Risk Agent', desc: 'Evaluación del nivel de riesgo policial' },
    { key: 'seal', name: 'Seal Agent', desc: 'Custodia digital y sellado en zkSYS Blockchain' },
    { key: 'alert', name: 'Alert Agent', desc: 'Generación de alertas y escalamiento a unidades' },
    { key: 'respond', name: 'Respond Agent', desc: 'Retorno de código y mensaje conversacional' },
  ];

  const getAgentResult = (agentKey: string) => {
    // Si la denuncia tiene "resultados", estos son un array de dicts (los resultados_json de cada agente)
    if (!denuncia.resultados) return null;
    return denuncia.resultados.find((r: any) => r.agente === agentKey) as AgentResult | undefined;
  };

  return (
    <div className="space-y-6">
      {/* Navigation & Actions Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Link
            href="/dashboard/policial"
            className="text-slate-400 hover:text-slate-600 bg-white border p-2 rounded-lg hover:shadow-sm transition"
          >
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-800">Expediente Denuncia</h1>
              {denuncia.tracking_code && (
                <span className="font-mono text-xs bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded uppercase tracking-wider">
                  {denuncia.tracking_code}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 font-mono">ID: {denuncia.id}</p>
          </div>
        </div>

        <button
          onClick={handleReprocesar}
          disabled={processing}
          className="inline-flex items-center justify-center bg-white border hover:bg-slate-50 disabled:bg-slate-100 text-slate-700 font-medium px-4 py-2 rounded-lg shadow-sm transition text-sm sm:self-end"
        >
          <RotateCw size={16} className={`mr-2 text-slate-500 ${processing ? 'animate-spin' : ''}`} />
          {processing ? 'Procesando...' : 'Re-analizar Caso'}
        </button>
      </div>

      {/* Banner Caso Resuelto */}
      {denuncia.estado === 'archivado' && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center space-x-3 shadow-sm">
          <CheckCircle2 size={24} className="text-green-600 shrink-0" />
          <div>
            <h2 className="font-semibold text-green-800 text-sm">Caso Resuelto y Archivado</h2>
            <p className="text-xs text-green-700">Esta denuncia ha sido atendida por la unidad policial y marcada como resuelta.</p>
          </div>
        </div>
      )}

      {/* Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: General metadata & Blockchain Custody */}
        <div className="lg:col-span-2 space-y-6">
          {/* Metadata Card */}
          <div className="bg-white border rounded-xl shadow-sm p-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-indigo-600" />
            <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center">
              <FileText size={18} className="mr-2 text-slate-500" /> Información General
            </h2>
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              <div className="space-y-3">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-slate-400">Fecha de Registro:</span>
                  <span className="font-medium text-slate-800">
                    {(() => {
                      const d = new Date(denuncia.created_at);
                      const day = d.getDate();
                      const month = d.toLocaleDateString('es-PE', { month: 'long' });
                      const year = d.getFullYear();
                      const hour = d.getHours().toString().padStart(2, '0');
                      const minute = d.getMinutes().toString().padStart(2, '0');
                      return `${day} de ${month}, ${year} - ${hour}:${minute}`;
                    })()}
                  </span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-slate-400">Canal de Entrada:</span>
                  <span className="font-medium text-slate-800 capitalize">{denuncia.canal}</span>
                </div>
                <div className="flex justify-between border-b pb-2 sm:border-0 sm:pb-0">
                  <span className="text-slate-400">Tipo de Contenido:</span>
                  <span className="font-medium text-slate-800 capitalize">{denuncia.tipo_contenido}</span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-slate-400">Estado de Análisis:</span>
                  <span className="font-semibold text-blue-700 capitalize">
                    {denuncia.estado.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-slate-400">DID Denunciante:</span>
                  <span className="font-mono text-xs text-slate-600 truncate max-w-[150px]" title={denuncia.did_denunciante || 'Anónimo'}>
                    {denuncia.did_denunciante || 'Anónimo / Sin DID'}
                  </span>
                </div>
                <div className="flex justify-between pb-2">
                  <span className="text-slate-400">Nivel de Riesgo:</span>
                  <span className={`font-semibold capitalize px-2 py-0.5 rounded text-xs ${
                    denuncia.nivel_riesgo === 'critico' ? 'bg-red-100 text-red-800 border border-red-200' :
                    denuncia.nivel_riesgo === 'alto' ? 'bg-orange-100 text-orange-800 border border-orange-200' :
                    denuncia.nivel_riesgo === 'medio' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                    'bg-green-100 text-green-800 border border-green-200'
                  }`}>
                    {denuncia.nivel_riesgo || 'No Evaluado'}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Raw Content Section */}
            {denuncia.contenido_raw && (
              <div className="mt-5 pt-4 border-t">
                <span className="text-xs text-slate-400 block mb-1">Declaración / Texto Recibido:</span>
                <p className="bg-slate-50 border rounded-lg p-3 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {denuncia.contenido_raw}
                </p>
              </div>
            )}
          </div>

          {/* AI Agents Accordion */}
          <div className="bg-white border rounded-xl shadow-sm p-6">
            <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center">
              <Cpu size={18} className="mr-2 text-slate-500" /> Resultados de Auditoría de IA
            </h2>
            <div className="space-y-3">
              {agentes.map((ag) => {
                const res = getAgentResult(ag.key);
                const isExecuted = !!res;

                return (
                  <div key={ag.key} className="border rounded-lg overflow-hidden transition">
                    <div className={`px-4 py-3 flex items-center justify-between bg-slate-50 ${isExecuted ? 'border-b' : ''}`}>
                      <div className="flex items-center space-x-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${
                          isExecuted ? (res.exitoso !== false ? 'bg-green-500' : 'bg-red-500') : 'bg-slate-300'
                        }`} />
                        <span className="font-semibold text-sm text-slate-700">{ag.name}</span>
                        <span className="text-xs text-slate-400 hidden sm:inline">— {ag.desc}</span>
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase ${
                        isExecuted ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'
                      }`}>
                        {isExecuted ? 'Ejecutado' : 'Omitido'}
                      </span>
                    </div>

                    {isExecuted && (
                      <div className="p-4 bg-white text-xs font-mono text-slate-600 space-y-3 overflow-x-auto">
                        {ag.key === 'intake' && (
                          <div className="grid sm:grid-cols-2 gap-3 text-slate-700">
                            <div><span className="text-slate-400">¿Válido?:</span> <span className="font-semibold">{res.valido ? '✓ Sí' : '❌ No'}</span></div>
                            <div><span className="text-slate-400">Prioridad:</span> <span className="font-semibold">{res.prioridad_inicial} / 5</span></div>
                            {res.categoria_preliminar && <div className="sm:col-span-2"><span className="text-slate-400">Categoría preliminar:</span> <span className="font-semibold capitalize">{res.categoria_preliminar}</span></div>}
                            {res.entidades_detectadas && res.entidades_detectadas.length > 0 && (
                              <div className="sm:col-span-2">
                                <span className="text-slate-400 block mb-1">Entidades Detectadas:</span>
                                <div className="flex flex-wrap gap-1 font-sans">
                                  {res.entidades_detectadas.map((ent: any, i: number) => (
                                    <span key={i} className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] border">
                                      {ent.tipo || ent.entity}: {ent.valor || ent.text}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        {ag.key === 'nlp' && (
                          <div className="space-y-3 font-sans text-slate-700 text-sm">
                            <div className="grid sm:grid-cols-2 gap-3 font-mono text-xs">
                              <div><span className="text-slate-400">Sentimiento:</span> <span className="font-semibold capitalize text-orange-600">{res.sentimiento}</span></div>
                              <div><span className="text-slate-400">Score de Amenaza:</span> <span className="font-semibold text-red-600">{res.score_amenaza !== undefined ? `${(res.score_amenaza * 100).toFixed(0)}%` : 'N/A'}</span></div>
                            </div>
                            <div className="border-t pt-2">
                              <span className="text-xs text-slate-400 font-mono block mb-1">Resumen del caso:</span>
                              <p className="text-slate-600 leading-relaxed">{res.resumen}</p>
                            </div>
                            {res.palabras_clave && res.palabras_clave.length > 0 && (
                              <div className="flex flex-wrap gap-1 pt-1 font-mono text-[10px]">
                                {res.palabras_clave.map((tag: string, i: number) => (
                                  <span key={i} className="bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">#{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        {ag.key === 'ocr' && res.texto_extraido && (
                          <div>
                            <span className="text-slate-400 block mb-1">Texto OCR extraído de imagen:</span>
                            <p className="bg-slate-50 border rounded p-3 text-slate-700 italic">"{res.texto_extraido}"</p>
                          </div>
                        )}
                        {ag.key === 'speech' && res.transcripcion && (
                          <div>
                            <span className="text-slate-400 block mb-1">Transcripción Whisper de voz:</span>
                            <p className="bg-slate-50 border rounded p-3 text-slate-700 italic">"{res.transcripcion}"</p>
                          </div>
                        )}
                        {ag.key === 'osint' && (
                          <div className="space-y-2 text-slate-700">
                            <div><span className="text-slate-400">Riesgo OSINT:</span> <span className="font-semibold">{res.riesgo_osint} / 5</span></div>
                            {res.telefonos && res.telefonos.length > 0 && (
                              <div>
                                <span className="text-slate-400 block mb-1">Teléfonos Implicados:</span>
                                <div className="space-y-1">
                                  {res.telefonos.map((tel: any, i: number) => (
                                    <div key={i} className="flex justify-between max-w-md border-b pb-1 font-mono text-xs">
                                      <span className="font-semibold">{tel.numero}</span>
                                      <span className="text-slate-400 text-[10px]">({tel.riesgo || tel.compania || 'Riesgo No Identificado'})</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {res.cuentas_bancarias && res.cuentas_bancarias.length > 0 && (
                              <div>
                                <span className="text-slate-400 block mb-1">Cuentas para depósito de cupos:</span>
                                <div className="space-y-1">
                                  {res.cuentas_bancarias.map((cta: any, i: number) => (
                                    <div key={i} className="flex justify-between max-w-md border-b pb-1 font-mono text-xs">
                                      <span className="font-semibold">{cta.numero}</span>
                                      <span className="text-slate-400 text-[10px]">({cta.titular || 'Titular sin verificar'} - {cta.banco || 'Banco'})</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        {ag.key === 'correlation' && (
                          <div className="space-y-2 text-slate-700">
                            <div><span className="text-slate-400">¿Red Criminal Detectada?:</span> <span className="font-semibold">{res.red_criminal_detectada ? '⚠️ Sí, vinculada a clúster' : 'No'}</span></div>
                            {res.modus_operandi_id && <div><span className="text-slate-400">Modus Operandi ID:</span> <span className="font-semibold">{res.modus_operandi_id}</span></div>}
                            {res.correlaciones && res.correlaciones.length > 0 && (
                              <div>
                                <span className="text-slate-400 block mb-1">Casos Relacionados:</span>
                                <div className="flex flex-wrap gap-1 font-sans">
                                  {res.correlaciones.map((corr: any, i: number) => (
                                    <span key={i} className="bg-orange-50 text-orange-800 border border-orange-200 px-2 py-0.5 rounded text-[10px]">
                                      ID: {(corr.denuncia_relacionada_id || corr.denuncia_id_relacionada || 'N/A').toString().slice(0,8)} (Similitud: {(corr.score_similitud ?? corr.similitud) !== undefined ? `${(((corr.score_similitud ?? corr.similitud) || 0) * 100).toFixed(0)}%` : 'N/A'})
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        {ag.key === 'risk' && (
                          <div className="space-y-2 text-slate-700">
                            <div className="flex justify-between border-b pb-1">
                              <span className="text-slate-400">Nivel de Riesgo:</span>
                              <span className="font-semibold capitalize text-red-600">{res.nivel_riesgo}</span>
                            </div>
                            <div className="flex justify-between border-b pb-1">
                              <span className="text-slate-400">Score de Riesgo:</span>
                              <span className="font-semibold text-red-600">{res.score_numerico !== undefined ? `${(res.score_numerico * 100).toFixed(0)}%` : 'N/A'}</span>
                            </div>
                            {res.factores && res.factores.length > 0 && (
                              <div className="font-sans">
                                <span className="text-slate-400 font-mono block mb-1">Factores determinantes:</span>
                                <ul className="list-disc pl-4 space-y-1 text-slate-600 text-xs">
                                  {res.factores.map((f: string, i: number) => <li key={i}>{f}</li>)}
                                </ul>
                              </div>
                            )}
                            {res.recomendacion_operativa && (
                              <div className="font-sans border-t pt-2">
                                <span className="text-slate-400 font-mono block mb-1">Recomendación PNP:</span>
                                <p className="text-slate-800 font-medium">{res.recomendacion_operativa}</p>
                              </div>
                            )}
                          </div>
                        )}
                        {ag.key === 'respond' && res.mensaje_ciudadano && (
                          <div>
                            <span className="text-slate-400 block mb-1">Mensaje enviado al ciudadano:</span>
                            <p className="bg-slate-50 border rounded p-3 text-slate-700 font-sans whitespace-pre-wrap">{res.mensaje_ciudadano}</p>
                          </div>
                        )}
                        {/* Fallback JSON visualizer for generic key-values */}
                        <details className="mt-2 pt-2 border-t border-slate-100 cursor-pointer">
                          <summary className="text-[10px] text-slate-400 font-sans hover:text-slate-600 transition">Ver salida JSON cruda</summary>
                          <pre className="mt-2 bg-slate-900 text-green-400 p-3 rounded text-[10px] leading-relaxed">
                            {JSON.stringify(res, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Evidencia multimedia & Blockchain Status */}
        <div className="space-y-6">
          {/* Evidence File Viewer */}
          <div className="bg-white border rounded-xl shadow-sm p-6">
            <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center">
              <ImageIcon size={18} className="mr-2 text-slate-500" /> Archivo de Evidencia
              {archivos.length > 1 && (
                <span className="ml-2 text-xs font-normal text-slate-400">
                  ({archivoActivo + 1} / {archivos.length})
                </span>
              )}
            </h2>

            {archivos.length > 0 ? (
              <div className="space-y-4">
                {/* Main Viewer */}
                <div className="border rounded-lg overflow-hidden bg-slate-50 p-2 flex items-center justify-center min-h-[150px] relative">
                  {(() => {
                    const activo = archivos[archivoActivo];
                    const tipo = (activo?.tipo || '').toLowerCase();
                    const src = `/api/agents/denuncias/${denuncia.id}/archivo?index=${activo?.index ?? 0}`;

                    if (tipo === 'imagen' || tipo === 'image' || tipo === 'mixto') {
                      return (
                        <img
                          src={src}
                          alt="Captura de evidencia"
                          className="max-h-[250px] object-contain rounded border shadow-sm"
                        />
                      );
                    }
                    if (tipo === 'audio' || tipo === 'voice') {
                      return (
                        <div className="w-full p-4 flex flex-col items-center justify-center space-y-3">
                          <FileAudio size={48} className="text-blue-500 animate-pulse" />
                          <span className="text-xs text-slate-500">Nota de voz grabada de extorsión</span>
                          <audio src={src} controls className="w-full mt-2" />
                        </div>
                      );
                    }
                    if (tipo === 'video') {
                      return (
                        <video
                          src={src}
                          controls
                          className="max-h-[250px] w-full rounded border shadow-sm"
                        />
                      );
                    }
                    return (
                      <div className="text-center p-4">
                        <FileText size={36} className="text-slate-400 mx-auto mb-2" />
                        <span className="text-xs text-slate-500 break-all">{activo?.filename}</span>
                      </div>
                    );
                  })()}

                  {/* Navigation Arrows */}
                  {archivos.length > 1 && (
                    <>
                      <button
                        onClick={() => setArchivoActivo((prev) => (prev > 0 ? prev - 1 : archivos.length - 1))}
                        className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-slate-600 p-1.5 rounded-full shadow border transition"
                        aria-label="Anterior"
                      >
                        <ChevronLeft size={20} />
                      </button>
                      <button
                        onClick={() => setArchivoActivo((prev) => (prev < archivos.length - 1 ? prev + 1 : 0))}
                        className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-slate-600 p-1.5 rounded-full shadow border transition"
                        aria-label="Siguiente"
                      >
                        <ChevronRight size={20} />
                      </button>
                    </>
                  )}
                </div>

                {/* Thumbnails Grid */}
                {archivos.length > 1 && (
                  <div className="grid grid-cols-5 gap-2">
                    {archivos.map((arch, idx) => {
                      const isActive = idx === archivoActivo;
                      const thumbTipo = (arch.tipo || '').toLowerCase();
                      const isImage = thumbTipo === 'imagen' || thumbTipo === 'image' || thumbTipo === 'mixto';
                      return (
                        <button
                          key={arch.index}
                          onClick={() => setArchivoActivo(idx)}
                          className={`relative border rounded overflow-hidden h-16 flex items-center justify-center transition ${isActive ? 'ring-2 ring-blue-500 border-blue-500' : 'hover:border-slate-300 opacity-70 hover:opacity-100'}`}
                        >
                          {isImage ? (
                            <img
                              src={`/api/agents/denuncias/${denuncia.id}/archivo?index=${arch.index}`}
                              alt={arch.filename}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="flex flex-col items-center justify-center p-1">
                              {thumbTipo === 'audio' || thumbTipo === 'voice' ? <FileAudio size={16} className="text-slate-400" /> : <FileText size={16} className="text-slate-400" />}
                              <span className="text-[8px] text-slate-400 truncate max-w-full mt-0.5">{arch.filename}</span>
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* File Details */}
                <div className="text-xs space-y-1 font-mono text-slate-600 border-t pt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Nombre:</span>
                    <span className="truncate max-w-[150px]" title={archivos[archivoActivo]?.filename || ''}>
                      {archivos[archivoActivo]?.filename || 'Desconocido'}
                    </span>
                  </div>
                  {denuncia.hash_archivo && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">SHA-256:</span>
                      <span className="font-semibold text-blue-600" title={denuncia.hash_archivo}>
                        {denuncia.hash_archivo.slice(0, 8)}...{denuncia.hash_archivo.slice(-8)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : denuncia.url_archivo ? (
              /* Fallback legacy single file */
              <div className="space-y-4">
                <div className="border rounded-lg overflow-hidden bg-slate-50 p-2 flex items-center justify-center min-h-[150px]">
                {denuncia.tipo_contenido === 'imagen' || denuncia.tipo_contenido === 'mixto' ? (
                  <img
                    src={`/api/agents/denuncias/${denuncia.id}/archivo`}
                    alt="Captura de evidencia"
                    className="max-h-[250px] object-contain rounded border shadow-sm"
                  />
                ) : denuncia.tipo_contenido === 'audio' ? (
                  <div className="w-full p-4 flex flex-col items-center justify-center space-y-3">
                    <FileAudio size={48} className="text-blue-500 animate-pulse" />
                    <span className="text-xs text-slate-500">Nota de voz grabada de extorsión</span>
                    <audio
                      src={`/api/agents/denuncias/${denuncia.id}/archivo`}
                      controls
                      className="w-full mt-2"
                    />
                  </div>
                ) : denuncia.tipo_contenido === 'video' ? (
                  <video
                    src={`/api/agents/denuncias/${denuncia.id}/archivo`}
                    controls
                    className="max-h-[250px] w-full rounded border shadow-sm"
                  />
                ) : (
                  <div className="text-center p-4">
                    <FileText size={36} className="text-slate-400 mx-auto mb-2" />
                    <span className="text-xs text-slate-500 break-all">{denuncia.url_archivo?.split('/').pop()}</span>
                  </div>
                )}
                </div>
                <div className="text-xs space-y-1 font-mono text-slate-600 border-t pt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Nombre:</span>
                    <span className="truncate max-w-[150px]" title={denuncia.url_archivo.split('/').pop() || ''}>
                      {denuncia.url_archivo.split('/').pop() || 'Desconocido'}
                    </span>
                  </div>
                  {denuncia.hash_archivo && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">SHA-256:</span>
                      <span className="font-semibold text-blue-600" title={denuncia.hash_archivo}>
                        {denuncia.hash_archivo.slice(0, 8)}...{denuncia.hash_archivo.slice(-8)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 border border-dashed rounded-lg">
                <FileText size={32} className="mx-auto mb-2 opacity-50" />
                <span className="text-xs">No hay archivo adjunto registrado en esta denuncia</span>
              </div>
            )}
          </div>

          {/* Blockchain Seal Details */}
          <div className="bg-white border rounded-xl shadow-sm p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50/20 rounded-full blur-2xl" />
            <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center">
              <Lock size={18} className="mr-2 text-slate-500" /> Preservación Blockchain
            </h2>
            {denuncia.seal_tx_hash ? (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs space-y-3 font-mono text-slate-700">
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Estado Custodia:</span>
                    <span className="text-green-700 font-semibold flex items-center">
                      <CheckCircle2 size={12} className="mr-1 text-green-600" /> {denuncia.seal_status || 'Completado'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Bloque:</span>
                    <span className="font-semibold text-slate-800">{denuncia.seal_block || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400 font-sans">Red:</span>
                    <span className="font-semibold text-slate-800">zkSYS Testnet</span>
                  </div>
                  <div className="pt-2 border-t border-blue-100">
                    <span className="text-slate-400 font-sans block mb-1">Hash de la Transacción:</span>
                    <span className="text-[10px] text-blue-800 break-all select-all font-semibold block bg-white p-2 border rounded">
                      {denuncia.seal_tx_hash}
                    </span>
                  </div>
                </div>

                <a
                  href={`https://explorer-zk.tanenbaum.io/tx/${denuncia.seal_tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-xs shadow-sm cursor-pointer"
                >
                  Ver en zkSYS Explorer <ExternalLink size={12} className="ml-1.5" />
                </a>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 border border-dashed rounded-lg bg-slate-50/50">
                <Lock size={28} className="mx-auto mb-2 opacity-50 text-slate-400" />
                <span className="text-xs block px-4">Evidencia no preservada en blockchain</span>
                <span className="text-[10px] text-slate-400 block px-4 mt-1">
                  (El sellado Web3 se realiza de forma automática únicamente para casos de riesgo ALTO o CRÍTICO)
                </span>
              </div>
            )}
          </div>

          {/* Resoluciones de Alertas */}
          {alertasDenuncia.some((a) => a.atendida && a.metadata_json?.mensaje_resolucion) && (
            <div className="bg-white border rounded-xl shadow-sm p-6">
              <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center">
                <CheckCircle2 size={18} className="mr-2 text-green-500" /> Resoluciones Oficiales
              </h2>
              <div className="space-y-3">
                {alertasDenuncia
                  .filter((a) => a.atendida && a.metadata_json?.mensaje_resolucion)
                  .map((a, idx) => (
                    <div key={idx} className="bg-green-50 border border-green-100 rounded-lg p-4">
                      <p className="text-xs font-semibold text-green-800 mb-1">
                        Alerta: {a.titulo}
                      </p>
                      <p className="text-sm text-green-900 whitespace-pre-wrap">
                        {a.metadata_json.mensaje_resolucion}
                      </p>
                      <p className="text-[10px] text-green-600 mt-2">
                        Atendida {a.metadata_json?.atendida_en ? new Date(a.metadata_json.atendida_en as string).toLocaleString() : ''}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
