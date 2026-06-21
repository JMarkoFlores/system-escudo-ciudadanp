'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const serieData = [
  { fecha: 'Lun', denuncias: 12, alertas: 3, resueltos: 5 },
  { fecha: 'Mar', denuncias: 19, alertas: 5, resueltos: 8 },
  { fecha: 'Mie', denuncias: 15, alertas: 2, resueltos: 6 },
  { fecha: 'Jue', denuncias: 22, alertas: 7, resueltos: 10 },
  { fecha: 'Vie', denuncias: 28, alertas: 9, resueltos: 12 },
  { fecha: 'Sab', denuncias: 18, alertas: 4, resueltos: 7 },
  { fecha: 'Dom', denuncias: 14, alertas: 3, resueltos: 6 },
];

const canalData = [
  { name: 'WhatsApp', value: 45, color: '#10b981' },
  { name: 'Telegram', value: 30, color: '#0ea5e9' },
  { name: 'Discord', value: 15, color: '#6366f1' },
  { name: 'Web', value: 10, color: '#64748b' },
];

const riesgoData = [
  { name: 'Bajo', value: 40, color: '#22c55e' },
  { name: 'Medio', value: 35, color: '#f59e0b' },
  { name: 'Alto', value: 18, color: '#ef4444' },
  { name: 'Crítico', value: 7, color: '#7f1d1d' },
];

export default function DashboardAnaliticoPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard Analítico</h1>
        <p className="text-slate-500 text-sm">Métricas, tendencias y patrones de denuncias de extorsión</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Serie Temporal */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Actividad Semanal</h3>
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
        </div>

        {/* Por Canal */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Denuncias por Canal</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={canalData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value">
                {canalData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center space-x-4 mt-2">
            {canalData.map((c) => (
              <div key={c.name} className="flex items-center text-xs">
                <span className="w-3 h-3 rounded-full mr-1" style={{ backgroundColor: c.color }} />
                {c.name}
              </div>
            ))}
          </div>
        </div>

        {/* Distribución de Riesgo */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Distribución por Nivel de Riesgo</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={riesgoData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#64748b" fontSize={12} />
              <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={12} width={60} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {riesgoData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* KPIs Adicionales */}
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Indicadores Clave</h3>
          <div className="space-y-4">
            {[
              { label: 'Tasa de resolución', value: 71, color: 'bg-green-500' },
              { label: 'Tiempo promedio de respuesta', value: 45, color: 'bg-blue-500' },
              { label: 'Evidencias en blockchain', value: 88, color: 'bg-indigo-500' },
              { label: 'Denuncias con DID verificado', value: 34, color: 'bg-amber-500' },
            ].map((kpi) => (
              <div key={kpi.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{kpi.label}</span>
                  <span className="font-semibold text-slate-800">{kpi.value}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className={`${kpi.color} h-2 rounded-full transition-all`} style={{ width: `${kpi.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
