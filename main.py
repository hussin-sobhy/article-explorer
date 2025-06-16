import os
import time
from dotenv import load_dotenv
import asyncio
import nest_asyncio

from langchain_groq import ChatGroq
import streamlit as st
import pickle
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from firecrawl import FirecrawlApp, ScrapeOptions
from langchain.schema import Document

load_dotenv()
# Initialize session state for all variables we'll need
if 'processed' not in st.session_state:
    st.session_state['processed'] = False
if 'vectorstore' not in st.session_state:
    st.session_state['vectorstore'] = None
if 'query_container' not in st.session_state:
    st.session_state['query_container'] = None
if 'llm' not in st.session_state:
    st.session_state['llm'] = ChatGroq(
        temperature=0,
        model_name="meta-llama/llama-4-maverick-17b-128e-instruct"
    )

# Page configuration
st.set_page_config(
    page_title="RockyBot: News Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, minimal look
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        border: none;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .custom-answer-box {
        background-color: #ffffff;
        color: #31333F;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
    }
    .custom-source-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #f8f9fa;
        margin: 5px 0;
        color: #31333F;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Main layout
st.title("News Research Tool 📈")

# Sidebar configuration
with st.sidebar:
    st.markdown("### 📰 News Article URLs")
    st.markdown("Enter up to 3 article URLs for analysis")
    
    urls = []
    for i in range(3):
        url = st.text_input(f"Article URL {i+1}", key=f"url_{i}", 
                           placeholder=f"Enter URL {i+1} here...")
        urls.append(url)
    
    process_url_clicked = st.button("🔍 Process URLs", type="primary")

file_path = "faiss_store_openai.pkl"

# Main content area
main_container = st.container()

# Function to load vectorstore
def load_vectorstore():
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Error loading processed data: {str(e)}")
            return None
    return None

# Process URLs
if process_url_clicked:
    valid_urls = [u.strip() for u in urls if u and u.strip()]
    if not valid_urls:
        st.sidebar.error("⚠️ Please enter at least one URL to process.")
    else:
        try:
            with st.spinner('Processing articles...'):
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Scrape URLs
                status_text.markdown("🔍 **Fetching articles with Firecrawl...**")
                progress_bar.progress(25)
                
                # loader = UnstructuredURLLoader(urls=urls)   
                # data = loader.load()
                app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
                data = []
                
                for idx, url in enumerate(valid_urls):
                    res = app.scrape_url(url, formats=["markdown", "html"])
                    text = res.markdown or res.get("markdown", "")
                    data.append(Document(page_content=text, metadata={"source": url}))
                
                # Process text
                status_text.markdown("📑 **Processing text...**")
                progress_bar.progress(50)
                text_splitter = RecursiveCharacterTextSplitter(
                    separators=['\n\n', '\n', '.', ','],
                    chunk_size=1000
                )
                docs = text_splitter.split_documents(data)
                
                # Create embeddings
                status_text.markdown("🔮 **Building embeddings...**")
                progress_bar.progress(75)
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
                vectorstore_openai = FAISS.from_documents(docs, embeddings)
                
                # Save index
                status_text.markdown("💾 **Saving processed data...**")
                progress_bar.progress(100)
                with open(file_path, "wb") as f:
                    pickle.dump(vectorstore_openai, f)
                
                st.session_state['processed'] = True
                st.session_state['vectorstore'] = vectorstore_openai
                
                status_text.empty()
                progress_bar.empty()
                st.success("✅ Processing complete! You can now ask questions about the articles.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state['processed'] = False
            st.session_state['vectorstore'] = None

# Query section
with main_container:
    st.markdown("### Ask Questions About the Articles")
    
    # Load vectorstore if it exists and not already loaded
    if st.session_state['vectorstore'] is None:
        st.session_state['vectorstore'] = load_vectorstore()
    
    if st.session_state['vectorstore'] is None:
        st.info("👆 Please process some articles first using the sidebar.")
        st.text_input("Your question:", placeholder="Process articles first...", 
                     disabled=True)
    else:
        query = st.text_input("Your question:", placeholder="What would you like to know about the articles?",
                            help="Ask any question about the content of the processed articles")
        
        if query:
            answer_container = st.empty()
            try:
                with st.spinner('🤔 Analyzing...'):
                    chain = RetrievalQAWithSourcesChain.from_llm(
                        llm=st.session_state['llm'],
                        retriever=st.session_state['vectorstore'].as_retriever()
                    )
                    
                    result = chain({"question": query}, return_only_outputs=True)
                    
                    # Display answer in the reserved container
                    with answer_container.container():
                        st.markdown("### 💡 Answer")
                        st.markdown(f"""
                        <div class="custom-answer-box">
                            {result["answer"]}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display sources
                        sources = result.get("sources", "")
                        if sources:
                            with st.expander("📚 View Sources"):
                                sources_list = sources.split("\n")
                                for source in sources_list:
                                    if source.strip():
                                        st.markdown(f"""
                                        <div class="custom-source-box">
                                            📄 {source}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
            except Exception as e:
                st.error(f"An error occurred while processing your question: {str(e)}")
                st.info("Please try refreshing the page and asking your question again.")