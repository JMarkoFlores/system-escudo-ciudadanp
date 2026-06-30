# Manual del Ciudadano - Cómo Reportar Información en IntelExtorsión

> **Última actualización:** 2026-06-29
> **Versión del sistema:** 1.0.0

---

## ⚠️ IMPORTANTE: Este es un Sistema de Inteligencia Ciudadana

**IntelExtorsión NO es un canal directo de denuncia formal a la policía.**

Este sistema es una plataforma de **INTELIGENCIA CIUDADANA** que:
- Recibe reportes de extorsión de ciudadanos
- Analiza la información con IA forense
- Correlaciona casos similares
- Entrega inteligencia procesada a las autoridades competentes (DIVINCRI La Libertad)
- Sella evidencias en blockchain para trazabilidad judicial

**Para denuncias formales ante la Fiscalía o la PNP, utiliza la línea 111 o acude a la comisaría más cercana.** Este sistema complementa, pero no reemplaza, los canales oficiales de denuncia.

---

## 1. Acceso al Portal Ciudadano

1. Abre tu navegador web y ve a: **`http://localhost:3000/portal`**
2. Se mostrará el **Portal Ciudadano** de IntelExtorsión.
3. También puedes consultar el estado de tu reporte en: **`http://localhost:3000/tracking?code=TRJ-XXXXXXXX`** (reemplaza `XXXXXXXX` por tu código de 8 caracteres).

---

## 2. Canales de Reporte Disponibles

En la parte superior encontrarás 4 canales. Selecciona el que prefieras:

| Canal | Color | Descripción |
|-------|-------|-------------|
| **WhatsApp** | Verde | Reporte vía WhatsApp |
| **Telegram** | Azul claro | Reporte vía Telegram |
| **Discord** | Índigo | Reporte vía Discord |
| **Web** | Gris oscuro | Reporte directo por la plataforma web *(recomendado)* |

> **Nota:** Actualmente todos los reportes se procesan de la misma manera independientemente del canal seleccionado. El canal sirve para clasificación estadística.

---

## 3. Menú de Clasificación del Reporte (RF-01)

Al interactuar por WhatsApp, Telegram o Discord, el bot te presentará un menú inicial:

1. **Reporte de extorsión ciudadana** → Procesa tu caso con los agentes de IA.
2. **Denuncia contra funcionario público o policía** → El bot te redirige a los canales oficiales (Inspectoría de la PNP o Fiscalía) **sin almacenar tu reporte en la base de evidencias**.

> **Privacidad:** Los bots no guardan tu número de teléfono, nombre de usuario ni otros identificadores personales. Solo se almacena un `session_id` anónimo para mantener la conversación.

---

## 4. Autenticación Opcional (DID)

En la esquina superior derecha verás un botón:
- **"Conectar DID"**: Permite vincular tu wallet (Pali Wallet) para mayor anonimato y trazabilidad en blockchain.
- Si no conectas DID, la denuncia será **completamente anónima**.

---

## 5. Escribir tu Denuncia

1. En el campo de texto inferior escribe tu situación. Sé lo más detallado posible:
   - **Números telefónicos** del extorsionador
   - **Montos** exigidos
   - **Plazos** o amenazas recibidas
   - **Métodos de pago** solicitados
   - Cualquier otro dato relevante

2. Presiona el botón **azul con ícono de avión** (o presiona `Enter`).

---

## 6. Confirmación de Recepción

Si la denuncia se registra correctamente, verás:
- Un mensaje del sistema: *"Tu denuncia ha sido registrada con ID: [UUID]. Nuestros agentes de IA están analizando la información..."*
- Una notificación verde arriba a la derecha: **"Denuncia registrada exitosamente"**

> **⚠️ Si ves "Error al registrar denuncia" en rojo:**
> - Verifica que todos los servicios Docker estén corriendo (`docker compose ps`)
> - Revisa que el backend (Agent API) esté saludable en `http://localhost:8000/health`
> - Contacta al administrador del sistema

---

## 7. Qué Sucede Después (Procesamiento Automático)

Una vez enviado, **10 agentes de IA** analizan tu reporte automáticamente:

| Agente | Función |
|--------|---------|
| **Intake** | Valida que sea una denuncia real de extorsión |
| **OCR** | Analiza imágenes o documentos adjuntos |
| **Speech** | Transcribe audios si los hay |
| **NLP** | Extrae entidades, sentimiento, score de amenaza |
| **Correlation** | Busca casos similares en la base de datos |
| **OSINT** | Investiga números telefónicos y cuentas en fuentes abiertas |
| **Risk** | Calcula el nivel de riesgo (bajo / medio / alto / crítico) |
| **Alert** | Si el riesgo es alto o crítico, genera alerta policial |

