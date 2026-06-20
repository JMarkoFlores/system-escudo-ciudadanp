# Manual del Ciudadano - Cómo Realizar una Denuncia en IntelExtorsión

> **Última actualización:** 2026-06-19
> **Versión del sistema:** 1.0.0 (Post-migración GroqCloud)

---

## 1. Acceso al Portal Ciudadano

1. Abre tu navegador web y ve a: **`http://localhost:3000/portal`**
2. Se mostrará el **Portal Ciudadano** de IntelExtorsión.

---

## 2. Canales de Denuncia Disponibles

En la parte superior encontrarás 4 canales. Selecciona el que prefieras:

| Canal | Color | Descripción |
|-------|-------|-------------|
| **WhatsApp** | Verde | Simula denuncia vía WhatsApp |
| **Telegram** | Azul claro | Simula denuncia vía Telegram |
| **Discord** | Índigo | Simula denuncia vía Discord |
| **Web** | Gris oscuro | Denuncia directa por la plataforma web *(recomendado)* |

> **Nota:** Actualmente todas las denuncias se procesan de la misma manera independientemente del canal seleccionado. El canal sirve para clasificación estadística.

---

## 3. Autenticación Opcional (DID)

En la esquina superior derecha verás un botón:
- **"Conectar DID"**: Permite vincular tu wallet (Pali Wallet) para mayor anonimato y trazabilidad en blockchain.
- Si no conectas DID, la denuncia será **completamente anónima**.

---

## 4. Escribir tu Denuncia

1. En el campo de texto inferior escribe tu situación. Sé lo más detallado posible:
   - **Números telefónicos** del extorsionador
   - **Montos** exigidos
   - **Plazos** o amenazas recibidas
   - **Métodos de pago** solicitados
   - Cualquier otro dato relevante

2. Presiona el botón **azul con ícono de avión** (o presiona `Enter`).

---

## 5. Confirmación de Recepción

Si la denuncia se registra correctamente, verás:
- Un mensaje del sistema: *"Tu denuncia ha sido registrada con ID: [UUID]. Nuestros agentes de IA están analizando la información..."*
- Una notificación verde arriba a la derecha: **"Denuncia registrada exitosamente"**

> **⚠️ Si ves "Error al registrar denuncia" en rojo:**
> - Verifica que todos los servicios Docker estén corriendo (`docker compose ps`)
> - Revisa que el backend (Agent API) esté saludable en `http://localhost:8000/health`
> - Contacta al administrador del sistema

---

## 6. Qué Sucede Después (Procesamiento Automático)

Una vez enviada, **8 agentes de IA** analizan tu denuncia automáticamente:

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

## 7. Niveles de Riesgo y Alertas

| Nivel | Descripción | Acción |
|-------|-------------|--------|
| **Bajo** | Amenaza genérica, sin datos personales | Análisis estándar |
| **Medio** | Amenaza con datos parciales | Revisión por analista |
| **Alto** | Amenaza con datos exactos, serie confirmada | **Alerta inmediata** |
| **Crítico** | Secuestro/amenaza de muerte inminente | **Alerta máxima + acción inmediata** |

---

## 8. Adjuntar Evidencias

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

> **Tip:** Las evidencias se preservan en blockchain (Rollux L2) si conectaste tu DID, garantizando inmutabilidad legal.

> **Nota:** Si adjuntas un archivo, el sistema detectará automáticamente el tipo (`imagen`, `audio` o `documento`) y los agentes de IA (OCR, Speech) lo analizarán según corresponda.

---

## 9. Confidencialidad y Seguridad

- ✅ Tu denuncia es **confidencial**.
- ✅ Los datos personales se minimizan (principio de minimización).
- ✅ Las comunicaciones usan HTTPS.
- ✅ Las evidencias en blockchain son inmutables y auditables.

---

## 10. Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| "Error al registrar denuncia" | Verifica `docker compose ps`. Reinicia con `docker compose restart` |
| Dashboard policial no muestra denuncias | Verifica que el Agent API tenga el endpoint `GET /v1/denuncias` activo |
| Botones de adjuntar no funcionan | Verifica que estés usando la última versión del frontend (`docker compose build frontend`) |
| Página en blanco | Verifica que el frontend esté en `localhost:3000` |
| No carga el chat | Limpia caché del navegador (Ctrl+F5) |
| Botón "Conectar DID" no hace nada | Instala Pali Wallet en tu navegador |

---

## 11. Endpoints de la API (para desarrolladores)

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

# Consultar estado
curl http://localhost:8000/v1/denuncias/{id}
```

---

## 12. Soporte

Para reportar problemas técnicos o solicitar ayuda:
- Revisa la documentación técnica en `AGENTS.md`
- Consulta la guía de instalación en `INSTALL.md`
- Revisa troubleshooting en `RUN.md`

---

*IntelExtorsión - Protegiendo a la ciudadanía con inteligencia artificial y blockchain.*
