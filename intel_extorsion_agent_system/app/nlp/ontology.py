"""
Ontología Forense Bootstrap para IntelExtorsión
Categorías de entidades, topónimos de Trujillo/La Libertad, jerga criminal y patrones de extorsión.
"""
from typing import Dict, List, Any, Optional
import re

# ==========================================
# 1. PATRONES DE ENTIDADES (Regex)
# ==========================================

ENTITY_PATTERNS = {
    "CUENTA_BANCARIA": {
        "regex": [
            r"\b\d{14,20}\b",
            r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}",
        ],
        "keywords": ["bcp", "interbank", "bbva", "scotiabank", "banco de la nación", "banbif", "mi banco", "caja arequipa", "caja piura", "caja trujillo"],
        "score": 2,
    },
    "YAPE_PLIN": {
        "regex": [
            r"\b(Yape|Plin)\b",
            r"\b9\d{8}\b",
            r"\+51\s?9\d{8}",
        ],
        "keywords": ["yapea", "yapeame", "plinme", "yape al", "plin al"],
        "score": 2,
    },
    "TELEFONO_EXTORSIVO": {
        "regex": [
            r"\b9\d{8}\b",
            r"\+51\s?9\d{8}",
            r"\b01\d{7}\b",
        ],
        "keywords": ["llámame", "escríbeme al", "mi número", "contacto"],
        "score": 1,
    },
    "MONTO": {
        "regex": [
            r"S[/\.\s]?\s*\d{1,6}(?:\.\d{2})?",
            r"\b\d{1,6}\s*(soles?|mil soles?|lucas?|miles?)",
            r"\b\d{1,3}\s*(semanales?|quincenales?|mensuales?|diarios?)\b",
        ],
        "keywords": ["paga", "deposita", "transfiere", "envía", "entrega", "cobro", "cobrar"],
        "score": 1,
    },
    "PLAZO": {
        "regex": [
            r"\b\d+\s*(hora|horas|día|días|semana|semanas|mes|meses)\b",
            r"hasta\s+(el\s+)?(lunes|martes|miércoles|jueves|viernes|sábado|domingo)",
            r"(mañana|pasado mañana|hoy|esta semana|la próxima semana|fin de mes)",
            r"(tienes|tienen|quedan|faltan)\s+\d+\s*(hora|horas|día|días)",
        ],
        "keywords": ["plazo", "tiempo", "fecha límite", "deadline", "vence"],
        "score": 1,
    },
    "JERGA_INTIMIDACION": {
        "regex": [],
        "keywords": [
            "cupo", "vacuna", "piso", "quemar", "picar", "brincar", "cobrarte",
            "te vamos a", "atentado", "te vamos a buscar", "te encontraremos",
            "cuidado con", "piénsalo bien", "no te conviene", "ya sabemos dónde",
            "a tu familia", "a tus hijos", "a tu mujer", "a tu esposa",
            "te vamos a quemar", "te vamos a picar", "te vamos a brincar",
            "estás advertido", "última advertencia", "no juegues con fuego",
            "sabemos todo de ti", "te estamos vigilando", "cuidadito",
        ],
        "score": 1,
    },
    "METODO_VIOLENCIA": {
        "regex": [],
        "keywords": [
            "granada", "petardo", "explosivo", "balazo", "sicario",
            "quemar el local", "hacerte daño", "a tu familia",
            "disparo", "arma", "pistola", "revólver", "cuchillo", "machete",
            "bomba", "dinamita", "gaseosa", "encapuchado", "encapuchados",
            "bala", "plomo", "tiro", "golpe", "golpear", "secuestro", "raptar",
        ],
        "score": 1,
    },
    "TOPONIMO_TRUJILLO": {
        "regex": [],
        "keywords": [],  # Se resuelve por matching exacto contra el diccionario
        "score": 1,
    },
    "NOMBRE_PERSONA": {
        "regex": [
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",
        ],
        "keywords": [],
        "score": 0.5,
    },
    "ALIAS_APODO": {
        "regex": [
            r'["\']([A-Za-z0-9_\s]+)["\']',
            r'\b(?:alias|apodo|conocido como|se hace llamar)\s+["\']?([A-Za-z0-9_\s]+)["\']?',
        ],
        "keywords": ["alias", "apodo", "conocido como", "se hace llamar", "le dicen"],
        "score": 0.5,
    },
    "TIPO_NEGOCIO": {
        "regex": [],
        "keywords": [
            "ferretería", "bodega", "tienda", "restaurante", "pollería",
            "taxi", "mototaxi", "colectivo", "grifo", "farmacia", "botica",
            "carnicería", "mercado", "puesto", "kiosko", "minimarket",
            "taller", "mecánica", "lavandería", "peluquería", "barbería",
            "discoteca", "bar", "cenador", "cevichería", "chifa",
        ],
        "score": 0.5,
    },
    "HORARIO_ENTREGA": {
        "regex": [
            r"\b\d{1,2}:\d{2}\b",
            r"\b\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)\b",
            r"(de la mañana|de la tarde|de la noche|madrugada)",
        ],
        "keywords": ["a las", "hora", "horario", "entregar", "depositar", "pagar a"],
        "score": 0.5,
    },
    "MEDIO_COMUNICACION": {
        "regex": [],
        "keywords": [
            "whatsapp", "telegram", "llamada", "mensaje", "carta", "nota",
            "papel", "volante", "panfleto", "email", "correo", "sms",
        ],
        "score": 0.5,
    },
    "FRECUENCIA_PAGO": {
        "regex": [],
        "keywords": [
            "semanal", "quincenal", "mensual", "diario", "todos los meses",
            "cada semana", "cada quince días", "cada mes", "una vez al mes",
            "dos veces al mes", "tres veces", "periódico", "regular",
        ],
        "score": 1,
    },
}

