import streamlit as st
from typing import List, Tuple, Optional, Callable

def setup_page():
    """Configure the basic page settings"""
    st.set_page_config(
        page_title="News Research",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom styling
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

def render_header():
    """Render the page header"""
    st.title("News Research Tool 📈")

def get_urls() -> Tuple[List[str], bool]:
    """Get URLs from sidebar and return them along with button state"""
    with st.sidebar:
        st.markdown("### 📰 News Article URLs")
        st.markdown("Enter up to 3 article URLs for analysis")
        
        urls = []
        for i in range(3):
            url = st.text_input(
                f"Article URL {i+1}",
                key=f"url_{i}",
                placeholder=f"Enter URL {i+1} here..."
            )
            urls.append(url)
        
        process_button = st.button("🔍 Process URLs", type="primary")
        
    return urls, process_button

def show_processing_status(status: str, progress: int):
    """Show processing status and progress"""
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.markdown(f"**{status}**")
    progress_bar.progress(progress)
    
    return status_text, progress_bar

def render_question_input(is_enabled: bool = True) -> Optional[str]:
    """Render the question input field"""
    st.markdown("### Ask Questions About the Articles")
    
    if not is_enabled:
        st.info("👆 Please process some articles first using the sidebar.")
        st.text_input("Your question:", placeholder="Process articles first...", 
                     disabled=True)
        return None
    
    return st.text_input(
        "Your question:",
        placeholder="What would you like to know about the articles?",
        help="Ask any question about the content of the processed articles"
    )

def show_answer_and_sources(answer: str, sources: str):
    """Display the answer and sources in a nicely formatted way"""
    st.markdown("### 💡 Answer")
    st.markdown(f"""
    <div class="custom-answer-box">
        {answer}
    </div>
    """, unsafe_allow_html=True)
    
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

def show_error(error: str):
    """Display an error message"""
    st.error(f"An error occurred: {error}")
    st.info("Please try again or refresh the page if the problem persists.")
