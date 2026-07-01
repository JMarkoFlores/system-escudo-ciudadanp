# IntelExtorsión — Sistema de Inteligencia Ciudadana contra la Extorsión

---

## ¿Qué es IntelExtorsión?

IntelExtorsión es una **plataforma de inteligencia ciudadana** diseñada para combatir el delito de extorsión. Permite a los ciudadanos reportar extorsiones de forma anónima y segura, mientras que el sistema analiza automáticamente la información con **10 agentes de inteligencia artificial**, la cruza con otros casos similares y entrega inteligencia procesada a las autoridades competentes.

> **Importante:** Este NO es un canal de denuncia formal a la policía. Es una herramienta de inteligencia que complementa los canales oficiales (línea 111, comisarías). Los ciudadanos reciben un código de seguimiento, y la información analizada se entrega a la DIVINCRI La Libertad para acciones operativas.

---

## ¿Por qué IntelExtorsión?

La extorsión es uno de los delitos que más afecta a la ciudadanía, pero muchas víctimas no denuncian por miedo o desconfianza. IntelExtorsión rompe esa barrera ofreciendo:

- **Anonimato total** — No necesitas dar tus datos personales
- **Múltiples canales** — Reporta por web, WhatsApp, Telegram o Discord
- **Análisis con IA** — 10 agentes especializados analizan tu reporte
- **Bloquechain** — Las evidencias quedan selladas con hash criptográfico
- **Inteligencia accionable** — Los patrones detectados ayudan a las autoridades a actuar

---

## Cómo Funciona: El Flujo Completo

### Paso 1: El Ciudadano Reporta

Puedes reportar una extorsión desde cualquiera de estos canales:

**🌐 Portal Web**
Entras al portal ciudadano, describes los hechos y adjuntas evidencias (capturas de pantalla, audios, documentos). No necesitas registrarte ni dar tus datos. Recibes un código de seguimiento.

**📱 WhatsApp**
Escribes al número del sistema. Un asistente conversacional te guía:
1. Te pregunta si la amenaza es de un particular/banda criminal o de un funcionario público
2. Te pide describir los hechos
3. Puedes enviar audios (se transcriben automáticamente), imágenes o documentos
4. El sistema agrupa todo lo que envíes en una sola denuncia
5. Recibes un código de seguimiento como `TRJ-A4K2`

**✈️ Telegram / 🎮 Discord**
Mismo flujo conversacional: el bot recibe tu reporte, lo procesa y te entrega un código.

### Paso 2: Llega al Sistema

En milisegundos, el reporte es recibido y almacenado de forma segura. El sistema inicia automáticamente el análisis con sus 10 agentes de IA.

### Paso 3: El Equipo de Agentes IA Trabaja

Aquí es donde ocurre la magia. El sistema despliega un **equipo de 10 especialistas en IA**, cada uno con una misión específica:

#### 1. Agente de Ingreso (Intake) 🚪
Evalúa si el reporte es una denuncia de extorsión válida. Si lo es, clasifica el tipo de extorsión y asigna una prioridad inicial.

#### 2. Agente OCR (Visión por Computador) 👁️
Si adjuntaste imágenes o capturas de pantalla, este agente extrae todo el texto usando reconocimiento óptico de caracteres. Ideal para cartas de extorsión, chats, o volantes.

#### 3. Agente de Transcripción (Speech) 🎙️
Si enviaste un audio o nota de voz, lo transcribe automáticamente usando Whisper (el mismo motor que usa OpenAI). Detecta emociones en la voz como miedo, estrés o ira.

#### 4. Agente de Procesamiento de Lenguaje (NLP) 📝
Analiza todo el texto disponible (el que escribiste + el extraído de imágenes + la transcripción del audio). Entiende la intención, detecta amenazas, extrae palabras clave y calcula un nivel de amenaza.

#### 5. Agente de Correlación 🔗
Busca en la base de datos histórica si hay otros casos similares. ¿El mismo número de teléfono ya fue reportado? ¿La misma cuenta bancaria? ¿El mismo _modus operandi_? Esto permite detectar bandas organizadas.

#### 6. Agente Forense (NER) 🔍
Un especialista en lingüística forense extrae información crítica del texto:
- **Cuentas bancarias** (BCP, BBVA, Interbank, etc.)
- **Teléfonos** de los extorsionadores
- **Montos** exigidos (con moneda y periodicidad)
- **Plazos** de pago
- **Zonas geográficas** donde ocurre la extorsión
- **Jerga criminal** ("vacuna", "cuota", "derecho de piso")
- **Métodos de violencia** (secuestro virtual, amenaza de muerte)
- **Medios de comunicación** usados (WhatsApp, Telegram, llamada)

#### 7. Agente de Inteligencia Abierta (OSINT) 🌐
Revisa fuentes públicas para enriquecer la información. Por ejemplo, si un número de teléfono aparece en reportes previos de extorsión, lo marca como alto riesgo.

