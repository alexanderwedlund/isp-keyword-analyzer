import streamlit as st
from pathlib import Path
import sys

current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if src_dir.exists():
    sys.path.append(str(current_dir))

from src.config.settings import KeywordSets
from src.data.session_store import SQLiteSessionRepository, SessionManager
from src.ui.app import setup_app_ui
from src.domain.ai.model import ModelManager

st.set_page_config(
    page_title="ISP Keyword Analyzer",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_app():
    """Initialize the application state and dependencies."""
    session_repo = SQLiteSessionRepository()
    session_manager = SessionManager(session_repo)
    
    if 'isps' not in st.session_state:
        st.session_state.isps = {}
    if 'current_isp_id' not in st.session_state:
        st.session_state.current_isp_id = None
    if 'next_isp_id' not in st.session_state:
        st.session_state.next_isp_id = 1
    if 'current_keyword' not in st.session_state:
        st.session_state.current_keyword = None
    if 'current_sentences' not in st.session_state:
        st.session_state.current_sentences = []
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'classifications' not in st.session_state:
        st.session_state.classifications = []
    if 'analyzed_keywords' not in st.session_state:
        st.session_state.analyzed_keywords = {}
    if 'language' not in st.session_state:
        st.session_state.language = "Swedish"
    if 'show_context' not in st.session_state:
        st.session_state.show_context = False
    if 'context_mode' not in st.session_state:
        st.session_state.context_mode = "normal"
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = ""
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False
    if 'ai_analysis_in_progress' not in st.session_state:
        st.session_state.ai_analysis_in_progress = False
    if 'show_ai_current_warning' not in st.session_state:
        st.session_state.show_ai_current_warning = False
    if 'show_ai_warning' not in st.session_state:
        st.session_state.show_ai_warning = False
    if 'suggestion_in_progress' not in st.session_state:
        st.session_state.suggestion_in_progress = False
    if 'current_suggestion' not in st.session_state:
        st.session_state.current_suggestion = None
    if 'all_keywords_analyzed' not in st.session_state:
        st.session_state.all_keywords_analyzed = False
    if 'classification_metadata' not in st.session_state:
        st.session_state.classification_metadata = {}
    
    if 'selected_model' not in st.session_state:
        available_models = ModelManager.get_available_models()
        if available_models.get("4B", {}).get("available", False):
            st.session_state.selected_model = "4B"
        elif available_models.get("12B", {}).get("available", False):
            st.session_state.selected_model = "12B"
        else:
            st.session_state.selected_model = None
    
    return session_manager

def main():
    """Main application entry point."""
    st.title("ISP Keyword Analyzer")
    st.markdown("""
    ### A Tool for Analyzing ISP Documents to Measure Keyword Loss of Specificity

    This application assists researchers and analysts in categorizing keyword occurrences in ISP (Information Security Policy) documents as either Actionable Advice (AA) or Other Information (OI). It calculates the Keyword Loss of Specificity metric, as proposed by [Rostami & Karlsson (2024)](https://www.emerald.com/insight/content/doi/10.1108/ics-10-2023-0187/full/pdf).

    **To get started, upload an ISP document using the sidebar.**
    """)
    
    session_manager = initialize_app()
    setup_app_ui(session_manager)

if __name__ == "__main__":
    main()