import axios from 'axios';
import { Denuncia, Alerta, MetricasDashboard, CriminalGraph, Cluster, ClusterDenunciaAnonima, HeatmapPoint } from '@/types';

const agentApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_AGENT_API_URL || '/api/agents',
  timeout: 30000,
});

const web3Api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_WEB3_API_URL || '/api/web3',
  timeout: 30000,
});

// Denuncias
export const denunciaService = {
  crear: (data: {
    canal: string;
    tipo_contenido: string;
    contenido_raw?: string;
    url_archivo?: string;
    did_denunciante?: string;
    metadata?: Record<string, unknown>;
  }) => agentApi.post<{ id: string }>('/denuncias', data),

  obtener: (id: string) => agentApi.get<Denuncia>(`/denuncias/${id}`),

  procesar: (id: string, modo?: string, agentes?: string[]) =>
    agentApi.post(`/denuncias/${id}/procesar`, { modo, agentes }),

  listar: (params?: { estado?: string; canal?: string }) =>
    agentApi.get<Denuncia[]>('/denuncias', { params }),

  buscarSemantica: (q: string, limit?: number) =>
    agentApi.get('/busqueda/semantica', { params: { q, limit } }),

  listarArchivos: (id: string) =>
    agentApi.get<{
      denuncia_id: string;
      total_archivos: number;
      archivos: Array<{
        index: number;
        path: string;
        filename: string;
        tipo: string;
        principal: boolean;
        existe: boolean;
      }>;
    }>(`/denuncias/${id}/archivos`),
};

// Alertas
export const alertaService = {
  listar: () => agentApi.get<Alerta[]>('/alertas'),
  obtenerPorDenuncia: (denunciaId: string) =>
    agentApi.get<{ alertas: Alerta[] }>(`/denuncias/${denunciaId}/alertas`),
};

// Dashboard
export const dashboardService = {
  metricas: () => agentApi.get<MetricasDashboard>('/dashboard/metricas'),
  serieTemporal: (dias?: number) =>
    agentApi.get('/dashboard/serie-temporal', { params: { dias } }),
};

// Web3 / Blockchain
export const web3Service = {
  health: () => web3Api.get('/health'),

  registrarEvidencia: (formData: FormData) =>
    web3Api.post<{
      success: boolean;
      evidence_id?: number;
      evidence_hash: string;
      tx_hash: string;
      block_number: number;
      ipfs_cid: string;
    }>('/evidencias', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  verificarEvidencia: (evidenceId: number, file: File) => {
    const formData = new FormData();
    formData.append('evidence_id', String(evidenceId));
    formData.append('file', file);
    return web3Api.post('/evidencias/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  crearCaso: (data: {
    did_denunciante: string;
    nivel_riesgo: number;
    resumen: string;
    metadata_uri?: string;
  }) => web3Api.post('/casos', data),

  obtenerCaso: (caseId: number) => web3Api.get(`/casos/${caseId}`),

  resolverDID: (did: string) => web3Api.get(`/did/${did}`),
};

// Grafos
export const graphService = {
  obtener: (denunciaId?: string) =>
    agentApi.get<CriminalGraph>('/grafos/criminal', { params: { denuncia_id: denunciaId } }),
};

// Clusters
export const clusterService = {
  listar: (params?: { estado?: string; zona?: string; nivel_alerta?: string }) =>
    agentApi.get<Cluster[]>('/clusters', { params }),
  obtener: (id: number) =>
    agentApi.get<Cluster>(`/clusters/${id}`),
  obtenerDenuncias: (id: number) =>
    agentApi.get<{ alertas: ClusterDenunciaAnonima[] }>(`/clusters/${id}/denuncias`),
  recalcular: () =>
    agentApi.post('/clusters/recalculate'),
};

// Heatmap
export const heatmapService = {
  obtener: (params?: { zona?: string; periodo?: number }) =>
    agentApi.get<{ puntos: HeatmapPoint[] }>('/heatmap', { params }),
};