# ==========================================
# 2. TOPÓNIMOS DE TRUJILLO / LA LIBERTAD (con coordenadas GPS)
# ==========================================

TOPONIMOS_TRUJILLO: Dict[str, Dict[str, Any]] = {
    # Distrito de Trujillo (capital)
    "El Centro": {"lat": -8.1117, "lng": -79.0289, "tipo": "urbano", "riesgo": "alto"},
    "La Esperanza": {"lat": -8.0750, "lng": -79.0450, "tipo": "urbano", "riesgo": "alto"},
    "El Porvenir": {"lat": -8.0750, "lng": -79.0450, "tipo": "urbano", "riesgo": "crítico"},
    "Víctor Larco Herrera": {"lat": -8.1333, "lng": -79.0500, "tipo": "urbano", "riesgo": "medio"},
    "Huanchaco": {"lat": -8.0833, "lng": -79.1167, "tipo": "turístico", "riesgo": "medio"},
    "Moche": {"lat": -8.1667, "lng": -79.0167, "tipo": "urbano", "riesgo": "medio"},
    "Laredo": {"lat": -8.0833, "lng": -78.9667, "tipo": "urbano", "riesgo": "bajo"},
    "Salaverry": {"lat": -8.2167, "lng": -78.9833, "tipo": "portuario", "riesgo": "medio"},
    "Florencia de Mora": {"lat": -8.0833, "lng": -79.0333, "tipo": "urbano", "riesgo": "alto"},
    "Cesar Vallejo": {"lat": -8.1000, "lng": -79.0333, "tipo": "urbano", "riesgo": "alto"},
    "San Andrés": {"lat": -8.1333, "lng": -79.0167, "tipo": "urbano", "riesgo": "medio"},
    "California": {"lat": -8.1167, "lng": -79.0333, "tipo": "urbano", "riesgo": "alto"},
    "Palmeras del Norte": {"lat": -8.1000, "lng": -79.0167, "tipo": "urbano", "riesgo": "medio"},
    "Palmeras del Sur": {"lat": -8.1333, "lng": -79.0333, "tipo": "urbano", "riesgo": "medio"},
    "San Isidro": {"lat": -8.1167, "lng": -79.0500, "tipo": "urbano", "riesgo": "bajo"},
    "La Rinconada": {"lat": -8.1000, "lng": -79.0667, "tipo": "urbano", "riesgo": "medio"},
    "Los Jardines": {"lat": -8.0833, "lng": -79.0500, "tipo": "urbano", "riesgo": "medio"},
    "La Merced": {"lat": -8.1167, "lng": -79.0167, "tipo": "urbano", "riesgo": "medio"},
    "Santiago de Huaman": {"lat": -8.1500, "lng": -79.0333, "tipo": "urbano", "riesgo": "bajo"},
    "Cerro Colorado": {"lat": -8.0667, "lng": -79.0500, "tipo": "urbano", "riesgo": "alto"},

    # Provincia de Trujillo (rural/periurbano)
    "Simbal": {"lat": -7.9833, "lng": -78.8167, "tipo": "rural", "riesgo": "bajo"},
    "Sánchez Carrión": {"lat": -7.9167, "lng": -78.6167, "tipo": "rural", "riesgo": "bajo"},
    "Poroto": {"lat": -7.9833, "lng": -78.7500, "tipo": "rural", "riesgo": "bajo"},
    "Agallpampa": {"lat": -7.9500, "lng": -78.5333, "tipo": "rural", "riesgo": "bajo"},

    # Otros distritos de La Libertad importantes
    "Virú": {"lat": -8.4167, "lng": -78.7500, "tipo": "provincial", "riesgo": "medio"},
    "Chao": {"lat": -8.5500, "lng": -78.6833, "tipo": "provincial", "riesgo": "bajo"},
    "Guadalupito": {"lat": -8.4833, "lng": -78.6833, "tipo": "provincial", "riesgo": "bajo"},
    "Ascope": {"lat": -7.7167, "lng": -79.1167, "tipo": "provincial", "riesgo": "medio"},
    "Chicama": {"lat": -7.6500, "lng": -79.1500, "tipo": "provincial", "riesgo": "medio"},
    "Chepén": {"lat": -7.2167, "lng": -79.4333, "tipo": "provincial", "riesgo": "medio"},
    "Pacasmayo": {"lat": -7.4000, "lng": -79.5667, "tipo": "turístico", "riesgo": "bajo"},
    "San Pedro de Lloc": {"lat": -7.4333, "lng": -79.5000, "tipo": "provincial", "riesgo": "bajo"},
    "Otuzco": {"lat": -7.9000, "lng": -78.5667, "tipo": "provincial", "riesgo": "medio"},
    "Usquil": {"lat": -7.8500, "lng": -78.6333, "tipo": "rural", "riesgo": "bajo"},
    "Santiago de Chuco": {"lat": -8.1500, "lng": -78.1833, "tipo": "provincial", "riesgo": "medio"},
    "Carmen de la Legua": {"lat": -8.0833, "lng": -79.0500, "tipo": "urbano", "riesgo": "medio"},
    "Huamachuco": {"lat": -7.8167, "lng": -78.0667, "tipo": "provincial", "riesgo": "medio"},
    "Julcán": {"lat": -8.0333, "lng": -78.4833, "tipo": "rural", "riesgo": "bajo"},
    "Bolívar": {"lat": -7.1833, "lng": -79.5333, "tipo": "rural", "riesgo": "bajo"},
    "Gran Chimú": {"lat": -7.6167, "lng": -78.7500, "tipo": "rural", "riesgo": "bajo"},
    "Sayapullo": {"lat": -7.8333, "lng": -78.5000, "tipo": "rural", "riesgo": "bajo"},
    "Quiruvilca": {"lat": -7.9667, "lng": -78.2167, "tipo": "rural", "riesgo": "bajo"},
    "Cartavio": {"lat": -7.8833, "lng": -79.2167, "tipo": "urbano", "riesgo": "medio"},
    "Llacuabamba": {"lat": -7.7500, "lng": -79.1500, "tipo": "rural", "riesgo": "bajo"},
    "Paiján": {"lat": -7.7333, "lng": -79.3000, "tipo": "provincial", "riesgo": "medio"},
    "Rázuri": {"lat": -7.5833, "lng": -79.4167, "tipo": "rural", "riesgo": "bajo"},
    "Cascas": {"lat": -7.4833, "lng": -78.8167, "tipo": "rural", "riesgo": "bajo"},
    "Marmot": {"lat": -7.4167, "lng": -78.3167, "tipo": "rural", "riesgo": "bajo"},
    "Bambamarca": {"lat": -7.1667, "lng": -78.5167, "tipo": "rural", "riesgo": "bajo"},
    "Huaso": {"lat": -7.3167, "lng": -78.6167, "tipo": "rural", "riesgo": "bajo"},
    "Lucma": {"lat": -7.6167, "lng": -77.6833, "tipo": "rural", "riesgo": "bajo"},
    "Sapo": {"lat": -7.4500, "lng": -78.6167, "tipo": "rural", "riesgo": "bajo"},
    "Yuramarca": {"lat": -7.3500, "lng": -78.4500, "tipo": "rural", "riesgo": "bajo"},
    "Curgos": {"lat": -7.7500, "lng": -78.0333, "tipo": "rural", "riesgo": "bajo"},
    "Sartimbamba": {"lat": -7.6167, "lng": -77.9833, "tipo": "rural", "riesgo": "bajo"},
    "Cochorco": {"lat": -7.7167, "lng": -78.0667, "tipo": "rural", "riesgo": "bajo"},
    "Huaylillas": {"lat": -7.8833, "lng": -78.2500, "tipo": "rural", "riesgo": "bajo"},
    "Marcabal": {"lat": -7.7333, "lng": -77.9833, "tipo": "rural", "riesgo": "bajo"},
    "Angasmarca": {"lat": -7.9833, "lng": -78.0667, "tipo": "rural", "riesgo": "bajo"},
    "Mollebamba": {"lat": -7.8500, "lng": -78.1667, "tipo": "rural", "riesgo": "bajo"},
    "Tacabamba": {"lat": -7.3167, "lng": -78.6167, "tipo": "rural", "riesgo": "bajo"},
    "Contumazá": {"lat": -7.3667, "lng": -78.8167, "tipo": "rural", "riesgo": "bajo"},
    "Chilete": {"lat": -7.2167, "lng": -78.8500, "tipo": "rural", "riesgo": "bajo"},
}

