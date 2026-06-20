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
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'system' | 'agent';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

type FileAttachment = {
  file: File;
  type: 'imagen' | 'audio' | 'documento';
  preview?: string;
};

export default function PortalPage() {
  const { account, isConnected, connect, did } = useWalletStore();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'system',
      content:
        'Bienvenido al Portal Ciudadano de IntelExtorsión. Puedes realizar tu denuncia de forma segura y anónima. Los mensajes serán analizados por nuestros agentes de IA y preservados en blockchain si así lo deseas.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<'whatsapp' | 'telegram' | 'discord' | 'web'>('web');
  const [attachment, setAttachment] = useState<FileAttachment | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, type: 'imagen' | 'audio' | 'documento') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const attach: FileAttachment = { file, type };

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

  const handleSend = async () => {
    if (!input.trim() && !attachment) return;

    const displayContent = attachment
      ? `${input || ''}\n[Archivo adjunto: ${attachment.file.name} (${attachment.type})]`.trim()
      : input;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: displayContent,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const tipoContenido = attachment ? attachment.type : 'texto';
      const contenidoRaw = input.trim() || `[Denuncia con archivo adjunto: ${attachment?.file.name}]`;

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

      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        content: `Tu denuncia ha sido registrada con ID: ${data.id}. Nuestros agentes de IA están analizando la información. Recibirás una notificación cuando el análisis esté completo.`,
        timestamp: new Date(),
        metadata: { denunciaId: data.id },
      };
      setMessages((prev) => [...prev, agentMsg]);
      toast.success('Denuncia registrada exitosamente');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error al registrar denuncia');
    } finally {
      setLoading(false);
      setAttachment(null);
    }
  };

  const channels = [
    { key: 'whatsapp' as const, label: 'WhatsApp', color: 'bg-green-600' },
    { key: 'telegram' as const, label: 'Telegram', color: 'bg-sky-600' },
    { key: 'discord' as const, label: 'Discord', color: 'bg-indigo-600' },
    { key: 'web' as const, label: 'Web', color: 'bg-slate-700' },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link href="/" className="text-slate-400 hover:text-slate-600">
              <ArrowLeft size={20} />
            </Link>
            <ShieldAlert className="text-blue-600" size={22} />
            <h1 className="font-bold text-slate-800">Portal Ciudadano</h1>
          </div>
          <div>
            {isConnected ? (
              <div className="text-xs text-green-600 font-medium flex items-center">
                <CheckCircle2 size={14} className="mr-1" /> {account?.slice(0, 8)}...
              </div>
            ) : (
              <button
                onClick={connect}
                className="text-xs flex items-center text-blue-600 hover:text-blue-700 font-medium"
              >
                <Wallet size={14} className="mr-1" /> Conectar DID
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Channel selector */}
        <div className="flex space-x-2 mb-4 overflow-x-auto pb-2">
          {channels.map((ch) => (
            <button
              key={ch.key}
              onClick={() => setSelectedChannel(ch.key)}
              className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition ${
                selectedChannel === ch.key
                  ? `${ch.color} text-white`
                  : 'bg-white text-slate-600 border hover:bg-slate-100'
              }`}
            >
              <MessageCircle size={14} className="mr-1.5" />
              {ch.label}
            </button>
          ))}
        </div>

        {/* Chat area */}
        <div className="bg-white border rounded-xl shadow-sm h-[60vh] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : msg.role === 'system'
                      ? 'bg-slate-100 text-slate-700 rounded-bl-none'
                      : 'bg-green-50 text-green-800 border border-green-100 rounded-bl-none'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-line">{msg.content}</p>
                  <span className="text-[10px] opacity-70 mt-1 block">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 rounded-2xl px-4 py-3 flex items-center space-x-2">
                  <Loader2 size={16} className="animate-spin text-slate-400" />
                  <span className="text-xs text-slate-500">Analizando con agentes de IA...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          {/* Input */}
          <div className="border-t p-3">
            {/* Attachment preview */}
            {attachment && (
              <div className="mb-2 flex items-center space-x-2 bg-slate-50 border rounded-lg px-3 py-2">
                {attachment.type === 'imagen' && attachment.preview ? (
                  <img src={attachment.preview} alt="preview" className="h-8 w-8 object-cover rounded" />
                ) : attachment.type === 'audio' ? (
                  <Mic size={16} className="text-slate-500" />
                ) : (
                  <FileText size={16} className="text-slate-500" />
                )}
                <span className="text-xs text-slate-600 truncate flex-1">{attachment.file.name}</span>
                <button onClick={removeAttachment} className="text-slate-400 hover:text-red-500">
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
                className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100"
                title="Adjuntar archivo"
              >
                <Paperclip size={18} />
              </button>
              <button
                onClick={() => imageInputRef.current?.click()}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100"
                title="Adjuntar imagen"
              >
                <ImageIcon size={18} />
              </button>
              <button
                onClick={() => audioInputRef.current?.click()}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100"
                title="Adjuntar audio"
              >
                <Mic size={18} />
              </button>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Describe tu situación..."
                className="flex-1 bg-slate-100 border-0 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              />
              <button
                onClick={handleSend}
                disabled={(!input.trim() && !attachment) || loading}
                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-full transition"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="text-[10px] text-slate-400 mt-2 text-center">
              Tu denuncia es confidencial. Puedes usar un DID para mayor anonimato.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