---

## 8. Niveles de Riesgo y Alertas

| Nivel | Descripción | Acción |
|-------|-------------|--------|
| **Bajo** | Amenaza genérica, sin datos personales | Análisis estándar |
| **Medio** | Amenaza con datos parciales | Revisión por analista |
| **Alto** | Amenaza con datos exactos, serie confirmada | **Alerta inmediata** |
| **Crítico** | Secuestro/amenaza de muerte inminente | **Alerta máxima + acción inmediata** |

---

## 9. Adjuntar Evidencias

En la barra inferior del chat encontrarás 3 botones para adjuntar evidencias:

| Botón | Icono | Qué adjunta |
|-------|-------|-------------|
| **Adjuntar archivo** | 📎 Paperclip | Documentos PDF, Word, TXT, etc. |
| **Adjuntar imagen** | 🖼️ Image | Capturas de pantalla, fotos (JPG, PNG, etc.) |
| **Adjuntar audio** | 🎙️ Mic | Grabaciones de llamadas de extorsión (MP3, WAV, etc.) |

### Cómo adjuntar:
1. Presiona el botón correspondiente al tipo de archivo.
2. Se abrirá el selector de archivos de tu sistema operativo.
3. Selecciona el archivo.
4. Verás una vista previa/nombre del archivo arriba del campo de texto.
5. Escribe una descripción si lo deseas.
6. Presiona **Enviar** (🔵).

> **Tip:** Las evidencias se preservan en blockchain (zkSYS Tanenbaum Testnet) si conectaste tu DID, garantizando trazabilidad.

> **Nota:** Si adjuntas un archivo, el sistema detectará automáticamente el tipo (`imagen`, `audio` o `documento`) y los agentes de IA (OCR, Speech) lo analizarán según corresponda.

---

## 10. Confidencialidad y Seguridad

- ✅ Tu reporte es **confidencial**.
- ✅ Los datos personales se minimizan (principio de minimización).
- ✅ Los canales conversacionales (WhatsApp, Telegram, Discord) no almacenan tu número, nombre de usuario ni chat ID.
- ✅ Las comunicaciones usan HTTPS.
- ✅ Las evidencias en blockchain son inmutables y auditables.
- ✅ Tu información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa.

---

## 11. Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| "Error al registrar denuncia" | Verifica `docker compose ps`. Reinicia con `docker compose restart` |
| Dashboard policial pide login o no muestra denuncias | Usa las credenciales seed (`admin` / `Admin123!`) o las configuradas en producción. Asegúrate de que el token JWT esté almacenado. |
| Botones de adjuntar no funcionan | Verifica que estés usando la última versión del frontend (`docker compose build frontend-citizen`) |
| Página en blanco | Verifica que el frontend ciudadano esté en `localhost:3000` |
| No carga el chat | Limpia caché del navegador (Ctrl+F5) |
| Botón "Conectar DID" no hace nada | Instala Pali Wallet en tu navegador y configura la red **zkSYS Tanenbaum Testnet (Chain ID 57057)** |
| Pali Wallet muestra red incorrecta | Cambia manualmente a **zkSYS Tanenbaum Testnet (Chain ID 57057)** en la extensión |

---

## 12. Endpoints de la API (para desarrolladores)

Si necesitas integrar el sistema externamente:

```bash
# Crear denuncia
curl -X POST http://localhost:8000/v1/denuncias \
  -H "Content-Type: application/json" \
  -d '{
    "canal": "web",
    "tipo_contenido": "texto",
    "contenido_raw": "Texto de la denuncia..."
  }'

# Procesar denuncia manualmente
curl -X POST http://localhost:8000/v1/denuncias/{id}/procesar \
  -H "Content-Type: application/json" \
  -d '{"denuncia_id": "{id}", "modo": "completo"}'

# Consultar estado por ID (requiere autenticación)
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!" | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/denuncias/{id}

# Consultar estado por tracking code (público para el ciudadano)
curl http://localhost:8000/v1/denuncias/tracking/TRJ-XXXXXXXX
```

---

## 13. Soporte

Para reportar problemas técnicos o solicitar ayuda:
- Revisa la documentación técnica en `AGENTS.md`
- Consulta la guía de instalación en `INSTALL.md`
- Revisa troubleshooting en `RUN.md`

---

*IntelExtorsión - Inteligencia ciudadana para combatir la extorsión con IA y blockchain zkSYS Tanenbaum Testnet.*
