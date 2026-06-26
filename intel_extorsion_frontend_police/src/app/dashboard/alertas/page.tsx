'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/stores/appStore';
import { alertaService, dashboardService } from '@/services/api';
import { Alerta } from '@/types';
import { ShieldAlert, AlertTriangle, CheckCircle2, Clock, X, FileText, Send } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';

const nivelConfig = {
  bajo: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle2 },
  medio: { color: 'bg-amber-100 text-amber-800 border-amber-200', icon: Clock },
  alto: { color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle },
  critico: { color: 'bg-red-600 text-white border-red-700', icon: ShieldAlert },
};

export default function AlertasPage() {
  const { alertas, setAlertas, marcarAlertaLeida, marcarAlertaAtendida, setMetricas } = useAppStore();
  const [filter, setFilter] = useState<'todas' | 'no_leidas' | 'criticas'>('todas');

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAlerta, setModalAlerta] = useState<Alerta | null>(null);
  const [mensajeResolucion, setMensajeResolucion] = useState('');
  const [resolverDenuncia, setResolverDenuncia] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await alertaService.listar();
        setAlertas(data);
      } catch {
        const demo: Alerta[] = [
          {
            id: 'a1',
            denuncia_id: 'd1',
            nivel: 'critico',
            titulo: 'Amenaza de secuestro virtual confirmada',
            descripcion: 'El Risk Agent detectó datos personales exactos de la víctima y modus operandi coincidente con serie criminal activa.',
            recomendacion: 'Activar unidad de reacción inmediata. Contactar a víctima para protección.',
            leida: false,
            atendida: false,
            created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
          },
          {
            id: 'a2',
            denuncia_id: 'd2',
            nivel: 'alto',
            titulo: 'Red de extorsión telefónica detectada',
            descripcion: 'Correlation Agent identificó 5 denuncias relacionadas al mismo número telefónico.',
            leida: false,
            atendida: false,
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
          },
          {
            id: 'a3',
            denuncia_id: 'd3',
            nivel: 'medio',
            titulo: 'Intento de fraude bancario',
            descripcion: 'OSINT Agent confirmó cuenta bancaria reportada previamente en otras 3 denuncias.',
            leida: true,
            atendida: false,
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
          },
        ];
        setAlertas(demo);
      }
    };
    fetch();
  }, [setAlertas]);

  const recargarMetricas = async () => {
    try {
      const { data } = await dashboardService.metricas();
      setMetricas(data);
    } catch {
      // silently fail
    }
  };

  const abrirModalAtender = (alerta: Alerta) => {
    setModalAlerta(alerta);
    setMensajeResolucion('');
    setResolverDenuncia(true);
    setModalOpen(true);
  };

  const cerrarModal = () => {
    setModalOpen(false);
    setModalAlerta(null);
    setMensajeResolucion('');
  };

  const handleAtender = async () => {
    if (!modalAlerta) return;
    if (!mensajeResolucion.trim()) {
      toast.error('Debes escribir un mensaje de resolución');
      return;
    }
    setSubmitting(true);
    try {
      await alertaService.atender(
        modalAlerta.id,
        mensajeResolucion.trim(),
        resolverDenuncia ? 'archivado' : undefined
      );
      marcarAlertaAtendida(modalAlerta.id);
      await recargarMetricas();
      toast.success('Alerta atendida y denuncia resuelta exitosamente');
      cerrarModal();
    } catch {
      toast.error('Error al atender la alerta');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = alertas.filter((a) => {
    if (filter === 'no_leidas') return !a.leida;
    if (filter === 'criticas') return a.nivel === 'critico' || a.nivel === 'alto';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Centro de Alertas</h1>
          <p className="text-slate-500 text-sm">Alertas generadas por el sistema de agentes autónomos</p>
        </div>
        <div className="flex space-x-2">
          {(['todas', 'no_leidas', 'criticas'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                filter === f ? 'bg-slate-800 text-white' : 'bg-white border text-slate-600 hover:bg-slate-50'
              }`}
            >
              {f === 'todas' ? 'Todas' : f === 'no_leidas' ? 'No leídas' : 'Críticas'}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400 bg-white border rounded-xl">
            No hay alertas en esta categoría
          </div>
        )}
        {filtered.map((alerta) => {
          const config = nivelConfig[alerta.nivel];
          const Icon = config.icon;
          const resolucion = (alerta.metadata_json?.mensaje_resolucion as string) || '';
          return (
            <div
              key={alerta.id}
              className={`bg-white border rounded-xl p-5 shadow-sm transition hover:shadow-md ${
                !alerta.leida ? 'border-l-4 border-l-blue-600' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg ${config.color}`}>
                    <Icon size={18} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-slate-800">{alerta.titulo}</h3>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${config.color}`}>
                        {alerta.nivel}
                      </span>
                      {!alerta.leida && (
                        <span className="w-2 h-2 bg-blue-600 rounded-full" />
                      )}
                      {alerta.atendida && (
                        <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded border border-green-200 font-semibold">
                          Atendida
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{alerta.descripcion}</p>
                    {alerta.recomendacion && (
                      <p className="text-xs text-blue-700 bg-blue-50 p-2 rounded mt-2">
                        <strong>Recomendación:</strong> {alerta.recomendacion}
                      </p>
                    )}
                    {resolucion && (
                      <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-xs font-semibold text-green-800 mb-1">Resolución del oficial:</p>
                        <p className="text-sm text-green-900 whitespace-pre-wrap">{resolucion}</p>
                      </div>
                    )}
                    <div className="flex items-center space-x-4 mt-3 text-xs text-slate-400">
                      <span>Denuncia: {alerta.denuncia_id}</span>
                      <span>
                        {formatDistanceToNow(new Date(alerta.created_at), { addSuffix: true, locale: es })}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col space-y-2 ml-4">
                  {!alerta.leida && (
                    <button
                      onClick={async () => {
                        try {
                          await alertaService.marcarLeida(alerta.id);
                          marcarAlertaLeida(alerta.id);
                          toast.success('Alerta marcada como leída');
                        } catch {
                          toast.error('Error al marcar alerta como leída');
                        }
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Marcar leída
                    </button>
                  )}
                  {!alerta.atendida && (
                    <button
                      onClick={() => abrirModalAtender(alerta)}
                      className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded transition"
                    >
                      Atender
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal Atender Alerta */}
      {modalOpen && modalAlerta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <FileText size={18} className="text-blue-600" />
                <h2 className="font-semibold text-slate-800">Atender Alerta</h2>
              </div>
              <button onClick={cerrarModal} className="text-slate-400 hover:text-slate-600 transition">
                <X size={18} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-500 mb-1">Alerta</p>
                <p className="font-semibold text-slate-800">{modalAlerta.titulo}</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Mensaje de Resolución
                </label>
                <textarea
                  value={mensajeResolucion}
                  onChange={(e) => setMensajeResolucion(e.target.value)}
                  placeholder="Describe el descubrimiento, las acciones tomadas y el resultado de la investigación..."
                  className="w-full border rounded-lg p-3 text-sm text-slate-700 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none min-h-[120px] resize-y"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  Este mensaje será visible en el expediente de la denuncia y en el portal del ciudadano.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  id="resolver-denuncia"
                  type="checkbox"
                  checked={resolverDenuncia}
                  onChange={(e) => setResolverDenuncia(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="resolver-denuncia" className="text-sm text-slate-700 select-none">
                  Marcar denuncia como <strong>resuelta</strong> (archivada)
                </label>
              </div>
            </div>

            <div className="px-6 py-4 border-t bg-slate-50 flex justify-end space-x-3">
              <button
                onClick={cerrarModal}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-200 transition"
              >
                Cancelar
              </button>
              <button
                onClick={handleAtender}
                disabled={submitting || !mensajeResolucion.trim()}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white disabled:bg-slate-300 disabled:cursor-not-allowed transition flex items-center space-x-2"
              >
                {submitting ? (
                  <span>Guardando...</span>
                ) : (
                  <>
                    <Send size={14} />
                    <span>Enviar Resolución</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
