"""
Tests de NLP Forense + Clustering (Fase 4)
"""
import pytest
from app.nlp.ontology import buscar_toponimo, detectar_banco, extraer_monto_numerico
from app.nlp.ner_engine import ner_engine
from app.nlp.clustering import ClusteringEngine


class TestNERExtraccion:
    def test_extrae_cuenta_bancaria_bcp(self):
        texto = "deposita a la cuenta BCP 00123456789012 o quemamos tu negocio"
        result = ner_engine.extract_entities(texto)
        cuentas = [e for e in result["entidades"] if e["tipo"] == "CUENTA_BANCARIA"]
        assert len(cuentas) >= 1
        assert cuentas[0]["valor"] == "00123456789012"
        assert cuentas[0]["entidad"] == "bcp"

    def test_extrae_zona_el_porvenir(self):
        texto = "tu negocio en El Porvenir está en riesgo"
        result = ner_engine.extract_entities(texto)
        assert result["zona_detectada"] == "El Porvenir"
        zonas = [e for e in result["entidades"] if e["tipo"] == "TOPONIMO_TRUJILLO"]
        assert len(zonas) >= 1
        assert zonas[0]["lat"] is not None
        assert zonas[0]["lng"] is not None

    def test_extrae_monto_y_plazo(self):
        texto = "deposita S/. 450 semanales, tienes 48 horas"
        result = ner_engine.extract_entities(texto)
        assert result["monto_principal"] == 450.0
        montos = [e for e in result["entidades"] if e["tipo"] == "MONTO"]
        assert len(montos) >= 1
        plazos = [e for e in result["entidades"] if e["tipo"] == "PLAZO"]
        assert len(plazos) >= 1

    def test_extrae_telefono_y_jerga(self):
        texto = "Llámame al 942847293 o te picamos. Deposita por Yape."
        result = ner_engine.extract_entities(texto)
        tels = [e for e in result["entidades"] if e["tipo"] == "TELEFONO_EXTORSIVO"]
        assert len(tels) >= 1
        jerga = [e for e in result["entidades"] if e["tipo"] == "JERGA_INTIMIDACION"]
        assert len(jerga) >= 1

    def test_detecta_banco_interbank(self):
        texto = "cuenta Interbank 9876543210987654"
        assert detectar_banco(texto) == "interbank"

    def test_extrae_monto_numerico(self):
        assert extraer_monto_numerico("S/ 500") == 500.0
        assert extraer_monto_numerico("500 soles") == 500.0


class TestClusteringDeteccion:
    def test_clustering_detecta_banda_3_denuncias_misma_cuenta(self):
        engine = ClusteringEngine()
        
        denuncias = [
            {"id": "d1", "cuentas": ["00123456789012"], "telefonos": [], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": [], "jerga": ["quemar"], "embedding": None},
            {"id": "d2", "cuentas": ["00123456789012"], "telefonos": [], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": [], "jerga": ["picar"], "embedding": None},
            {"id": "d3", "cuentas": ["00123456789012"], "telefonos": [], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": [], "jerga": ["quemar"], "embedding": None},
        ]
        
        engine.build_graph(denuncias)
        clusters = engine.find_active_clusters()
        
        assert len(clusters) >= 1
        assert len(clusters[0]) == 3

    def test_clustering_no_detecta_banda_2_denuncias(self):
        engine = ClusteringEngine()
        
        denuncias = [
            {"id": "d1", "cuentas": ["00123456789012"], "telefonos": [], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": [], "jerga": [], "embedding": None},
            {"id": "d2", "cuentas": ["00123456789012"], "telefonos": [], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": [], "jerga": [], "embedding": None},
        ]
        
        engine.build_graph(denuncias)
        clusters = engine.find_active_clusters()
        
        assert len(clusters) == 0  # Necesita ≥3 nodos

    def test_perfil_banda_completo(self):
        engine = ClusteringEngine()
        
        denuncias = [
            {"id": "d1", "cuentas": ["00123456789012"], "telefonos": ["942847293"], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": ["quemar"], "jerga": ["vacuna"], "embedding": None},
            {"id": "d2", "cuentas": ["00123456789012"], "telefonos": ["942847293"], "zona": "El Porvenir", "fecha": None, "monto": 450.0, "metodos_violencia": ["quemar"], "jerga": ["vacuna"], "embedding": None},
            {"id": "d3", "cuentas": ["00123456789012"], "telefonos": ["942847293"], "zona": "El Porvenir", "fecha": None, "monto": 500.0, "metodos_violencia": ["quemar"], "jerga": ["piso"], "embedding": None},
        ]
        
        engine.build_graph(denuncias)
        clusters = engine.find_active_clusters()
        assert len(clusters) >= 1
        
        profile = engine.calculate_cluster_profile(clusters[0])
        assert profile["total_denuncias"] == 3
        assert profile["zona_principal"] == "El Porvenir"
        assert "00123456789012" in profile["cuentas_detectadas"]
        assert profile["monto_min"] is not None
        assert profile["monto_max"] is not None
        assert len(profile["jerga_frecuente"]) > 0
        assert len(profile["metodos_violencia"]) > 0

    def test_generar_codigo_cluster(self):
        codigo = ClusteringEngine.generar_codigo_cluster()
        assert codigo.startswith("CLU-")
        assert len(codigo) == 8  # CLU-XXXX
