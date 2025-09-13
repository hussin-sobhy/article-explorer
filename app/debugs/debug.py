from app.services.fetcher import FetcherService
from app.services.chunker import ChunkerService
from app.services.indexer import IndexerService

if __name__ == "__main__":
    fetcher = FetcherService()
    chunker = ChunkerService()
    indexer = IndexerService(collection_name="articles")

    docs = fetcher.fetch_urls(["https://jamesclear.com/saying-no"])
    chunks = chunker.split(docs)
    print("chunks:", len(chunks))

    n = indexer.upsert(chunks)
    print(f"Upserted {n} chunks into Qdrant")