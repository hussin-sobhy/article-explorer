from typing import Iterable, List, Dict, Tuple, Optional
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.errors import ServerSelectionTimeoutError
from app.config import settings


Row = Tuple[str, str, int, int, str, Optional[str]]

class MongoDocStoreService:
    """
    Authoritative store for chunk texts & metadata keyed by chunk_id (UUID5).
    Qdrant keeps vectors+light payload; full text lives here.
    """

    def __init__(self, uri: str | None = None, db: str | None = None, coll: str | None = None) -> None:
        """
        Initialize a connection to MongoDB.
        - uri/db/coll can be provided explicitly (e.g., in tests)
        - Otherwise, they are pulled from app.config.settings at runtime
        """
        if uri is None:
            uri = settings.mongodb_uri
        if not uri:
            raise EnvironmentError("MONGODB_URI not set or empty")

        if db is None:
            db = settings.mongodb_db
        if not db:
            raise EnvironmentError("MONGODB_DB not set or empty")

        if coll is None:
            coll = settings.mongodb_collection
        if not coll:
            raise EnvironmentError("MONGODB_COLLECTION not set or empty")

        # --- Connect to MongoDB ---
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        try: 
            self.client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            raise RuntimeError(f"Could not connect to MongoDB Atlas: {e}") from e

        # --- Cache handles for reuse ---
        self.db: Database = self.client[db]
        self.coll: Collection = self.db[coll]

        # --- Ensure indexes exist ---
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        # chunk_id is the Mongo _id for idempotency
        self.coll.create_index([("_id", ASCENDING)])
        self.coll.create_index([("source", ASCENDING)])
        self.coll.create_index([("source_tag", ASCENDING)])

    
    def upsert_chunks(self, rows: Iterable[Row]) -> int:
        """Bulk upsert: (chunk_id, source, start, end, text, source_tag)."""
        operation: List[UpdateOne] = []
        count = 0

        for cid, src, start, end, text, tag in rows:
            doc = {
                "_id": cid,
                "source": src,
                "start_index": start,
                "end_index": end,
                "text": text,
                "source_tag": tag,
            }

            operation.append(UpdateOne({"_id": cid}, {"$set": doc}, upsert=True))
            count +=1
        if not operation:
            return 0
            
        self.coll.bulk_write(operation, ordered=False)
        
        return count


    def get_by_chunk_ids(self, ids: List[str]) -> Dict[str, Row]:
        """Return mapping chunk_id -> row tuple."""
        if not ids:
            return {}
        cur: Cursor = self.coll.find(
            {"_id": {"$in": ids}},
            projection={"_id": 1, "source": 1, "start_index": 1, "end_index": 1, "text": 1, "source_tag": 1},
        )
        out: Dict[str, Row] = {}
        
        for d in cur:
            out[d["_id"]] = (
                d["_id"],
                d.get("source", ""),
                int(d.get("start_index", 0)),
                int(d.get("end_index", 0)),
                d.get("text", ""),
                d.get("source_tag"),
            )
        return out