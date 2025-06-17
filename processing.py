import os
import pickle
from typing import List, Dict, Optional, Callable, Any
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_groq import ChatGroq
from firecrawl import FirecrawlApp

class ArticleExplorerProcessor:
    def __init__(self, file_path: str = "faiss_store_openai.pkl"):
        self.file_path = file_path
        self.llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0
        )
        self.vectorstore = None
        
    def fetch_and_build_index(self, urls: List[str], progress_callback=None) -> bool:
        """
        Fetch articles and build search index
        Returns True if successful, False otherwise
        """
        if not urls:
            raise ValueError("No URLs provided")
            
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")
            
        try:
            # Progress update
            if progress_callback:
                progress_callback("🔍 Fetching articles with Firecrawl...", 25)
            
            # Fetch articles
            app = FirecrawlApp(api_key=api_key)
            data = []
            
            for url in urls:
                try:
                    res = app.scrape_url(url, formats=["markdown", "html"])
                    text = res.markdown if hasattr(res, 'markdown') else None
                    if not text:
                        raise ValueError(f"No content found for URL: {url}")
                    data.append(Document(page_content=text, metadata={"source": url}))
                except Exception as e:
                    raise Exception(f"Error processing URL {url}: {str(e)}")
            
            if not data:
                raise ValueError("No content was successfully retrieved from any URL")
            
            # Process text
            if progress_callback:
                progress_callback("📑 Processing text...", 50)
                
            text_splitter = RecursiveCharacterTextSplitter(
                separators=['\n\n', '\n', '.', ','],
                chunk_size=1000
            )
            docs = text_splitter.split_documents(data)
            
            # Create embeddings
            if progress_callback:
                progress_callback("🔮 Building embeddings...", 75)
                
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            self.vectorstore = FAISS.from_documents(docs, embeddings)
            
            # Save index
            if progress_callback:
                progress_callback("💾 Saving processed data...", 100)
            
            try:    
                with open(self.file_path, "wb") as f:
                    pickle.dump(self.vectorstore, f)
            except Exception as e:
                raise Exception(f"Error saving vector store: {str(e)}")
            
            return True
            
        except Exception as e:
            # Clear the vectorstore if anything fails
            self.vectorstore = None
            raise Exception(f"Error processing URLs: {str(e)}")
    
    def load_vectorstore(self) -> bool:
        """Load the vector store from disk if it exists"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "rb") as f:
                    self.vectorstore = pickle.load(f)
                return True
            except Exception as e:
                raise Exception(f"Error loading vector store: {str(e)}")
        return False
    
    def answer_query(self, query: str) -> Dict[str, str]:
        """Answer a query using the loaded vector store"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        if not self.vectorstore:
            if not self.load_vectorstore():
                raise Exception("No processed articles available. Please process some URLs first.")
                
        if not isinstance(self.vectorstore, FAISS):
            raise Exception("Invalid vector store state. Please process articles again.")
        
        try:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Get top 3 most relevant chunks
            )
            
            chain = RetrievalQAWithSourcesChain.from_llm(
                llm=self.llm,
                retriever=retriever
            )
            
            result = chain({"question": query}, return_only_outputs=True)
            
            if not result.get("answer"):
                raise Exception("No answer found in the processed articles")
                
            return result
            
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")
