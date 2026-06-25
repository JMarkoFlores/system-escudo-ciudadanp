"""
Sistema de Memoria para Agentes (PostgreSQL + Qdrant)
"""
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.embeddings import Embeddings
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

from app.config.settings import settings
from app.models.database import MemoriaConversacional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

class FastEmbedLocal(Embeddings):
    """
    Wrapper de FastEmbed para LangChain.
    Embeddings locales ultraligeros sin dependencia de torch.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return list(self._model.embed(texts))

    def embed_query(self, text: str) -> list[float]:
        return list(self._model.embed([text]))[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)

class HybridMemory:
    """
    Memoria híbrida que combina:
    - Memoria conversacional a corto plazo (PostgreSQL)
    - Memoria semántica a largo plazo (Qdrant vector DB)
    """
    
    def __init__(self):
        self.embeddings = FastEmbedLocal()
        self.qdrant = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY
        )
        self._ensure_collection()
    
    def _ensure_collection(self):
        collections = [c.name for c in self.qdrant.get_collections().collections]
        if settings.QDRANT_COLLECTION_DENUNCIAS not in collections:
            self.qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION_DENUNCIAS,
                vectors_config=VectorParams(
                    size=settings.QDRANT_DIMENSION,
                    distance=Distance.COSINE
                )
            )
    
    async def save_conversational_turn(
        self,
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None
    ) -> None:
        """Guarda un mensaje en la memoria conversacional SQL"""
        mem = MemoriaConversacional(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        db.add(mem)
        await db.commit()
    
    async def get_conversational_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 20
    ) -> List[BaseMessage]:
        """Recupera últimos N mensajes de la conversación"""
        result = await db.execute(
            select(MemoriaConversacional)
            .where(MemoriaConversacional.session_id == session_id)
            .order_by(desc(MemoriaConversacional.created_at))
            .limit(limit)
        )
        rows = result.scalars().all()
        
        messages = []
        for row in reversed(rows):  # Orden cronológico
            if row.role == "human":
                messages.append(HumanMessage(content=row.content))
            elif row.role == "ai":
                messages.append(AIMessage(content=row.content, tool_calls=row.tool_calls or []))
            elif row.role == "system":
                messages.append(SystemMessage(content=row.content))
            elif row.role == "tool":
                messages.append(ToolMessage(content=row.content, tool_call_id=row.tool_calls.get("tool_call_id", "") if row.tool_calls else ""))
        return messages
    
    async def save_semantic_memory(
        self,
        denuncia_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Guarda embedding en Qdrant para búsqueda semántica futura"""
        vector = await self.embeddings.aembed_query(text)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "denuncia_id": str(denuncia_id),
                "texto": text,
                "metadata": metadata,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        self.qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION_DENUNCIAS,
            points=[point]
        )
    
    async def search_similar_cases(
        self,
        query: str,
        denuncia_id_excluir: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica de casos similares"""
        vector = await self.embeddings.aembed_query(query)
        results = self.qdrant.search(
            collection_name=settings.QDRANT_COLLECTION_DENUNCIAS,
            query_vector=vector,
            limit=limit + 1,
            with_payload=True
        )
        
        casos = []
        for r in results:
            payload = r.payload
            if denuncia_id_excluir and payload.get("denuncia_id") == denuncia_id_excluir:
                continue
            casos.append({
                "denuncia_id": payload.get("denuncia_id"),
                "score": r.score,
                "texto": payload.get("texto"),
                "metadata": payload.get("metadata")
            })
        return casos[:limit]
    
    async def get_relevant_context(
        self,
        db: AsyncSession,
        session_id: str,
        query: str,
        k_short: int = 10,
        k_long: int = 5
    ) -> str:
        """Compila contexto relevante combinando corto y largo plazo"""
        # Corto plazo: última conversación
        short_term = await self.get_conversational_history(db, session_id, limit=k_short)
        short_context = "\n".join([f"{m.type}: {m.content}" for m in short_term])
        
        # Largo plazo: casos similares
        similar = await self.search_similar_cases(query, limit=k_long)
        long_context = "\n".join([
            f"[Caso similar {i+1}] {c['texto'][:500]}..."
            for i, c in enumerate(similar)
        ])
        
        return f"""### Contexto de conversación reciente
{short_context}

### Casos históricos similares
{long_context}
"""

memory_system = HybridMemory()
