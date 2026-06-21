'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/stores/appStore';
import { alertaService } from '@/services/api';
import { Alerta } from '@/types';
import { ShieldAlert, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const nivelConfig = {
  bajo: { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle2 },
  medio: { color: 'bg-amber-100 text-amber-800 border-amber-200', icon: Clock },
  alto: { color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle },
  critico: { color: 'bg-red-600 text-white border-red-700', icon: ShieldAlert },
};

export default function AlertasPage() {
  const { alertas, setAlertas, marcarAlertaLeida } = useAppStore();
  const [filter, setFilter] = useState<'todas' | 'no_leidas' | 'criticas'>('todas');

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
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-slate-800">{alerta.titulo}</h3>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${config.color}`}>
                        {alerta.nivel}
                      </span>
                      {!alerta.leida && (
                        <span className="w-2 h-2 bg-blue-600 rounded-full" />
                      )}
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{alerta.descripcion}</p>
                    {alerta.recomendacion && (
                      <p className="text-xs text-blue-700 bg-blue-50 p-2 rounded mt-2">
                        <strong>Recomendación:</strong> {alerta.recomendacion}
                      </p>
                    )}
                    <div className="flex items-center space-x-4 mt-3 text-xs text-slate-400">
                      <span>Denuncia: {alerta.denuncia_id}</span>
                      <span>
                        {formatDistanceToNow(new Date(alerta.created_at), { addSuffix: true, locale: es })}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col space-y-2">
                  {!alerta.leida && (
                    <button
                      onClick={() => marcarAlertaLeida(alerta.id)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Marcar leída
                    </button>
                  )}
                  {!alerta.atendida && (
                    <button className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded transition">
                      Atender
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
