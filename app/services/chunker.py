from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)

class ChunkerService:
    """
    Split raw Documents into retrieval-friendly chunks with overlap.
    Deterministic, preserves source metadata, and assigns stable chunk_ids.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150,) -> None:

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size= chunk_size,
            chunk_overlap= chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function= len,
            add_start_index= True
        )
        

    def _normalize(self, text: str) -> str:
        """
        Light, deterministic cleanup to reduce junk and make splitting predictable.
        Avoid aggressive HTML/markdown stripping here — we want to keep useful headings/links.
        """
        # collapse repeated whitespace
        text = re.sub(r"[ \t]+", " ", text)
        # collapse >2 newlines into exactly 2 (paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


    def _chunk_id(self, source: str, start: int, end: int, idx: int) -> str:
        """
        Generate a deterministic UUID5 from source + span.
        Keeps the same value across re-runs as long as upstream text & splitter params don't change.
        """
        namespace = uuid.NAMESPACE_DNS
        name = f"{source}|{start}|{end}|{idx}"
        return str(uuid.uuid5(namespace, name))


    def split(self, docs: List[Document]) -> List[Document]:
        if not docs:
            return []

        # Normalize first so split results are stable
        normalized_docs = [
            Document(page_content=self._normalize(d.page_content or ""), metadata=d.metadata.copy())
            for d in docs
        ]

        sub_docs = self.splitter.split_documents(normalized_docs)

        # Attach stable chunk_id from source + span
        chunks: List[Document] = []
        blanks = 0
        for i, doc in enumerate(sub_docs):
            txt = (doc.page_content or "").strip()
            if not txt:
                blanks += 1
                continue
            source = str(doc.metadata.get("source", "unknown"))
            start = int(doc.metadata.get("start_index", 0))
            end = start + len(txt)
            doc.metadata["chunk_id"] = self._chunk_id(source, start, end, i)
            chunks.append(doc)

        logger.info(
        "Chunker: in=%d docs -> sub_docs=%d, filtered_blanks=%d, out_chunks=%d",
        len(docs), len(sub_docs), blanks, len(chunks)
    )

        return chunks