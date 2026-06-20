# IntelExtorsión Frontend

Frontend completo de la plataforma IntelExtorsión construido con **Next.js 14**, **TypeScript** y **Tailwind CSS**.

## Arquitectura

```
src/
├── app/                     # App Router (Next.js 14)
│   ├── layout.tsx           # Root layout global
│   ├── page.tsx             # Landing Page
│   ├── globals.css          # Tailwind + variables CSS
│   ├── portal/
│   │   └── page.tsx         # Portal Ciudadano + Chat
│   └── dashboard/
│       ├── layout.tsx       # Layout con Sidebar
│       ├── policial/
│       │   └── page.tsx     # Dashboard Policial
│       ├── analitico/
│       │   └── page.tsx     # Dashboard Analítico (Recharts)
│       ├── grafos/
│       │   └── page.tsx     # Visualización de redes (Force Graph)
│       └── alertas/
│           └── page.tsx     # Centro de Alertas
├── components/
│   ├── layout/              # Layouts compartidos
│   ├── ui/                  # Componentes UI reutilizables
│   └── charts/              # Wrappers de gráficos
├── hooks/                   # Custom hooks (si se necesitan fuera de stores)
├── services/
│   └── api.ts               # Servicios API tipados (axios)
├── stores/
│   ├── appStore.ts          # Estado global de la app (Zustand)
│   └── walletStore.ts       # Estado Web3 / Pali Wallet
├── types/
│   └── index.ts             # Tipos TypeScript compartidos
└── lib/
    └── utils/
        └── cn.ts            # Utilidad cn() para Tailwind
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Framework | Next.js 14 (App Router) |
| Lenguaje | TypeScript 5 |
| Estilos | Tailwind CSS + CSS Variables |
| Estado Global | Zustand |
| Gráficos | Recharts |
| Grafos | react-force-graph-2d |
| HTTP Client | Axios |
| Web3 | ethers.js v6 + Pali Wallet |
| Fechas | date-fns |
| Icons | Lucide React |
| Toast | react-hot-toast |

## Páginas Implementadas

### 1. Landing Page (`/`)
- Hero section con CTA
- Características del sistema (Agentes IA, Web3, Análisis)
- Canales de denuncia (WhatsApp, Telegram, Discord)
- Sección Web3 / DID / Pali Wallet

### 2. Portal Ciudadano (`/portal`)
- Chat interactivo para realizar denuncias
- Selector de canal (WhatsApp, Telegram, Discord, Web)
- Integración con DID vía Pali Wallet
- Envío de archivos (audio, imagen, documento)
- Conexión a API de Agentes

### 3. Dashboard Policial (`/dashboard/policial`)
- KPIs en tiempo real (stats cards)
- Tabla de denuncias recientes
- Estados de procesamiento con badges

### 4. Dashboard Analítico (`/dashboard/analitico`)
- Gráfico de líneas: actividad semanal
- Gráfico de pastel: denuncias por canal
- Gráfico de barras: distribución por riesgo
- KPIs adicionales con progress bars

### 5. Redes Criminales (`/dashboard/grafos`)
- Visualización de grafos interactivos (Force Graph 2D)
- Nodos: denunciantes, sospechosos, teléfonos, cuentas, casos
- Links: relaciones entre entidades
- Leyenda de colores por grupo

### 6. Centro de Alertas (`/dashboard/alertas`)
- Listado de alertas por nivel (bajo, medio, alto, crítico)
- Filtros: todas, no leídas, críticas
- Acciones: marcar leída, atender
- Metadata de denuncia asociada

## Estado Global (Zustand)

### App Store
- `denuncias`, `denunciaActiva`
- `alertas`, `alertasNoLeidas`
- `metricas`
- `grafoActivo`
- `sidebarOpen`, `temaOscuro`
- `loading`

### Wallet Store
- `account`, `chainId`, `isConnected`, `provider`
- `did`, `reputation`
- `connect()`, `disconnect()`, `switchToZkSYS()`

## Servicios API

Todos los servicios están centralizados en `services/api.ts`:

- `denunciaService` - CRUD de denuncias + búsqueda semántica
- `alertaService` - Listado de alertas
- `dashboardService` - Métricas y series temporales
- `web3Service` - Registro/verificación de evidencias, casos, DID
- `graphService` - Obtención de datos de grafos

## Integración Web3

### Pali Wallet
La store `walletStore` gestiona:
1. Detección de `window.pali`
2. Conexión vía `eth_requestAccounts`
 3. Validación de red (Chain ID 5700 = zkSYS Genesis Testnet)
 4. Cambio automático a red zkSYS (`wallet_addEthereumChain`)
 5. Generación automática de DID: `did:zksys:<address>`

### Contratos
Las direcciones de contratos se configuran en variables de entorno:
- `NEXT_PUBLIC_CONTRACT_EVIDENCE_REGISTRY`
- `NEXT_PUBLIC_CONTRACT_CASE_MANAGER`
- `NEXT_PUBLIC_CONTRACT_DID_REGISTRY`
- `NEXT_PUBLIC_CONTRACT_TOKEN`

## Instalación y Ejecución

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con las URLs de las APIs y contratos

# 3. Modo desarrollo
npm run dev

# 4. Type check
npm run type-check

# 5. Build de producción
npm run build
npm start
```

### Variables de Entorno (.env.local)
```
NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000
NEXT_PUBLIC_WEB3_API_URL=http://localhost:8001
NEXT_PUBLIC_RPC_URL=https://rpc.genesis.zksys.io
NEXT_PUBLIC_CHAIN_ID=5700
NEXT_PUBLIC_CONTRACT_EVIDENCE_REGISTRY=0x...
NEXT_PUBLIC_CONTRACT_CASE_MANAGER=0x...
NEXT_PUBLIC_CONTRACT_DID_REGISTRY=0x...
NEXT_PUBLIC_CONTRACT_TOKEN=0x...
```

## Buenas Prácticas Aplicadas

1. **App Router:** Uso de la nueva arquitectura de Next.js 14 con layouts anidados
2. **TypeScript Estricto:** Tipado completo de stores, servicios y componentes
3. **Separación de Concerns:** Stores, servicios, componentes y tipos desacoplados
4. **Client Components:** Uso explícito de `'use client'` solo donde se necesita interactividad
5. **Tailwind:** Utilidades atómicas sin CSS modules innecesarios
6. **Responsive:** Grid system mobile-first en todos los dashboards
7. **Loading States:** Estados de carga y datos demo como fallback
8. **Accessibility:** Iconos con labels, contrastes adecuados, estructura semántica

## Integración con Subsistemas

```
Frontend (Next.js)
    │
    ├──► Agent System API (FastAPI :8000)
    │     POST /v1/denuncias
    │     GET  /v1/denuncias/{id}
    │     GET  /v1/busqueda/semantica
    │
    └──► Web3 Backend API (FastAPI :8001)
          POST /v1/evidencias
          POST /v1/evidencias/verify
          POST /v1/casos
          GET  /v1/did/{did}
          │
          └──► zkSYS Genesis Testnet (JSON-RPC)
```

---

*Frontend enterprise listo para producción.*
