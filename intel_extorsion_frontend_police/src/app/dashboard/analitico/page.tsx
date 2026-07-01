'use client';

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from 'recharts';
import { heatmapService, dashboardService } from '@/services/api';
import { useAppStore } from '@/stores/appStore';

const HeatmapMap = dynamic(() => import('./HeatmapMap'), { ssr: false });

export default function DashboardAnaliticoPage() {
  const { t } = useTranslation();
  const { heatmapData, setHeatmapData } = useAppStore();
  const [periodo, setPeriodo] = useState(30);
  const [loadingMap, setLoadingMap] = useState(true);
  const [serieData, setSerieData] = useState<{ fecha: string; denuncias: number; alertas: number; resueltos: number }[]>([]);
  const [metricas, setMetricas] = useState<{
    total_denuncias: number;
    denuncias_hoy: number;
    alertas_criticas: number;
    casos_resueltos: number;
    tiempo_promedio_respuesta_min: number;
    evidencias_registradas: number;
  } | null>(null);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        setLoadingMap(true);
        const { data } = await heatmapService.obtener({ periodo });
        setHeatmapData(data?.puntos || []);
      } catch (e) {
        console.error('Error cargando heatmap:', e);
        setHeatmapData([]);
      } finally {
        setLoadingMap(false);
      }
    };
    fetchHeatmap();
  }, [periodo, setHeatmapData]);

  useEffect(() => {
    const fetchSerie = async () => {
      try {
        const { data } = await dashboardService.serieTemporal(periodo);
        if (data?.puntos) {
          setSerieData(data.puntos);
        }
      } catch (e) {
        console.error('Error cargando serie temporal:', e);
      }
    };
    fetchSerie();
  }, [periodo]);

  useEffect(() => {
    const fetchMetricas = async () => {
      try {
        const { data } = await dashboardService.metricas();
        setMetricas(data);
      } catch (e) {
        console.error('Error cargando metricas:', e);
      }
    };
    fetchMetricas();
  }, []);

  const tasaResolucion = metricas && metricas.total_denuncias > 0
    ? Math.round((metricas.casos_resueltos / metricas.total_denuncias) * 100)
    : 0;
  const tasaBlockchain = metricas && metricas.total_denuncias > 0
    ? Math.round((metricas.evidencias_registradas / metricas.total_denuncias) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{t('dashboard.analitico.title')}</h1>
        <p className="text-slate-500 text-sm">{t('dashboard.analitico.subtitle')}</p>
      </div>

      {/* Mapa de Calor */}
      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">Mapa de Calor - Zonas de Extorsión (Trujillo/La Libertad)</h3>
          <select
            value={periodo}
            onChange={(e) => setPeriodo(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value={7}>Últimos 7 días</option>
            <option value={30}>Últimos 30 días</option>
            <option value={90}>Últimos 90 días</option>
          </select>
        </div>
        {loadingMap ? (
          <div className="h-96 flex items-center justify-center text-slate-400">Cargando mapa...</div>
        ) : (
          <div className="h-96 rounded-lg overflow-hidden border">
            <HeatmapMap puntos={heatmapData} />
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Serie Temporal */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Actividad Temporal</h3>
          {serieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={serieData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="fecha" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="denuncias" stroke="#3b82f6" strokeWidth={2} name="Denuncias" />
                <Line type="monotone" dataKey="alertas" stroke="#ef4444" strokeWidth={2} name="Alertas" />
                <Line type="monotone" dataKey="resueltos" stroke="#22c55e" strokeWidth={2} name="Resueltos" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-slate-400 text-sm">
              Sin datos disponibles — se mostrarán cuando haya denuncias registradas
            </div>
          )}
        </div>

        {/* KPIs desde API */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Indicadores Clave</h3>
          {metricas ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-blue-600">{metricas.total_denuncias}</div>
                  <div className="text-xs text-slate-500 mt-1">Total Denuncias</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-green-600">{metricas.denuncias_hoy}</div>
                  <div className="text-xs text-slate-500 mt-1">Hoy</div>
                </div>
                <div className="bg-red-50 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-red-600">{metricas.alertas_criticas}</div>
                  <div className="text-xs text-slate-500 mt-1">Alertas Críticas</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold text-purple-600">{metricas.casos_resueltos}</div>
                  <div className="text-xs text-slate-500 mt-1">Resueltos</div>
                </div>
              </div>
              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Tasa de resolución</span>
                    <span className="font-semibold text-slate-800">{tasaResolucion}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full transition-all" style={{ width: `${tasaResolucion}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Evidencias registradas</span>
                    <span className="font-semibold text-slate-800">{metricas.evidencias_registradas}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-indigo-500 h-2 rounded-full transition-all" style={{ width: `${Math.min(tasaBlockchain, 100)}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Tiempo promedio respuesta</span>
                    <span className="font-semibold text-slate-800">{metricas.tiempo_promedio_respuesta_min} min</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-slate-400 text-sm">
              Cargando métricas...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
