IntelExtorsión — Especificación de Requerimientos Funcionales y No Funcionales
Documento de especificación técnica derivado del análisis de diseño del sistema IntelExtorsión, plataforma de inteligencia ciudadana contra la extorsión en Trujillo / La Libertad, alineada con la realidad operativa de la DIVINCRI La Libertad y la DIRINCRI PNP.
Resumen del Sistema
IntelExtorsión es una plataforma de dos capas que: (1) recibe denuncias anónimas de extorsión vía bot conversacional en WhatsApp/Telegram/Discord, y (2) permite la carga de evidencia trazable vía DApp Web3 con identidad descentralizada. Todo el contenido recibido es procesado por un motor NLP forense que correlaciona patrones entre casos, genera inteligencia accionable, y la entrega a los analistas de la DIVINCRI a través de un dashboard operativo. La evidencia cargada queda sellada con hash SHA-256 en Syscoin Rollux para garantizar su integridad.[^1]
Módulo 1 — Bot de Denuncia Anónima (Capa 1)
Qué hace
El bot es el punto de entrada masivo del sistema. Atiende a cualquier ciudadano con WhatsApp o Telegram o Discord, guía la denuncia paso a paso, extrae el contenido relevante y lo entrega al pipeline de análisis sin retener ningún dato identificador del denunciante.
RF-01 — Clasificación inicial de denuncia
Qué hace: Al iniciar la conversación, el bot presenta un menú de clasificación de dos niveles:
·         Nivel 1: ¿La amenaza proviene de (a) particular/banda criminal, o (b) funcionario público / policía?
·         Nivel 2 (solo si responde "b"): redirige automáticamente al canal de la Inspectoría General PNP o Fiscalía Anticorrupción y no registra la denuncia en el dashboard de la DIVINCRI.
Cómo lo hace: Árbol de decisión estático en el flujo del bot (no requiere NLP); se implementa con botones de respuesta rápida en la API de WhatsApp Business y la API de Telegram Bots.
Por qué: Evita que una denuncia contra un policía corrupto llegue precisamente al dashboard de su propia unidad.
RF-02 — Recepción y extracción de contenido multimedia
Qué hace: Acepta tres formatos de entrada y extrae texto de todos ellos:
·         Texto libre escrito por el usuario → pasa directamente al pipeline NLP
·         Imagen de carta/nota extorsiva → procesada con OCR (reconocimiento óptico de caracteres) para extraer el texto de la imagen
·         Audio o nota de voz → transcrita a texto mediante motor de Speech-to-Text
Cómo lo hace:
·         OCR: servicio de visión computacional (Google Vision API o Tesseract OCR open-source) configurado para español latinoamericano
·         Speech-to-Text: Whisper de OpenAI (modelo open-source) o Google Speech-to-Text, con perfil de idioma español peruano
·         El archivo multimedia original (imagen o audio) se descarta tras la extracción; solo el texto resultante entra al silo de evidencia
Criterio de aceptación: el sistema debe extraer texto con una precisión mínima del 85% en imágenes de cartas manuscritas de calidad media.
RF-03 — Extracción de zona geográfica
Qué hace: Intenta obtener la zona del incidente por dos vías:
1.   	Extracción automática del contenido (NLP): detecta referencias geográficas en el texto ("tu negocio en El Porvenir", "el cerro El Milagro", "la avenida Industrial") y mapea al cuadrante correspondiente del Plan Cuadrante PNP de Trujillo
2.  	Pregunta voluntaria al final del flujo: si el NLP no detectó zona, el bot pregunta "¿En qué zona o cerro ocurrió esto? (puedes responder solo el nombre del lugar o escribir 'no sé')" — la respuesta es opcional; si el usuario no responde o dice "no sé", el caso se registra sin dato geográfico
Cómo lo hace: Diccionario georreferenciado de topónimos de Trujillo y La Libertad mapeados a cuadrantes del Plan Cuadrante; reconocimiento de entidades nombradas (NER) dentro del pipeline NLP.
Lo que NO hace: el sistema no accede a la ubicación GPS del dispositivo, no solicita coordenadas, no lee metadatos EXIF de las imágenes recibidas.
RF-04 — Confirmación y entrega de código de seguimiento
Qué hace: Al finalizar el flujo, el bot envía al usuario:
·         Confirmación de que su denuncia fue recibida
·         Un código alfanumérico aleatorio de 8 caracteres (ej. TRJ-4X9K) que le permite consultar en qué estado de análisis se encuentra su caso, sin revelar ningún dato de identidad
·         Opcionalmente, el hash SHA-256 del contenido de su denuncia para verificación personal
Cómo lo hace: El código se genera aleatoriamente en el momento; no contiene ningún dato derivado del número telefónico ni del dispositivo. Se almacena en la base de datos de evidencia junto al contenido procesado, no en el silo de metadatos de canal.
Estados del ciclo de vida de una denuncia
El ciclo tiene 6 estados, diseñados para que el ciudadano entienda qué está pasando sin revelar nada operativo que pueda comprometer la investigación.
#
Estado interno (sistema)
Lo que ve el ciudadano al consultar su código
Descripción técnica
1
RECIBIDA
"Tu denuncia fue recibida y está en cola de procesamiento."
El contenido llegó al silo de evidencia. El pipeline NLP aún no la procesó.
2
EN_ANÁLISIS
"Tu denuncia está siendo analizada por nuestro sistema."
El motor NLP está extrayendo entidades; aún no hay resultado de clustering.
3
PROCESADA_AISLADA
"Tu denuncia fue procesada. La información aportada ha sido registrada."
El NLP terminó. No se encontró correlación con otros casos aún — el caso existe como nodo sin aristas en el grafo.
4
CORRELACIONADA
"Tu denuncia fue vinculada con otros reportes similares. La información está siendo analizada por el equipo especializado."
El caso forma parte de un clúster activo (≥ 3 nodos, ≥ 2 vectores comunes). El analista de la DIVINCRI ya tiene visibilidad del clúster.
5
EN_SEGUIMIENTO_POLICIAL
"La información de tu denuncia está siendo utilizada activamente por las autoridades."
El clúster fue marcado como "banda activa" por el analista y se activó alerta operativa. No se revela qué acción policial se está tomando.
6
ARCHIVADA
"Tu denuncia ha sido archivada. Gracias por contribuir a la seguridad de tu comunidad."
Pasaron 5 años (plazo de retención) o el caso fue cerrado judicialmente. El contenido se elimina de forma segura.

