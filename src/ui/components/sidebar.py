# src/ui/components/sidebar.py
import streamlit as st
from typing import Dict, List, Callable, Any, Optional
from src.config.settings import KeywordSets
from src.data.file.reader import FileReader
from src.domain.analyzer import SentenceExtractor
from src.domain.ai.classifier import BatchClassifier
from src.ui.utils import show_congratulations

def render_sidebar(on_file_upload: Callable, get_current_isp: Callable, session_manager) -> None:
    """Render the sidebar UI."""
    st.header("Settings")
    
    # Language selection
    st.subheader("Language")
    language_options = KeywordSets.get_available_languages()
    
    if not st.session_state.isps:
        selected_language = st.selectbox(
            "Select keyword language",
            language_options,
            index=language_options.index(st.session_state.language)
        )
        if selected_language != st.session_state.language:
            st.session_state.language = selected_language
            st.session_state.current_keyword = None
            st.session_state.current_sentences = []
            st.session_state.current_index = 0
            st.session_state.classifications = []
    else:
        st.info(f"Language: {st.session_state.language} (cannot change after adding ISPs)")
    
    # ISP Management
    st.subheader("ISP Management")
    
    with st.expander("Add New ISP", expanded=(st.session_state.current_isp_id is None)):
        new_isp_name = st.text_input(
            "ISP Name", 
            disabled=not st.session_state.file_uploaded,
            key="new_isp_name"
        )
        
        uploaded_file = st.file_uploader(
            "Choose an ISP file", 
            type=["txt", "pdf"], 
            key="new_isp_file",
            on_change=on_file_upload
        )
        
        if st.button("Add ISP"):
            handle_add_isp(new_isp_name, uploaded_file)
    
    # ISP Selection
    if st.session_state.isps:
        render_isp_selector(get_current_isp)
        
        # Keyword selection
        current_isp = get_current_isp()
        if current_isp:
            render_keyword_selector(current_isp)
            
            # AI-Assisted Analysis section
            render_ai_analysis_section(current_isp)
    
    # Save/Load Session
    render_session_panel(session_manager, get_current_isp)


def handle_add_isp(new_isp_name, uploaded_file):
    """Handle adding a new ISP document."""
    if not new_isp_name:
        st.error("Please enter an ISP name")
        return
    elif not uploaded_file:
        st.error("Please upload an ISP file")
        return

    existing_names = [isp.get('name', f"ISP {isp_id}") for isp_id, isp in st.session_state.isps.items()]
    if new_isp_name in existing_names:
        st.error(f"An ISP with the name '{new_isp_name}' already exists. Please choose a different name.")
        return

    # Extract text based on file type
    reader = FileReader.get_reader_for_type(uploaded_file.type)
    isp_text = reader.extract_text(uploaded_file)
    
    if isp_text:
        isp_id = st.session_state.next_isp_id
        st.session_state.isps[isp_id] = {
            'name': new_isp_name,
            'text': isp_text,
            'analysis_results': {}
        }
        st.session_state.analyzed_keywords[isp_id] = set()
        st.session_state.current_isp_id = isp_id
        st.session_state.current_keyword = None
        st.session_state.current_sentences = []
        st.session_state.current_index = 0
        st.session_state.classifications = []
        st.session_state.next_isp_id += 1
        st.session_state.file_uploaded = False
        st.session_state.uploaded_filename = ""
        st.rerun()


def render_isp_selector(get_current_isp):
    """Render ISP selection component."""
    st.subheader("Select ISP")
    isp_options = [(isp_id, data.get('name', f"ISP {isp_id}"))
                  for isp_id, data in st.session_state.isps.items()]
    selected_isp_index = 0
    if st.session_state.current_isp_id is not None:
        for i, (isp_id, _) in enumerate(isp_options):
            if isp_id == st.session_state.current_isp_id:
                selected_isp_index = i
                break
                
    selected_isp_id = st.selectbox(
        "Choose an ISP to analyze",
        [isp_id for isp_id, _ in isp_options],
        format_func=lambda x: next((name for id, name in isp_options if id == x), "Unknown"),
        index=selected_isp_index,
        key="isp_selector"
    )
    
    if selected_isp_id != st.session_state.current_isp_id:
        st.session_state.current_isp_id = selected_isp_id
        st.session_state.current_keyword = None
        st.session_state.current_sentences = []
        st.session_state.current_index = 0
        st.session_state.classifications = []
        st.rerun()