#### 8. Agente de Riesgo ⚠️
El más importante. Toma toda la información recopilada por los agentes anteriores y calcula el nivel de riesgo:
- **BAJO** — Amenaza genérica, sin datos personales
- **MEDIO** — Amenaza con datos parciales
- **ALTO** — Amenaza con datos exactos, posible reincidencia
- **CRÍTICO** — Amenaza de muerte inminente, peligro real

#### 9. Agente de Sellado Blockchain 🔐
Si el riesgo es ALTO o CRÍTICO, este agente toma el contenido de la denuncia, calcula su huella digital (hash SHA-256) y la **sella en la blockchain de zkSYS Tanenbaum**. Esto garantiza que la evidencia no puede ser modificada ni borrada, y queda trazable para procesos judiciales.

#### 10. Agente de Respuesta ✅
Finalmente, genera un **código de seguimiento único** (`TRJ-XXXX`) y prepara un mensaje para el ciudadano. Si el riesgo es alto, el mensaje indica que el caso ha sido escalado a la unidad de inteligencia.

### Paso 4: El Ciudadano Recibe su Código

En cuestión de segundos, el ciudadano recibe:
- Su código de seguimiento: `TRJ-A4K2`
- El nivel de riesgo estimado
- Instrucciones de qué sigue

Puede consultar el estado de su denuncia en cualquier momento usando ese código.

### Paso 5: Generación de Inteligencia

El sistema no solo procesa denuncias individuales. También:

- **Agrupa casos similares** — Automáticamente detecta bandas criminales conectando denuncias que comparten el mismo teléfono, cuenta bancaria, zona geográfica o método de operación
- **Crea alertas** — Si se detecta un patrón de alto riesgo, se genera una alerta oficial
- **Mapa de calor** — Visualiza las zonas con más incidencia de extorsión usando datos del Plan Cuadrante PNP

### Paso 6: Las Autoridades Actúan

La información procesada llega al **dashboard policial**, donde los oficiales pueden:
- Ver todas las denuncias registradas
- Consultar alertas generadas (filtradas por nivel de riesgo)
- Visualizar redes criminales en un grafo interactivo
- Ver mapas de calor por zonas
- Dar seguimiento a casos específicos

---

## Tecnología por Debajo (Para Curiosos)

Sin entrar en detalle técnico, el sistema usa:

- **10 Agentes con IA** impulsados por **GroqCloud** (modelo Llama 3.3 de 70 mil millones de parámetros)
- **Blockchain zkSYS Tanenbaum** para sellado de evidencias (como un notario digital inmutable)
- **Base de datos vectorial** que permite buscar casos similares por "significado" y no solo por palabras exactas
- **Reconocimiento de imágenes** con Tesseract OCR (el mismo que usa Google)
- **Transcripción de audio** con Whisper (el mismo que usa ChatGPT)
- **Cifrado y privacidad** — Las imágenes subidas pierden todos los metadatos (GPS, serial de cámara, etc.)

---

## ¿Quién Está Detrás?

IntelExtorsión es una iniciativa de **inteligencia ciudadana** desarrollada para apoyar la labor de la **DIVINCRI La Libertad** en la lucha contra la extorsión. No reemplaza a las instituciones, sino que las potencia con tecnología de vanguardia.

---

## Canales Disponibles

| Canal | Cómo acceder |
|-------|-------------|
| 🌐 Web | Portal ciudadano en el sitio oficial |
| 📱 WhatsApp | Envía un mensaje al número oficial del sistema |
| ✈️ Telegram | Busca el bot oficial IntelExtorsión |
| 🎮 Discord | Únete al servidor oficial de inteligencia ciudadana |

---

## Privacidad y Seguridad

Tu privacidad es lo más importante:
- **No necesitas registrarte** ni dar tu nombre, DNI o dirección
- **Las imágenes son anonimizadas** — se eliminan los metadatos que puedan identificar tu ubicación o dispositivo
- **Tu conversación por WhatsApp es confidencial** — no almacenamos tu número, solo un hash anónimo
- **Puedes consultar tu caso** solo con el código que recibiste
- **Las evidencias se sellan en blockchain** para que no puedan ser alteradas por nadie

---

## Lo Que NO Hace Este Sistema

- ❌ No es una línea de emergencia (para eso está el 111)
- ❌ No reemplaza una denuncia formal ante la Fiscalía
- ❌ No asigna policías para que te protejan
- ❌ No funciona como chat de ayuda psicológica

## Lo Que SÍ Hace

- ✅ Recibe tu reporte de forma anónima y segura
- ✅ Lo analiza con inteligencia artificial forense
- ✅ Lo cruza con otros casos para detectar bandas
- ✅ Genera inteligencia procesada para las autoridades
- ✅ Preserva las evidencias en blockchain para procesos judiciales

---

*IntelExtorsión — Inteligencia Ciudadana contra la Extorsión*
*Porque la seguridad se construye entre todos.*