Módulo 2 — DApp Web3 de Evidencia Trazable (Capa 2)
Qué hace
La DApp es el canal para usuarios que desean aportar evidencia con trazabilidad judicial, usando una identidad descentralizada (DID) que les permite ser seudónimos (no anónimos) — es decir, identificables ante la DIVINCRI si ellos mismos lo autorizan, pero sin exposición de su identidad civil en el sistema.
RF-05 — Autenticación con Pali Wallet V2 e Identidad Descentralizada (DID)
Qué hace: El usuario conecta su Pali Wallet V2 a la DApp. Si es primera vez, el sistema genera un DID (Identificador Descentralizado) vinculado a la wallet. Este DID es el único identificador del usuario dentro del sistema; no se recopilan nombre, DNI, teléfono ni correo.
Cómo lo hace: Protocolo DID estándar W3C; la wallet firma un challenge criptográfico que prueba posesión de la clave privada sin revelarla. El DID se registra en Syscoin Rollux como ancla de identidad.
RF-06 — Carga de evidencia con captura forense automática
Qué hace: El usuario sube archivos (imágenes, documentos PDF, audios, videos). Por cada archivo, el sistema captura automáticamente:
·         Hash SHA-256 del archivo original antes de cualquier procesamiento
·         Timestamp UTC del momento de recepción en el servidor
·         Tipo MIME del archivo
·         Metadatos técnicos del archivo (tamaño, resolución si aplica) — sin metadatos de identidad del dispositivo (EXIF con GPS se elimina antes del almacenamiento)
Cómo lo hace: Módulo de ingesta del lado del servidor (Node.js o Python FastAPI); el hash se calcula sobre el stream binario antes de escribirlo en disco.[^10]
RF-07 — Sellado de hash en Syscoin Rollux
Qué hace: El hash de cada archivo subido se graba en un smart contract de sellado desplegado en Syscoin Rollux (Layer 2). El resultado es una transacción pública con timestamp que cualquier fiscal, juez o perito puede verificar en el explorador de bloques sin necesidad de acceder al sistema.[1][9]
Cómo lo hace: Smart contract EvidenceSeal.sol en Solidity; función seal(bytes32 hash, uint256 caseId) → emite evento EvidenceSealed con timestamp del bloque. La DApp llama al contrato usando ethers.js via Pali Wallet V2 como firmante.
Respaldo secundario: adicionalmente, el sistema exporta un PDF firmado digitalmente con el hash, timestamp y número de bloque — este PDF puede verificarse sin que la red Rollux esté activa, resolviendo el riesgo de continuidad del nodo blockchain.[^7]
RF-08 — Acta digital forense compatible con CPP
Qué hace: Genera automáticamente un documento PDF estructurado que incluye: hash del archivo, timestamp, DID del aportante, número de bloque en Rollux, y firma digital del servidor del sistema. Este documento está diseñado para ser compatible con los requisitos del artículo 158-B propuesto del Código Procesal Penal peruano, que establece que la evidencia digital debe registrarse desde su fuente original con trazabilidad.[^6]
Cómo lo hace: Generación automática con librería reportlab (Python) o PDFKit (Node.js); el PDF se firma con certificado digital del operador del sistema.
Módulo 3 — Pipeline NLP Forense
Qué hace
Es el núcleo analítico del sistema. Procesa el texto de cada denuncia recibida (de ambas capas) para extraer entidades relevantes, y luego correlaciona casos entre sí para detectar patrones que indiquen banda criminal activa.[11][12]
RF-09 — Extracción de entidades forenses (NER especializado)
Qué hace: Por cada denuncia recibida, el motor NLP extrae:
·         Números de cuenta bancaria / wallets mencionados como destino de pago
·         Números de teléfono mencionados en el texto de la amenaza (no el teléfono del denunciante)
·         Montos exigidos (rangos y patrones de escalamiento)
·         Términos de jerga criminal detectados contra el diccionario ontológico forense
·         Métodos de intimidación (explosivos, armas, daño a negocio, daño a familia)
·         Referencias geográficas (para georreferenciación)
·         Plazos de pago exigidos
Cómo lo hace: Modelo de NER (reconocimiento de entidades nombradas) en dos fases:
1.   	Fase bootstrap (ontología manual): un diccionario de reglas y términos construido con analistas de la DIVINCRI y fiscales especializados — no requiere datos reales de víctimas para funcionar, solo conocimiento experto de los investigadores[^13]
2.  	Fase de aprendizaje (modelo supervisado): a medida que el sistema acumula denuncias validadas, se entrena un clasificador spaCy o similar sobre el corpus anonimizado
RF-10 — Motor de clustering y correlación de casos
Qué hace: Agrupa automáticamente denuncias que comparten dos o más vectores comunes. Los vectores de correlación son:
·         Misma cuenta bancaria o número de teléfono de cobro
·         Jerga idéntica o muy similar (similitud coseno > 0.85 en embeddings del texto)
·         Misma zona geográfica en ventana temporal de 21 días
·         Monto exigido dentro del mismo rango ± 20%
·         Mismo método de intimidación
Cómo lo hace: Algoritmo de clustering basado en grafos (NetworkX en Python): cada denuncia es un nodo; se añade arista cuando comparte ≥ 2 vectores. Un componente conectado con ≥ 3 nodos = clúster activo que genera alerta.
Umbral de activación de alerta operativa: mínimo 3 denuncias con mínimo 2 vectores comunes → el clúster se eleva como "banda activa en formación". Una denuncia aislada nunca activa un operativo por sí sola.
RF-11 — Anonimización del corpus de entrenamiento
Qué hace: Antes de que cualquier denuncia entre al corpus de entrenamiento del modelo NLP, pasa por un módulo de anonimización que enmascara: nombres propios de personas, nombres de negocios específicos, direcciones exactas y números de documento.
Cómo lo hace: Pipeline de redacción automática con presidio (librería de Microsoft para anonimización de PII) + revisión manual por el equipo legal antes de que el texto entre al corpus de entrenamiento. Los campos enmascarados se reemplazan por etiquetas genéricas: [NOMBRE], [NEGOCIO], [DIRECCION].[^6]
Módulo 4 — Dashboard Operativo DIVINCRI
Qué hace
Es la interfaz que usan los analistas y oficiales de la DIVINCRI La Libertad para consumir la inteligencia generada por el sistema. Está diseñado para integrarse con el Plan Cuadrante operativo real de Trujillo y para funcionar con alertas push, no solo consulta activa.[13][5]
RF-12 — Mapa de calor por cuadrantes del Plan Cuadrante PNP
Qué hace: Muestra un mapa de Trujillo y La Libertad dividido por las delimitaciones oficiales del Plan Cuadrante PNP, con intensidad de color según volumen de incidentes correlacionados. Los cuadrantes se actualizan en tiempo real conforme llegan nuevas denuncias.
Cómo lo hace: Mapa base con Leaflet.js + capa GeoJSON con los polígonos del Plan Cuadrante (datos a obtener de la DIVINCRI La Libertad como parte del convenio de cooperación). La intensidad de color usa una escala logarítmica para que zonas con 3 casos sean visibles junto a zonas con 30.
Lo que NO muestra: ningún punto de ubicación individual, ninguna dirección exacta, ningún marcador que identifique a un denunciante específico.
RF-13 — Perfil automático de banda por clúster
Qué hace: Al hacer clic en un clúster activo en el mapa, el oficial ve una ficha generada automáticamente:
Campo
Dato inferido por NLP
Zona de operación
Cuadrante(s) afectados
Monto exigido
Rango y tendencia (escalamiento o estable)
Método de cobro
Cuenta(s) bancaria(s) detectada(s) en N de M casos
Jerga característica
Términos más frecuentes del clúster
Nivel de violencia
Bajo / Medio / Alto según métodos de intimidación
Tendencia temporal
Gráfico de frecuencia semanal de nuevos casos
Casos del clúster
Número total; enlaces a evidencia verificable

 
RF-14 — Sistema de alertas push
Qué hace: Cuando un nuevo clúster supera el umbral de activación (RF-10), el sistema envía automáticamente una alerta push al oficial de turno de la DIVINCRI. El sistema no espera a que el oficial abra el dashboard.
Cómo lo hace: Notificaciones vía correo institucional + SMS al número de guardia registrado + (opcionalmente) webhook hacia el sistema SIRDIC/SIDPOL si la DIVINCRI habilita la integración. El mensaje de alerta incluye: zona, número de casos del clúster, vectores de correlación detectados, y enlace directo al perfil del clúster en el dashboard.[^13]
RF-15 — Verificador de evidencia blockchain
Qué hace: Para cada incidente de un clúster, el oficial puede ver el hash SHA-256 y un enlace al explorador de bloques de Syscoin Rollux donde se puede verificar que ese hash existe, con su timestamp de bloque, de forma pública. También puede descargar el PDF de acta forense (RF-08) para adjuntarlo al expediente.
Cómo lo hace: Enlace directo al explorador público de Rollux (https://rollux.tanenbaum.io/tx/[txHash]); el PDF se descarga desde el servidor del sistema. Ninguna de estas operaciones requiere que el oficial tenga una wallet ni conocimiento de blockchain.[^9]
RF-16 — Log de auditoría de accesos
Qué hace: Cada acción realizada por un usuario del dashboard queda registrada en un log inmutable: usuario, timestamp, acción ejecutada, ID del caso consultado. Este log se sella periódicamente (cada 24 horas) en Syscoin Rollux para que no pueda ser alterado retroactivamente.
Por qué: Mitiga el riesgo del "puente humano" y la corrupción interna documentada en la DIVINCRI Trujillo. Si un oficial usa indebidamente el sistema, queda trazado.[^3]
Cómo lo hace: Log append-only en base de datos (PostgreSQL con extensión de audit trail); hash del log diario sellado en Rollux como RF-07.
RF-17 — Control de acceso por roles
Qué hace: Define tres roles con permisos diferenciados:
Rol
Quién
Qué puede ver
Analista DIVINCRI
Oficial de inteligencia
Dashboard completo: mapa, perfiles de clústeres, evidencia hasheada; NO puede ver quién denunció
Supervisor DIVINCRI
Jefe de unidad
Todo lo anterior + métricas agregadas del sistema + puede solicitar formalmente el proceso extraordinario de cruce identidad-evidencia
Administrador del sistema
Equipo técnico del operador
Configuración técnica; NO tiene acceso al contenido de denuncias ni al dashboard operativo

 
El proceso extraordinario de cruce identidad-evidencia requiere: solicitud documentada del Supervisor + orden judicial o fiscal → solo entonces un operador técnico designado puede ejecutarlo manualmente, fuera del sistema automatizado, con registro en log de auditoría.[7][6]
RF-18 — Enriquecimiento OSINT automático
Qué hace: Cuando el NLP extrae un número de cuenta bancaria o número de teléfono de una denuncia, el sistema lo consulta automáticamente contra:
·         Alertas públicas de OSIPTEL sobre números reportados como extorsivos
·         Listas públicas de cuentas reportadas en plataformas de denuncia ciudadana verificadas
·         (Con convenio) reportes de cuentas sospechosas de la UIF-Perú
Cómo lo hace: Módulo de consulta via API REST o scraping estructurado de fuentes públicas; los resultados enriquecen el perfil del clúster con un campo "Confirmación OSINT: sí/no/parcial".[^13]
Requerimientos No Funcionales
RNF-01 — Anonimato por arquitectura (privacidad)
Regla: ningún proceso automatizado del sistema puede tener credenciales de acceso simultáneo a ambos silos de datos (silo de metadatos de canal + silo de evidencia procesada).
Implementación: dos bases de datos físicamente separadas (pueden estar en el mismo servidor, pero con credenciales distintas y sin foreign keys entre ellas). El número de teléfono del denunciante de WhatsApp se descarta en el webhook de recepción antes de escribir cualquier dato en la base de evidencia. Se verifica mediante prueba de penetración antes del despliegue.
RNF-02 — Disponibilidad
·         El bot (Capa 1) debe tener disponibilidad mínima del 99.5% mensual — es el canal masivo y las víctimas pueden intentar denunciar en cualquier momento
·         El dashboard (DIVINCRI) debe tener disponibilidad mínima del 99% en horario operativo (6am–12am)
·         La DApp (Capa 2) puede tolerar hasta 2 horas de mantenimiento programado fuera de horario sin incumplir SLA
Implementación: despliegue en contenedores Docker con orquestación Kubernetes o Railway/Render (para MVP); balanceo de carga básico; monitoreo con uptime robot o similar.
RNF-03 — Tiempo de respuesta del bot
·         El bot debe responder a cada mensaje del usuario en menos de 3 segundos en condiciones normales de carga
·         El OCR de una imagen debe completarse en menos de 15 segundos
·         La transcripción de audio de hasta 60 segundos debe completarse en menos de 30 segundos
RNF-04 — Escalabilidad
El sistema debe soportar al menos 500 denuncias simultáneas en Capa 1 sin degradación de rendimiento. El pipeline NLP debe procesar el backlog dentro de 5 minutos de recibido el último mensaje de un flujo. La arquitectura de microservicios permite escalar el módulo NLP independientemente del bot.
RNF-05 — Seguridad de datos
·         Todos los datos en tránsito entre el usuario y el servidor cifrados con TLS 1.3
·         Datos en reposo cifrados con AES-256
·         El silo de evidencia procesada usa cifrado a nivel de campo para el texto de las denuncias
·         Tokens de autenticación del dashboard con expiración máxima de 8 horas (sesión de turno policial)
·         Rate limiting en el bot: máximo 20 mensajes por número de teléfono por hora para desincentivar spam sin bloquear usuarios legítimos
·         Pentesting obligatorio antes del despliegue en producción[10][6]
RNF-06 — Mantenibilidad y auditoría del modelo NLP
·         El diccionario ontológico forense (Fase bootstrap) debe ser editable por el equipo de analistas de la DIVINCRI sin intervención del equipo técnico
·         Cada versión del modelo NLP desplegado en producción debe ser versionada y almacenada para poder reproducir resultados históricos en un proceso judicial
·         El rendimiento del modelo (precisión en extracción de entidades) se mide mensualmente y se documenta; si cae por debajo del 80%, se activa proceso de reentrenamiento[^11]
RNF-07 — Interoperabilidad con sistemas PNP existentes
El dashboard debe ser capaz de exportar perfiles de clúster en formato PDF estructurado y en CSV, compatibles con los sistemas SIRDIC y SIDPOL actualmente en uso por la DIRINCRI. En fase de escala, se provee API REST documentada (OpenAPI 3.0) para que la DIVINCRI pueda integrar las alertas directamente en sus flujos de trabajo existentes.[^13]
RNF-08 — Cumplimiento normativo
·         Operación compatible con la Ley N° 29733 (Ley de Protección de Datos Personales del Perú): el sistema por diseño no recolecta datos personales identificables en el flujo principal
·         Evidencia blockchain diseñada para ser compatible con el artículo 158-B del CPP propuesto (evidencia digital con cadena de custodia)[^6]
·         Política de retención de datos: el contenido procesado de denuncias se retiene por 5 años (plazo de prescripción de delitos graves en el CPP); tras ese plazo, se elimina de forma segura con certificación
·         Los menores de edad no son identificados ni registrados en ningún campo del sistema[^15]
RNF-09 — Continuidad de la cadena de custodia blockchain
Para garantizar que la evidencia pueda verificarse incluso si Syscoin Rollux dejara de operar:[^1]
·         Cada hash se respalda también en una segunda red pública (Ethereum Sepolia en testnet para MVP; mainnet en producción)
·         Se generan PDFs de verificación mensualmente para todos los hashes activos, firmados digitalmente por el operador
·         Los PDFs de verificación se almacenan en almacenamiento frío offline (IPFS + copia local) independiente de cualquier red blockchain
RNF-10 — Usabilidad para el ciudadano
·         El bot debe operar completamente en español peruano coloquial, sin tecnicismos
·         El flujo completo de una denuncia básica (texto libre) debe completarse en menos de 5 minutos
·         El bot debe estar disponible en WhatsApp (canal con > 90% de penetración en Lima y ciudades del norte del Perú) y Telegram como canal secundario[^2]
·         El bot debe funcionar en condiciones de conectividad limitada (2G/3G); los mensajes de audio y foto son opcionales, nunca obligatorios
References
1.   	Rollux is built by SYS Labs, powered by Syscoin ... - Rollux, built by SYS Labs, is a project dedicated to scaling blockchain technology and expanding its...
2.  	Central 111: La línea telefónica para denunciar extorsiones - La línea 111 es crucial para que los ciudadanos puedan denunciar de manera anónima cualquier acto ex...
3.  	4 policías de la Divincri Trujillo fueron detenidos por ... - Los detenidos fueron identificados como Jonatan Martínez Santa Cruz, Julio Reyna Pereda, Jimmy Ruiz ...
4.  	#LaLibertad l El general PNP Franco Moreno señaló que los 4 ... - LaLibertad l El general PNP Franco Moreno señaló que los 4 suboficiales detenidos de la Divincri de ...
5.   	PNP toma control de los cerros de Trujillo y declara la ... - En las últimas 24 horas se desarticularon redes criminales vinculadas al sicariato, tráfico de explo...
6.  	Proponen incorporar la evidencia digital como medio de ... - El proyecto plantea una modificación a los artículos 157, 172, 185 y 187 del Código Procesal Penal, ...
7.   	La evidencia digital: ¿cómo ayuda el blockchain en un ... - Cada vez que un documento se incorpore al expediente judicial se gestionaría una transacción en la c...
8.  	Valoración de la veracidad de las pruebas digitales en ... - Alicia - Concluyendo que urge regular las pruebas digitales dentro del texto normativo Código Procesal Civil ...
9.  	Syscoin - Bitcoin's only Modular Network - Syscoin gives Bitcoin ultimate functionality. Our modular EVM execution layer finally enables Bitcoi...
10.   ¿Qué es la cadena de custodia digital y por qué necesitas ... - La cadena de custodia digital garantiza la fiabilidad de la prueba digital que se aporta en el juici...
11.	Qué es el Procesamiento del Lenguaje Natural (PLN o NLP) - El procesamiento del lenguaje natural (PLN o NLP) es un campo dentro de la inteligencia artificial y...
12.   Procesamiento de Lenguaje Natural (NLP): Qué es y utilidad - El Procesamiento del Lenguaje Natural (NLP) es una tecnología de machine learning que permite a las ...
13.   plan de investigacion criminal - INVESTIGACIÓNES ASIGNADAS A LA DIRINCRI PNP. FUENTE: DIRINCRI PNP. 200.- EXTORSIÓN. 152.- SECUESTRO....
14.   La Libertad concentra la mayor cantidad de denuncias por ... - Entre enero y julio de 2025, La Libertad registró en promedio 394 denuncias de extorsión al mes, equ...
15.	Trujillo: More than 330 minors have been apprehended for ... - La Policía Nacional del Perú informó que, en lo que va del 2025, más de 330 menores de edad han sido...

