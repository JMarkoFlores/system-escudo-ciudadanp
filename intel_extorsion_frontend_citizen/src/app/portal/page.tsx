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
  const { account, isConnected, connect, did, error, switchToZkSYS, init, disconnect, provider } = useWalletStore();

  useEffect(() => {
    init();
  }, [init]);

  useEffect(() => {
    if (error) {
      toast.error(error, { id: 'wallet-error' });
    }
  }, [error]);

  const handleConnectWallet = async () => {
    const pali = (window as any).pali || (window as any).ethereum;
    if (!pali) {
      toast.error('Pali Wallet no detectada. Instálala desde https://paliwallet.com');
      return;
    }
    try {
      // wallet_requestPermissions SIEMPRE muestra el modal de selección de cuentas
      await pali.request({
        method: 'wallet_requestPermissions',
        params: [{ eth_accounts: {} }],
      });
      // Después de que el usuario elija, leer la cuenta seleccionada (sin modal)
      const accounts = await pali.request({ method: 'eth_accounts' });
      const chainIdHex = await pali.request({ method: 'eth_chainId' });
      const chainId = parseInt(chainIdHex, 16);
      if (accounts && accounts.length > 0) {
        useWalletStore.setState({
          account: accounts[0],
          chainId,
          provider: pali,
          isConnected: true,
          did: `did:zsys:tanenbaum:${accounts[0].toLowerCase()}`,
          error: chainId !== 57057 ? 'Por favor cambia a la red zkSYS Tanenbaum Testnet (Chain ID 57057)' : null,
        });
      }
    } catch (err: any) {
      // Usuario canceló el modal
      if (err?.code === 4001) return;
      console.error('Connection error:', err);
    }
  };

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
        '🛡️ *Bienvenido al Portal Ciudadano de IntelExtorsión*\n\nSoy tu asistente seguro para registrar reportes de extorsión. Tus evidencias se sellan de forma inmutable en la blockchain zkSYS y tu identidad permanece 100% anónima bajo criptografía W3C.\n\n📋 *¿Qué puedes hacer aquí?*\n• Registrar un nuevo reporte de extorsión\n• Adjuntar imágenes, audios o documentos como evidencia\n• Rastrear el estado de un caso existente con tu código TRJ-XXXX\n\nPresiona el botón de abajo para comenzar de forma segura.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const [attachments, setAttachments] = useState<Array<{file: File, type: string, preview: string}>>([]);
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<Record<string, 'pending' | 'uploading' | 'done' | 'error'>>({});
  const addMenuRef = useRef<HTMLDivElement>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);
  const mainContainerRef = useRef<HTMLDivElement>(null);

  const renderMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-slate-700/50 px-1.5 py-0.5 rounded text-teal-300 text-xs font-mono">$1</code>')
      .replace(/\n/g, '<br />');
  };

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

  // Close add menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (addMenuRef.current && !addMenuRef.current.contains(e.target as Node)) {
        setIsAddMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, type: 'imagen' | 'audio' | 'documento') => {
    const files = e.target.files;
    if (!files) return;

    const remaining = 5 - attachments.length;
    const filesToProcess = Array.from(files).slice(0, remaining);

    filesToProcess.forEach((file) => {
      const attach = { file, type, preview: '' };

      if (type === 'imagen' && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          attach.preview = reader.result as string;
          setAttachments((prev) => [...prev, attach]);
        };
        reader.readAsDataURL(file);
      } else {
        setAttachments((prev) => [...prev, attach]);
      }
    });

    if (remaining <= 0 && files.length > 0) {
      toast('Máximo 5 archivos adjuntos', { icon: '⚠️' });
    }

    e.target.value = '';
  };

  const removeAttachment = (index: number) => setAttachments((prev) => prev.filter((_, i) => i !== index));

  const handleSend = async (forcedText?: string) => {
    const textToSend = forcedText !== undefined ? forcedText : input;
    if (!textToSend.trim() && attachments.length === 0) return;

    const attachmentLabels = attachments.map((a) => a.file.name).join(', ');
    const displayContent = attachments.length > 0
      ? `${textToSend || ''}\n[Archivos adjuntos: ${attachmentLabels}]`.trim()
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

      if ((esSaludo || esIntencionPura || esRelleno) && attachments.length === 0) {
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
      if (textVal.length < 20 && attachments.length === 0) {
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
        const primaryType = attachments.length > 0 ? attachments[0].type : 'texto';
        const contenidoRaw = textVal || `[Denuncia con ${attachments.length} archivo(s) adjunto(s)]`;

        const metadataObj: Record<string, any> | undefined = attachments.length > 0
          ? {
              files: attachments.map((a) => ({
                filename: a.file.name,
                filetype: a.file.type,
                filesize: a.file.size,
                attachment_type: a.type,
              })),
            }
          : undefined;

        const { data } = await denunciaService.crear({
          canal: 'web',
          tipo_contenido: primaryType,
          contenido_raw: contenidoRaw,
          did_denunciante: did || undefined,
          metadata: metadataObj,
        });

        // Subir archivos adjuntos secuencialmente
        if (attachments.length > 0) {
          const fileStatuses: Record<string, 'pending' | 'uploading' | 'done' | 'error'> = {};
          attachments.forEach((a) => { fileStatuses[a.file.name] = 'pending'; });
          setUploadingFiles(fileStatuses);

          for (const attach of attachments) {
            setUploadingFiles((prev) => ({ ...prev, [attach.file.name]: 'uploading' }));
            try {
              await denunciaService.adjuntar(data.id, attach.file, attach.type);
              setUploadingFiles((prev) => ({ ...prev, [attach.file.name]: 'done' }));
            } catch (uploadErr) {
              console.error('Error subiendo archivo:', attach.file.name, uploadErr);
              setUploadingFiles((prev) => ({ ...prev, [attach.file.name]: 'error' }));
            }
          }
        }

        // Simular inicio del análisis
        setMessages((prev) => [...prev, {
          id: `bot-proc-${Date.now()}`,
          role: 'system',
          content: `✅ *Denuncia Registrada Exitosamente*\n\nExpediente ID: \`${data.id}\`\n${attachments.length > 0 ? `\n📎 *${attachments.length} archivo(s) adjunto(s) subido(s) exitosamente.*\n` : ''}\nNuestros agentes autónomos de IA han iniciado la auditoría de evidencias en segundo plano.`,
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
        setAttachments([]);
        setUploadingFiles({});
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
        {/* DID Identity Card - Premium */}
        <div className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-teal-950/30 border border-teal-500/20 rounded-2xl p-6 shadow-2xl overflow-hidden group">
          {/* Animated glow */}
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-teal-500/10 rounded-full blur-3xl pointer-events-none group-hover:bg-teal-500/15 transition-all duration-700" />
          <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2.5">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/20 to-blue-500/10 border border-teal-500/30 flex items-center justify-center shadow-inner">
                  <ShieldAlert className="text-teal-400" size={20} />
                </div>
                <div>
                  <span className="text-xs text-teal-400 font-bold uppercase tracking-wider block">Identidad Descentralizada</span>
                  <span className="text-[10px] text-slate-500 font-mono">W3C DID Core 1.0</span>
                </div>
              </div>
              <div className="flex items-center space-x-1.5 bg-teal-500/10 border border-teal-500/20 px-2.5 py-1 rounded-full">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                <span className="text-[10px] text-teal-400 font-bold uppercase tracking-wider">Activo</span>
              </div>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/50 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between gap-4">
                <span className="font-mono text-sm text-teal-300/90 break-all select-all leading-relaxed">{did}</span>
                <button
                  onClick={copyToClipboard}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-xl border border-slate-700/50 transition flex items-center space-x-2 shrink-0 font-semibold shadow-sm hover:border-teal-500/30 active:scale-95"
                >
                  <Copy size={14} />
                  {isCopied ? <span className="text-teal-400">¡Copiado!</span> : <span>Copiar</span>}
                </button>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-[10px]">
              <div className="flex items-center space-x-1.5 text-slate-400">
                <CheckCircle2 size={12} className="text-teal-400" />
                <span>Sin datos personales</span>
              </div>
              <div className="w-px h-3 bg-slate-700" />
              <div className="flex items-center space-x-1.5 text-slate-400">
                <CheckCircle2 size={12} className="text-teal-400" />
                <span>Seudónimo verificable</span>
              </div>
              <div className="w-px h-3 bg-slate-700" />
              <div className="flex items-center space-x-1.5 text-slate-400">
                <span className="font-mono text-blue-400">zkSYS Tanenbaum</span>
                <span>·</span>
                <span className="font-mono text-slate-500">57057</span>
              </div>
            </div>
          </div>
        </div>

        {/* KPIs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-slate-900 to-teal-950/20 border border-teal-500/15 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-teal-500/30 transition-all duration-300 group hover:shadow-[0_4px_24px_rgba(13,148,136,0.08)]">
            <span className="text-xs text-teal-500/80 font-bold uppercase tracking-wider block">Evidencias Selladas</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-teal-400 transition">{selladasCount}</span>
              <span className="text-sm text-teal-400 font-bold">✓</span>
            </div>
            <span className="text-xs text-slate-500 font-mono">Blockchain zkSYS</span>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-amber-950/10 border border-amber-500/10 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-amber-500/25 transition-all duration-300 group hover:shadow-[0_4px_24px_rgba(245,158,11,0.06)]">
            <span className="text-xs text-amber-500/70 font-bold uppercase tracking-wider block">En Proceso</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-amber-400 transition">{enProcesoCount}</span>
            </div>
            <span className="text-xs text-slate-500">Agentes ejecutándose</span>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-blue-950/10 border border-blue-500/10 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-blue-500/25 transition-all duration-300 group hover:shadow-[0_4px_24px_rgba(59,130,246,0.06)]">
            <span className="text-xs text-blue-500/70 font-bold uppercase tracking-wider block">Autoridades Notif.</span>
            <div className="flex items-baseline space-x-2 my-2">
              <span className="text-4xl font-extrabold text-white group-hover:text-blue-400 transition">{notificadasCount}</span>
            </div>
            <span className="text-xs text-slate-500">Riesgo Alto / Crítico</span>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-purple-950/10 border border-purple-500/10 rounded-2xl p-5 shadow-lg flex flex-col justify-between h-32 hover:border-purple-500/25 transition-all duration-300 group hover:shadow-[0_4px_24px_rgba(168,85,247,0.06)]">
            <span className="text-xs text-purple-500/70 font-bold uppercase tracking-wider block">Clústeres Activos</span>
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
            <div className="bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border border-slate-800/80 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Evidencias Recientes</h4>
                  {denuncias.length > 0 && (
                    <span className="text-[10px] bg-teal-500/10 text-teal-400 px-2 py-0.5 rounded-full font-bold border border-teal-500/20">{denuncias.length}</span>
                  )}
                </div>
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
                <div className="space-y-3">
                  {denuncias.slice(0, 3).map((d) => {
                    const isSealed = d.seal_status === 'success' || !!d.seal_tx_hash;
                    return (
                      <div key={d.id} className="bg-slate-950/40 border border-slate-800/50 rounded-xl p-4 hover:border-slate-700/60 transition-all duration-300 group hover:shadow-lg">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="flex items-center space-x-3.5 truncate">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${
                              isSealed 
                                ? 'bg-teal-500/10 border-teal-500/20 text-teal-400' 
                                : 'bg-slate-800/50 border-slate-800 text-slate-400'
                            }`}>
                              {isSealed ? <CheckCircle2 size={18} /> : <FileText size={18} />}
                            </div>
                            <div className="truncate space-y-0.5">
                              <span className="text-sm font-bold text-slate-200 block group-hover:text-teal-400 transition">
                                {d.tracking_code || 'Custodia en proceso...'}
                              </span>
                              <div className="flex items-center flex-wrap gap-1.5 text-[10px] text-slate-500">
                                <span>{new Date(d.created_at).toLocaleDateString([], { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                <span className="text-slate-700">·</span>
                                <span className="text-slate-400 uppercase font-semibold">{d.tipo_contenido}</span>
                                <span className="text-slate-700">·</span>
                                <span className="text-slate-400 uppercase font-semibold">{d.canal}</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
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
                            
                            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border tracking-wide flex items-center space-x-1 ${
                              isSealed
                                ? 'bg-teal-500/10 text-teal-400 border-teal-500/20'
                                : 'bg-slate-800/40 text-slate-400 border-slate-700/80'
                            }`}>
                              {isSealed && <div className="w-1 h-1 rounded-full bg-teal-400 animate-pulse" />}
                              <span>{isSealed ? 'SELLADO' : 'CUSTODIA'}</span>
                            </span>

                            {d.tracking_code && (
                              <Link
                                href={`/tracking?code=${d.tracking_code}`}
                                className="text-[10px] bg-teal-600/80 hover:bg-teal-500 text-white px-3 py-1.5 rounded-lg transition font-bold flex items-center space-x-1 shadow-sm hover:shadow-[0_2px_8px_rgba(13,148,136,0.2)]"
                              >
                                <span>Auditar</span>
                                <ExternalLink size={10} />
                              </Link>
                            )}
                          </div>
                        </div>

                        {isSealed && d.seal_tx_hash && (
                          <div className="mt-3 pt-3 border-t border-slate-800/50 flex items-center space-x-1.5 text-[10px]">
                            <span className="text-slate-500">TX:</span>
                            <a
                              href={`https://explorer-zk.tanenbaum.io/tx/${d.seal_tx_hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-teal-400/80 hover:text-teal-300 font-mono truncate max-w-[280px] flex items-center space-x-1 transition"
                            >
                              <span className="truncate">{d.seal_tx_hash}</span>
                              <ExternalLink size={9} />
                            </a>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Acciones Rápidas</h4>
              
              <button
                onClick={() => setActiveTab('chat')}
                className="w-full group bg-gradient-to-r from-teal-900/30 to-slate-800/50 border border-teal-500/20 hover:border-teal-500/40 rounded-xl p-4 text-left transition-all duration-300 flex items-center space-x-4 shadow-sm hover:shadow-[0_4px_16px_rgba(13,148,136,0.08)]"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500/15 to-teal-500/5 border border-teal-500/20 flex items-center justify-center text-teal-400 shrink-0 group-hover:scale-110 transition-all duration-300 shadow-inner">
                  <PlusCircle size={20} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200 group-hover:text-teal-300 transition">Subir Evidencia</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Audio, chat, número extorsionador o documentos.</p>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('evidencias')}
                className="w-full group bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/60 rounded-xl p-4 text-left transition-all duration-300 flex items-center space-x-4 shadow-sm"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-700/30 border border-slate-700/50 flex items-center justify-center text-slate-400 shrink-0 group-hover:scale-110 transition-all duration-300 shadow-inner">
                  <FileText size={20} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200 group-hover:text-white transition">Ver Mis Evidencias</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Historial con enlaces de verificación blockchain.</p>
                </div>
              </button>
            </div>

            {/* Blockchain Info Card */}
            <div className="bg-gradient-to-br from-teal-950/20 to-slate-900/80 border border-teal-500/10 rounded-2xl p-5 text-xs space-y-3">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                  <ShieldAlert className="text-teal-400" size={16} />
                </div>
                <h4 className="font-bold text-teal-300 uppercase tracking-wider text-[10px]">Custodia Forense</h4>
              </div>
              <div className="space-y-2.5 text-slate-400 leading-relaxed">
                <div className="flex items-start space-x-2">
                  <CheckCircle2 size={12} className="text-teal-400 mt-0.5 shrink-0" />
                  <span>Cada evidencia recibe un hash <strong className="text-teal-300 font-bold font-mono">SHA-256</strong> inmutable.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 size={12} className="text-teal-400 mt-0.5 shrink-0" />
                  <span>El hash se sella en la <strong className="text-teal-300 font-bold">blockchain zkSYS</strong> (testnet).</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 size={12} className="text-teal-400 mt-0.5 shrink-0" />
                  <span>Se genera un <strong className="text-teal-300 font-bold">acta PDF</strong> compatible con el art. 158-B del CPP.</span>
                </div>
              </div>
              <div className="pt-2 mt-2 border-t border-teal-500/10 flex items-center space-x-1.5 text-[10px] text-slate-500">
                <span className="font-mono text-teal-400/70">zkSYS Tanenbaum</span>
                <span>·</span>
                <span className="font-mono">Chain 57057</span>
                <span>·</span>
                <span className="text-teal-400/70">Testnet</span>
              </div>
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
        <div className="text-center py-20 bg-gradient-to-br from-slate-900 to-slate-900/80 border border-slate-800/50 rounded-2xl max-w-lg mx-auto shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center mx-auto mb-4">
            <FileText className="text-teal-400" size={28} />
          </div>
          <h3 className="font-bold text-slate-200 text-sm mb-2">Sin evidencias registradas</h3>
          <p className="text-xs text-slate-500 mb-6 max-w-xs mx-auto leading-relaxed">
            Aún no has registrado ningún reporte de extorsión con este DID. Tu primera evidencia será sellada en blockchain zkSYS.
          </p>
          <button
            onClick={() => setActiveTab('chat')}
            className="bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white text-xs font-bold px-6 py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-[0_4px_16px_rgba(13,148,136,0.3)] flex items-center space-x-2 mx-auto"
          >
            <PlusCircle size={14} />
            <span>Registrar Primera Evidencia</span>
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-5 w-full animate-fadeIn">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Historial de Evidencias</h3>
            <span className="text-[10px] bg-teal-500/10 text-teal-400 px-2.5 py-0.5 rounded-full font-bold border border-teal-500/20">{denuncias.length} registros</span>
          </div>
          <button
            onClick={() => setActiveTab('chat')}
            className="text-xs bg-teal-600/80 hover:bg-teal-500 text-white px-3 py-1.5 rounded-lg transition font-bold flex items-center space-x-1"
          >
            <PlusCircle size={12} />
            <span>Nueva</span>
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {denuncias.map((d) => {
            const isSealed = d.seal_status === 'success' || !!d.seal_tx_hash;
            return (
              <div key={d.id} className={`bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border rounded-2xl p-5 transition-all duration-300 shadow-md group ${
                isSealed ? 'border-teal-500/15 hover:border-teal-500/30' : 'border-slate-800/80 hover:border-slate-700/80'
              }`}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-5">
                  <div className="space-y-3 truncate max-w-full md:max-w-xl">
                    <div className="flex items-center flex-wrap gap-2">
                      <div className="flex items-center space-x-2">
                        {isSealed && <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />}
                        <span className="text-base font-bold text-white group-hover:text-teal-400 transition">
                          Expediente {d.tracking_code || 'Custodiando...'}
                        </span>
                      </div>
                      <span className="text-[10px] bg-slate-800/80 text-slate-400 px-2 py-0.5 rounded font-mono uppercase font-bold border border-slate-750">
                        {d.tipo_contenido}
                      </span>
                      <span className="text-[10px] bg-slate-800/80 text-slate-400 px-2 py-0.5 rounded font-mono uppercase font-bold border border-slate-750">
                        {d.canal}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 truncate leading-relaxed">
                      {d.contenido_raw}
                    </p>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[10px]">
                      <div className="flex items-center space-x-1.5 text-slate-500">
                        <span className="text-slate-400">Registrado:</span>
                        <span className="text-slate-400 font-medium">{new Date(d.created_at).toLocaleString()}</span>
                      </div>
                      {d.seal_block && (
                        <div className="flex items-center space-x-1.5 text-slate-500">
                          <span className="text-slate-400">Bloque:</span>
                          <span className="text-blue-400 font-mono font-bold">#{d.seal_block}</span>
                        </div>
                      )}
                      {isSealed && d.seal_tx_hash && (
                        <div className="flex items-center space-x-1.5 font-mono">
                          <span className="text-slate-500">TX:</span>
                          <a
                            href={`https://explorer-zk.tanenbaum.io/tx/${d.seal_tx_hash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-teal-400/80 hover:text-teal-300 flex items-center space-x-1 transition"
                          >
                            <span className="truncate max-w-[200px]">{d.seal_tx_hash}</span>
                            <ExternalLink size={9} />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-row md:flex-col items-center md:items-end gap-3 shrink-0 w-full md:w-auto justify-between border-t md:border-t-0 pt-4 md:pt-0 border-slate-800/50">
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
                      <span className={`text-[10px] font-bold px-3 py-1 rounded-full border tracking-wide uppercase flex items-center space-x-1 ${
                        isSealed
                          ? 'bg-teal-500/10 text-teal-400 border-teal-500/20'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {isSealed && <div className="w-1 h-1 rounded-full bg-teal-400 animate-pulse" />}
                        <span>{isSealed ? 'SELLADO' : 'CUSTODIA'}</span>
                      </span>
                    </div>

                    {d.tracking_code && (
                      <Link
                        href={`/tracking?code=${d.tracking_code}`}
                        className="bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white font-bold px-4 py-2 rounded-xl text-xs transition-all duration-300 flex items-center space-x-1.5 shadow-md hover:shadow-[0_4px_16px_rgba(13,148,136,0.25)]"
                      >
                        <span>Auditar IA & Web3</span>
                        <ExternalLink size={11} />
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderAyuda = () => {
    return (
      <div className="w-full max-w-4xl space-y-6 animate-fadeIn">
        {/* Glosario */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border border-slate-800/60 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 mb-5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
              <ShieldAlert className="text-teal-400" size={16} />
            </div>
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">Glosario de Seguridad</h3>
          </div>
          <div className="space-y-5 text-xs md:text-sm leading-relaxed text-slate-400">
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-6 h-6 rounded-md bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-[10px] font-bold text-purple-400">1</div>
                <h4 className="font-bold text-slate-200">Identidad Descentralizada (DID)</h4>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Identificador único bajo estándar <strong className="text-slate-300">W3C DID Core 1.0</strong> generado desde tu Pali Wallet. No almacena nombres, correos ni datos personales. Tu reporte es <strong className="text-teal-400">seudónimo pero verificable</strong> ante la DIVINCRI si tú lo autorizas.
              </p>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-6 h-6 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-[10px] font-bold text-emerald-400">2</div>
                <h4 className="font-bold text-slate-200">Sellado en Blockchain</h4>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Tu evidencia se protege con un hash <strong className="text-emerald-400">SHA-256</strong> inmutable registrado en <strong className="text-slate-300">zkSYS Tanenbaum Testnet</strong>. Nadie puede alterar, borrar o manipular la evidencia — ni siquiera administradores o la policía.
              </p>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-6 h-6 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-[10px] font-bold text-blue-400">3</div>
                <h4 className="font-bold text-slate-200">Clústeres y Redes Criminales</h4>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Los agentes de IA correlacionan teléfonos, cuentas bancarias y patrones lingüísticos. Si tu reporte coincide con otros en Trujillo, se detecta automáticamente un <strong className="text-blue-400">clúster o red delictiva activa</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border border-slate-800/60 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 mb-5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <HelpCircle className="text-blue-400" size={16} />
            </div>
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">Preguntas Frecuentes</h3>
          </div>
          <div className="space-y-4 text-xs md:text-sm leading-relaxed text-slate-400">
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <h4 className="font-bold text-slate-200 mb-2 flex items-center space-x-2">
                <span className="text-teal-400">Q.</span>
                <span>¿Cómo puedo ver el estado de mi caso?</span>
              </h4>
              <p className="text-slate-400 pl-5">
                Cada reporte recibe un código único <code className="text-teal-300 font-mono font-bold bg-slate-900 px-1.5 py-0.5 rounded">TRJ-XXXX</code>. Úsalo en "Mis Evidencias" → "Auditar IA & Web3" o en el Portal de Tracking.
              </p>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <h4 className="font-bold text-slate-200 mb-2 flex items-center space-x-2">
                <span className="text-teal-400">Q.</span>
                <span>¿La policía puede ver mi clave privada?</span>
              </h4>
              <p className="text-slate-400 pl-5">
                <strong className="text-red-400">No.</strong> Conectar Pali Wallet solo firma tu reporte de forma anónima. El sistema nunca accede a tus claves privadas ni fondos.
              </p>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-4">
              <h4 className="font-bold text-slate-200 mb-2 flex items-center space-x-2">
                <span className="text-teal-400">Q.</span>
                <span>¿Qué es el acta forense PDF?</span>
              </h4>
              <p className="text-slate-400 pl-5">
                Documento digital con hash SHA-256, timestamp, DID, número de bloque y firma del sistema. Compatible con el <strong className="text-slate-300">artículo 158-B del CPP peruano</strong> para evidencia digital trazable.
              </p>
            </div>
          </div>
        </div>

        {/* Canales de Atención */}
        <div className="bg-gradient-to-br from-teal-950/20 to-slate-900/80 border border-teal-500/10 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
              <MessageCircle className="text-teal-400" size={16} />
            </div>
            <h3 className="font-bold text-sm text-teal-300 uppercase tracking-wider">Canales de Atención</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-3 text-center">
              <span className="text-lg block mb-1">📱</span>
              <span className="text-slate-300 font-bold block">WhatsApp</span>
              <span className="text-slate-500">Envía un mensaje directo</span>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-3 text-center">
              <span className="text-lg block mb-1">✈️</span>
              <span className="text-slate-300 font-bold block">Telegram</span>
              <span className="text-slate-500">@IntelExtorsion_bot</span>
            </div>
            <div className="bg-slate-950/40 border border-slate-800/40 rounded-xl p-3 text-center">
              <span className="text-lg block mb-1">💬</span>
              <span className="text-slate-300 font-bold block">Discord</span>
              <span className="text-slate-500">Servidor oficial</span>
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
    return (
      <div className="w-full h-[calc(100vh-10rem)] animate-fadeIn flex gap-5">
        {/* Left: Chat Panel */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="bg-gradient-to-br from-slate-900 to-slate-900/80 backdrop-blur border border-slate-800/60 rounded-2xl shadow-2xl flex-1 flex flex-col overflow-hidden">
            {/* Chat Header */}
            <div className="px-5 py-3.5 border-b border-slate-800/40 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500/15 to-blue-500/10 border border-teal-500/20 flex items-center justify-center">
                  <ShieldAlert className="text-teal-400" size={16} />
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-200 block">Asistente de Ingesta</span>
                  <span className="text-[10px] text-slate-500">Agentes de IA forense disponibles</span>
                </div>
              </div>
              <div className="flex items-center space-x-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                <span className="text-[10px] text-green-400 font-bold">En línea</span>
              </div>
            </div>

            {/* Messages */}
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role !== 'user' && (
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500/15 to-blue-500/10 border border-teal-500/20 flex items-center justify-center shrink-0 mr-2.5 mt-1">
                      <ShieldAlert className="text-teal-400" size={12} />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-teal-600 to-teal-700 text-white rounded-br-md shadow-lg shadow-teal-500/10'
                        : msg.role === 'system'
                        ? 'bg-slate-800/40 border border-slate-700/30 text-slate-200 rounded-bl-md'
                        : 'bg-gradient-to-br from-green-950/40 to-green-950/20 text-green-200 border border-green-500/20 rounded-bl-md'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-line">{msg.content}</p>
                    ) : (
                      <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                    )}

                    {msg.id === 'welcome' && chatState === 'idle' && (
                      <div className="mt-5 space-y-3 select-none">
                        <button
                          onClick={() => {
                            setChatState('waiting_for_denuncia');
                            setMessages((prev) => [
                              ...prev,
                              {
                                id: `bot-start-${Date.now()}`,
                                role: 'system',
                                content: '📝 *Asistente de Ingesta Activado.*\n\nPor favor, redacta detalladamente lo sucedido en tu siguiente mensaje. Puedes adjuntar capturas, audios o documentos como evidencia.\n\n💡 *Consejo:* Incluye datos clave como teléfonos de extorsión, números de cuenta, montos o fechas.\n\n*Si deseas cancelar en cualquier momento, escribe "cancelar".*',
                                timestamp: new Date(),
                              },
                            ]);
                          }}
                          className="w-full flex items-center justify-center space-x-2.5 bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white font-bold px-6 py-3.5 rounded-xl text-sm transition-all duration-300 shadow-lg hover:shadow-[0_4px_20px_rgba(13,148,136,0.3)] active:scale-[0.98]"
                        >
                          <div className="w-6 h-6 rounded-md bg-white/10 flex items-center justify-center">
                            <Send size={12} />
                          </div>
                          <span>Iniciar Reporte Seguro</span>
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
                          className="w-full flex items-center justify-center space-x-2.5 bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/50 hover:border-slate-600/60 font-bold px-5 py-3 rounded-xl text-sm transition-all duration-300"
                        >
                          <span>Rastrear Caso Existente</span>
                        </button>
                      </div>
                    )}

                    {!!msg.metadata?.trackingCode && (
                      <div className="mt-4 bg-gradient-to-br from-green-950/30 to-teal-950/20 border border-green-500/20 rounded-xl p-4 select-none">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-6 h-6 rounded-md bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                            <CheckCircle2 size={12} className="text-green-400" />
                          </div>
                          <span className="text-[10px] text-green-400 font-bold uppercase tracking-wider">Caso Procesado y Sellado</span>
                        </div>
                        <p className="text-xs text-slate-300 mb-3 leading-relaxed">Tu reporte ha sido analizado por los agentes de IA y sellado de forma inmutable en blockchain zkSYS.</p>
                        <Link
                          href={`/tracking?code=${String(msg.metadata.trackingCode)}`}
                          className="inline-flex items-center space-x-1.5 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all duration-300 shadow-md hover:shadow-[0_4px_16px_rgba(34,197,94,0.25)]"
                        >
                          <span>Ver Expediente {String(msg.metadata.trackingCode)}</span>
                          <ExternalLink size={11} />
                        </Link>
                      </div>
                    )}

                    {!!msg.metadata?.showTrackingButton && (
                      <div className="mt-4 bg-gradient-to-br from-teal-950/30 to-slate-900/50 border border-teal-500/20 rounded-xl p-4 select-none">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-6 h-6 rounded-md bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                            <Loader2 size={12} className="text-teal-400" />
                          </div>
                          <span className="text-[10px] text-teal-400 font-bold uppercase tracking-wider">Código Detectado</span>
                        </div>
                        <Link
                          href={`/tracking?code=${String(msg.metadata.showTrackingButton)}`}
                          className="inline-flex items-center space-x-1.5 bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all duration-300 shadow-md hover:shadow-[0_4px_16px_rgba(13,148,136,0.25)]"
                        >
                          <span>Rastrear {String(msg.metadata.showTrackingButton)}</span>
                          <ExternalLink size={11} />
                        </Link>
                      </div>
                    )}

                    <span className="text-[10px] opacity-30 mt-2 block text-right">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500/15 to-blue-500/10 border border-teal-500/20 flex items-center justify-center shrink-0 mr-2.5">
                    <ShieldAlert className="text-teal-400" size={12} />
                  </div>
                  <div className="bg-slate-800/40 border border-slate-700/30 rounded-2xl px-5 py-3.5 flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-xs text-slate-400 font-medium">Agentes procesando...</span>
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            {/* Input */}
            <div className="border-t border-slate-800/40 p-4 bg-slate-900/40 shrink-0">
              {attachments.length > 0 && (
                <div className="mb-3 flex items-center space-x-2 overflow-x-auto pb-1">
                  {attachments.map((att, idx) => (
                    <div
                      key={`${att.file.name}-${idx}`}
                      className="flex items-center space-x-2 bg-slate-800/50 border border-slate-700/40 rounded-xl px-3 py-2 shrink-0 group hover:border-slate-600/50 transition"
                    >
                      {att.type === 'imagen' && att.preview ? (
                        <img src={att.preview} alt="preview" className="h-8 w-8 object-cover rounded-lg border border-slate-600" />
                      ) : att.type === 'audio' ? (
                        <div className="h-8 w-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
                          <Mic size={14} className="text-teal-400" />
                        </div>
                      ) : (
                        <div className="h-8 w-8 rounded-lg bg-slate-700/50 flex items-center justify-center">
                          <FileText size={14} className="text-slate-400" />
                        </div>
                      )}
                      <div className="max-w-[120px]">
                        <p className="text-[10px] text-slate-200 font-semibold truncate">{att.file.name}</p>
                        <p className="text-[9px] text-slate-500 capitalize">{att.type}</p>
                      </div>
                      <button
                        onClick={() => removeAttachment(idx)}
                        className="text-slate-500 hover:text-red-400 p-0.5 rounded-full hover:bg-slate-700 transition ml-1"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                  <div className="shrink-0 bg-slate-800/50 border border-slate-700/40 rounded-full px-2.5 py-1">
                    <span className="text-[10px] text-slate-400 font-bold">{attachments.length}/5</span>
                  </div>
                </div>
              )}

              <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => handleFileSelect(e, 'documento')} />
              <input ref={imageInputRef} type="file" accept="image/*" className="hidden" onChange={(e) => handleFileSelect(e, 'imagen')} />
              <input ref={audioInputRef} type="file" accept="audio/*" className="hidden" onChange={(e) => handleFileSelect(e, 'audio')} />

              <div className="flex items-end space-x-2">
                <div className="relative" ref={addMenuRef}>
                  <button
                    onClick={() => setIsAddMenuOpen(!isAddMenuOpen)}
                    className="p-3 text-slate-400 hover:text-teal-400 rounded-xl hover:bg-slate-800/50 transition border border-transparent hover:border-slate-700/50"
                    title="Adjuntar archivo"
                  >
                    <PlusCircle size={20} />
                  </button>
                  {isAddMenuOpen && (
                    <div className="absolute bottom-full left-0 mb-2 bg-slate-800/95 backdrop-blur border border-slate-700/60 rounded-xl shadow-2xl overflow-hidden z-50 min-w-[160px]">
                      <button
                        onClick={() => { imageInputRef.current?.click(); setIsAddMenuOpen(false); }}
                        className="w-full flex items-center space-x-3 px-4 py-3 text-xs font-semibold text-slate-300 hover:bg-slate-700/60 hover:text-white transition"
                      >
                        <ImageIcon size={14} className="text-blue-400" />
                        <span>Imagen</span>
                      </button>
                      <button
                        onClick={() => { audioInputRef.current?.click(); setIsAddMenuOpen(false); }}
                        className="w-full flex items-center space-x-3 px-4 py-3 text-xs font-semibold text-slate-300 hover:bg-slate-700/60 hover:text-white transition border-t border-slate-700/30"
                      >
                        <Mic size={14} className="text-teal-400" />
                        <span>Audio</span>
                      </button>
                      <button
                        onClick={() => { fileInputRef.current?.click(); setIsAddMenuOpen(false); }}
                        className="w-full flex items-center space-x-3 px-4 py-3 text-xs font-semibold text-slate-300 hover:bg-slate-700/60 hover:text-white transition border-t border-slate-700/30"
                      >
                        <FileText size={14} className="text-purple-400" />
                        <span>Documento</span>
                      </button>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => imageInputRef.current?.click()}
                  className="p-3 text-slate-500 hover:text-blue-400 rounded-xl hover:bg-slate-800/50 transition hidden sm:block"
                  title="Adjuntar imagen"
                >
                  <ImageIcon size={18} />
                </button>
                <button
                  onClick={() => audioInputRef.current?.click()}
                  className="p-3 text-slate-500 hover:text-teal-400 rounded-xl hover:bg-slate-800/50 transition hidden sm:block"
                  title="Adjuntar audio"
                >
                  <Mic size={18} />
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !loading && handleSend()}
                  placeholder={chatState === 'waiting_for_denuncia' ? "Describe los detalles de la extorsión..." : "Escribe un mensaje..."}
                  className="flex-1 bg-slate-950/50 border border-slate-800/40 rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-teal-500/40 focus:border-teal-500/30 outline-none text-slate-200 placeholder-slate-500 transition-all duration-300"
                />

                <button
                  onClick={() => handleSend()}
                  disabled={(!input.trim() && attachments.length === 0) || loading}
                  className="p-3 bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl transition-all duration-300 shadow-md hover:shadow-[0_4px_16px_rgba(13,148,136,0.3)] shrink-0 active:scale-95"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Info Panel */}
        <div className="hidden xl:flex w-72 flex-col gap-4 shrink-0">
          {/* Security Badge */}
          <div className="bg-gradient-to-br from-teal-950/20 to-slate-900/80 border border-teal-500/10 rounded-2xl p-4">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center">
                <ShieldAlert className="text-teal-400" size={14} />
              </div>
              <span className="text-[10px] font-bold text-teal-300 uppercase tracking-wider">Custodia Segura</span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-400">
              <div className="flex items-center space-x-2">
                <CheckCircle2 size={11} className="text-teal-400 shrink-0" />
                <span>Hash SHA-256 inmutable</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 size={11} className="text-teal-400 shrink-0" />
                <span>Sellado en blockchain zkSYS</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 size={11} className="text-teal-400 shrink-0" />
                <span>Acta PDF forense</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 size={11} className="text-teal-400 shrink-0" />
                <span>Identidad pseudónima DID</span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-slate-900/50 border border-slate-800/40 rounded-2xl p-4 flex-1">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Consejos para tu reporte</h4>
            <div className="space-y-3 text-[11px] text-slate-400 leading-relaxed">
              <div className="bg-slate-950/30 border border-slate-800/30 rounded-lg p-3">
                <span className="text-slate-300 font-semibold block mb-1">Teléfonos</span>
                <span>Incluye todos los números desde los que te contactaron.</span>
              </div>
              <div className="bg-slate-950/30 border border-slate-800/30 rounded-lg p-3">
                <span className="text-slate-300 font-semibold block mb-1">Cuentas bancarias</span>
                <span>Números de cuenta o CCI donde piden los depósitos.</span>
              </div>
              <div className="bg-slate-950/30 border border-slate-800/30 rounded-lg p-3">
                <span className="text-slate-300 font-semibold block mb-1">Montos y fechas</span>
                <span>Cuánto pidieron y cuándo ocurrió la extorsión.</span>
              </div>
              <div className="bg-slate-950/30 border border-slate-800/30 rounded-lg p-3">
                <span className="text-slate-300 font-semibold block mb-1">Evidencia</span>
                <span>Adjunta audios, capturas de chat o documentos.</span>
              </div>
            </div>
          </div>

          {/* Network Status */}
          <div className="bg-slate-900/50 border border-slate-800/40 rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                <span className="text-[10px] text-slate-400 font-mono">zkSYS Tanenbaum</span>
              </div>
              <span className="text-[10px] text-teal-400/70 font-mono">57057</span>
            </div>
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
              onClick={handleConnectWallet}
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
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500/20 to-blue-500/10 border border-teal-500/20 flex items-center justify-center">
              <ShieldAlert className="text-teal-400" size={20} />
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-tight text-white block">IntelExtorsión</span>
              <span className="text-[10px] text-slate-500 block">Custodia Forense · DID</span>
            </div>
          </div>

          {/* DID Card */}
          <div className="bg-gradient-to-br from-teal-950/30 to-slate-900 border border-teal-500/15 rounded-xl p-3.5 mb-6 shadow-inner relative overflow-hidden">
            <div className="absolute -top-8 -right-8 w-16 h-16 bg-teal-500/5 rounded-full blur-xl pointer-events-none" />
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-teal-400 select-none">Tu DID</span>
              <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            </div>
            <span className="text-[10px] font-mono text-teal-300/80 break-all select-all block leading-tight">
              {did ? `${did.slice(0, 16)}...${did.slice(-10)}` : 'did:zksys:unknown'}
            </span>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1.5 flex-1">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => {
                    setActiveTab(item.key);
                    setIsSidebarOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-xl text-xs font-bold transition-all duration-200 select-none ${
                    isActive
                      ? 'bg-gradient-to-r from-teal-600 to-teal-500 text-white shadow-lg shadow-teal-500/15'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
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
          <div className="flex items-center justify-center space-x-2 text-[10px] text-slate-500 font-mono">
            <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            <span>zkSYS Tanenbaum</span>
            <span className="text-slate-700">·</span>
            <span className="text-teal-400/70">57057</span>
          </div>
          <button
            onClick={() => disconnect()}
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
        <header className="absolute top-0 left-0 right-0 h-16 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-xl px-6 flex items-center justify-between select-none z-10">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 hover:bg-slate-800/60 rounded-xl lg:hidden text-slate-400 hover:text-white transition"
              title="Menu"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center space-x-2">
              <h2 className="font-bold text-xs md:text-sm text-slate-200 uppercase tracking-wider">
                {activeTab === 'dashboard' && 'Panel Principal'}
                {activeTab === 'chat' && 'Nueva Denuncia'}
                {activeTab === 'evidencias' && 'Mis Evidencias'}
                {activeTab === 'ayuda' && 'Ayuda y Glosario'}
              </h2>
              {activeTab === 'chat' && (
                <span className="text-[9px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/20 font-bold uppercase tracking-wider">En vivo</span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2.5">
            {error && (
              <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 animate-pulse font-medium">
                Red Errónea
              </span>
            )}
            <div className="flex items-center space-x-2 bg-slate-800/50 border border-slate-700/40 px-3 py-1.5 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              <span className="text-[10px] text-teal-400 font-mono font-bold">{account?.slice(0, 6)}...{account?.slice(-4)}</span>
            </div>
          </div>
        </header>

        {/* Tab Content Container */}
        <div ref={mainContainerRef} className="absolute top-16 left-0 right-0 bottom-0 overflow-y-auto p-4 md:p-8 bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'chat' && renderChat()}
          {activeTab === 'evidencias' && renderEvidencias()}
          {activeTab === 'ayuda' && renderAyuda()}
        </div>
      </main>
    </div>
  );
}
