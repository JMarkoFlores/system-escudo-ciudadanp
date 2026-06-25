"""
OSINT Enrichment (Bootstrap / Simulado)
Placeholder para consultas a fuentes abiertas.
En producción, integraría OSIPTEL, SBS, HaveIBeenPwned, etc.
"""
from typing import Dict, Any, Optional


class OSINTEnricher:
    """
    Enriquecedor OSINT bootstrap.
    Devuelve datos simulados estructurados listos para ser reemplazados
    por consultas a APIs reales.
    """

    def lookup_telefono(self, telefono: str) -> Dict[str, Any]:
        """Consulta simulada de información de un número telefónico."""
        return {
            "telefono": telefono,
            "operador": "Claro/Movistar/Entel (simulado)",
            "reportes_previos": 2,
            "primer_reporte": "2024-03-15",
            "ultimo_reporte": "2024-06-10",
            "riesgo": "alto",
            "fuentes": ["base_interna_simulada"],
        }

    def lookup_cuenta_bancaria(self, cuenta: str, entidad: Optional[str] = None) -> Dict[str, Any]:
        """Consulta simulada de información de una cuenta bancaria."""
        return {
            "cuenta": cuenta,
            "entidad": entidad or "Desconocida",
            "reportes_previos": 1,
            "tipo": "ahorro/corriente (simulado)",
            "riesgo": "medio",
            "alertas_sbs": False,
            "fuentes": ["base_interna_simulada"],
        }

    def lookup_alias(self, alias: str) -> Dict[str, Any]:
        """Consulta simulada de información de un alias/apodo."""
        return {
            "alias": alias,
            "redes_sociales": ["telegram", "facebook"],
            "reportes_previos": 0,
            "riesgo": "desconocido",
            "fuentes": ["redes_sociales_simuladas"],
        }

    def enrich_denuncia(self, nlp_entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece todas las entidades de una denuncia con OSINT simulado.
        """
        entidades = nlp_entities.get("entidades", [])
        enriched = {
            "telefonos": [],
            "cuentas": [],
            "alias": [],
            "timestamp": "2024-01-01T00:00:00Z",
        }

        for e in entidades:
            tipo = e.get("tipo", "")
            valor = e.get("valor", "")
            if tipo == "TELEFONO_EXTORSIVO" and valor:
                enriched["telefonos"].append(self.lookup_telefono(str(valor)))
            elif tipo == "CUENTA_BANCARIA" and valor:
                enriched["cuentas"].append(
                    self.lookup_cuenta_bancaria(str(valor), e.get("entidad"))
                )
            elif tipo == "YAPE_PLIN" and valor:
                enriched["cuentas"].append(
                    self.lookup_cuenta_bancaria(str(valor), e.get("plataforma"))
                )
            elif tipo == "ALIAS_APODO" and valor:
                enriched["alias"].append(self.lookup_alias(str(valor)))

        return enriched


osint_enricher = OSINTEnricher()