def render_keyword_selector(current_isp):
    """Render keyword selection component."""
    st.subheader("Select Keyword")
    
    # Set up keyword tracking if not already in session state
    if st.session_state.current_isp_id not in st.session_state.analyzed_keywords:
        st.session_state.analyzed_keywords[st.session_state.current_isp_id] = set()
    
    # Get all keywords and which ones have been analyzed
    keywords = KeywordSets.get_keywords(st.session_state.language)
    analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
    
    # Show progress
    analyzed = len(analyzed_for_isp)
    total = len(keywords)
    st.progress(analyzed / total if total > 0 else 0)
    st.write(f"Analyzed: {analyzed}/{total} keywords")
    
    # Check if all keywords are analyzed
    if analyzed == total:
        st.success("All keywords analyzed! 🎉")
    
    # Prepare keyword selection dropdown
    remaining_keywords = [k for k in keywords.keys() if k not in analyzed_for_isp]
    default_selected = remaining_keywords[0] if remaining_keywords else list(keywords.keys())[0]
    
    # If we don't have a current keyword, set to default
    if st.session_state.current_keyword is None:
        st.session_state.current_keyword = default_selected
    
    # Keyword selection dropdown
    selected_keyword = st.selectbox(
        "Select keyword to analyze",
        list(keywords.keys()),
        format_func=lambda x: f"{x} {' ✓' if x in analyzed_for_isp else ''}",
        index=list(keywords.keys()).index(st.session_state.current_keyword if st.session_state.current_keyword in keywords else default_selected)
    )
    
    if selected_keyword != st.session_state.current_keyword:
        st.info(f"Loading keyword: {selected_keyword}")
        st.session_state.current_keyword = selected_keyword
        st.session_state.current_sentences = SentenceExtractor.find_sentences_with_keyword(
            current_isp.get('text', ''), selected_keyword
        )
        st.write(f"Found {len(st.session_state.current_sentences)} sentences with '{selected_keyword}'")
        st.session_state.current_index = 0
        st.session_state.classifications = []
        
        if 'analysis_results' not in current_isp:
            current_isp['analysis_results'] = {}
        if selected_keyword not in current_isp['analysis_results']:
            current_isp['analysis_results'][selected_keyword] = {'AA': [], 'OI': []}
            
        if st.button("Start analyzing this keyword"):
            st.rerun()


def render_ai_analysis_section(current_isp):
    """Render AI-assisted analysis section."""
    if not current_isp:
        return
        
    st.subheader("AI-Assisted Analysis")
    
    # If any warning is active, show it instead of the buttons
    if st.session_state.show_ai_current_warning:
        st.warning(f"⚠️ WARNING: AI analysis of '{st.session_state.current_keyword}' may produce inaccurate classifications. Please review all results carefully after processing is complete.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancel", key="cancel_ai_current", use_container_width=True):
                st.session_state.show_ai_current_warning = False
                st.rerun()
        with c2:
            if st.button("I understand, proceed", key="confirm_ai_current", use_container_width=True):
                st.session_state.show_ai_current_warning = False
                st.session_state.ai_analysis_in_progress = True
                
                # Store the current keyword before analysis
                keyword_to_analyze = st.session_state.current_keyword
                
                with st.spinner(f"AI analyzing '{keyword_to_analyze}'..."):
                    handle_ai_analysis_for_keyword(current_isp, keyword_to_analyze)
                st.session_state.ai_analysis_in_progress = False
                
                # Check if all keywords are analyzed
                all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
                analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
                if len(analyzed_for_isp) == len(all_keywords):
                    show_congratulations()
                
                st.success(f"AI analysis of '{keyword_to_analyze}' complete! Please review the results.")
                st.rerun()
                
    elif st.session_state.show_ai_warning:
        st.warning("⚠️ WARNING: Bulk AI analysis may produce inaccurate classifications. Please review all results carefully after processing is complete.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancel", key="cancel_ai_all", use_container_width=True):
                st.session_state.show_ai_warning = False
                st.rerun()
        with c2:
            if st.button("I understand, proceed", key="confirm_ai_all", use_container_width=True):
                st.session_state.show_ai_warning = False
                st.session_state.ai_analysis_in_progress = True
                with st.spinner("AI analyzing all keywords..."):
                    keywords = KeywordSets.get_keywords(st.session_state.language)
                    all_keywords = list(keywords.keys())
                    remaining_keywords = [k for k in all_keywords if k not in st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())]
                    
                    # If there are remaining keywords, analyze the first one and set it as current
                    if remaining_keywords:
                        first_keyword = remaining_keywords[0]
                        handle_ai_analysis_for_keyword(current_isp, first_keyword)
                        # The rest can be processed in bulk
                        if len(remaining_keywords) > 1:
                            handle_ai_analysis_for_all_keywords(current_isp, remaining_keywords[1:])
                    
                st.session_state.ai_analysis_in_progress = False
                
                # Show congratulations after bulk analysis
                all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
                analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
                if len(analyzed_for_isp) == len(all_keywords):
                    show_congratulations()
                    
                st.success("AI analysis complete! Please review the results.")
                st.rerun()
                
    else:
        # Show the regular buttons if no warnings are active
        ai_col1, ai_col2 = st.columns(2)
        with ai_col1:
            if st.button("Analyze Current Keyword with AI", key="ai_current_button", use_container_width=True):
                st.session_state.show_ai_current_warning = True
                st.rerun()
        
        with ai_col2:
            if st.button("Analyze All Keywords with AI", key="ai_all_button", use_container_width=True):
                st.session_state.show_ai_warning = True
                st.rerun()


