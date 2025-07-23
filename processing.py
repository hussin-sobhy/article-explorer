from typing import List, Dict
import os

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_groq import ChatGroq
from firecrawl import FirecrawlApp


class ArticleExplorerProcessor:
    """Core pipeline: scrape → chunk → embed → index → answer."""

    def __init__(self) -> None:
        # Deterministic Groq Llama‑4 model
        self.llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0,
        )
        self.vectorstore: FAISS | None = None

    
    # BUILD INDEX
    def fetch_and_build_index(self, urls: List[str], progress_callback=None) -> bool:
        """Scrape URLs and build an in‑memory FAISS index.

        Parameters
        ----------
        urls : list[str]
            List of article URLs to process.
        progress_callback : callable | None
            Optional hook ``cb(text:str, percent:int)`` to update UI progress.
        """
        if not urls:
            raise ValueError("No URLs provided")

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise EnvironmentError("FIRECRAWL_API_KEY not set")

        # FETCH 
        if progress_callback:
            progress_callback("🔍 Fetching articles with Firecrawl…", 25)

        firecrawl = FirecrawlApp(api_key=api_key)
        documents: list[Document] = []

        for url in urls:
            try:
                res = firecrawl.scrape_url(url, formats=["markdown", "html"])
                text = getattr(res, "markdown", "")
                if not text:
                    raise ValueError("No content")
                documents.append(Document(page_content=text, metadata={"source": url}))
            except Exception as err:
                raise RuntimeError(f"Error scraping {url}: {err}") from err

        if not documents:
            raise RuntimeError("Failed to retrieve any content from provided URLs")

        # SPLIT 
        if progress_callback:
            progress_callback("📑 Splitting text…", 50)

        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", ","],
            chunk_size=1000,
        )
        chunks = splitter.split_documents(documents)

        # EMBED & INDEX 
        if progress_callback:
            progress_callback("🔮 Creating embeddings…", 75)

        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.vectorstore = FAISS.from_documents(chunks, embedder)

        if progress_callback:
            progress_callback("✅ Index ready!", 100)
        return True

    # ---------------------------------------------------------------------
    # QUERY
    # ---------------------------------------------------------------------
    def answer_query(self, query: str) -> Dict[str, str]:
        """Return LLM answer + sources for a given query."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        if self.vectorstore is None:
            raise RuntimeError("You must process URLs before asking questions.")

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        rag_chain = RetrievalQAWithSourcesChain.from_llm(llm=self.llm, retriever=retriever)

        result = rag_chain({"question": query}, return_only_outputs=True)
        if not result.get("answer"):
            raise RuntimeError("LLM did not return an answer")
        return result
