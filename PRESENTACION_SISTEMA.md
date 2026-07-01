# IntelExtorsión — Presentación del Sistema

---

## Diapositiva 1 — Portada

**IntelExtorsión**
Sistema de Inteligencia Ciudadana contra la Extorsión

Plataforma de recepción, análisis y correlación de denuncias con IA forense + Blockchain

---

## Diapositiva 2 — El Problema

**La extorsión en el Perú**

- Es uno de los delitos que más afecta a la ciudadanía
- Muchas víctimas no denuncian por:
  - Miedo a represalias
  - Desconfianza en el sistema
  - Falta de canales accesibles
- Las bandas criminales operan en redes organizadas
- La información se pierde al no estar centralizada ni correlacionada

---

## Diapositiva 3 — La Solución

**IntelExtorsión** es una plataforma que:

- ✅ Recibe reportes de extorsión por múltiples canales: Web, WhatsApp, Telegram y Discord
- ✅ Analiza la información con 10 agentes de Inteligencia Artificial especializados
- ✅ Correlaciona casos similares para detectar bandas criminales
- ✅ Preserva las evidencias en Blockchain para garantizar su integridad
- ✅ Entrega inteligencia procesada a las autoridades (DIVINCRI La Libertad)

---

## Diapositiva 4 — ¿Qué NO es el sistema?

- ❌ **NO** es un canal de denuncia formal a la policía
- ❌ **NO** reemplaza la línea 111 ni a la Fiscalía
- ❌ **NO** asigna protección policial

> Es una herramienta de **inteligencia ciudadana** que complementa los canales oficiales

---

## Diapositiva 5 — Canales de Ingreso

**4 canales para reportar:**

| Canal | Cómo funciona |
|-------|--------------|
| 🌐 **Web** | Portal ciudadano anónimo, sin registro |
| 📱 **WhatsApp** | Chat conversacional con asistente IA |
| ✈️ **Telegram** | Bot interactivo con soporte multi-archivo |
| 🎮 **Discord** | Bot con embeds y comandos |

**Características comunes:**
- Reporte 100% anónimo
- Soporta texto, imágenes, audios y documentos
- Sin necesidad de registrarse ni dar datos personales

---

## Diapositiva 6 — El Corazón del Sistema: 10 Agentes IA

**Un equipo de 10 especialistas virtuales trabajando en cadena:**

| Agente | Función |
|--------|---------|
| 1. Intake | Valida y clasifica la denuncia |
| 2. OCR | Extrae texto de imágenes |
| 3. Speech | Transcribe audios con Whisper |
| 4. NLP | Analiza lenguaje, sentimiento y entidades |
| 5. Correlation | Busca casos similares |
| 6. Cluster/NER | Detecta teléfonos, cuentas, montos, zonas |
| 7. OSINT | Enriquece con fuentes abiertas |
| 8. Risk | Calcula nivel de riesgo |
| 9. Seal | Sella evidencias en Blockchain |
| 10. Respond | Genera código de seguimiento |

---

## Diapositiva 7 — Flujo Completo del Sistema

**Paso a paso:**

1. **Ciudadano reporta** por cualquier canal
2. **Intake Agent** valida que sea extorsión
3. Procesamiento multimedia (OCR para imágenes, Whisper para audios)
4. **NLP Agent** analiza el texto completo y extrae entidades
5. **Correlation Agent** busca en el histórico casos similares
6. **Cluster Agent** detecta teléfonos, cuentas bancarias, montos, zonas
7. **OSINT Agent** enriquece la información
8. **Risk Agent** calcula nivel de riesgo (bajo, medio, alto, crítico)
9. Si es **ALTO/CRÍTICO**: se sella en Blockchain y se genera alerta
10. **Respond Agent** entrega código TRJ-XXXX al ciudadano

**Tiempo total:** segundos

---

## Diapositiva 8 — Motor Forense (NER)

**Extracción automática de 10 tipos de entidades:**

| Entidad | Ejemplo |
|---------|---------|
| Cuentas bancarias | BCP, BBVA, Interbank |
| Yape / Plin | Números asociados |
| Teléfonos extorsivos | +51 9XXXXXXXX |
| Montos | S/5,000 soles |
| Plazos | "tienes 24 horas" |
| Zonas geográficas | Distritos de La Libertad |
| Jerga criminal | "vacuna", "cuota", "derecho de piso" |
| Métodos de violencia | Secuestro virtual, amenaza de muerte |
| Frecuencia de pago | Diario, semanal, mensual |
| Medio de comunicación | WhatsApp, Telegram, llamada |

