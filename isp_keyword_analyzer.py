# isp_analyzer.py
# This is the main Streamlit application file that contains the UI logic.
import streamlit as st
import pandas as pd

from config import KEYWORDS_SETS
from db import SessionDB
from file_processor import FileProcessor
from analyzer import Analyzer
from exporter import Exporter

# Initialize the SQLite database
SessionDB.init_db()

# Set the page configuration (must be set before other Streamlit calls)
st.set_page_config(page_title="ISP Keyword Analyzer", layout="wide")

# Application title and description
st.title("ISP Keyword Analyzer")
st.markdown("""
### A Tool for Analyzing ISP Documents to Measure Keyword Loss of Specificity

This application assists researchers and analysts in categorizing keyword occurrences in ISP (Information Security Policy) documents as either Actionable Advice (AA) or Other Information (OI). It calculates the Keyword Loss of Specificity metric, as proposed by [Rostami & Karlsson (2024)](https://www.emerald.com/insight/content/doi/10.1108/ics-10-2023-0187/full/pdf).

**To get started, upload an ISP document using the sidebar.**
""")

# Initialize Streamlit session state variables if they are not already defined
if 'isps' not in st.session_state:
    st.session_state.isps = {}  # {isp_id: {name, text, analysis_results}}
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
    st.session_state.analyzed_keywords = {}  # {isp_id: set(keywords)}
if 'language' not in st.session_state:
    st.session_state.language = "Swedish"  # Default language
if 'show_context' not in st.session_state:
    st.session_state.show_context = False

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

# Sidebar UI
col_sidebar, col_main = st.columns([1, 3])

