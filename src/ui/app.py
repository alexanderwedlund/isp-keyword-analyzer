# src/ui/app.py
import streamlit as st
from typing import Dict, Any

from src.domain.analyzer import SentenceExtractor
from src.domain.metrics import MetricsCalculator
from src.domain.ai.classifier import SentenceClassifier, BatchClassifier
from src.config.settings import KeywordSets
from src.ui.components.sidebar import render_sidebar
from src.ui.pages.analysis import render_sentence_analysis_ui, render_analysis_complete_ui
from src.ui.pages.upload import render_upload_ui
from src.ui.pages.export import render_export_ui
from src.ui.utils import show_congratulations

def setup_app_ui(session_manager):
    """Setup the main application UI."""
    # Create instances of key services
    classifier = SentenceClassifier()
    batch_classifier = BatchClassifier()
    
    # Define utility functions
    def on_file_upload():
        """Callback when a file is uploaded to set the ISP name."""
        if st.session_state.new_isp_file is not None:
            filename = st.session_state.new_isp_file.name
            filename_without_ext = filename.rsplit(".", 1)[0] if "." in filename else filename
            st.session_state.uploaded_filename = filename_without_ext
            st.session_state.file_uploaded = True
            st.session_state.new_isp_name = filename_without_ext
        else:
            st.session_state.file_uploaded = False
            st.session_state.uploaded_filename = ""
    
    def get_current_isp():
        """Get the currently selected ISP data."""
        if st.session_state.current_isp_id is None:
            return None
        try:
            st.session_state.current_isp_id = int(st.session_state.current_isp_id)
        except ValueError:
            st.error(f"Invalid ISP ID: {st.session_state.current_isp_id}")
            return None
        return st.session_state.isps.get(st.session_state.current_isp_id)
    
    # Render sidebar
    render_sidebar(on_file_upload, get_current_isp, session_manager)
    
    # Main content area
    # AI processing status indicator
    if st.session_state.ai_analysis_in_progress:
        st.info("AI analysis in progress... Please wait.")
    
    # Get current ISP
    current_isp = get_current_isp()
    
    # Main content logic
    if current_isp and st.session_state.current_keyword:
        # Make sure sentences are loaded
        if not st.session_state.current_sentences:
            st.session_state.current_sentences = SentenceExtractor.find_sentences_with_keyword(
                current_isp.get('text', ''), st.session_state.current_keyword
            )
        
        # Make sure keyword is in analysis_results
        if 'analysis_results' not in current_isp:
            current_isp['analysis_results'] = {}
        if st.session_state.current_keyword not in current_isp['analysis_results']:
            current_isp['analysis_results'][st.session_state.current_keyword] = {'AA': [], 'OI': []}
            
        # Sentence analysis UI
        if len(st.session_state.current_sentences) > 0:
            if st.session_state.current_index < len(st.session_state.current_sentences):
                render_sentence_analysis_ui(current_isp, classifier)
            else:
                render_analysis_complete_ui(current_isp)
        else:
            # No sentences found - automatic analysis complete
            st.info(f"No sentences with '{st.session_state.current_keyword}' were found.")
            
            # Mark this keyword as analyzed
            st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(st.session_state.current_keyword)
            
            # Check if all keywords have been analyzed
            all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
            analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
            
            if len(analyzed_for_isp) == len(all_keywords):
                show_congratulations()
            
            # Next keyword button
            if st.button("Next keyword"):
                next_keyword = get_next_keyword(all_keywords, analyzed_for_isp, st.session_state.current_keyword)
                if next_keyword:
                    st.session_state.current_keyword = next_keyword
                    st.session_state.current_sentences = SentenceExtractor.find_sentences_with_keyword(
                        current_isp.get('text', ''), next_keyword
                    )
                    st.session_state.current_index = 0
                    st.session_state.classifications = []
                    
                    if 'analysis_results' not in current_isp:
                        current_isp['analysis_results'] = {}
                    if next_keyword not in current_isp['analysis_results']:
                        current_isp['analysis_results'][next_keyword] = {'AA': [], 'OI': []}
                    
                    st.rerun()
            
    elif current_isp and not st.session_state.current_keyword:
        st.info("Select a keyword from the sidebar to begin analysis.")
    elif not current_isp:
        render_upload_ui()
    
    # Analysis results section (if applicable)
    if st.session_state.isps and any(isp.get('analysis_results') for isp in st.session_state.isps.values()):
        render_export_ui(st.session_state.isps, st.session_state.language)

def get_next_keyword(all_keywords, analyzed_keywords, current_keyword):
    """Get the next keyword to analyze."""
    if current_keyword is None:
        for kw in all_keywords:
            if kw not in analyzed_keywords:
                return kw
        return all_keywords[0] if all_keywords else None
        
    try:
        current_index = all_keywords.index(current_keyword)
    except ValueError:
        return all_keywords[0] if all_keywords else None
        
    # Try to find a keyword that hasn't been analyzed yet
    for i in range(current_index + 1, len(all_keywords)):
        if all_keywords[i] not in analyzed_keywords:
            return all_keywords[i]
            
    for i in range(0, current_index):
        if all_keywords[i] not in analyzed_keywords:
            return all_keywords[i]
            
    # If all keywords have been analyzed, just move to the next one
    return all_keywords[(current_index + 1) % len(all_keywords)]