# debug_chunker_fetch.py (run from project root)
import logging
from app.services.fetcher import FetcherService
from app.services.chunker import ChunkerService

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    urls = ["https://jamesclear.com/saying-no"]  # change to any public page
    fetcher = FetcherService()
    chunker = ChunkerService(chunk_size=800, chunk_overlap=120)

    docs = fetcher.fetch_urls(urls)
    print(f"Fetched {len(docs)} doc(s). First doc source: {docs[0].metadata.get('source')}")

    chunks = chunker.split(docs)
    print(f"Produced {len(chunks)} chunks.")

    # show first 3 chunks
    for c in chunks[:3]:
        meta = {k: v for k, v in c.metadata.items() if k in ("source", "chunk_id", "start_index")}
        preview = c.page_content.replace("\n", " ")[:120]
        print("meta:", meta)
        print("text:", repr(preview))
        print("-" * 60)