with col_sidebar:
    st.header("Settings")
    
    # Language selection (only allowed if no ISPs exist)
    st.subheader("Language")
    language_options = list(KEYWORDS_SETS.keys())
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
    
    keywords = KEYWORDS_SETS[st.session_state.language]
    
    # ISP Management
    st.subheader("ISP Management")
    
    with st.expander("Add New ISP", expanded=(st.session_state.current_isp_id is None)):
        new_isp_name = st.text_input("ISP Name", key="new_isp_name")
        uploaded_file = st.file_uploader("Choose an ISP file", type=["txt", "pdf"], key="new_isp_file")
        
        if st.button("Add ISP"):
            if not new_isp_name:
                st.error("Please enter an ISP name")
            elif not uploaded_file:
                st.error("Please upload an ISP file")
            else:
                isp_text = ""
                if uploaded_file.type == "text/plain":
                    isp_text = FileProcessor.read_text_file(uploaded_file)
                elif uploaded_file.type == "application/pdf":
                    isp_text = FileProcessor.extract_text_from_pdf(uploaded_file)
                if isp_text:
                    isp_id = st.session_state.next_isp_id
                    st.session_state.isps[isp_id] = {
                        'name': new_isp_name,
                        'text': isp_text,
                        'analysis_results': {}
                    }
                    st.session_state.analyzed_keywords[isp_id] = set()
                    st.session_state.current_isp_id = isp_id
                    st.session_state.next_isp_id += 1
                    st.rerun()
    
    if st.session_state.isps:
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
            if st.button("Select this ISP"):
                st.rerun()
    
    # Keyword selection
    current_isp = get_current_isp()
    if current_isp:
        st.subheader("Select Keyword")
        if st.session_state.current_isp_id not in st.session_state.analyzed_keywords:
            st.session_state.analyzed_keywords[st.session_state.current_isp_id] = set()
        analyzed = len(st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set()))
        total = len(keywords)
        st.progress(analyzed / total if total > 0 else 0)
        st.write(f"Analyzed: {analyzed}/{total} keywords")
        analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
        remaining_keywords = [k for k in keywords.keys() if k not in analyzed_for_isp]
        default_selected = remaining_keywords[0] if remaining_keywords else list(keywords.keys())[0]
        selected_keyword = st.selectbox(
            "Select keyword to analyze",
            list(keywords.keys()),
            format_func=lambda x: f"{x} {' ✓' if x in analyzed_for_isp else ''}",
            index=list(keywords.keys()).index(default_selected)
        )
        if selected_keyword != st.session_state.current_keyword:
            st.info(f"Loading keyword: {selected_keyword}")
            st.session_state.current_keyword = selected_keyword
            st.session_state.current_sentences = Analyzer.find_sentences_with_keyword(
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
    
    # Save/Load Session
    st.subheader("Save/Load Session")
    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("Save Session"):
            timestamp = SessionDB.save_session()
            st.success(f"Session saved at {timestamp}")
    with col_load:
        saved_sessions = SessionDB.get_sessions()
        if saved_sessions:
            session_options = {f"ID: {sid} at {ts}": sid for sid, ts in saved_sessions}
            selected_session_display = st.selectbox("Select session to load", list(session_options.keys()))
            selected_session_id = session_options[selected_session_display]
            if st.button("Load Session"):
                if SessionDB.load_session(selected_session_id):
                    st.success("Session loaded successfully!")
                    current_isp = get_current_isp()
                    if current_isp:
                        st.info(f"Currently selected ISP: {current_isp.get('name', f'ISP {st.session_state.current_isp_id}')}")
                    if st.button("Continue Analysis"):
                        st.rerun()
        else:
            st.info("No saved sessions found.")
    
    if st.button("Reset Analysis"):
        st.session_state.isps = {}
        st.session_state.current_isp_id = None
        st.session_state.next_isp_id = 1
        st.session_state.current_keyword = None
        st.session_state.current_sentences = []
        st.session_state.current_index = 0
        st.session_state.classifications = []
        st.session_state.analyzed_keywords = {}
        st.rerun()

# Main content area
with col_main:
    current_isp = get_current_isp()
    if current_isp and st.session_state.current_keyword:
        st.header(f"Analyzing '{st.session_state.current_keyword}' in {current_isp.get('name', f'ISP {st.session_state.current_isp_id}')}")
        total_sentences = len(st.session_state.current_sentences)
        if total_sentences > 0:
            if st.session_state.current_index < total_sentences:
                st.progress(st.session_state.current_index / total_sentences)
                st.write(f"Sentence {st.session_state.current_index + 1} of {total_sentences}")
                st.markdown("### Current sentence:")
                current_item = st.session_state.current_sentences[st.session_state.current_index]
                current_sentence = current_item['sentence']
                start_pos = current_item['start']
                end_pos = current_item['end']
                before_match = current_sentence[:start_pos]
                match_text = current_sentence[start_pos:end_pos]
                after_match = current_sentence[end_pos:]
                highlighted_sentence = (
                    f"{before_match}"
                    f"<span style=\"background-color: #ff0000; font-weight: bold; padding: 0 2px; border-radius: 3px; color: white;\">{match_text}</span>"
                    f"{after_match}"
                )
                st.markdown(highlighted_sentence, unsafe_allow_html=True)
                occurrence_count = sum(1 for i, item in enumerate(st.session_state.current_sentences)
                                       if i < st.session_state.current_index and item['sentence'] == current_sentence) + 1
                st.write(f"Occurrence {occurrence_count} of keyword \"{st.session_state.current_keyword}\" in this sentence")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Actionable Advice (AA)", key="aa_button", use_container_width=True):
                        occurrence_id = f"{current_item['sentence']}::{current_item['start']}::{current_item['end']}"
                        if occurrence_id not in current_isp['analysis_results'][st.session_state.current_keyword]['AA']:
                            current_isp['analysis_results'][st.session_state.current_keyword]['AA'].append(occurrence_id)
                        if occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['OI']:
                            current_isp['analysis_results'][st.session_state.current_keyword]['OI'].remove(occurrence_id)
                        st.session_state.classifications.append(('AA', occurrence_id))
                        st.session_state.current_index += 1
                        st.rerun()
                with col2:
                    if st.button("Other Information (OI)", key="oi_button", use_container_width=True):
                        occurrence_id = f"{current_item['sentence']}::{current_item['start']}::{current_item['end']}"
                        if occurrence_id not in current_isp['analysis_results'][st.session_state.current_keyword]['OI']:
                            current_isp['analysis_results'][st.session_state.current_keyword]['OI'].append(occurrence_id)
                        if occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['AA']:
                            current_isp['analysis_results'][st.session_state.current_keyword]['AA'].remove(occurrence_id)
                        st.session_state.classifications.append(('OI', occurrence_id))
                        st.session_state.current_index += 1
                        st.rerun()
                with col3:
                    if st.button("Context", key="context_button", use_container_width=True):
                        st.session_state.show_context = not st.session_state.show_context
                        st.rerun()
                if st.session_state.show_context:
                    st.markdown("### Sentence Context:")
                    context_item = st.session_state.current_sentences[st.session_state.current_index]
                    st.markdown(
                        "<div style='margin:10px 0; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
                        f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px;'>"
                        f"<strong>Previous:</strong> {context_item.get('before_context', '')}</div><br/>"
                        f"<strong>Current:</strong> {highlighted_sentence}<br/>"
                        f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px;'>"
                        f"<strong>Next:</strong> {context_item.get('after_context', '')}</div>"
                        "</div>",
                        unsafe_allow_html=True
                    )
                col_back, col_forward = st.columns(2)
                with col_back:
                    if st.button("Back", key="back_button", use_container_width=True) and st.session_state.current_index > 0:
                        st.session_state.current_index -= 1
                        st.rerun()
                with col_forward:
                    if st.button("Forward", key="forward_button", use_container_width=True) and st.session_state.current_index < total_sentences - 1:
                        occurrence_id = f"{current_item['sentence']}::{current_item['start']}::{current_item['end']}"
                        is_classified = (occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['AA'] or 
                                         occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['OI'])
                        if is_classified:
                            st.session_state.current_index += 1
                            st.rerun()
                        else:
                            st.warning("Please classify the current sentence before moving forward.")
            else:
                st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(st.session_state.current_keyword)
                st.success(f"All {total_sentences} sentences with '{st.session_state.current_keyword}' have been classified!")
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Actionable Advice (AA)")
                    st.write(f"Count: {len(current_isp['analysis_results'][st.session_state.current_keyword]['AA'])}")
                with col2:
                    st.subheader("Other Information (OI)")
                    st.write(f"Count: {len(current_isp['analysis_results'][st.session_state.current_keyword]['OI'])}")
                aa_count = len(current_isp['analysis_results'][st.session_state.current_keyword]['AA'])
                oi_count = len(current_isp['analysis_results'][st.session_state.current_keyword]['OI'])
                total_count = aa_count + oi_count
                if total_count > 0:
                    loss_specificity = (oi_count / total_count) * 100
                    st.write(f"### Keyword Loss of Specificity: {loss_specificity:.2f}%")
                with st.expander("Show all Actionable Advice sentences"):
                    for i, occ in enumerate(current_isp['analysis_results'][st.session_state.current_keyword]['AA']):
                        parts = occ.split("::")
                        if len(parts) >= 3:
                            sentence = parts[0]
                            start = int(parts[1])
                            end = int(parts[2])
                            highlighted = (
                                f"{sentence[:start]}"
                                f"<span style='background-color: #ff0000; font-weight: bold; color: white;'>{sentence[start:end]}</span>"
                                f"{sentence[end:]}"
                            )
                            st.markdown(f"{i+1}. {highlighted}", unsafe_allow_html=True)
                with st.expander("Show all Other Information sentences"):
                    for i, occ in enumerate(current_isp['analysis_results'][st.session_state.current_keyword]['OI']):
                        parts = occ.split("::")
                        if len(parts) >= 3:
                            sentence = parts[0]
                            start = int(parts[1])
                            end = int(parts[2])
                            highlighted = (
                                f"{sentence[:start]}"
                                f"<span style='background-color: #ff0000; font-weight: bold; color: white;'>{sentence[start:end]}</span>"
                                f"{sentence[end:]}"
                            )
                            st.markdown(f"{i+1}. {highlighted}", unsafe_allow_html=True)
                def get_next_keyword(current_keyword, all_keywords, analyzed_keywords):
                    if current_keyword is None:
                        for kw in all_keywords:
                            if kw not in analyzed_keywords:
                                return kw
                        return all_keywords[0] if all_keywords else None
                    try:
                        current_index = all_keywords.index(current_keyword)
                    except ValueError:
                        return all_keywords[0] if all_keywords else None
                    for i in range(current_index + 1, len(all_keywords)):
                        if all_keywords[i] not in analyzed_keywords:
                            return all_keywords[i]
                    for i in range(0, current_index):
                        if all_keywords[i] not in analyzed_keywords:
                            return all_keywords[i]
                    return all_keywords[(current_index + 1) % len(all_keywords)]
                if st.button("Next keyword"):
                    all_keywords = list(keywords.keys())
                    analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
                    next_keyword = get_next_keyword(st.session_state.current_keyword, all_keywords, analyzed_for_isp)
                    if next_keyword:
                        st.session_state.current_keyword = next_keyword
                        st.session_state.current_sentences = Analyzer.find_sentences_with_keyword(
                            current_isp.get('text', ''), next_keyword
                        )
                        st.session_state.current_index = 0
                        st.session_state.classifications = []
                        if 'analysis_results' not in current_isp:
                            current_isp['analysis_results'] = {}
                        if next_keyword not in current_isp['analysis_results']:
                            current_isp['analysis_results'][next_keyword] = {'AA': [], 'OI': []}
                        st.rerun()
        else:
            st.info(f"No sentences with '{st.session_state.current_keyword}' were found.")
            st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(st.session_state.current_keyword)
            if st.button("Next keyword"):
                all_keywords = list(keywords.keys())
                analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
                current_index = all_keywords.index(st.session_state.current_keyword) if st.session_state.current_keyword in all_keywords else -1
                next_keyword = None
                for i in range(current_index + 1, len(all_keywords)):
                    if all_keywords[i] not in analyzed_for_isp:
                        next_keyword = all_keywords[i]
                        break
                if next_keyword is None:
                    for i in range(0, current_index):
                        if all_keywords[i] not in analyzed_for_isp:
                            next_keyword = all_keywords[i]
                            break
                if next_keyword is None:
                    next_keyword = all_keywords[(current_index + 1) % len(all_keywords)]
                st.session_state.current_keyword = next_keyword
                st.session_state.current_sentences = Analyzer.find_sentences_with_keyword(
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
        st.info("Add a new ISP or select an existing one to start analysis.")
        st.markdown("""
        ## Instructions

        1. **Add a new ISP**: Enter an ISP name and upload the document
        2. **Select a keyword**: Choose a specific keyword from the predefined list for analysis, or proceed with the default first keyword that appears in the selection menu
        3. **Classify sentences**: Mark each sentence as either:
           - **Actionable Advice (AA)**
           - **Other Information (OI)**
        4. **Use context when needed**: Toggle the Context button to view surrounding sentences (previous and next) for better understanding of how the keyword is used in its larger textual environment
        5. **Save your progress**: You can save your session anytime
        6. **Export data**: Generate an Excel file with analysis results
        """)
    
    if st.session_state.isps and any(isp.get('analysis_results') for isp in st.session_state.isps.values()):
        st.header("Analysis Results")
        all_metrics = Analyzer.calculate_all_metrics(st.session_state.isps, st.session_state.language)
        if all_metrics:
            st.subheader("Table 1: Total Keyword Loss of Specificity")
            table1_data = []
            for isp_id, metrics in all_metrics.items():
                if metrics:
                    isp_data = st.session_state.isps[isp_id]
                    table1_data.append({
                        'ISP': isp_id,
                        'ISP Name': isp_data.get('name', f"ISP {isp_id}"),
                        'Actionable advice': metrics['total_aa'],
                        'Other information': metrics['total_oi'],
                        'Total': metrics['total_count'],
                        'Total keyword loss of specificity (%)': f"{metrics['total_loss_specificity']:.1f}%"
                    })
            if table1_data:
                st.table(pd.DataFrame(table1_data))
        st.subheader("Export Results")
        st.markdown(Exporter.to_excel(st.session_state.isps, st.session_state.language), unsafe_allow_html=True)