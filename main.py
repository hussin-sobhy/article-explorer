import os
from dotenv import load_dotenv
import streamlit as st

from processing import ArticleExplorerProcessor
import ui

# Load environment variables
load_dotenv()

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state['processor'] = ArticleExplorerProcessor()

def main():
    # Setup the page
    ui.setup_page()
    ui.render_header()
    
    # Get URLs from sidebar
    urls, process_clicked = ui.get_urls()
    
    # Process URLs if requested
    if process_clicked:
        valid_urls = [u.strip() for u in urls if u and u.strip()]
        if not valid_urls:
            st.sidebar.error("⚠️ Please enter at least one URL to process.")
        else:
            try:
                with st.spinner('Processing articles...'):
                    # Create progress callback
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    def progress_callback(status: str, progress: int):
                        status_text.markdown(f"**{status}**")
                        progress_bar.progress(progress)
                    
                    # Process the URLs
                    success = st.session_state['processor'].fetch_and_build_index(
                        valid_urls,
                        progress_callback
                    )
                    
                    # Clean up progress indicators
                    status_text.empty()
                    progress_bar.empty()
                    
                    if success:
                        st.success("✅ Processing complete! You can now ask questions about the articles.")
                    
            except Exception as e:
                ui.show_error(str(e))

    # Handle query input and processing
    query = ui.render_question_input(
        is_enabled=st.session_state['processor'].vectorstore is not None
    )
    
    if query:
        try:
            with st.spinner('🤔 Analyzing...'):
                result = st.session_state['processor'].answer_query(query)
                ui.show_answer_and_sources(
                    answer=result["answer"],
                    sources=result.get("sources", "")
                )
        except Exception as e:
            ui.show_error(str(e))


if __name__ == "__main__":
    main()

