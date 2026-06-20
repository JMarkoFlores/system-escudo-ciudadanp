export interface Denuncia {
  id: string;
  canal: 'whatsapp' | 'telegram' | 'discord' | 'web' | 'api';
  estado: string;
  tipo_contenido: 'texto' | 'imagen' | 'audio' | 'video' | 'documento' | 'mixto';
  contenido_raw?: string;
  url_archivo?: string;
  hash_archivo?: string;
  did_denunciante?: string;
  created_at: string;
  updated_at?: string;
  resultados?: AgenteResultado[];
}

export interface AgenteResultado {
  agente: string;
  exitoso: boolean;
  resultado: Record<string, unknown>;
  created_at: string;
}

export interface Alerta {
  id: string;
  denuncia_id: string;
  nivel: 'bajo' | 'medio' | 'alto' | 'critico';
  titulo: string;
  descripcion: string;
  recomendacion?: string;
  leida: boolean;
  atendida: boolean;
  created_at: string;
}

export interface EvidenceChain {
  evidence_id: number;
  evidence_hash: string;
  tx_hash: string;
  block_number: number;
  ipfs_cid: string;
  custodian: string;
  timestamp: number;
  active: boolean;
}

export interface CasoBlockchain {
  id: number;
  did_denunciante: string;
  creador: string;
  estado: number;
  nivel_riesgo: number;
  resumen: string;
  created_at: number;
  updated_at: number;
  active: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  group: 'denunciante' | 'sospechoso' | 'evidencia' | 'telefono' | 'cuenta' | 'caso';
  val?: number;
  metadata?: Record<string, unknown>;
}

export interface GraphLink {
  source: string;
  target: string;
  label?: string;
  value?: number;
}

export interface CriminalGraph {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface MetricasDashboard {
  total_denuncias: number;
  denuncias_hoy: number;
  alertas_criticas: number;
  casos_resueltos: number;
  tiempo_promedio_respuesta_min: number;
  evidencias_registradas: number;
}

export interface SerieTemporal {
  fecha: string;
  denuncias: number;
  alertas: number;
  resueltos: number;
}
