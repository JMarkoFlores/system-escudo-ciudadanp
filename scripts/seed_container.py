import asyncio
import sys, os
sys.path.insert(0, '/app')

from app.models.db_session import AsyncSessionLocal, init_db
from app.models.database import Denuncia, Cluster, EstadoDenuncia, NivelRiesgo
from app.nlp.ner_engine import ner_engine
from app.nlp.clustering import clustering_engine
import uuid

SEED_DENUNCIAS = [
    {"contenido": "Me llegó una carta: deposita S/. 450 semanales a la cuenta BCP 00123456789012345678 o quemamos tu negocio en El Porvenir. Tienes 48 horas.", "canal": "whatsapp", "tipo_contenido": "texto"},
    {"contenido": "Vacúnate o te picamos. Deposita 500 soles al 942847293 (Yape). Tu ferretería en El Milagro lo sabe.", "canal": "telegram", "tipo_contenido": "texto"},
    {"contenido": "Si no pagas el piso de S/. 450 semanales a la cuenta BCP 00123456789012345678, te vamos a quemar el local en El Porvenir. Tienes hasta el viernes.", "canal": "web", "tipo_contenido": "texto"},
    {"contenido": "Paga la vacuna de 500 soles al Yape 942847293 o te brincamos en El Milagro. Sabemos dónde vives.", "canal": "whatsapp", "tipo_contenido": "texto"},
    {"contenido": "Deposita S/. 450 semanales a BCP 00123456789012345678 o quemamos tu negocio en El Porvenir. Cuidadito.", "canal": "discord", "tipo_contenido": "texto"},
    {"contenido": "Llámame al 942847293. Deposita 500 soles por Yape o te picamos en El Milagro. Te estamos vigilando.", "canal": "telegram", "tipo_contenido": "texto"},
    {"contenido": "Necesito que pagues S/. 300 mensuales a la cuenta Interbank 98765432109876543210 o hacemos daño a tu familia en California.", "canal": "web", "tipo_contenido": "texto"},
    {"contenido": "Paga el cupo de 300 soles mensuales a Interbank 98765432109876543210 o te vamos a buscar en California.", "canal": "whatsapp", "tipo_contenido": "texto"},
    {"contenido": "Deposita S/. 200 semanales al BBVA 11223344556677889900 o granada en tu local de Huanchaco.", "canal": "discord", "tipo_contenido": "texto"},
    {"contenido": "Llamada amenazante: paga 200 soles semanales a BBVA 11223344556677889900 o petardo en tu negocio de Huanchaco.", "canal": "telegram", "tipo_contenido": "texto"},
]

async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        print("Insertando 10 denuncias de seed...")
        denuncias_objs = []
        for data in SEED_DENUNCIAS:
            ner_result = ner_engine.extract_entities(data["contenido"])
            d = Denuncia(
                id=uuid.uuid4(),
                canal=data["canal"],
                tipo_contenido=data["tipo_contenido"],
                contenido_raw=data["contenido"],
                nlp_entities_json=ner_result,
                zona_detectada=ner_result.get("zona_detectada"),
                estado=EstadoDenuncia.procesado,
                nivel_riesgo=NivelRiesgo.alto,
            )
            db.add(d)
            denuncias_objs.append(d)
        await db.commit()
        for d in denuncias_objs:
            await db.refresh(d)
        print(f"Insertadas {len(denuncias_objs)} denuncias. Ejecutando clustering...")
        clustering_engine.build_graph(denuncias_objs)
        active = clustering_engine.find_active_clusters()
        print(f"Clusters detectados: {len(active)}")
        for component in active:
            profile = clustering_engine.calculate_cluster_profile(component)
            codigo = clustering_engine.generar_codigo_cluster()
            cluster = Cluster(
                codigo=codigo,
                zona_principal=profile.get("zona_principal"),
                estado="activo",
                nivel_alerta=profile.get("nivel_alerta", "medio"),
                total_denuncias=profile.get("total_denuncias", 0),
                monto_min=str(profile.get("monto_min")) if profile.get("monto_min") else None,
                monto_max=str(profile.get("monto_max")) if profile.get("monto_max") else None,
                cuentas_detectadas=profile.get("cuentas_detectadas"),
                jerga_frecuente=profile.get("jerga_frecuente"),
                metodos_violencia=profile.get("metodos_violencia"),
                primera_denuncia=profile.get("primera_denuncia"),
                ultima_denuncia=profile.get("ultima_denuncia"),
            )
            db.add(cluster)
            await db.flush()
            for d_id in component:
                d_obj = await db.get(Denuncia, d_id)
                if d_obj:
                    d_obj.cluster_id = cluster.id
            print(f"  Cluster {codigo}: {len(component)} denuncias, zona={profile.get('zona_principal')}, cuentas={profile.get('cuentas_detectadas')}")
        await db.commit()
        print("Seed completado exitosamente.")

asyncio.run(seed())