# Sinónimos y variantes comunes para fuzzy matching
TOPONIMO_VARIANTES = {
    "El Porvenir": ["el porvenir", "porvenir"],
    "La Esperanza": ["la esperanza", "esperanza"],
    "El Milagro": ["el milagro", "milagro", "cerro el milagro"],
    "Florencia de Mora": ["florencia de mora", "florencia", "mora"],
    "Alto Trujillo": ["alto trujillo", "alto"],
    "Víctor Larco": ["víctor larco", "victor larco", "víctor larco herrera", "larco"],
    "Víctor Larco Herrera": ["víctor larco herrera", "victor larco herrera", "larco"],
    "Huanchaco": ["huanchaco", "huanchaquillo"],
    "Moche": ["moche", "mochica"],
    "Cerro Colorado": ["cerro colorado", "colorado"],
    "California": ["california", "la california"],
    "Salaverry": ["salaverry", "puerto de salaverry"],
    "Laredo": ["laredo"],
    "La Rinconada": ["la rinconada", "rinconada"],
    "Los Jardines": ["los jardines", "jardines"],
    "La Merced": ["la merced", "merced"],
    "San Isidro": ["san isidro", "isidro"],
    "San Andrés": ["san andrés", "san andres", "andres", "andrés"],
    "Santiago de Huaman": ["santiago de huaman", "huaman", "huamán"],
    "Cesar Vallejo": ["cesar vallejo", "vallejo"],
    "Palmeras del Norte": ["palmeras del norte", "palmeras norte"],
    "Palmeras del Sur": ["palmeras del sur", "palmeras sur"],
    "Cerro El Milagro": ["cerro el milagro", "el milagro", "milagro"],
    "Carmen de la Legua": ["carmen de la legua", "carmen"],
}

