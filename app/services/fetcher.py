from typing import List
import firecrawl
from langchain.schema import Document
from firecrawl import FirecrawlApp
from app.config import settings
from pydantic import HttpUrl 

class FetcherService:
    def __init__(self):
        api_key= settings.FIRECRAWL_API_KEY
        if not api_key:
            raise EnvironmentError("FIRECRAWL_API_KEY not set")
        
        self.client= FirecrawlApp(api_key= api_key)


    def fetch_urls(self, urls: List[HttpUrl])-> List[Document]:
        """
        Fetch pages and return LangChain Documents with markdown content.
        Prefer markdown; fall back to html if markdown is missing.
        """
        if not urls:
            raise ValueError("No URLs provided")

        documents : List[Document]= []

        for url in urls:
            try:
                res= self.client.scrape_url(url, formats=["markdown", "html"])
                text= getattr(res, "markdown", "")
                if not text:
                    raise ValueError(f"no content extracted from {url}")
                
                documents.append(Document(page_content= text, metadata= {"source": url}))

            except Exception as e:

                raise RuntimeError(f"failed to fetch this URL {url}: {e}") from e

        return documents

