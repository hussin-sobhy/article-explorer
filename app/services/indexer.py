from typing import List
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from numpy import source
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from app.config import settings
from app.services.docstore_mongo import MongoDocStoreService


class IndexerService:
    def __init__(self, collection_name: str = "articles") -> None:
         # Embedding model
        self.embedder = HuggingFaceEmbeddings(model_name= "sentence-transformers/all-mpnet-base-v2")
        # Qdrant client (uses the URL from your config)
        self.client = QdrantClient(url= settings.Qdrant_url)

        self.collection_name = collection_name
        self.docstore = MongoDocStoreService(coll= collection_name)
        self._ensure_collection()


    def _ensure_collection(self) -> None:
        """Create collection if missing"""

        if not self.client.collection_exists(self.collection_name):
            self.client.recreate_collection(
                collection_name= self.collection_name,
                vectors_config= VectorParams(size= 768, distance= Distance.COSINE)
            )


    def upsert(self, chunks: List[Document]) -> int:
        """
        1) Persist full text to Mongo (authoritative doc store) keyed by chunk_id (UUID5).
        2) Embed chunk texts with HuggingFace.
        3) Upsert vectors + light payload to Qdrant (no full text).
        Returns number of chunks indexed.
        """
        if not chunks:
            return 0

        # ---- 1) Write text & metadata to Mongo (idempotent) ----
        rows = []
        for c in chunks:
            cid = c.metadata["chunk_id"]                        # UUID5 from your chunker
            source = str(c.metadata.get("source", "unknown"))
            start = int(c.metadata.get("start_index", 0))
            # prefer explicit end_index if your chunker set it; otherwise compute
            end = int(c.metadata.get("end_index", start + len(c.page_content or "")))
            tag = c.metadata.get("source_tag")                  # optional corpus label

            rows.append((cid, source, start, end, c.page_content, tag))

        # Mongo bulk upsert (authoritative text store)
        self.docstore.upsert_chunks(rows)

        # ---- 2) Embed for vector search ----
        texts = [c.page_content for c in chunks]
        vectors = self.embedder.embed_documents(texts)

        # ---- 3) Upsert to Qdrant with lean payload (no full text) ----
        points = []
        for c, vec in zip(chunks, vectors):
            cid = c.metadata["chunk_id"]
            source = str(c.metadata.get("source", "unknown"))
            start = int(c.metadata.get("start_index", 0))
            end = int(c.metadata.get("end_index", start + len(c.page_content or "")))

            payload = {
                "chunk_id": cid,                # join key back to Mongo
                "source": source,
                "start_index": start,
                "end_index": end,
                "source_tag": c.metadata.get("source_tag"),
                "content_type": c.metadata.get("content_type"),
            }

            points.append(PointStruct(id=cid, vector=vec, payload=payload))

        # One network call; Qdrant will overwrite on id collision (idempotent)
        self.client.upsert(collection_name=self.collection_name, points=points)

        return len(points)