def handle_ai_analysis_for_keyword(current_isp, keyword):
    """Handle AI analysis for a specific keyword."""
    from src.domain.ai.classifier import BatchClassifier
    
    classifier = BatchClassifier()
    sentences = SentenceExtractor.find_sentences_with_keyword(current_isp.get('text', ''), keyword)
    
    if not sentences:
        st.warning(f"No sentences found with keyword '{keyword}'")
        if keyword not in current_isp['analysis_results']:
            current_isp['analysis_results'][keyword] = {'AA': [], 'OI': []}
        # Mark as analyzed even if no sentences found
        st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(keyword)
        return
    
    st.info(f"Found {len(sentences)} sentences containing keyword '{keyword}'")
    
    # Setup progress bar
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0, text="Initializing...")
    
    def update_progress(progress, text):
        progress_bar.progress(progress, text=text)
    
    # First, get classifications with rationales
    classification_results = []
    for i, item in enumerate(sentences):
        update_progress(i / len(sentences), f"Analyzing {i+1}/{len(sentences)}")
        result = classifier.classifier.get_classification_with_rationale(item, keyword)
        classification_results.append(result)
        update_progress((i + 1) / len(sentences), f"Completed {i+1}/{len(sentences)}")
    
    # Process results
    if keyword not in current_isp['analysis_results']:
        current_isp['analysis_results'][keyword] = {'AA': [], 'OI': []}
    
    aa_count = 0
    oi_count = 0
    
    for item, result in zip(sentences, classification_results):
        occurrence_id = f"{item['sentence']}::{item['start']}::{item['end']}"
        classification = result['classification']
        rationale = result['rationale']
        
        # Store metadata for this classification
        metadata_key = f"{st.session_state.current_isp_id}::{keyword}::{occurrence_id}"
        st.session_state.classification_metadata[metadata_key] = {
            "method": "AI",
            "rationale": rationale
        }
        
        if classification == "AA":
            aa_count += 1
            if occurrence_id not in current_isp['analysis_results'][keyword]['AA']:
                current_isp['analysis_results'][keyword]['AA'].append(occurrence_id)
            if occurrence_id in current_isp['analysis_results'][keyword]['OI']:
                current_isp['analysis_results'][keyword]['OI'].remove(occurrence_id)
        else:
            oi_count += 1
            if occurrence_id not in current_isp['analysis_results'][keyword]['OI']:
                current_isp['analysis_results'][keyword]['OI'].append(occurrence_id)
            if occurrence_id in current_isp['analysis_results'][keyword]['AA']:
                current_isp['analysis_results'][keyword]['AA'].remove(occurrence_id)
    
    # Clear progress bar
    progress_placeholder.empty()
    
    # Add keyword to analyzed keywords
    st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(keyword)
    
    # Set the current keyword and prepare the app to show results
    st.session_state.current_keyword = keyword
    st.session_state.current_sentences = sentences
    st.session_state.current_index = len(sentences)  # Set to end to trigger result display
    
    # Show summary
    st.success(f"Analysis complete for '{keyword}':\n"
              f"- Actionable Advice (AA): {aa_count}\n"
              f"- Other Information (OI): {oi_count}")


