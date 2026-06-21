import { create } from 'zustand';
import { Denuncia, Alerta, MetricasDashboard, CriminalGraph } from '@/types';

interface AppState {
  // Denuncias
  denuncias: Denuncia[];
  denunciaActiva: Denuncia | null;
  setDenuncias: (d: Denuncia[]) => void;
  setDenunciaActiva: (d: Denuncia | null) => void;

  // Alertas
  alertas: Alerta[];
  alertasNoLeidas: number;
  setAlertas: (a: Alerta[]) => void;
  marcarAlertaLeida: (id: string) => void;

  // Dashboard
  metricas: MetricasDashboard | null;
  setMetricas: (m: MetricasDashboard) => void;

  // Grafos
  grafoActivo: CriminalGraph | null;
  setGrafoActivo: (g: CriminalGraph | null) => void;

  // UI
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  temaOscuro: boolean;
  toggleTema: () => void;

  // Loading global
  loading: boolean;
  setLoading: (v: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  denuncias: [],
  denunciaActiva: null,
  setDenuncias: (denuncias) => set({ denuncias }),
  setDenunciaActiva: (denunciaActiva) => set({ denunciaActiva }),

  alertas: [],
  alertasNoLeidas: 0,
  setAlertas: (alertas) =>
    set({ alertas, alertasNoLeidas: alertas.filter((a) => !a.leida).length }),
  marcarAlertaLeida: (id) =>
    set((state) => ({
      alertas: state.alertas.map((a) => (a.id === id ? { ...a, leida: true } : a)),
      alertasNoLeidas: state.alertasNoLeidas - 1,
    })),

  metricas: null,
  setMetricas: (metricas) => set({ metricas }),

  grafoActivo: null,
  setGrafoActivo: (grafoActivo) => set({ grafoActivo }),

  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  temaOscuro: false,
  toggleTema: () => set((state) => ({ temaOscuro: !state.temaOscuro })),

  loading: false,
  setLoading: (loading) => set({ loading }),
}));