# Lista plana para matching rápido
TOPONIMOS_LISTA_PLANA = []
for canonico, variantes in TOPONIMO_VARIANTES.items():
    TOPONIMOS_LISTA_PLANA.extend(variantes)
TOPONIMOS_LISTA_PLANA = list(set(TOPONIMOS_LISTA_PLANA))

# ==========================================
# 3. JERGA CRIMINAL Y METODOS DE VIOLENCIA
# ==========================================

JERGA_EXTORSION = [
    "cupo", "vacuna", "piso", "quemar", "picar", "picamos", "picaron", "brincar", "brincamos",
    "cobrarte", "te vamos a", "atentado", "te vamos a buscar", "te encontraremos",
    "cuidado con", "piénsalo bien", "no te conviene", "ya sabemos dónde",
    "a tu familia", "a tus hijos", "a tu mujer", "a tu esposa",
    "te vamos a quemar", "te vamos a picar", "te vamos a brincar",
    "estás advertido", "última advertencia", "no juegues con fuego",
    "sabemos todo de ti", "te estamos vigilando", "cuidadito",
    "tengo tus fotos", "tengo videos tuyos", "te vamos a difamar",
    "conocí a tu", "sé dónde vives", "sé dónde trabajas",
    "paga o te arrepentirás", "te lo advertí", "no te hagas el valiente",
    "ya sabemos quién eres", "ya sabemos tu dirección",
    "mejor paga", "no es broma", "lo decimos en serio",
    "pronto lo verás", "ya llegará tu hora", "te daremos una lección",
    "te haremos pagar", "no olvides lo que te dijimos",
    "cumple o cumplirás", "respeta las reglas", "obedece",
]

METODOS_VIOLENCIA = [
    "granada", "petardo", "explosivo", "balazo", "sicario",
    "quemar el local", "hacerte daño", "a tu familia",
    "disparo", "arma", "pistola", "revólver", "cuchillo", "machete",
    "bomba", "dinamita", "gaseosa", "encapuchado", "encapuchados",
    "bala", "plomo", "tiro", "golpe", "golpear", "secuestro", "raptar",
    "incendio provocado", "ataque armado", "amenaza de muerte",
    "tortura", "vejación", "agresión física", "golpiza",
    "robo a mano armada", "asalto", "atraco", "extorsión armada",
]

