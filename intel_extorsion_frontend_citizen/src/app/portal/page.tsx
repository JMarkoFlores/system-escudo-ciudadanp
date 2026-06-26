'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useWalletStore } from '@/stores/walletStore';
import { denunciaService } from '@/services/api';
import toast from 'react-hot-toast';
import {
  ShieldAlert,
  Send,
  Paperclip,
  Mic,
  Image as ImageIcon,
  MessageCircle,
  Wallet,
  CheckCircle2,
  Loader2,
  ArrowLeft,
  X,
  FileText,
  ExternalLink,
  LayoutDashboard,
  HelpCircle,
  Copy,
  PlusCircle,
  LogOut,
  AlertTriangle,
  Menu,
} from 'lucide-react';
import { Denuncia } from '@/types';

export default function PortalPage() {
  const { account, isConnected, connect, did, error, switchToZkSYS, init, disconnect } = useWalletStore();
  
  useEffect(() => {
    init();
  }, [init]);

  useEffect(() => {
    if (error) {
      toast.error(error, { id: 'wallet-error' });
    }
  }, [error]);

  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'evidencias' | 'ayuda'>('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [denuncias, setDenuncias] = useState<Denuncia[]>([]);
  const [loadingDenuncias, setLoadingDenuncias] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Chat States
  const [chatState, setChatState] = useState<'idle' | 'waiting_for_denuncia'>('idle');
  const [messages, setMessages] = useState<any[]>([
    {
      id: 'welcome',
      role: 'system',
      content:
        '👋 ¡Hola! Bienvenido al Portal Ciudadano de IntelExtorsión.\n\nEstoy aquí para ayudarte a registrar reportes de extorsión de forma segura, anónima y protegida en blockchain.\n\n¿Qué te gustaría hacer hoy? Puedes presionar alguno de los botones rápidos de abajo o escribirme tu consulta.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<'whatsapp' | 'telegram' | 'discord' | 'web'>('web');
  const [attachment, setAttachment] = useState<any | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);
  const mainContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom
  useEffect(() => {
    if (activeTab === 'chat') {
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
      }, 50);
    }
  }, [messages, activeTab]);

  // Load complaints for DID
  const cargarDenuncias = async () => {
    if (!did) return;
    setLoadingDenuncias(true);
    try {
      const { data } = await denunciaService.listar({ did_denunciante: did });
      setDenuncias(data);
    } catch (e) {
      console.error("Error al cargar denuncias", e);
    } finally {
      setLoadingDenuncias(false);
    }
  };

  useEffect(() => {
    if (isConnected && did) {
      cargarDenuncias();
    } else {
      setDenuncias([]);
    }
  }, [isConnected, did]);

  // Scroll to top when tab changes
  useEffect(() => {
    if (mainContainerRef.current) {
      mainContainerRef.current.scrollTop = 0;
    }
  }, [activeTab]);

  // Lock body scroll and reset window scroll when connected to prevent layout shift
  useEffect(() => {
    if (isConnected) {
      window.scrollTo(0, 0);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isConnected]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, type: 'imagen' | 'audio' | 'documento') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const attach = { file, type, preview: '' };

    if (type === 'imagen' && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => {
        attach.preview = reader.result as string;
        setAttachment(attach);
      };
      reader.readAsDataURL(file);
    } else {
      setAttachment(attach);
    }

    e.target.value = '';
  };

  const removeAttachment = () => setAttachment(null);

  const handleSend = async (forcedText?: string) => {
    const textToSend = forcedText !== undefined ? forcedText : input;
    if (!textToSend.trim() && !attachment) return;

    const displayContent = attachment
      ? `${textToSend || ''}\n[Archivo adjunto: ${attachment.file.name} (${attachment.type})]`.trim()
      : textToSend;

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: displayContent,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    if (forcedText === undefined) setInput('');

    // Si el estado conversacional es 'idle' (Saludos o comandos)
    if (chatState === 'idle') {
      const cleanText = textToSend.toLowerCase().trim();
      const saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"];
      const intencionNueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "iniciar denuncia", "denunciar"];

      setLoading(true);
      await new Promise(r => setTimeout(r, 850)); // Simular respuesta asíncrona de IA

      if (saludos.includes(cleanText) || saludos.some(s => cleanText.includes(s))) {
        setMessages((prev) => [...prev, {
          id: `bot-${Date.now()}`,
          role: 'system',
          content: '👋 ¡Hola! Soy tu asistente virtual de IntelExtorsión.\n\nPara iniciar un reporte seguro de extorsión, por favor presiona el botón "Iniciar Reporte" de abajo o escríbeme "denunciar" para activar el asistente de ingesta.',
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      if (intencionNueva.some(i => cleanText.includes(i))) {
        setChatState('waiting_for_denuncia');
        setMessages((prev) => [...prev, {
          id: `bot-${Date.now()}`,
          role: 'system',
          content: '📝 *Asistente de Ingesta Activado.*\n\nPor favor, redacta detalladamente lo sucedido en tu siguiente mensaje (puedes adjuntar capturas, audios o documentos). Asegúrate de incluir datos clave como teléfonos de extorsión o números de cuenta si los tienes.',
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      // Si escribe un código TRJ
      if (cleanText.startsWith("trj-") || (cleanText.length === 8 && cleanText.startsWith("trj"))) {
        setMessages((prev) => [...prev, {
          id: `bot-${Date.now()}`,
          role: 'system',
          content: `🔍 Detecté un código de seguimiento: *${cleanText.toUpperCase()}*.\n\nPuedes consultar el estado del análisis de IA y la custodia en blockchain directamente en nuestro portal de tracking haciendo clic en el botón de abajo.`,
          timestamp: new Date(),
          metadata: { showTrackingButton: cleanText.toUpperCase() }
        }]);
        setLoading(false);
        return;
      }

      // Fallback
      setMessages((prev) => [...prev, {
        id: `bot-${Date.now()}`,
        role: 'system',
        content: '🤖 *Hola. Para poder procesar una denuncia formal de extorsión, primero debemos activar el asistente.*\n\nPor favor, presiona el botón **"Iniciar Reporte"** en el primer mensaje de arriba, o escribe "denunciar" para empezar.',
        timestamp: new Date()
      }]);
      setLoading(false);
      return;
    }

    // Si el estado es 'waiting_for_denuncia' (Procesamiento real)
    if (chatState === 'waiting_for_denuncia') {
      const textVal = textToSend.trim();
      const cleanText = textVal.toLowerCase();

      // 1. Comando de cancelación
      if (cleanText === 'cancelar' || cleanText === 'salir' || cleanText === 'cancel') {
        setChatState('idle');
        setLoading(true);
        await new Promise(r => setTimeout(r, 600));
        setMessages((prev) => [...prev, {
          id: `bot-cancel-${Date.now()}`,
          role: 'system',
          content: '❌ *Reporte cancelado.*\n\nEl asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué te gustaría hacer hoy? Puedes presionar alguno de los botones rápidos de abajo o escribirme tu consulta.',
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      // Filtrar saludos e intenciones de denuncia sin detalles reales
      const saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"];
      const intencionesPuras = [
        "quiero denunciar",
        "quisiera hacer una denuncia",
        "hacer una denuncia",
        "hacer otra denuncia",
        "otra denuncia",
        "nueva denuncia",
        "registrar otra",
        "iniciar denuncia",
        "denunciar",
        "quiero hacer una denuncia",
        "quisiera denunciar",
        "quiero reportar",
        "quisiera reportar",
        "reportar una extorsion",
        "hacer un reporte",
        "quiero hacer un reporte",
        "ayuda por favor",
        "ayudeme",
        "quiero registrar una denuncia"
      ];
      
      const frasesRelleno = [
        "esta bien", "está bien", "ahora te envio", "ahora te envío", "te envio lo necesario", 
        "te envío lo necesario", "ya te envio", "ya te envío", "te lo envio", "te lo envío", 
        "un momento", "un minuto", "un segundo", "espera", "esperame", "espérame", "listo", 
        "ok", "okay", "entendido", "vale", "bien", "espera un momento", "ya te mando", 
        "ahora te mando", "te mando lo necesario", "te lo mando", "voy a redactar", 
        "te envio", "te envío", "te mando", "ahora te paso lo necesario", "ahora te paso",
        "ya te lo envio", "ya te lo envío", "ya te lo paso"
      ];

      const esSaludo = saludos.includes(cleanText) || saludos.some(s => cleanText === s);
      const esIntencionPura = intencionesPuras.includes(cleanText) || intencionesPuras.some(i => cleanText === i) || 
                              (intencionesPuras.some(i => cleanText.includes(i)) && cleanText.length < 50 && !cleanText.match(/\d+/) && !cleanText.includes("soles") && !cleanText.includes("dolares") && !cleanText.includes("pesos") && !cleanText.includes("bcp") && !cleanText.includes("cuenta"));
      
      const esRelleno = frasesRelleno.includes(cleanText) || frasesRelleno.some(f => cleanText === f) ||
                        (frasesRelleno.some(f => cleanText.startsWith(f)) && cleanText.length < 50 && !cleanText.match(/\d+/) && !cleanText.includes("soles") && !cleanText.includes("dolares") && !cleanText.includes("cuenta"));

      if ((esSaludo || esIntencionPura || esRelleno) && !attachment) {
        setLoading(true);
        await new Promise(r => setTimeout(r, 600));
        setMessages((prev) => [...prev, {
          id: `bot-guiado-${Date.now()}`,
          role: 'system',
          content: '📝 *Asistente Esperando Detalles.*\n\n⚠️ No detectamos detalles de la extorsión en tu mensaje.\n\nPor favor, redacta **en un único mensaje consolidado** todo lo sucedido cuando estés listo (incluyendo números de teléfono de extorsionadores, cuentas bancarias, montos, etc.), o envíanos un audio explicativo.\n\n*Si deseas cancelar el reporte actual, escribe **"cancelar"**.*',
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      // Validar longitud mínima
      if (textVal.length < 20 && !attachment) {
        setLoading(true);
        await new Promise(r => setTimeout(r, 600));
        setMessages((prev) => [...prev, {
          id: `bot-${Date.now()}`,
          role: 'system',
          content: '⚠️ *Descripción muy corta.* Para que nuestros agentes de IA puedan realizar un análisis forense coherente, por favor descríbenos los hechos de manera más amplia (mínimo 20 caracteres) o adjunta un archivo válido.',
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const tipoContenido = attachment ? attachment.type : 'texto';
        const contenidoRaw = textVal || `[Denuncia con archivo adjunto: ${attachment?.file.name}]`;

        const { data } = await denunciaService.crear({
          canal: selectedChannel,
          tipo_contenido: tipoContenido,
          contenido_raw: contenidoRaw,
          did_denunciante: did || undefined,
          metadata: attachment
            ? {
                filename: attachment.file.name,
                filetype: attachment.file.type,
                filesize: attachment.file.size,
                attachment_type: attachment.type,
              }
            : undefined,
        });

        // Simular inicio del análisis
        setMessages((prev) => [...prev, {
          id: `bot-proc-${Date.now()}`,
          role: 'system',
          content: `✅ *Denuncia Registrada Exitosamente*\n\nExpediente ID: \`${data.id}\`\n\nNuestros agentes autónomos de IA han iniciado la auditoría de evidencias en segundo plano.`,
          timestamp: new Date()
        }]);

        // Polling para conseguir el tracking_code final del backend
        let intentos = 0;
        const intervalId = setInterval(async () => {
          intentos++;
          try {
            const { data: dData } = await denunciaService.obtener(data.id);
            if (dData.tracking_code || intentos > 8) {
              clearInterval(intervalId);
              const code = dData.tracking_code || "TRJ-FALLO";
              const riesgoStr = dData.nivel_riesgo ? dData.nivel_riesgo.toUpperCase() : "BAJO";
              
              setMessages((prev) => [...prev, {
                id: `bot-final-${Date.now()}`,
                role: 'agent',
                content: `🎫 *Código de Seguimiento Asignado:* \`${code}\`\n⚖️ *Riesgo Estimado:* *${riesgoStr}*\n\nSe ha completado el análisis y el sellado de la cadena de custodia en blockchain.\n\nPuedes ver el expediente interactivo completo en el Portal de Seguimiento.`,
                timestamp: new Date(),
                metadata: { trackingCode: code }
              }]);
              setChatState('idle'); // Reiniciar estado
              cargarDenuncias(); // Recargar la lista
            }
          } catch (e) {
            clearInterval(intervalId);
          }
        }, 2000);

      } catch (err: any) {
        toast.error('Error al registrar denuncia');
        setMessages((prev) => [...prev, {
          id: `bot-err-${Date.now()}`,
          role: 'system',
          content: `❌ *Error al procesar la denuncia:* ${err.response?.data?.detail || 'Servidor no disponible'}`,
          timestamp: new Date()
        }]);
      } finally {
        setLoading(false);
        setAttachment(null);
      }
    }
  };

  // Counts for connected dashboard
  const selladasCount = denuncias.filter(d => d.seal_status === 'success' || !!d.seal_tx_hash).length;
  const enProcesoCount = denuncias.filter(d => !d.tracking_code).length;
  const notificadasCount = denuncias.filter(d => {
    const r = d.nivel_riesgo?.toLowerCase();
    return r === 'alto' || r === 'critico';
  }).length;
  const clustersCount = denuncias.filter(d => d.nivel_riesgo?.toLowerCase() === 'critico' || d.nivel_riesgo?.toLowerCase() === 'alto').length > 0 ? 1 : 0;

  // Render Sub-Views
  const renderDashboard = () => {
    const copyToClipboard = () => {
      if (!did) return;
      navigator.clipboard.writeText(did);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
      toast.success('DID copiado al portapapeles');
    };

    return (
      <div className="space-y-6 w-full animate-fadeIn">
        {/* Profile Card */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-full blur-xl pointer-events-none" />
          <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-2">
            Tu Identidad Descentralizada (DID)
          </span>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <span className="font-mono text-sm text-teal-300 break-all select-all">{did}</span>
            <button
              onClick={copyToClipboard}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl border border-slate-700 transition flex items-center space-x-2 shrink-0 self-start md:self-center font-semibold shadow-sm"
            >
              <Copy size={14} />
              {isCopied ? <span>¡Copiado!</span> : <span>Copiar DID</span>}
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-4 flex items-center space-x-2">
            <span>🛡️</span>
            <span>No se recopilan datos personales. Anonimato garantizado por protocolo DID W3C.</span>
          </p>
        </div>

        {/* KPIs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-teal-500/30 transition group hover:shadow-[0_4px_20px_rgba(13,148,136,0.05)]">
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Evidencias Selladas</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-teal-400 transition">{selladasCount}</span>
              <span className="text-sm text-teal-400 font-bold">✓</span>
            </div>
            <span className="text-xs text-slate-500 font-mono">Blockchain zkSYS</span>
          </div>

          <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-amber-500/30 transition group hover:shadow-[0_4px_20px_rgba(245,158,11,0.05)]">
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">En Proceso</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-amber-400 transition">{enProcesoCount}</span>
            </div>
            <span className="text-xs text-slate-500">Agentes ejecutándose</span>
          </div>

          <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-blue-500/30 transition group hover:shadow-[0_4px_20px_rgba(59,130,246,0.05)]">
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Autoridades Notif.</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-blue-400 transition">{notificadasCount}</span>
            </div>
            <span className="text-xs text-slate-500">Riesgo Alto / Crítico</span>
          </div>

          <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-purple-500/30 transition group hover:shadow-[0_4px_20px_rgba(168,85,247,0.05)]">
            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Clústeres Activos</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-purple-400 transition">{clustersCount}</span>
            </div>
            <span className="text-xs text-slate-500">Coincidencias en Trujillo</span>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Cluster Warning Banner */}
            {clustersCount > 0 && (
              <div className="bg-red-950/20 border border-red-500/30 rounded-2xl p-5 shadow-lg flex items-start space-x-4">
                <AlertTriangle className="text-red-400 mt-0.5 shrink-0 animate-pulse" size={24} />
                <div>
                  <h4 className="text-sm font-bold text-red-300 uppercase tracking-wider mb-1">Clúster Criminal Detectado</h4>
                  <p className="text-xs md:text-sm text-red-400 leading-relaxed">
                    Nuestros agentes de correlación han identificado un patrón activo de extorsión coincidente con tu caso en Trujillo. Tus evidencias han sido vinculadas de forma inmutable para robustecer la investigación penal de la fiscalía.
                  </p>
                </div>
              </div>
            )}

            {/* Recent Evidences List */}
            <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-5">
                <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Evidencias Recientes</h4>
                <button
                  onClick={() => setActiveTab('evidencias')}
                  className="text-xs text-teal-400 hover:text-teal-300 font-bold transition hover:underline"
                >
                  Ver todas →
                </button>
              </div>

              {loadingDenuncias ? (
                <div className="py-12 flex justify-center items-center">
                  <Loader2 className="animate-spin text-teal-400" size={24} />
                </div>
              ) : denuncias.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  No se han registrado evidencias con este DID.
                </div>
              ) : (
                <div className="divide-y divide-slate-800/80">
                  {denuncias.slice(0, 3).map((d) => (
                    <div key={d.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 first:pt-0 last:pb-0">
                      <div className="flex items-center space-x-4 truncate">
                        <div className="w-10 h-10 rounded-xl bg-slate-800/50 flex items-center justify-center text-slate-400 shrink-0 border border-slate-800">
                          <FileText size={18} />
                        </div>
                        <div className="truncate space-y-0.5">
                          <span className="text-sm font-bold text-slate-200 block">
                            {d.tracking_code || 'En proceso de custodia...'}
                          </span>
                          <span className="text-xs text-slate-500 block uppercase">
                            {new Date(d.created_at).toLocaleDateString([], { day: '2-digit', month: 'short', year: 'numeric' })} · {d.tipo_contenido} · {d.canal}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 shrink-0 self-end sm:self-center">
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border tracking-wide ${
                          d.nivel_riesgo?.toLowerCase() === 'critico'
                            ? 'bg-red-500/10 text-red-400 border-red-500/20'
                            : d.nivel_riesgo?.toLowerCase() === 'alto'
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                            : d.nivel_riesgo?.toLowerCase() === 'medio'
                            ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                            : 'bg-slate-800/40 text-slate-400 border-slate-700/80'
                        }`}>
                          {d.nivel_riesgo ? d.nivel_riesgo.toUpperCase() : 'PENDIENTE'}
                        </span>
                        
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border tracking-wide ${
                          d.seal_status === 'success' || !!d.seal_tx_hash
                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                            : 'bg-slate-800/40 text-slate-400 border-slate-700/80'
                        }`}>
                          {d.seal_status === 'success' || !!d.seal_tx_hash ? 'SELLADO' : 'CUSTODIA'}
                        </span>

                        {d.tracking_code && (
                          <Link
                            href={`/tracking?code=${d.tracking_code}`}
                            className="text-xs bg-slate-850 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-xl border border-slate-700 transition font-semibold"
                          >
                            Auditar
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Acciones de Emergencia</h4>
              
              <button
                onClick={() => setActiveTab('chat')}
                className="w-full group bg-gradient-to-r from-teal-900/20 to-slate-800 border border-teal-500/20 hover:border-teal-500/40 rounded-xl p-4 text-left transition flex items-center space-x-4 shadow-sm"
              >
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal-400 shrink-0 group-hover:scale-105 transition shadow-inner">
                  <PlusCircle size={20} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">Subir Evidencia</h4>
                  <p className="text-xs text-slate-400 mt-0.5">Reportar audio, chat o número extorsionador.</p>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('evidencias')}
                className="w-full group bg-slate-800 border border-slate-700 hover:border-slate-650 rounded-xl p-4 text-left transition flex items-center space-x-4 shadow-sm"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center text-slate-400 shrink-0 group-hover:scale-105 transition shadow-inner">
                  <FileText size={20} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">Ver Mis Evidencias</h4>
                  <p className="text-xs text-slate-400 mt-0.5 font-medium">Historial completo con enlaces de blockchain.</p>
                </div>
              </button>
            </div>

            {/* Quick Tips */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 text-xs text-slate-400 space-y-3 leading-relaxed">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <span>💡</span> <span>Consejo Útil</span>
              </h4>
              <p>
                Recuerda que cada reporte recibe un código único de custodia <strong className="text-teal-450 font-bold">TRJ-XXXX</strong>.
              </p>
              <p>
                Puedes compartir este código con fiscalías o autoridades policiales para que auditen el expediente inmutable y la validez forense en la blockchain zkSYS.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderEvidencias = () => {
    if (loadingDenuncias) {
      return (
        <div className="py-16 flex justify-center items-center">
          <Loader2 className="animate-spin text-teal-400" size={32} />
        </div>
      );
    }

    if (denuncias.length === 0) {
      return (
        <div className="text-center py-16 bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl max-w-lg mx-auto shadow-md">
          <FileText className="mx-auto text-slate-600 mb-3" size={40} />
          <h3 className="font-semibold text-slate-300 text-sm mb-1">Sin evidencias registradas</h3>
          <p className="text-xs text-slate-500 mb-5 max-w-xs mx-auto">
            Aún no has registrado ningún reporte de extorsión con este DID.
          </p>
          <button
            onClick={() => setActiveTab('chat')}
            className="bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-md"
          >
            📝 Registrar Primera Evidencia
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-4 w-full animate-fadeIn">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Historial de Evidencias</h3>
          <span className="text-xs text-slate-400 font-mono">{denuncias.length} registros</span>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {denuncias.map((d) => (
            <div key={d.id} className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-5 hover:border-slate-700/80 transition flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-md group">
              <div className="space-y-3 truncate max-w-full md:max-w-xl">
                <div className="flex items-center flex-wrap gap-2">
                  <span className="text-base font-bold text-white group-hover:text-teal-400 transition">
                    Expediente {d.tracking_code || 'Custodiando...'}
                  </span>
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono uppercase font-bold border border-slate-750">
                    {d.tipo_contenido}
                  </span>
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono uppercase font-bold border border-slate-750">
                    {d.canal}
                  </span>
                </div>
                <p className="text-sm text-slate-300 truncate leading-relaxed">
                  {d.contenido_raw}
                </p>
                <div className="text-xs text-slate-450 space-y-1.5">
                  <div className="flex items-center space-x-1 text-slate-500">
                    <span>🗓️ Registrado:</span>
                    <span>{new Date(d.created_at).toLocaleString()}</span>
                  </div>
                  {(d.seal_tx_hash || d.seal_status === 'success') && (
                    <div className="flex items-center space-x-1.5 font-mono text-xs text-teal-450">
                      <span className="text-slate-500">TX Hash:</span>
                      <a
                        href={`https://explorer.genesis.zksys.io/tx/${d.seal_tx_hash || '0x0000000000000000000000000000000000000000'}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline flex items-center space-x-1 truncate max-w-[280px]"
                      >
                        <span className="truncate">{d.seal_tx_hash || 'Simulado en testnet'}</span>
                        <ExternalLink size={12} />
                      </a>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-row md:flex-col items-center md:items-end gap-3 shrink-0 w-full md:w-auto justify-between border-t md:border-t-0 pt-4 md:pt-0 border-slate-800/80">
                <div className="flex items-center space-x-2 md:mb-1.5">
                  <span className={`text-[10px] font-bold px-3 py-1 rounded-full border tracking-wide uppercase ${
                    d.nivel_riesgo?.toLowerCase() === 'critico'
                      ? 'bg-red-500/10 text-red-400 border-red-500/20'
                      : d.nivel_riesgo?.toLowerCase() === 'alto'
                      ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                      : d.nivel_riesgo?.toLowerCase() === 'medio'
                      ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}>
                    {d.nivel_riesgo ? d.nivel_riesgo : 'PENDIENTE'}
                  </span>
                  <span className={`text-[10px] font-bold px-3 py-1 rounded-full border tracking-wide uppercase ${
                    d.seal_status === 'success' || !!d.seal_tx_hash
                      ? 'bg-green-500/10 text-green-400 border-green-500/20'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}>
                    {d.seal_status === 'success' || !!d.seal_tx_hash ? 'SELLADO' : 'CUSTODIA'}
                  </span>
                </div>

                {d.tracking_code && (
                  <Link
                    href={`/tracking?code=${d.tracking_code}`}
                    className="bg-teal-600 hover:bg-teal-500 text-white font-bold px-4 py-2 rounded-xl text-xs transition flex items-center space-x-1.5 shadow-md hover:shadow-[0_4px_12px_rgba(13,148,136,0.25)]"
                  >
                    <span>Auditar IA & Web3</span>
                    <ExternalLink size={12} />
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderAyuda = () => {
    return (
      <div className="w-full max-w-4xl space-y-6 animate-fadeIn">
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-sm">
          <h3 className="font-bold text-sm text-slate-200 mb-4 uppercase tracking-wider">Glosario de Seguridad</h3>
          <div className="space-y-4 text-xs md:text-sm leading-relaxed text-slate-400">
            <div>
              <h4 className="font-semibold text-slate-300 mb-1">1. Identidad Descentralizada (DID)</h4>
              <p>
                Es un identificador único regulado bajo el estándar del W3C que se genera directamente a partir de tu billetera criptográfica. A diferencia de las cuentas tradicionales, un DID no almacena nombres, correos ni datos personales, garantizando que tu reporte sea 100% anónimo pero verificable.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-300 mb-1">2. Sellado en Blockchain</h4>
              <p>
                Una vez que envías una evidencia (texto, audio o captura de pantalla), calculamos su huella digital criptográfica (SHA-256) y la registramos en la blockchain zkSYS Genesis Testnet. Esto asegura que la evidencia no pueda ser alterada, borrada o manipulada por nadie (incluso por administradores o la policía), preservando la cadena de custodia legal.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-300 mb-1">3. Clústeres y Redes Criminales</h4>
              <p>
                Los agentes de inteligencia correlacionan los números telefónicos, cuentas bancarias de cobro y patrones lingüísticos de las denuncias históricas. Si tu reporte comparte datos con otros reportes en la base de datos de Trujillo, el sistema detecta automáticamente un "clúster" o red delictiva activa.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl p-6 shadow-sm">
          <h3 className="font-bold text-sm text-slate-200 mb-4 uppercase tracking-wider">Preguntas Frecuentes</h3>
          <div className="space-y-4 text-xs md:text-sm leading-relaxed text-slate-400">
            <div>
              <h4 className="font-semibold text-slate-300 mb-1">¿Cómo puedo ver el estado de mi caso?</h4>
              <p>
                Cada reporte recibe un código de seguimiento del tipo <code className="text-teal-300 font-mono font-bold bg-slate-950 px-1.5 py-0.5 rounded">TRJ-XXXX</code>. Puedes usar la pestaña "Mis Evidencias" para hacer clic en "Auditar IA & Web3" o ingresar el código directamente en el Portal de Tracking.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-300 mb-1">¿La policía puede ver mi clave privada o mis fondos?</h4>
              <p>
                No. Conectar tu Pali Wallet solo sirve para firmar digitalmente el reporte de forma anónima y asociarlo a tu DID. El sistema nunca tendrá acceso a tus claves privadas ni a tus activos.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const sidebarItems = [
    { key: 'dashboard' as const, label: 'Panel Principal', icon: LayoutDashboard },
    { key: 'chat' as const, label: 'Nueva Denuncia', icon: MessageCircle },
    { key: 'evidencias' as const, label: 'Mis Evidencias', icon: FileText },
    { key: 'ayuda' as const, label: 'Ayuda', icon: HelpCircle },
  ];

  const renderChat = () => {
    const channels = [
      { key: 'whatsapp' as const, label: 'WhatsApp', color: 'bg-green-600' },
      { key: 'telegram' as const, label: 'Telegram', color: 'bg-sky-600' },
      { key: 'discord' as const, label: 'Discord', color: 'bg-indigo-600' },
      { key: 'web' as const, label: 'Web', color: 'bg-slate-700' },
    ];

    return (
      <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-10rem)] w-full animate-fadeIn">
        {/* Channel selector */}
        <div className="flex space-x-2 mb-4 overflow-x-auto pb-2 shrink-0 select-none">
          {channels.map((ch) => (
            <button
              key={ch.key}
              onClick={() => setSelectedChannel(ch.key)}
              className={`flex items-center px-3.5 py-2 rounded-full text-xs font-semibold transition ${
                selectedChannel === ch.key
                  ? `${ch.color} text-white shadow-md`
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <MessageCircle size={14} className="mr-1.5" />
              {ch.label}
            </button>
          ))}
        </div>

        {/* Chat area */}
        <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-2xl shadow-2xl flex-1 flex flex-col overflow-hidden">
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-teal-600 text-white rounded-br-none shadow-md'
                      : msg.role === 'system'
                      ? 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm'
                      : 'bg-green-950/20 text-green-300 border border-green-500/20 rounded-bl-none shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.content}</p>

                  {msg.id === 'welcome' && chatState === 'idle' && (
                    <div className="mt-4 flex flex-wrap gap-2 select-none">
                      <button
                        onClick={() => {
                          setChatState('waiting_for_denuncia');
                          setMessages((prev) => [
                            ...prev,
                            {
                              id: `bot-start-${Date.now()}`,
                              role: 'system',
                              content: '📝 *Asistente de Ingesta Activado.*\n\nPor favor, redacta detalladamente lo sucedido en tu siguiente mensaje (puedes adjuntar capturas, audios o documentos). Asegúrate de incluir datos clave como teléfonos de extorsión o números de cuenta si los tienes.',
                              timestamp: new Date(),
                            },
                          ]);
                        }}
                        className="flex items-center space-x-1.5 bg-teal-600 hover:bg-teal-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs transition shadow-md hover:shadow-[0_2px_8px_rgba(13,148,136,0.2)]"
                      >
                        <span>📝 Iniciar Reporte</span>
                      </button>
                      <button
                        onClick={() => {
                          setMessages((prev) => [
                            ...prev,
                            {
                              id: `bot-track-${Date.now()}`,
                              role: 'system',
                              content: '🔍 *Rastreo de Denuncia.*\n\nPor favor, escribe tu código de seguimiento (por ejemplo, `TRJ-AFEZ`) en el chat y presiona enviar.',
                              timestamp: new Date(),
                            },
                          ]);
                        }}
                        className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-bold px-4 py-2.5 rounded-xl text-xs transition shadow-sm"
                      >
                        <span>🔍 Rastrear Caso</span>
                      </button>
                    </div>
                  )}

                  {!!msg.metadata?.trackingCode && (
                    <div className="mt-3 select-none">
                      <Link
                        href={`/tracking?code=${String(msg.metadata.trackingCode)}`}
                        className="inline-flex items-center space-x-1.5 bg-green-600 hover:bg-green-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition shadow-md"
                      >
                        <span>Ver Expediente de Rastreo</span>
                        <ExternalLink size={12} />
                      </Link>
                    </div>
                  )}

                  {!!msg.metadata?.showTrackingButton && (
                    <div className="mt-3 select-none">
                      <Link
                        href={`/tracking?code=${String(msg.metadata.showTrackingButton)}`}
                        className="inline-flex items-center space-x-1.5 bg-teal-600 hover:bg-teal-500 text-white font-bold px-4 py-2 rounded-xl text-xs transition shadow-md"
                      >
                        <span>Rastrear Código {String(msg.metadata.showTrackingButton)}</span>
                        <ExternalLink size={12} />
                      </Link>
                    </div>
                  )}

                  <span className="text-[10px] opacity-40 mt-2 block text-right">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-850 rounded-2xl px-5 py-3.5 flex items-center space-x-2 border border-slate-800 shadow-sm animate-pulse">
                  <Loader2 size={16} className="animate-spin text-teal-400" />
                  <span className="text-xs text-slate-400">Analizando evidencias con agentes de IA...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-800 p-3 bg-slate-900/80 shrink-0">
            {/* Attachment preview */}
            {attachment && (
              <div className="mb-2 flex items-center space-x-2 bg-slate-850 border border-slate-800 rounded-xl px-3.5 py-2.5">
                {attachment.type === 'imagen' && attachment.preview ? (
                  <img src={attachment.preview} alt="preview" className="h-10 w-10 object-cover rounded-lg border border-slate-700" />
                ) : attachment.type === 'audio' ? (
                  <Mic size={16} className="text-teal-400 animate-pulse shrink-0" />
                ) : (
                  <FileText size={16} className="text-teal-400 shrink-0" />
                )}
                <span className="text-xs text-slate-200 truncate flex-1 font-semibold">{attachment.file.name}</span>
                <button onClick={removeAttachment} className="text-slate-400 hover:text-red-500 p-1 rounded-full hover:bg-slate-800 transition">
                  <X size={14} />
                </button>
              </div>
            )}

            <div className="flex items-center space-x-2">
              {/* Hidden file inputs */}
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => handleFileSelect(e, 'documento')}
              />
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleFileSelect(e, 'imagen')}
              />
              <input
                ref={audioInputRef}
                type="file"
                accept="audio/*"
                className="hidden"
                onChange={(e) => handleFileSelect(e, 'audio')}
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2.5 text-slate-400 hover:text-slate-200 rounded-full hover:bg-slate-800 transition"
                title="Adjuntar archivo"
              >
                <Paperclip size={18} />
              </button>
              <button
                onClick={() => imageInputRef.current?.click()}
                className="p-2.5 text-slate-400 hover:text-slate-200 rounded-full hover:bg-slate-800 transition"
                title="Adjuntar imagen"
              >
                <ImageIcon size={18} />
              </button>
              <button
                onClick={() => audioInputRef.current?.click()}
                className="p-2.5 text-slate-400 hover:text-slate-200 rounded-full hover:bg-slate-800 transition"
                title="Adjuntar audio"
              >
                <Mic size={18} />
              </button>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={chatState === 'waiting_for_denuncia' ? "Escribe los detalles aquí..." : "Escribe un mensaje o activa el asistente..."}
                className="flex-1 bg-slate-950 border border-slate-850 rounded-full px-5 py-3 text-sm focus:ring-1 focus:ring-teal-500 outline-none text-slate-200 placeholder-slate-500 shadow-inner"
              />
              <button
                onClick={() => handleSend()}
                disabled={(!input.trim() && !attachment) || loading}
                className="p-3 bg-teal-600 hover:bg-teal-550 disabled:bg-slate-850 disabled:text-slate-600 text-white rounded-full transition shadow-md hover:shadow-[0_2px_8px_rgba(13,148,136,0.2)] shrink-0"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="text-[10px] text-slate-500 mt-2.5 text-center">
              Tu denuncia es anónima y custodiada bajo hash SHA-256 en blockchain zkSYS.
            </p>
          </div>
        </div>
      </div>
    );
  };

  // If wallet not connected, render connecting landing card
  if (!isConnected) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col justify-between relative overflow-hidden">
        {/* Background glow animations */}
        <div className="absolute top-[-30%] left-[-10%] w-[600px] h-[600px] bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Navbar */}
        <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="text-teal-400 animate-pulse" size={26} />
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-teal-400 to-blue-500 bg-clip-text text-transparent">IntelExtorsión</span>
            </div>
            <Link href="/" className="text-xs text-slate-400 hover:text-white transition flex items-center space-x-1.5">
              <ArrowLeft size={14} /> <span>Volver a Inicio</span>
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 py-12 max-w-lg mx-auto w-full z-10">
          <div className="w-16 h-16 bg-teal-500/10 border border-teal-500/20 rounded-2xl flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(20,184,166,0.15)] animate-pulse">
            <ShieldAlert className="text-teal-400" size={32} />
          </div>

          <h2 className="text-3xl font-extrabold text-center mb-1 tracking-tight text-white">IntelExtorsión</h2>
          <p className="text-sm text-slate-500 text-center mb-8">Plataforma ciudadana de denuncia · Trujillo, Perú</p>

          <div className="bg-slate-900/60 backdrop-blur border border-slate-800/80 rounded-2xl p-6 w-full shadow-2xl">
            <h3 className="font-bold text-base text-slate-200 mb-2">Conecta tu wallet</h3>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Usa Pali Wallet V2 para conectarte de forma anónima. Se generará automáticamente un DID (Identidad Descentralizada) vinculado a tu denuncia.
            </p>

            <div className="bg-teal-950/20 border border-teal-500/30 rounded-xl px-4 py-3 mb-6 flex items-start space-x-3">
              <CheckCircle2 size={16} className="text-teal-400 mt-0.5 shrink-0" />
              <p className="text-xs text-teal-300 leading-normal">
                No se recopilan datos personales. Tu identidad permanece 100% anónima bajo criptografía W3C.
              </p>
            </div>

            <button
              onClick={connect}
              className="w-full bg-teal-600 hover:bg-teal-550 text-white font-semibold py-3 px-4 rounded-xl transition shadow-[0_4px_12px_rgba(13,148,136,0.25)] flex items-center justify-center space-x-2 text-sm font-bold"
            >
              <Wallet size={16} />
              <span>Conectar Pali Wallet</span>
            </button>
            
            {error && (
              <p className="text-xs text-red-400 mt-3 text-center bg-red-500/10 border border-red-500/20 py-2 px-3 rounded-lg">
                {error}
              </p>
            )}
          </div>

          {/* Features Checklist */}
          <div className="w-full grid grid-cols-1 gap-3 mt-8">
            <div className="bg-slate-900/30 border border-slate-850 rounded-xl p-4 flex items-center space-x-4">
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center text-teal-400 shrink-0">
                <CheckCircle2 size={16} />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Anonimato garantizado</h4>
                <p className="text-[10px] text-slate-505">Tu identidad nunca se almacena ni se expone públicamente.</p>
              </div>
            </div>

            <div className="bg-slate-900/30 border border-slate-850 rounded-xl p-4 flex items-center space-x-4">
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center text-teal-400 shrink-0">
                <Wallet size={16} />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-200">DID automático</h4>
                <p className="text-[10px] text-slate-550">Se genera un identificador descentralizado al conectar.</p>
              </div>
            </div>

            <div className="bg-slate-900/30 border border-slate-855 rounded-xl p-4 flex items-center space-x-4">
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center text-teal-400 shrink-0">
                <ShieldAlert size={16} />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Evidencia inmutable</h4>
                <p className="text-[10px] text-slate-550">Cada denuncia queda sellada y protegida en zkSYS Genesis.</p>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="py-6 border-t border-slate-900 text-center text-[10px] text-slate-500 z-10">
          IntelExtorsión v1.0.0 · Trujillo, Perú · Syscoin zkSYS Genesis Testnet
        </footer>
      </div>
    );
  }

  // Connected View
  return (
    <div className="fixed inset-0 bg-slate-950 text-slate-100 overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Sidebar Overlay (Mobile) */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`absolute top-0 left-0 bottom-0 w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between z-50 transition-transform duration-300 lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 flex-1 flex flex-col overflow-y-auto min-h-0">
          <div className="flex items-center space-x-2.5 mb-6 px-1 select-none">
            <ShieldAlert className="text-teal-400" size={24} />
            <div>
              <span className="font-extrabold text-sm tracking-tight text-white block">IntelExtorsión</span>
              <span className="text-[10px] text-slate-400 block">Syscoin zkSYS · DID</span>
            </div>
          </div>

          {/* DID Card */}
          <div className="bg-teal-950/20 border border-teal-500/30 rounded-xl p-3.5 mb-6 shadow-inner">
            <span className="text-[10px] uppercase font-bold tracking-wider text-teal-400 block mb-1.5 select-none">Tu DID</span>
            <span className="text-[10px] font-mono text-teal-300 break-all select-all block leading-tight">
              {did ? `${did.slice(0, 16)}...${did.slice(-10)}` : 'did:zksys:unknown'}
            </span>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1 flex-1">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  onClick={() => {
                    setActiveTab(item.key);
                    setIsSidebarOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-xl text-xs font-bold transition select-none ${
                    activeTab === item.key
                      ? 'bg-teal-600 text-white shadow-[0_4px_12px_rgba(13,148,136,0.25)]'
                      : 'text-slate-450 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-900/50 shrink-0">
          <div className="text-[10px] text-slate-500 text-center font-mono">
            Chain ID: 57057
          </div>
          <button
            onClick={disconnect}
            className="w-full flex items-center justify-center space-x-2 text-xs font-semibold text-slate-400 hover:text-red-400 transition bg-slate-800 hover:bg-red-500/10 py-2.5 rounded-xl border border-slate-700/60 hover:border-red-500/20"
          >
            <LogOut size={14} />
            <span>Desconectar Wallet</span>
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <main className="absolute top-0 right-0 bottom-0 left-0 lg:left-64 flex flex-col bg-transparent overflow-hidden">
        {/* Top Header */}
        <header className="absolute top-0 left-0 right-0 h-16 border-b border-slate-800 bg-slate-900/40 backdrop-blur px-6 flex items-center justify-between select-none z-10">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 hover:bg-slate-800 rounded-xl lg:hidden text-slate-400 hover:text-white transition"
              title="Menu"
            >
              <Menu size={20} />
            </button>
            <h2 className="font-bold text-xs md:text-sm text-slate-200 uppercase tracking-wider">
              {activeTab === 'dashboard' && 'Panel Principal'}
              {activeTab === 'chat' && 'Nueva Denuncia'}
              {activeTab === 'evidencias' && 'Mis Evidencias'}
              {activeTab === 'ayuda' && 'Ayuda y Glosario'}
            </h2>
          </div>
          <div className="flex items-center space-x-3">
            {error && (
              <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 animate-pulse font-medium">
                Red Errónea
              </span>
            )}
            <div className="text-xs text-teal-400 font-medium flex items-center bg-teal-950/20 px-3 py-1.5 rounded-full border border-teal-500/30 shadow-inner">
              <CheckCircle2 size={12} className="mr-1.5 text-teal-400" /> {account?.slice(0, 8)}...
            </div>
          </div>
        </header>

        {/* Tab Content Container */}
        <div ref={mainContainerRef} className="absolute top-16 left-0 right-0 bottom-0 overflow-y-auto p-4 md:p-8 bg-slate-950">
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'chat' && renderChat()}
          {activeTab === 'evidencias' && renderEvidencias()}
          {activeTab === 'ayuda' && renderAyuda()}
        </div>
      </main>
    </div>
  );
}
