from app.services.docstore_mongo import MongoDocStoreService
import uuid

if __name__ == "__main__":
    store = MongoDocStoreService()
    cid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'debug-cid'))
    rows = [(cid, "https://example.com", 0, 11, "hello world", "demo")]
    n = store.upsert_chunks(rows)
    print("upserted:", n)
    got = store.get_by_chunk_ids([cid])
    print("fetched:", got[cid])