# ==========================================
# 4. BANCOS Y ENTIDADES FINANCIERAS PERUANAS
# ==========================================

BANCOS_PERU = {
    "bcp": ["bcp", "banco de crédito", "banco de credito", "credit bank"],
    "interbank": ["interbank", "banco interbank"],
    "bbva": ["bbva", "bbva continental", "bbva perú", "bbva peru"],
    "scotiabank": ["scotiabank", "banco scotiabank"],
    "banbif": ["banbif"],
    "mi banco": ["mi banco", "mibanco"],
    "banco de la nación": ["banco de la nación", "banco de la nacion", "nación", "nacion"],
    "caja arequipa": ["caja arequipa"],
    "caja piura": ["caja piura"],
    "caja trujillo": ["caja trujillo", "caja huancayo", "caja sullana"],
    "caja huancayo": ["caja huancayo"],
    "caja sullana": ["caja sullana"],
    "caja cusco": ["caja cusco"],
    "caja ica": ["caja ica"],
    "caja tacna": ["caja tacna"],
    "caja puntarenas": ["caja puntarenas"],
    "yape": ["yape", "plin"],
    "plin": ["plin", "yape"],
    "banco falabella": ["banco falabella", "falabella"],
    "banco ripley": ["banco ripley", "ripley"],
    "banco azteca": ["banco azteca", "azteca"],
    "banco gnb": ["banco gnb", "gnb"],
    "banco santander": ["banco santander", "santander"],
    "banco comercio": ["banco comercio", "comercio"],
}

# ==========================================
# 5. FUNCIONES UTILITARIAS
# ==========================================

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para matching: minúsculas, sin acentos comunes."""
    texto = texto.lower()
    # Simplificar acentos comunes
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
        'ñ': 'n', 'Ñ': 'n', 'ü': 'u', 'Ü': 'u',
    }
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    return texto


def buscar_toponimo(texto: str) -> Optional[Dict[str, Any]]:
    """
    Busca un topónimo de Trujillo/La Libertad en el texto.
    Devuelve el nombre canónico, coordenadas y metadatos.
    """
    texto_norm = normalizar_texto(texto)
    for canonico, variantes in TOPONIMO_VARIANTES.items():
        for variante in variantes:
            if variante in texto_norm:
                datos = TOPONIMOS_TRUJILLO.get(canonico, {})
                return {
                    "nombre": canonico,
                    "lat": datos.get("lat"),
                    "lng": datos.get("lng"),
                    "tipo": datos.get("tipo"),
                    "riesgo_base": datos.get("riesgo"),
                    "match": variante,
                }
    return None


def detectar_banco(texto: str) -> Optional[str]:
    """Detecta el nombre del banco/entidad financiera mencionada."""
    texto_norm = normalizar_texto(texto)
    for banco, variantes in BANCOS_PERU.items():
        for variante in variantes:
            if variante in texto_norm:
                return banco
    return None


def extraer_monto_numerico(texto: str) -> Optional[float]:
    """Extrae el primer monto numérico encontrado en soles."""
    # Patrón S/ 1234.56 o S/1234
    match = re.search(r"(?<!\w)S[/\.\s]*(\d{1,6}(?:\.\d{2})?)", texto, re.IGNORECASE)
    if match:
        return float(match.group(1))
    # Patrón "1234 soles"
    match = re.search(r"(\d{1,6})\s*(?:soles?|mil soles?|lucas?)", texto, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def extraer_frecuencia(texto: str) -> Optional[str]:
    """Extrae frecuencia de pago mencionada."""
    texto_norm = normalizar_texto(texto)
    frecuencias = ["diario", "semanal", "quincenal", "mensual", "trimestral", "anual"]
    for f in frecuencias:
        if f in texto_norm:
            return f
    return None


def get_all_toponimos_for_heatmap() -> List[Dict[str, Any]]:
    """Devuelve todos los topónimos con coordenadas para el mapa de calor base."""
    resultados = []
    for nombre, datos in TOPONIMOS_TRUJILLO.items():
        resultados.append({
            "nombre": nombre,
            "lat": datos["lat"],
            "lng": datos["lng"],
            "tipo": datos["tipo"],
            "riesgo_base": datos["riesgo"],
        })
    return resultados
