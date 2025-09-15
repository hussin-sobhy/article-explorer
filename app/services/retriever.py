from typing import List, Optional
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.services.docstore_mongo import MongoDocStoreService
import logging

logger = logging.getLogger(__name__)

class QdrantRetriever:

    def __init__(
        self, collection: str, 
        qdrant: QdrantClient, embedder: HuggingFaceEmbeddings, 
        docstore: MongoDocStoreService
    ) -> None:

        self.collection = collection
        self.qdrant = qdrant
        self.embedder = embedder
        self.docstore = docstore

    def retrieve(self, query: str, k: int = 5, source_filter: Optional[str] = None) -> List[Document]:

        #Embed the query (uses model's query pipeline)
        qvec = self.embedder.embed_query(query)

        #Optional tag filter
        qfilter = None
        if source_filter:
            qfilter = Filter(must= [FieldCondition(key= "source_tag", match= MatchValue(source_filter))])

         #Vector search
        hits = self.qdrant.search(
            collection_name= self.collection,
            query_vector= qvec,
            limit = k,
            query_filter= qfilter
        )

        #Hydrate text by chunk_id from Mongo
        ids = [h.payloads.get("chunk_id") for h in hits]
        chunks_by_id = self.docstore.get_by_chunk_ids(ids)

        docs: List[Document] = []
        for hit in hits:
            payload = hit.payload
            cid = hit.payload["chunk_id"]
            row = chunks_by_id.get(cid)
            if not row:
                # Orphaned vector: text not found in Mongo; skip but warn
                logger.warning("No Mongo row for chunk_id=%s; skipping", cid)
                continue
            
            _, source, start, end, text, tag_from_mongo = row

            # Merge: start from Mongo-derived metadata, add vector hit details
            md = {
                "chunk_id": cid,
                "source": source,
                "start_index": start,
                "end_index": end,
                "source_tag": tag_from_mongo,
                "score": hit.score,  # Qdrant similarity score (higher is closer for COSINE)
            }

            
            for k2, v2 in payload.items():
                md.setdefault(k2, v2) # keep Mongo-derived values if conflict
                
            docs.append(Document(page_content=text, metadata=md)) 

        return docs

         