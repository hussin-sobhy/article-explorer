import os
import time
from dotenv import load_dotenv

from langchain_groq import ChatGroq
import streamlit as st
import pickle
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from firecrawl import FirecrawlApp
from langchain.schema import Document

load_dotenv()

st.title("News Research Tool 📈")
st.sidebar.title("News Article URLs")

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    urls.append(url)

process_url_clicked = st.sidebar.button("Process URLs")
file_path = "faiss_store_openai.pkl"


main_placeholder = st.empty()
llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")


if process_url_clicked:
    # Keep only non-empty URLs
    valid_urls = [u.strip() for u in urls if u and u.strip()]
    if not valid_urls:
        st.warning("Please enter at least one URL to process.")
    else:
        # Pass only the valid ones to Unstructured

        #use unstructured loader to load the data from the URLs

        #loader = UnstructuredURLLoader(urls=valid_urls)
        #main_placeholder.text("Data Loading...Started...✅✅✅")
        #data = loader.load()

        # Use Firecrawl to scrape the URLs
        main_placeholder.text("Fetching articles with Firecrawl...✅")
        app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

        data = []
        for url in valid_urls:
            # for a single-page scrape
            res = app.scrape_url(url, formats=["markdown", "html"])
            text = getattr(res, "markdown", "") or ""

            data.append(Document(page_content= text, metadata= {"source": url}))


        # split data
        main_placeholder.text("Text Splitter...Started...✅✅✅")
        text_splitter = RecursiveCharacterTextSplitter(
            separators=['\n\n', '\n', '.', ','],
            chunk_size=1000
        )

        docs = text_splitter.split_documents(data)


        # create embeddings and save it to FAISS index
        main_placeholder.text("Embedding Vector Started Building...✅✅✅")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        vectorstore_openai = FAISS.from_documents(docs, embeddings)
        time.sleep(2)

        # Save the FAISS index to a pickle file
        with open(file_path, "wb") as f:
            pickle.dump(vectorstore_openai, f)


query = main_placeholder.text_input("Question: ")
if query:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            vectorstore = pickle.load(f)
            chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=vectorstore.as_retriever())
            result = chain({"question": query}, return_only_outputs=True)
            # result will be a dictionary of this format --> {"answer": "", "sources": [] }
            st.header("Answer")
            st.write(result["answer"])

            # Display sources, if available
            sources = result.get("sources", "")
            if sources:
                st.subheader("Sources:")
                sources_list = sources.split("\n")  # Split the sources by newline
                for source in sources_list:
                    st.write(source)