def handle_ai_analysis_for_all_keywords(current_isp, keywords):
    """Handle AI analysis for all remaining keywords."""
    if not keywords:
        return
        
    total = len(keywords)
    progress_placeholder = st.empty()
    progress_text = st.empty()
    
    for i, keyword in enumerate(keywords):
        progress_text.text(f"Analyzing keyword {i+1}/{total}: '{keyword}'")
        progress_placeholder.progress(i / total)
        
        # For all keywords except the last one, we just mark them as analyzed
        if i < total - 1:
            # Process the keyword but don't set it as current
            from src.domain.ai.classifier import BatchClassifier
            
            classifier = BatchClassifier()
            sentences = SentenceExtractor.find_sentences_with_keyword(current_isp.get('text', ''), keyword)
            
            if sentences:
                # Setup a simple progress indicator
                inner_progress = st.progress(0)
                
                # Classify sentences
                classifications = []
                for i, item in enumerate(sentences):
                    result = classifier.classifier.get_classification_with_rationale(item, keyword)
                    classifications.append(result)
                    inner_progress.progress((i + 1) / len(sentences))
                
                # Process results
                if keyword not in current_isp['analysis_results']:
                    current_isp['analysis_results'][keyword] = {'AA': [], 'OI': []}
                
                for item, result in zip(sentences, classifications):
                    occurrence_id = f"{item['sentence']}::{item['start']}::{item['end']}"
                    classification = result['classification']
                    rationale = result['rationale']
                    
                    # Store metadata for this classification
                    metadata_key = f"{st.session_state.current_isp_id}::{keyword}::{occurrence_id}"
                    st.session_state.classification_metadata[metadata_key] = {
                        "method": "AI",
                        "rationale": rationale
                    }
                    
                    if classification == "AA":
                        if occurrence_id not in current_isp['analysis_results'][keyword]['AA']:
                            current_isp['analysis_results'][keyword]['AA'].append(occurrence_id)
                        if occurrence_id in current_isp['analysis_results'][keyword]['OI']:
                            current_isp['analysis_results'][keyword]['OI'].remove(occurrence_id)
                    else:
                        if occurrence_id not in current_isp['analysis_results'][keyword]['OI']:
                            current_isp['analysis_results'][keyword]['OI'].append(occurrence_id)
                        if occurrence_id in current_isp['analysis_results'][keyword]['AA']:
                            current_isp['analysis_results'][keyword]['AA'].remove(occurrence_id)
            else:
                # No sentences found
                if keyword not in current_isp['analysis_results']:
                    current_isp['analysis_results'][keyword] = {'AA': [], 'OI': []}
            
            # Mark as analyzed
            st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(keyword)
        else:
            # For the last keyword, use the standard function to process it
            # This will set it as the current keyword for display
            handle_ai_analysis_for_keyword(current_isp, keyword)
        
    progress_placeholder.empty()
    progress_text.empty()
    
    # Check if all keywords have been analyzed and show congratulations
    all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
    analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
    
    if len(analyzed_for_isp) == len(all_keywords):
        show_congratulations()


def render_session_panel(session_manager, get_current_isp):
    """Render session save/load panel."""
    st.subheader("Save/Load Session")

    with st.container():
        st.markdown("""
        <style>
        .session-container {
            background-color: rgba(20, 20, 30, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 5px;
        }
        .btn-session {
            margin-bottom: 10px;
        }
        </style>
        <div class="session-container"></div>
        """, unsafe_allow_html=True)
        
        # Save Session
        st.text("Save Session")
        if st.button("Save Analysis", key="save_btn", use_container_width=True):
            timestamp = session_manager.save_current_session()
            st.success(f"Session saved at {timestamp}")
        
        saved_sessions = session_manager.get_available_sessions()
        if saved_sessions:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            st.text("Load Session")
            session_options = {f"ID: {sid} at {ts}": sid for sid, ts in saved_sessions}
            selected_session_display = st.selectbox(
                "Select saved session", 
                list(session_options.keys()), 
                key="session_select",
                label_visibility="collapsed"
            )
            selected_session_id = session_options[selected_session_display]
            
            if st.button("Continue Analysis", key="load_btn", use_container_width=True):
                if session_manager.load_session(selected_session_id):
                    st.success("Session loaded successfully!")
                    current_isp = get_current_isp()
                    if current_isp:
                        st.info(f"Selected ISP: {current_isp.get('name', f'ISP {st.session_state.current_isp_id}')}")
                    if st.button("Start Analysis", key="continue_btn"):
                        st.rerun()
        else:
            st.info("No saved sessions found.")
        
        st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        
        if st.button("Reset Analysis", key="reset_btn", 
                use_container_width=True, 
                help="WARNING: This will clear all your analysis data!",
                type="primary"):
            st.session_state.isps = {}
            st.session_state.current_isp_id = None
            st.session_state.next_isp_id = 1
            st.session_state.current_keyword = None
            st.session_state.current_sentences = []
            st.session_state.current_index = 0
            st.session_state.classifications = []
            st.session_state.analyzed_keywords = {}
            st.rerun()
        
        st.markdown("""
        <style>
        [data-testid="stButton"] > button[kind="primary"] {
            background-color: #cc0000;
            color: white;
        }
        [data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #aa0000;
            border: 1px solid white;
        }
        </style>
        """, unsafe_allow_html=True)