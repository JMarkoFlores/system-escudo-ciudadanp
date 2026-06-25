"""
Motor de Clustering con NetworkX para IntelExtorsión
Detecta bandas criminales conectando denuncias por vectores compartidos.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone, timedelta
import uuid as uuid_module
import networkx as nx
import numpy as np
from collections import Counter

from app.nlp.ontology import normalizar_texto, buscar_toponimo


class ClusteringEngine:
    """
    Motor de clustering basado en grafos.
    Cada denuncia es un nodo. Las aristas representan similitud forense.
    Un clúster = componente conectada con ≥3 nodos y ≥2 vectores compartidos.
    """

    MIN_NODOS_CLUSTER = 3
    MIN_VECTORES_COMPARTIDOS = 2
    UMBRAL_COSINE_EMBEDDING = 0.85
    UMBRAL_MONTO_TOLERANCIA = 0.20  # ±20%
    UMBRAL_DIAS_ZONA = 21

    def __init__(self):
        self.G = nx.Graph()

    # -----------------------------------------
    # Construcción del grafo
    # -----------------------------------------

    def build_graph(self, denuncias: List[Any]) -> nx.Graph:
        """
        Construye el grafo de denuncias.
        `denuncias` es una lista de objetos ORM (Denuncia) o dicts con atributos.
        """
        self.G = nx.Graph()

        # Añadir nodos
        for d in denuncias:
            node_id = str(getattr(d, "id", d.get("id") if isinstance(d, dict) else ""))
            if not node_id:
                continue
            self.G.add_node(node_id, data=d)

        # Añadir aristas
        ids = list(self.G.nodes())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                d1 = self.G.nodes[ids[i]]["data"]
                d2 = self.G.nodes[ids[j]]["data"]
                shared = self._count_shared_vectors(d1, d2)
                if shared >= self.MIN_VECTORES_COMPARTIDOS:
                    self.G.add_edge(ids[i], ids[j], weight=shared)

        return self.G

    def _count_shared_vectors(self, d1_raw: Any, d2_raw: Any) -> int:
        """
        Calcula cuántos vectores comparten dos denuncias.
        """
        score = 0

        # Normalizar a dict
        d1 = self._denuncia_to_dict(d1_raw)
        d2 = self._denuncia_to_dict(d2_raw)

        # 1. Cuentas bancarias / Yape compartidas (+2 si hay intersección)
        cuentas1 = set(d1.get("cuentas", []))
        cuentas2 = set(d2.get("cuentas", []))
        if cuentas1 and cuentas2 and cuentas1 & cuentas2:
            score += 2

        # 2. Teléfonos compartidos (+2)
        tels1 = set(d1.get("telefonos", []))
        tels2 = set(d2.get("telefonos", []))
        if tels1 and tels2 and tels1 & tels2:
            score += 2

        # 3. Similaridad de embeddings (+1)
        emb1 = d1.get("embedding")
        emb2 = d2.get("embedding")
        if emb1 and emb2 and self._cosine_similarity(emb1, emb2) > self.UMBRAL_COSINE_EMBEDDING:
            score += 1

        # 4. Misma zona + fecha cercana (+1)
        zona1 = d1.get("zona")
        zona2 = d2.get("zona")
        fecha1 = d1.get("fecha")
        fecha2 = d2.get("fecha")
        if zona1 and zona2 and zona1 == zona2:
            if fecha1 and fecha2:
                dias = abs((fecha1 - fecha2).days)
                if dias <= self.UMBRAL_DIAS_ZONA:
                    score += 1
            else:
                score += 1  # Si no hay fecha, solo coincidir zona da punto

        # 5. Montos similares (+1)
        m1 = d1.get("monto")
        m2 = d2.get("monto")
        if m1 and m2 and m1 > 0 and m2 > 0:
            if abs(m1 - m2) / max(m1, m2) <= self.UMBRAL_MONTO_TOLERANCIA:
                score += 1

        # 6. Mismo método de violencia (+1)
        met1 = set(d1.get("metodos_violencia", []))
        met2 = set(d2.get("metodos_violencia", []))
        if met1 and met2 and met1 & met2:
            score += 1

        # 7. Misma jerga intimidatoria (+1)
        jerga1 = set(d1.get("jerga", []))
        jerga2 = set(d2.get("jerga", []))
        if jerga1 and jerga2 and jerga1 & jerga2:
            score += 1

        return score

    def _denuncia_to_dict(self, d: Any) -> Dict[str, Any]:
        """Normaliza una denuncia (ORM o dict) a dict plano para comparación."""
        if isinstance(d, dict):
            return d

        # Es un objeto ORM
        result = {}
        result["id"] = str(getattr(d, "id", ""))
        result["zona"] = getattr(d, "zona_detectada", None)
        result["fecha"] = getattr(d, "created_at", None)
        result["monto"] = None
        result["cuentas"] = []
        result["telefonos"] = []
        result["metodos_violencia"] = []
        result["jerga"] = []
        result["embedding"] = None

        # Extraer desde nlp_entities_json si existe
        entities = getattr(d, "nlp_entities_json", None) or {}
        if isinstance(entities, dict):
            ent_list = entities.get("entidades", [])
            for e in ent_list:
                tipo = e.get("tipo", "")
                valor = e.get("valor", "")
                if tipo == "CUENTA_BANCARIA" and valor:
                    result["cuentas"].append(str(valor))
                elif tipo == "YAPE_PLIN" and valor:
                    result["cuentas"].append(str(valor))  # Yape/Plin cuenta como cuenta
                    result["telefonos"].append(str(valor))
                elif tipo == "TELEFONO_EXTORSIVO" and valor:
                    result["telefonos"].append(str(valor))
                elif tipo == "MONTO" and valor:
                    try:
                        result["monto"] = float(valor)
                    except (ValueError, TypeError):
                        pass
                elif tipo == "METODO_VIOLENCIA" and valor:
                    result["metodos_violencia"].append(normalizar_texto(str(valor)))
                elif tipo == "JERGA_INTIMIDACION" and valor:
                    result["jerga"].append(normalizar_texto(str(valor)))

            # Embedding no está en nlp_entities, se toma de memoria semántica si existe
            # Por ahora dejamos None; el service puede pasarlo si lo tiene

        return result

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calcula cosine similarity entre dos vectores."""
        if not a or not b:
            return 0.0
        a_arr = np.array(a)
        b_arr = np.array(b)
        norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if norm == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / norm)

    # -----------------------------------------
    # Detección de clusters activos
    # -----------------------------------------

    def find_active_clusters(self) -> List[List[str]]:
        """
        Encuentra componentes conectadas que califican como clústeres activos.
        Devuelve lista de listas de IDs de denuncia.
        """
        clusters = []
        for component in nx.connected_components(self.G):
            if len(component) >= self.MIN_NODOS_CLUSTER:
                clusters.append(list(component))
        return clusters

    # -----------------------------------------
    # Perfil de banda (cluster profile)
    # -----------------------------------------

    def calculate_cluster_profile(self, cluster_nodes: List[str]) -> Dict[str, Any]:
        """
        Genera el perfil forense de una banda criminal a partir de sus denuncias.
        """
        denuncias = [self.G.nodes[n]["data"] for n in cluster_nodes if n in self.G.nodes]
        if not denuncias:
            return {}

        # Agregar entidades de todas las denuncias
        todas_cuentas = []
        todos_telefonos = []
        todos_montos = []
        todas_jergas = []
        todos_metodos = []
        todas_zonas = []
        fechas = []

        for d in denuncias:
            dd = self._denuncia_to_dict(d)
            todas_cuentas.extend(dd.get("cuentas", []))
            todos_telefonos.extend(dd.get("telefonos", []))
            if dd.get("monto"):
                todos_montos.append(dd["monto"])
            todas_jergas.extend(dd.get("jerga", []))
            todos_metodos.extend(dd.get("metodos_violencia", []))
            if dd.get("zona"):
                todas_zonas.append(dd["zona"])
            if dd.get("fecha"):
                fechas.append(dd["fecha"])

        # Zona principal (moda)
        zona_principal = None
        if todas_zonas:
            zona_principal = Counter(todas_zonas).most_common(1)[0][0]

        # Montos
        monto_min = min(todos_montos) if todos_montos else None
        monto_max = max(todos_montos) if todos_montos else None

        # Tendencia (comparar primera mitad vs segunda mitad de fechas)
        tendencia = "estable"
        if len(fechas) >= 3:
            fechas_ordenadas = sorted(fechas)
            mitad = len(fechas_ordenadas) // 2
            primeras = fechas_ordenadas[:mitad]
            ultimas = fechas_ordenadas[mitad:]
            delta_primeras = (primeras[-1] - primeras[0]).days if len(primeras) > 1 else 0
            delta_ultimas = (ultimas[-1] - ultimas[0]).days if len(ultimas) > 1 else 0
            if delta_ultimas < delta_primeras:
                tendencia = "creciente"  # Más frecuente recientemente
            elif delta_ultimas > delta_primeras:
                tendencia = "decreciente"

        # Nivel de alerta
        nivel_alerta = "bajo"
        if len(cluster_nodes) >= 10:
            nivel_alerta = "critico"
        elif len(cluster_nodes) >= 5:
            nivel_alerta = "alto"
        elif len(cluster_nodes) >= 3:
            nivel_alerta = "medio"

        return {
            "total_denuncias": len(cluster_nodes),
            "zona_principal": zona_principal,
            "monto_min": monto_min,
            "monto_max": monto_max,
            "cuentas_detectadas": list(set(todas_cuentas)),
            "telefonos_detectados": list(set(todos_telefonos)),
            "jerga_frecuente": Counter(todas_jergas).most_common(10),
            "metodos_violencia": list(set(todos_metodos)),
            "tendencia": tendencia,
            "nivel_alerta": nivel_alerta,
            "primera_denuncia": min(fechas) if fechas else None,
            "ultima_denuncia": max(fechas) if fechas else None,
        }

    # -----------------------------------------
    # Asignación de denuncia a cluster existente
    # -----------------------------------------

    def find_best_cluster_for_denuncia(
        self,
        denuncia: Any,
        existing_clusters: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Busca el clúster existente al que mejor encaja una nueva denuncia.
        `existing_clusters`: lista de dicts con `id`, `denuncias` (lista de objetos/dicts).
        Devuelve el `cluster_id` o None.
        """
        d_dict = self._denuncia_to_dict(denuncia)
        best_cluster_id = None
        best_score = 0

        for cluster in existing_clusters:
            cluster_denuncias = cluster.get("denuncias", [])
            total_score = 0
            for cd in cluster_denuncias:
                score = self._count_shared_vectors(d_dict, cd)
                total_score += score
            avg_score = total_score / len(cluster_denuncias) if cluster_denuncias else 0
            if avg_score >= self.MIN_VECTORES_COMPARTIDOS and avg_score > best_score:
                best_score = avg_score
                best_cluster_id = cluster.get("id")

        return best_cluster_id

    # -----------------------------------------
    # Generación de código de clúster
    # -----------------------------------------

    @staticmethod
    def generar_codigo_cluster() -> str:
        """Genera un código único CLU-XXXX."""
        import random
        import string
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CLU-{suffix}"


# Instancia singleton
clustering_engine = ClusteringEngine()
