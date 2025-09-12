from typing import List
from langchain.schema import Document
from langchain_core import embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from numpy import source
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, CollectionStatus
from app.config import settings
import hashlib
import uuid


class IndexerService:
    def __init__(self, collection_name: str = "articles") -> None:
         # Embedding model
        self.embedder = HuggingFaceEmbeddings(model_name= "sentence-transformers/all-mpnet-base-v2")
        # Qdrant client (uses the URL from your config)
        self.client = QdrantClient(url= settings.Qdrant_url)

        self.collection_name = collection_name
        self._ensure_collection()


    def _ensure_collection(self) -> None:
        """Create collection if missing"""

        if not self.client.collection_exists(self.collection_name):
            self.client.recreate_collection(
                collection_name= self.collection_name,
                vectors_config= VectorParams(size= 768, distance= Distance.COSINE)
            )


    def _point_id(self, chunk: Document) -> str:
        """Use the chunk_id directly as it's already in UUID format"""
        return chunk.metadata["chunk_id"]

    
    def upsert(self, chunks: List[Document]) -> int:
        """Embed and upsert documents into Qdrant. Returns number indexed."""
        
        if not chunks:
            return 0

        texts = [c.page_content for c in chunks]
        embeddings= self.embedder.embed_documents(texts)

        points = []
        for chunk, vector in zip(chunks, embeddings):
            pid = self._point_id(chunk)
            payload = chunk.metadata.copy()
            points.append(PointStruct(id=pid, vector= vector, payload= payload))

        self.client.upsert(collection_name=self.collection_name, points= points)

        return len(points)