---

## Diapositiva 9 — Clustering de Bandas Criminales

**Detección automática de organizaciones criminales**

- Conecta denuncias que comparten:
  - Mismos números de teléfono
  - Mismas cuentas bancarias
  - Misma zona geográfica
  - Mismo método de operación
  - Montos similares
- Genera perfiles completos de bandas con:
  - Zona de operación principal
  - Miembros identificados (teléfonos, cuentas)
  - Nivel de alerta
  - Tendencia (creciente/decreciente)

---

## Diapositiva 10 — Blockchain y Evidencias

**Doble capa de integridad:**

1. **Sellado en zkSYS Tanenbaum Testnet**
   - Cada evidencia se reduce a un hash SHA-256
   - Ese hash se registra en la blockchain
   - Garantiza que la evidencia no fue alterada

2. **Smart Contracts**
   - **EvidenceRegistry**: Cadena de custodia
   - **CaseManager**: Gestión de casos
   - **DIDRegistry**: Identidad descentralizada
   - **Token**: NFT Soulbound por evidencia

3. **Acta Forense PDF**
   - Generación automática con firma digital ECDSA
   - Compatible con CPP art. 158-B
   - Sellada en blockchain

---

## Diapositiva 11 — Dashboard Policial

**Herramientas para las autoridades:**

- 📊 **Métricas:** Total denuncias, denuncias hoy, alertas críticas
- 🔍 **Búsqueda semántica:** Encuentra casos similares por lenguaje natural
- 🗺️ **Mapa de calor:** Zonas con más incidencia (Plan Cuadrante PNP)
- 🔗 **Grafos criminales:** Visualización de redes delictivas
- 🚨 **Centro de alertas:** Alertas priorizadas por nivel de riesgo
- 👥 **Gestión de usuarios:** Control de acceso por roles (admin, supervisor, analista)

---

## Diapositiva 12 — Privacidad y Seguridad

- **Anonimato total:** Sin registro, sin datos personales
- **RF-06:** Eliminación de metadatos EXIF de imágenes (GPS, serial, dispositivo)
- **Tracking:** Solo con código TRJ-XXXX, no se almacena identidad
- **Canales:** Filtros anti-bucles y anti-spam
- **Acceso:** Autenticación JWT para dashboard policial
- **Roles:** admin, supervisor, analista

---

## Diapositiva 13 — Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Lenguaje IA | GroqCloud (Llama 3.3 70B) |
| Agentes | LangGraph (grafo de estado) |
| Frontend | Next.js 14 + Tailwind |
| Backend | FastAPI + Python |
| Base de datos | PostgreSQL 16 + Qdrant + Redis |
| Blockchain | zkSYS Tanenbaum Testnet |
| Smart Contracts | Solidity 0.8.24 + OpenZeppelin |
| OCR | Tesseract (español) |
| STT | Groq Whisper |
| Contenedores | Docker Compose (8 servicios) |
| Despliegue | DigitalOcean + nginx |

---

## Diapositiva 14 — Despliegue Actual

**En producción (DigitalOcean):**

```
Frontend Ciudadano:    intelextorsion.duckdns.org
Frontend Policial:     intelextorsion.duckdns.org/policial
Agent API:             intelextorsion.duckdns.org/api
Web3 API:              intelextorsion.duckdns.org/web3api
```

**8 contenedores Docker corriendo:**
postgres, redis, qdrant, agent-api, web3-backend, citizen, police, dapp

---

## Diapositiva 15 — Roadmap

**Estado actual:** ✅ Fase 1 completada

**Próximos pasos:**
1. 🔐 HTTPS/SSL con Let's Encrypt
2. 💰 Despliegue en Syscoin NEVM Mainnet (producción real)
3. 🤖 Configurar canales reales (tokens de WhatsApp, Telegram, Discord)
4. 📍 GeoJSON oficial del Plan Cuadrante PNP
5. 📱 Notificaciones SMS / SIRDIC-SIDPOL
6. ⚡ Fase 2: Gas dinámico EIP-1559, firma digital real, Sepolia

---

## Diapositiva 16 — Cierre

**IntelExtorsión**
*Inteligencia Ciudadana contra la Extorsión*

_"Porque la seguridad se construye entre todos"_

**Preguntas?**
