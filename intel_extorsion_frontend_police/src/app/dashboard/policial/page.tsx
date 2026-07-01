'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/stores/appStore';
import { denunciaService, dashboardService } from '@/services/api';
import { Denuncia, MetricasDashboard } from '@/types';
import {
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle,
  Activity,
  TrendingUp,
  Users,
  ShieldCheck,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

const StatCard = ({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) => (
  <div className="bg-white border rounded-xl p-5 shadow-sm hover:shadow-md transition">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-slate-500 mb-1">{title}</p>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
      </div>
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
    </div>
  </div>
);

export default function DashboardPolicialPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { denuncias, setDenuncias, metricas, setMetricas } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [{ data: denunciasData }, { data: metricasData }] = await Promise.all([
          denunciaService.listar(),
          dashboardService.metricas(),
        ]);
        setDenuncias(denunciasData);
        setMetricas(metricasData);
      } catch (e) {
        console.error('Error cargando datos del dashboard:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [setDenuncias, setMetricas]);

  const m = metricas || ({} as MetricasDashboard);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{t('dashboard.title')}</h1>
        <p className="text-slate-500 text-sm">{t('dashboard.subtitle')}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard title={t('dashboard.statsTotal')} value={m.total_denuncias ?? '-'} icon={FileText} color="bg-blue-600" />
        <StatCard title={t('dashboard.statsToday')} value={m.denuncias_hoy ?? '-'} icon={Activity} color="bg-emerald-600" />
        <StatCard title={t('dashboard.statsAlerts')} value={m.alertas_criticas ?? '-'} icon={AlertTriangle} color="bg-red-600" />
        <StatCard title={t('dashboard.statsResolved')} value={m.casos_resueltos ?? '-'} icon={CheckCircle} color="bg-green-600" />
        <StatCard title={t('dashboard.statsResponseTime')} value={`${m.tiempo_promedio_respuesta_min ?? '-'}m`} icon={Clock} color="bg-amber-600" />
        <StatCard title={t('dashboard.statsEvidences')} value={m.evidencias_registradas ?? '-'} icon={ShieldCheck} color="bg-indigo-600" />
      </div>

      {/* Denuncias Recientes */}
      <div className="bg-white border rounded-xl shadow-sm">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-slate-800">{t('dashboard.recentTitle')}</h2>
          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">{t('dashboard.updatedAgo')}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs">
              <tr>
                <th className="px-6 py-3">{t('dashboard.tableId')}</th>
                <th className="px-6 py-3">{t('dashboard.tableChannel')}</th>
                <th className="px-6 py-3">{t('dashboard.tableStatus')}</th>
                <th className="px-6 py-3">{t('dashboard.tableType')}</th>
                <th className="px-6 py-3">{t('dashboard.tableTimeAgo')}</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    {t('common.loading')}
                  </td>
                </tr>
              ) : denuncias.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    {t('dashboard.noDenuncias')}
                  </td>
                </tr>
              ) : (
                denuncias.slice(0, 10).map((d) => (
                  <tr
                    key={d.id}
                    onClick={() => router.push(`/dashboard/policial/${d.id}`)}
                    className="hover:bg-slate-100 cursor-pointer transition"
                  >
                    <td className="px-6 py-3 font-mono text-xs text-blue-600 font-semibold">{d.id.slice(0, 8)}...</td>
                    <td className="px-6 py-3 capitalize">{d.canal}</td>
                    <td className="px-6 py-3">
                      <StatusBadge estado={d.estado} />
                    </td>
                    <td className="px-6 py-3 capitalize">{d.tipo_contenido}</td>
                    <td className="px-6 py-3 text-slate-500">
                      {formatDistanceToNow(new Date(d.created_at), { addSuffix: true, locale: es })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ estado }: { estado: string }) {
  const colors: Record<string, string> = {
    recibido: 'bg-slate-100 text-slate-700',
    en_analisis: 'bg-amber-100 text-amber-700',
    procesado: 'bg-blue-100 text-blue-700',
    alerta_generada: 'bg-red-100 text-red-700',
    archivado: 'bg-green-100 text-green-700',
  };
  return (
    <span className={`text-xs font-medium px-2.5 py-0.5 rounded ${colors[estado] || 'bg-slate-100 text-slate-700'}`}>
      {estado.replace(/_/g, ' ')}
    </span>
  );
}
