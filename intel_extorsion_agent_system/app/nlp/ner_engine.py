
"""
Motor NER Forense para IntelExtorsión
Extracción de entidades criminales usando regex + ontología bootstrap.
"""
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

from app.nlp.ontology import (
    JERGA_EXTORSION,
    METODOS_VIOLENCIA,
    normalizar_texto,
    buscar_toponimo,
    detectar_banco,
    extraer_monto_numerico,
    extraer_frecuencia,
)


class ForensicNEREngine:
    """
    Motor de Named Entity Recognition forense especializado en extorsión.
    No requiere modelos de ML entrenados; funciona con patrones + ontología.
    """

    def __init__(self):
        pass

    def extract_entities(self, texto: str) -> Dict[str, Any]:
        """
        Extrae todas las entidades forenses del texto.
        """
        if not texto or not isinstance(texto, str):
            return {"entidades": [], "score_total": 0.0, "zona_detectada": None}

        texto_norm = normalizar_texto(texto)
        entidades: List[Dict[str, Any]] = []
        score_total = 0

        # 1. Cuentas bancarias
        cuentas = self._extract_cuentas(texto)
        for c in cuentas:
            entidades.append({
                "tipo": "CUENTA_BANCARIA",
                "valor": c["numero"],
                "entidad": c["entidad"],
                "confianza": 0.9,
                "span": c["span"],
            })
            score_total += 2

        # 2. Yape / Plin
        yapes = self._extract_yape_plin(texto)
        for y in yapes:
            entidades.append({
                "tipo": "YAPE_PLIN",
                "valor": y["numero"],
                "plataforma": y["plataforma"],
                "confianza": 0.85,
                "span": y["span"],
            })
            score_total += 2

        # 3. Teléfonos
        telefonos = self._extract_telefonos(texto)
        for t in telefonos:
            entidades.append({
                "tipo": "TELEFONO_EXTORSIVO",
                "valor": t["numero"],
                "confianza": 0.8,
                "span": t["span"],
            })
            score_total += 1

        # 4. Montos
        montos = self._extract_montos(texto)
        for m in montos:
            entidades.append({
                "tipo": "MONTO",
                "valor": m["valor"],
                "moneda": m["moneda"],
                "periodicidad": m["periodicidad"],
                "confianza": 0.85,
                "span": m["span"],
            })
            score_total += 1

        # 5. Plazos
        plazos = self._extract_plazos(texto)
        for p in plazos:
            entidades.append({
                "tipo": "PLAZO",
                "valor": p["valor"],
                "confianza": 0.75,
                "span": p["span"],
            })
            score_total += 1

        # 6. Topónimos
        toponimo = buscar_toponimo(texto)
        if toponimo:
            entidades.append({
                "tipo": "TOPONIMO_TRUJILLO",
                "valor": toponimo["nombre"],
                "lat": toponimo["lat"],
                "lng": toponimo["lng"],
                "tipo_zona": toponimo["tipo"],
                "confianza": 0.9,
                "span": toponimo["match"],
            })
            score_total += 1

        # 7. Jerga intimidatoria
        jergas = self._extract_jerga(texto)
        for j in jergas:
            entidades.append({
                "tipo": "JERGA_INTIMIDACION",
                "valor": j["valor"],
                "confianza": 0.9,
                "span": j["span"],
            })
            score_total += 1

        # 8. Métodos de violencia
        metodos = self._extract_metodos_violencia(texto)
        for m in metodos:
            entidades.append({
                "tipo": "METODO_VIOLENCIA",
                "valor": m["valor"],
                "confianza": 0.85,
                "span": m["span"],
            })
            score_total += 1

        # 9. Frecuencia de pago
        frecuencia = extraer_frecuencia(texto)
        if frecuencia:
            entidades.append({
                "tipo": "FRECUENCIA_PAGO",
                "valor": frecuencia,
                "confianza": 0.7,
                "span": frecuencia,
            })
            score_total += 1

        # 10. Medio de comunicación
        medios = self._extract_medio_comunicacion(texto)
        for med in medios:
            entidades.append({
                "tipo": "MEDIO_COMUNICACION",
                "valor": med["valor"],
                "confianza": 0.7,
                "span": med["span"],
            })
            score_total += 0.5

        score_normalizado = min(1.0, score_total / 10.0)

        return {
            "entidades": entidades,
            "score_total": round(score_total, 2),
            "score_normalizado": round(score_normalizado, 2),
            "zona_detectada": toponimo["nombre"] if toponimo else None,
            "zona_coords": {"lat": toponimo["lat"], "lng": toponimo["lng"]} if toponimo else None,
            "banco_detectado": detectar_banco(texto),
            "monto_principal": extraer_monto_numerico(texto),
            "frecuencia_pago": frecuencia,
            "total_entidades": len(entidades),
            "extraido_en": datetime.utcnow().isoformat(),
        }

    def _extract_cuentas(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        vistos = set()
        for pat in [r"\b\d{14,20}\b", r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"]:
            for match in re.finditer(pat, texto):
                num = match.group().replace(" ", "").replace("-", "")
                if num in vistos or len(num) < 10:
                    continue
                vistos.add(num)
                entidad = detectar_banco(texto[max(0, match.start()-50):match.end()+50])
                resultados.append({"numero": num, "entidad": entidad, "span": match.group()})
        return resultados

    def _extract_yape_plin(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        texto_norm = normalizar_texto(texto)
        patron = r"(?:yape|plin)\s*(?:al|a|en|por)?\s*[+]?(51)?\s*(9\d{8})"
        for match in re.finditer(patron, texto_norm):
            numero = match.group(2)
            plataforma = "yape" if "yape" in match.group(0) else "plin"
            resultados.append({"numero": numero, "plataforma": plataforma, "span": match.group(0)})
        if "yape" in texto_norm or "plin" in texto_norm:
            for m in re.finditer(r"\b9\d{8}\b", texto_norm):
                plataforma = "yape" if "yape" in texto_norm else "plin"
                resultados.append({"numero": m.group(), "plataforma": plataforma, "span": m.group()})
        return resultados

    def _extract_telefonos(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        vistos = set()
        for pat in [r"\+51\s?9\d{8}", r"\b9\d{8}\b", r"\b01\d{7}\b"]:
            for match in re.finditer(pat, texto):
                num = match.group().replace(" ", "")
                if num in vistos:
                    continue
                vistos.add(num)
                resultados.append({"numero": num, "span": match.group()})
        return resultados

    def _extract_montos(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        for pat, moneda in [(r"S[/\.\s]?\s*(\d{1,6}(?:\.\d{2})?)", "S/"),
                            (r"(\d{1,6})\s*(?:soles?|mil soles?)", "S/")]:
            for match in re.finditer(pat, texto, re.IGNORECASE):
                try:
                    valor = float(match.group(1))
                except ValueError:
                    continue
                contexto = texto[max(0, match.start()-30):match.end()+30]
                periodicidad = extraer_frecuencia(contexto)
                resultados.append({"valor": valor, "moneda": moneda, "periodicidad": periodicidad, "span": match.group(0)})
        return resultados

    def _extract_plazos(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        for pat in [r"\b\d+\s*(hora|horas|día|días|semana|semanas|mes|meses)\b",
                    r"hasta\s+(el\s+)?(lunes|martes|miércoles|jueves|viernes|sábado|domingo)",
                    r"(mañana|pasado mañana|hoy|esta semana|la próxima semana|fin de mes)",
                    r"(tienes|tienen|quedan|faltan)\s+\d+\s*(hora|horas|día|días)"]:
            for match in re.finditer(pat, texto, re.IGNORECASE):
                resultados.append({"valor": match.group(0), "span": match.group(0)})
        return resultados

    def _extract_jerga(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        texto_norm = normalizar_texto(texto)
        for termino in JERGA_EXTORSION:
            if termino in texto_norm:
                resultados.append({"valor": termino, "span": termino})
        return resultados

    def _extract_metodos_violencia(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        texto_norm = normalizar_texto(texto)
        for metodo in METODOS_VIOLENCIA:
            if metodo in texto_norm:
                resultados.append({"valor": metodo, "span": metodo})
        return resultados

    def _extract_medio_comunicacion(self, texto: str) -> List[Dict[str, Any]]:
        resultados = []
        texto_norm = normalizar_texto(texto)
        for medio in ["whatsapp", "telegram", "llamada", "mensaje", "carta", "nota", "papel", "volante", "panfleto", "email", "correo", "sms"]:
            if medio in texto_norm:
                resultados.append({"valor": medio, "span": medio})
        return resultados


ner_engine = ForensicNEREngine()
