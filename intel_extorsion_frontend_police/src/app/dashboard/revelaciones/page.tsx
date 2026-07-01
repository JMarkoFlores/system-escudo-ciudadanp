'use client';

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ExternalLink,
  User,
  FileText,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { agentApi } from '@/services/api';

interface RevealRequest {
  id: number;
  citizen_did: string;
  case_id: string;
  motivo_revelacion: string;
  state: number;
  state_label: string;
  timestamp: number;
  expires_at: number;
  civil_identity_hash?: string;
  revealed_at?: number;
}

const STATE_CONFIG: Record<number, { label: string; color: string; bgColor: string; icon: React.ReactNode }> = {
  0: { label: 'Pendiente', color: 'text-amber-700', bgColor: 'bg-amber-100', icon: <Clock size={14} /> },
  1: { label: 'Autorizada', color: 'text-green-700', bgColor: 'bg-green-100', icon: <CheckCircle2 size={14} /> },
  2: { label: 'Revelada', color: 'text-blue-700', bgColor: 'bg-blue-100', icon: <Shield size={14} /> },
  3: { label: 'Rechazada', color: 'text-red-700', bgColor: 'bg-red-100', icon: <AlertTriangle size={14} /> },
  4: { label: 'Expirada', color: 'text-gray-700', bgColor: 'bg-gray-100', icon: <Clock size={14} /> },
};

export default function RevelacionesPage() {
  const [requests, setRequests] = useState<RevealRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterState, setFilterState] = useState<number | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      // Por ahora usamos datos de ejemplo hasta que se despliegue el contrato
      // En producción, esto llamaría a la API
      setRequests([]);
    } catch (error) {
      console.error('Error fetching reveal requests:', error);
      toast.error('Error al cargar solicitudes de revelación');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const formatDate = (timestamp: number) => {
    if (!timestamp) return '—';
    return new Date(timestamp * 1000).toLocaleString('es-PE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTimeRemaining = (expiresAt: number) => {
    if (!expiresAt) return '';
    const now = Math.floor(Date.now() / 1000);
    const diff = expiresAt - now;
    if (diff <= 0) return 'Expirada';
    const days = Math.floor(diff / 86400);
    const hours = Math.floor((diff % 86400) / 3600);
    if (days > 0) return `${days}d ${hours}h`;
    return `${hours}h`;
  };

  const filteredRequests = requests.filter(req => {
    const matchesSearch = 
      req.citizen_did.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.motivo_revelacion.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesState = filterState === null || req.state === filterState;
    return matchesSearch && matchesState;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Shield className="text-blue-600" size={28} />
            Solicitudes de Revelación de Identidad
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Gestiona las solicitudes para vincular DIDs con identidades civiles
          </p>
        </div>
      </div>

      {/* Info card */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Shield size={16} className="text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-blue-800">¿Cómo funciona?</h3>
            <p className="text-xs text-blue-700 mt-1 leading-relaxed">
              Cuando necesites vincular el DID (seudónimo) de un ciudadano con su identidad civil para un caso, 
              envías una solicitud. El ciudadano recibirá una notificación en su DApp y deberá autorizar 
              <strong> explícitamente</strong> antes de que puedas acceder a su identidad.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por DID, caso o motivo..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={filterState ?? ''}
            onChange={(e) => setFilterState(e.target.value ? Number(e.target.value) : null)}
            className="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los estados</option>
            <option value="0">Pendientes</option>
            <option value="1">Autorizadas</option>
            <option value="2">Reveladas</option>
            <option value="3">Rechazadas</option>
            <option value="4">Expiradas</option>
          </select>
        </div>
      </div>

      {/* Requests list */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 size={32} className="animate-spin mx-auto text-blue-600 mb-3" />
            <p className="text-sm text-slate-500">Cargando solicitudes...</p>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center">
            <Shield size={48} className="mx-auto text-slate-300 mb-3" />
            <p className="text-sm font-medium text-slate-600">No hay solicitudes de revelación</p>
            <p className="text-xs text-slate-400 mt-1">
              Las solicitudes aparecerán aquí cuando las envíes desde un caso
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredRequests.map((req) => {
              const stateConfig = STATE_CONFIG[req.state] || STATE_CONFIG[4];
              return (
                <div key={req.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${stateConfig.bgColor} ${stateConfig.color}`}>
                          {stateConfig.icon}
                          {stateConfig.label}
                        </span>
                        <span className="text-xs text-slate-400">#{req.id}</span>
                      </div>
                      
                      <p className="text-sm font-medium text-slate-800 mb-1">
                        {req.motivo_revelacion}
                      </p>
                      
                      <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <User size={12} />
                          DID: {req.citizen_did.slice(0, 20)}...
                        </span>
                        <span className="flex items-center gap-1">
                          <FileText size={12} />
                          Caso: {req.case_id}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock size={12} />
                          {formatDate(req.timestamp)}
                        </span>
                        {req.state === 0 && (
                          <span className="text-amber-600 font-medium">
                            Expira en: {getTimeRemaining(req.expires_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      {req.state === 0 && (
                        <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                          Esperando autorización
                        </span>
                      )}
                      {req.state === 1 && (
                        <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                          Lista para ejecutar
                        </span>
                      )}
                      {req.state === 2 && (
                        <a
                          href={`https://explorer-zk.tanenbaum.io/address/${req.civil_identity_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                        >
                          Ver en explorer <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-2xl font-bold text-slate-800">
            {requests.filter(r => r.state === 0).length}
          </div>
          <div className="text-xs text-slate-500">Pendientes</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-2xl font-bold text-green-600">
            {requests.filter(r => r.state === 1).length}
          </div>
          <div className="text-xs text-slate-500">Autorizadas</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-2xl font-bold text-blue-600">
            {requests.filter(r => r.state === 2).length}
          </div>
          <div className="text-xs text-slate-500">Reveladas</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="text-2xl font-bold text-red-600">
            {requests.filter(r => r.state === 3).length}
          </div>
          <div className="text-xs text-slate-500">Rechazadas</div>
        </div>
      </div>
    </div>
  );
}
