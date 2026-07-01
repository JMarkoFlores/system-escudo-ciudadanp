# Ejemplo de Denuncia — Reporte de Extorsión

> **Contexto:** Víctima es dueña de una bodega en Florencia de Mora, Trujillo.
> **Idioma:** Inglés (con jerga peruana traducida para contexto internacional).
> **Contenido:** Texto del mensaje + 2 evidencias (captura de WhatsApp + audio de amenaza).

---

## 1. Texto del Mensaje (vía WhatsApp Web)

```
From: +51 948 123 456 (unknown)
Date: June 25, 2026, 8:47 PM
Attachments: amenaza.jpeg, audio_amenaza.mp3
---

Hey, listen up. This is the second time I'm writing to you.

We know you run the bodega on Los Olivos Avenue, corner with
Miraflores Street. We know your kids leave school at 2 PM.

The quota is 5,000 soles per month. You pay on the 1st or bad
things happen. First payment is this Friday, July 3, via Yape
to 948 123 456. No excuses.

Don't even think about going to the cops. We have people in
the precinct too. We'll know.

This is not a joke. We burned down Don José's store last week
because he didn't pay. You want the same?

You have 48 hours. Tick-tock.
```

---

## 2. Evidencia 1 — Captura de WhatsApp (`amenaza.jpeg`)

> **Descripción:** Screenshot del chat donde se ve el mensaje de texto
> escrito arriba, con el número +51 948 123 456, hora 8:47 PM,
> check azul (leído), perfil genérico sin foto.

```
┌─────────────────────────────────────┐
│  WhatsApp  │     8:47 PM     │ 87%  │
├─────────────────────────────────────┤
│                                     │
│  +51 948 123 456                     │
│  ───────────────────────────────    │
│                                     │
│  [8:47 PM]                          │
│                                     │
│  Hey, listen up. This is the       │
│  second time I'm writing to you.   │
│                                     │
│  We know you run the bodega on     │
│  Los Olivos Avenue...               │
│                                     │
│  [Read ✓✓]                          │
│                                     │
│  ───────────────────────────────    │
│                                     │
│         Type a message...           │
│                                     │
└─────────────────────────────────────┘

Propiedades del archivo:
  Nombre:     amenaza.jpeg
  Tamaño:     342 KB
  Resolución: 1080 x 2340 px
  Metadatos:  ELIMINADOS (RF-06)
  SHA-256:    a3f2b8c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

---

## 3. Evidencia 2 — Audio de Amenaza (`audio_amenaza.mp3`)

> **Descripción:** Grabación de 23 segundos donde una voz masculina
> repite las mismas amenazas. Transcrito por Whisper (Groq).

```
Propiedades del archivo:
  Nombre:     audio_amenaza.mp3
  Tamaño:     1.2 MB
  Duración:   23 segundos
  Formato:    MP3, 44.1 kHz, 128 kbps
  SHA-256:    b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9

Transcripción (Whisper Groq - whisper-large-v3-turbo):
───────────────────────────────────────────────────────────────────
"Escucha, concha tu madre. ¿Crees que estamos jugando? Cinco mil
soles, por Yape, para el viernes. O te quemamos el local con tu
vieja adentro. Sabemos dónde estudian tus hijos. No nos pruebes.
Cuarenta y ocho horas. Después de eso, es tu funeral."
───────────────────────────────────────────────────────────────────

Idioma detectado: Spanish (es)
Confianza: 0.94
```

---

## 4. Resumen Forense (lo que extraerían los agentes IA)

```
ENTIDADES DETECTADAS (NER Agent)
────────────────────────────────
📞 Teléfono extorsivo:    +51 948 123 456
💳 Cuenta / Yape:         948 123 456
💰 Monto:                 S/ 5,000 soles
📆 Plazo:                 Viernes 3 de julio
⏱ Frecuencia:            Mensual
🏠 Zona:                  Florencia de Mora, Trujillo
📍 Dirección:             Av. Los Olivos cdra. 3 (esq. Miraflores)
🏫 Colegio:               (referencia: hijos salen a las 2 PM)
🔥 Método de violencia:   Quema de local (Don José)
👶 Amenaza a familia:     Sí (hijos, cónyuge)
📱 Medio:                 WhatsApp
🗣 Audio amenaza:         Sí (23 seg, voz masculina)

RIESGO: ALTO
────────────────
- Amenaza directa de daño físico
- Antecedente de violencia inmediata (Don José)
- Conocimiento de rutina familiar (horario del colegio)
- Plazo corto (48 horas)
- Múltiples canales (texto + audio)  →  Requiere escalamiento

BANDA DETECTADA (Cluster Agent)
────────────────
- Mismo modus operandi que caso #TRJ-K9X3 (Jul 2026)
- Mismo teléfono: +51 948 123 456 (coincidencia exacta)
- Mismo método: Yape + amenaza de quema
- Denuncias vinculadas: 4 (incluyendo esta)

CLUSTER: "LOS QUEMADORES DE FLORENCIA"
- Zona: Florencia de Mora / El Porvenir
- Miembros identificados: 2 números de teléfono
- Tendencia: CRECIENTE (+3 casos en junio)
```
