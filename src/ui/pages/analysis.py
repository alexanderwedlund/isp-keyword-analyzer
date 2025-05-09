import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from src.domain.analyzer import SentenceExtractor
from src.domain.ai.classifier import SentenceClassifier
from src.config.settings import KeywordSets
from src.ui.utils import show_congratulations

def render_sentence_analysis_ui(current_isp: Dict[str, Any], classifier: SentenceClassifier) -> None:
    """Render the UI for analyzing individual sentences."""
    if not current_isp or not st.session_state.current_keyword:
        return
        
    st.header(f"Analyzing '{st.session_state.current_keyword}' in {current_isp.get('name', f'ISP {st.session_state.current_isp_id}')}")
    total_sentences = len(st.session_state.current_sentences)
    
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
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("Actionable Advice (AA)", key="aa_button", use_container_width=True):
            handle_classification(current_isp, current_item, "AA", method="Manual")
            
    with col2:
        if st.button("Other Information (OI)", key="oi_button", use_container_width=True):
            handle_classification(current_isp, current_item, "OI", method="Manual")
            
    with col3:
        if st.button("Context", key="context_button", use_container_width=True):
            st.session_state.show_context = not st.session_state.show_context
            st.rerun()
            
    with col4:
        if st.button("Suggestion", key="suggestion_button", use_container_width=True, 
                     disabled=not st.session_state.get("ai_available", False)):
            st.session_state.suggestion_in_progress = True
            st.session_state.current_suggestion = None
            st.rerun()
            
    with col5:
        if st.button("Skip", key="skip_button", use_container_width=True):
            if st.session_state.current_index < len(st.session_state.current_sentences):
                st.session_state.current_sentences.pop(st.session_state.current_index)
                if st.session_state.current_index >= len(st.session_state.current_sentences):
                    st.session_state.current_index = max(0, len(st.session_state.current_sentences) - 1)
                st.session_state.current_suggestion = None 
                st.session_state.suggestion_in_progress = False
                st.rerun()
    
    if st.session_state.suggestion_in_progress:
        if not st.session_state.get("ai_available", False):
            st.error("AI suggestion is not available because the llama-cpp-python library is not installed.")
            st.session_state.suggestion_in_progress = False
        else:
            render_suggestion_ui(current_isp, current_item, classifier)
    
    if st.session_state.show_context:
        render_context_ui(current_item)
    
    col_back, col_forward = st.columns(2)
    with col_back:
        if st.button("Back", key="back_button", use_container_width=True) and st.session_state.current_index > 0:
            st.session_state.current_index -= 1
            st.session_state.current_suggestion = None
            st.session_state.suggestion_in_progress = False
            st.rerun()
    with col_forward:
        if st.button("Forward", key="forward_button", use_container_width=True) and st.session_state.current_index < total_sentences - 1:
            occurrence_id = f"{current_item['sentence']}::{current_item['start']}::{current_item['end']}"
            is_classified = (occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['AA'] or 
                             occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['OI'])
            if is_classified:
                st.session_state.current_index += 1
                st.session_state.current_suggestion = None
                st.session_state.suggestion_in_progress = False
                st.rerun()
            else:
                st.warning("Please classify the current sentence before moving forward.")


def handle_classification(current_isp: Dict[str, Any], current_item: Dict[str, Any], classification: str, method: str = "Manual", rationale: str = None) -> None:
    """Handle classification of a sentence.
    
    Args:
        current_isp: Dictionary containing current ISP data
        current_item: Dictionary with current sentence data
        classification: Classification category ("AA" or "OI")
        method: Method used for classification ("Manual", "AI", or "Suggestion")
        rationale: Rationale for classification (if provided by AI)
    """
    occurrence_id = f"{current_item['sentence']}::{current_item['start']}::{current_item['end']}"
    
    if 'analysis_results' not in current_isp:
        current_isp['analysis_results'] = {}
    if st.session_state.current_keyword not in current_isp['analysis_results']:
        current_isp['analysis_results'][st.session_state.current_keyword] = {'AA': [], 'OI': []}
    
    if classification == "AA":
        if occurrence_id not in current_isp['analysis_results'][st.session_state.current_keyword]['AA']:
            current_isp['analysis_results'][st.session_state.current_keyword]['AA'].append(occurrence_id)
        if occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['OI']:
            current_isp['analysis_results'][st.session_state.current_keyword]['OI'].remove(occurrence_id)
    else:  # OI
        if occurrence_id not in current_isp['analysis_results'][st.session_state.current_keyword]['OI']:
            current_isp['analysis_results'][st.session_state.current_keyword]['OI'].append(occurrence_id)
        if occurrence_id in current_isp['analysis_results'][st.session_state.current_keyword]['AA']:
            current_isp['analysis_results'][st.session_state.current_keyword]['AA'].remove(occurrence_id)
    
    metadata_key = f"{st.session_state.current_isp_id}::{st.session_state.current_keyword}::{occurrence_id}"
    st.session_state.classification_metadata[metadata_key] = {
        "method": method,
        "rationale": rationale
    }
    
    st.session_state.classifications.append((classification, occurrence_id))
    st.session_state.current_index += 1
    st.session_state.current_suggestion = None
    st.session_state.suggestion_in_progress = False
    
    if st.session_state.current_index >= len(st.session_state.current_sentences):
        st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(st.session_state.current_keyword)
        
        all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
        analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
        if len(analyzed_for_isp) == len(all_keywords):
            show_congratulations()
    
    st.rerun()


def render_suggestion_ui(current_isp: Dict[str, Any], current_item: Dict[str, Any], classifier: SentenceClassifier) -> None:
    """Render the suggestion UI."""
    if not st.session_state.current_suggestion:
        with st.spinner("Analyzing sentence..."):
            st.session_state.current_suggestion = classifier.get_classification_with_rationale(
                current_item, 
                st.session_state.current_keyword
            )
    
    if st.session_state.current_suggestion:
        suggestion = st.session_state.current_suggestion
        classification = suggestion["classification"]
        rationale = suggestion["rationale"]
        
        if classification == "AA":
            box_color = "#1E6823"
            text_color = "white"
        else:
            box_color = "#A93226"
            text_color = "white"
        
        st.markdown(f"""
        <div style="margin: 15px 0; padding: 10px; border-radius: 5px; background-color: {box_color}; color: {text_color};">
            <h3 style="margin-top: 0;">Suggested Classification: {classification}</h3>
            <p><strong>Rationale:</strong> {rationale}</p>
        </div>
        """, unsafe_allow_html=True)
        
        accept_col1, accept_col2 = st.columns(2)
        with accept_col1:
            if st.button("Accept Suggestion", key="accept_suggestion", use_container_width=True):
                handle_classification(current_isp, current_item, classification, method="Suggestion", 
                                    rationale=rationale)
        with accept_col2:
            if st.button("Cancel", key="cancel_suggestion", use_container_width=True):
                st.session_state.current_suggestion = None
                st.session_state.suggestion_in_progress = False
                st.rerun()


def render_context_ui(current_item: Dict[str, Any]) -> None:
    """Render the context UI."""
    context_col1, context_col2 = st.columns(2)
    with context_col1:
        context_mode = st.radio(
            "Context Mode:",
            ["Normal (1 sentence)", "Extended (5 sentences)"],
            horizontal=True,
            index=0 if st.session_state.context_mode == "normal" else 1
        )
        st.session_state.context_mode = "normal" if context_mode == "Normal (1 sentence)" else "extended"
    
    st.markdown("### Sentence Context:")
    
    if st.session_state.context_mode == "normal":
        st.markdown(
            "<div style='margin:10px 0; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
            f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px;'>"
            f"<strong>Previous:</strong> {current_item.get('before_context', '')}</div><br/>"
            f"<strong>Current:</strong> {current_item['sentence']}<br/>"
            f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px;'>"
            f"<strong>Next:</strong> {current_item.get('after_context', '')}</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        extended_before = current_item.get('extended_before_context', [])
        extended_after = current_item.get('extended_after_context', [])
        
        context_html = "<div style='margin:10px 0; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
        
        context_html += "<div style='background-color: #333333; color: white; padding: 5px; border-radius: 3px; margin-bottom: 10px;'>"
        context_html += "<strong>Extended Context (Before):</strong></div>"
        
        for sentence in extended_before:
            context_html += f"<div style='background-color: #994d00; color: white; padding: 5px; margin-bottom: 5px;'>{sentence}</div>"
        
        context_html += f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px; margin: 10px 0;'>"
        context_html += f"<strong>Previous:</strong> {current_item.get('before_context', '')}</div>"
        
        context_html += f"<div style='margin: 10px 0;'><strong>Current:</strong> {current_item['sentence']}</div>"
        
        context_html += f"<div style='background-color: #530003; color: white; padding: 5px; border-radius: 3px; margin: 10px 0;'>"
        context_html += f"<strong>Next:</strong> {current_item.get('after_context', '')}</div>"
        
        context_html += "<div style='background-color: #333333; color: white; padding: 5px; border-radius: 3px; margin-top: 10px;'>"
        context_html += "<strong>Extended Context (After):</strong></div>"
        
        for sentence in extended_after:
            context_html += f"<div style='background-color: #994d00; color: white; padding: 5px; margin-top: 5px;'>{sentence}</div>"
        
        context_html += "</div>"
        
        st.markdown(context_html, unsafe_allow_html=True)


def render_analysis_complete_ui(current_isp: Dict[str, Any]) -> None:
    """Render the UI when analysis is complete."""
    st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(st.session_state.current_keyword)
    st.success(f"All {len(st.session_state.current_sentences)} sentences with '{st.session_state.current_keyword}' have been classified!")
    
    all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
    analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())

    if len(analyzed_for_isp) == len(all_keywords):
        show_congratulations()
    
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
        render_classified_sentences(current_isp, "AA")
        
    with st.expander("Show all Other Information sentences"):
        render_classified_sentences(current_isp, "OI")
    
    with st.expander("Show Raw Data for current keyword", expanded=False):
        render_current_keyword_raw_data(current_isp)
    
    render_next_keyword_button()

def render_current_keyword_raw_data(current_isp: Dict[str, Any]) -> None:
    """Render raw data table only for the current keyword."""
    if 'analysis_results' not in current_isp or st.session_state.current_keyword not in current_isp['analysis_results']:
        st.info("No analysis data available.")
        return
        
    data = []
    keyword = st.session_state.current_keyword
    isp_id = st.session_state.current_isp_id
    
    for occurrence in current_isp['analysis_results'][keyword].get('AA', []):
        parts = occurrence.split("::")
        if len(parts) >= 3:
            sentence = parts[0]
            start_pos = int(parts[1])
            end_pos = int(parts[2])
            keyword_instance = sentence[start_pos:end_pos]
            
            highlighted_sentence = (
                sentence[:start_pos] +
                '[' + keyword_instance + ']' +
                sentence[end_pos:]
            )
            
            metadata_key = f"{isp_id}::{keyword}::{occurrence}"
            metadata = st.session_state.classification_metadata.get(metadata_key, {})
            method = metadata.get("method", "Manual")
            rationale = metadata.get("rationale", "")
            
            data.append({
                'Classification': 'AA',
                'Sentence': highlighted_sentence,
                'Keyword Instance': keyword_instance,
                'Method': method,
                'Rationale': rationale
            })
    
    for occurrence in current_isp['analysis_results'][keyword].get('OI', []):
        parts = occurrence.split("::")
        if len(parts) >= 3:
            sentence = parts[0]
            start_pos = int(parts[1])
            end_pos = int(parts[2])
            keyword_instance = sentence[start_pos:end_pos]
            
            highlighted_sentence = (
                sentence[:start_pos] +
                '[' + keyword_instance + ']' +
                sentence[end_pos:]
            )
            
            metadata_key = f"{isp_id}::{keyword}::{occurrence}"
            metadata = st.session_state.classification_metadata.get(metadata_key, {})
            method = metadata.get("method", "Manual")
            rationale = metadata.get("rationale", "")
            
            data.append({
                'Classification': 'OI',
                'Sentence': highlighted_sentence,
                'Keyword Instance': keyword_instance,
                'Method': method,
                'Rationale': rationale
            })
    
    if data:
        for row in data:
            for key in row:
                row[key] = str(row[key])
        
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True)
    else:
        st.info("No raw data available for this keyword.")


def render_classified_sentences(current_isp: Dict[str, Any], classification: str) -> None:
    """Render the classified sentences."""
    for i, occ in enumerate(current_isp['analysis_results'][st.session_state.current_keyword][classification]):
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


def render_next_keyword_button() -> None:
    """Render the next keyword button."""
    if st.button("Next keyword"):
        keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
        analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
        next_keyword = get_next_keyword(st.session_state.current_keyword, keywords, analyzed_for_isp)
        
        if next_keyword:
            current_isp = st.session_state.isps[st.session_state.current_isp_id]
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
                
            if len(st.session_state.current_sentences) == 0:
                st.session_state.analyzed_keywords.setdefault(st.session_state.current_isp_id, set()).add(next_keyword)
                
                all_keywords = list(KeywordSets.get_keywords(st.session_state.language).keys())
                analyzed_for_isp = st.session_state.analyzed_keywords.get(st.session_state.current_isp_id, set())
                if len(analyzed_for_isp) == len(all_keywords):
                    st.session_state.all_keywords_analyzed = True
                
            st.rerun()


def get_next_keyword(current_keyword, all_keywords, analyzed_keywords):
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
        
    for i in range(current_index + 1, len(all_keywords)):
        if all_keywords[i] not in analyzed_keywords:
            return all_keywords[i]
            
    for i in range(0, current_index):
        if all_keywords[i] not in analyzed_keywords:
            return all_keywords[i]
            
    return all_keywords[(current_index + 1) % len(all_keywords)]


def render_current_keyword_raw_data(current_isp: Dict[str, Any]) -> None:
    """Render raw data table only for the current keyword."""
    if 'analysis_results' not in current_isp or st.session_state.current_keyword not in current_isp['analysis_results']:
        st.info("No analysis data available.")
        return
        
    data = []
    keyword = st.session_state.current_keyword
    isp_id = st.session_state.current_isp_id
    
    for occurrence in current_isp['analysis_results'][keyword].get('AA', []):
        parts = occurrence.split("::")
        if len(parts) >= 3:
            sentence = parts[0]
            start_pos = int(parts[1])
            end_pos = int(parts[2])
            keyword_instance = sentence[start_pos:end_pos]
            
            highlighted_sentence = (
                sentence[:start_pos] +
                '[' + keyword_instance + ']' +
                sentence[end_pos:]
            )
            
            metadata_key = f"{isp_id}::{keyword}::{occurrence}"
            metadata = st.session_state.classification_metadata.get(metadata_key, {})
            method = metadata.get("method", "Manual")
            rationale = metadata.get("rationale", "")
            
            data.append({
                'Classification': 'AA',
                'Sentence': highlighted_sentence,
                'Keyword Instance': keyword_instance,
                'Method': method,
                'Rationale': rationale
            })
    
    for occurrence in current_isp['analysis_results'][keyword].get('OI', []):
        parts = occurrence.split("::")
        if len(parts) >= 3:
            sentence = parts[0]
            start_pos = int(parts[1])
            end_pos = int(parts[2])
            keyword_instance = sentence[start_pos:end_pos]
            
            highlighted_sentence = (
                sentence[:start_pos] +
                '[' + keyword_instance + ']' +
                sentence[end_pos:]
            )
            
            metadata_key = f"{isp_id}::{keyword}::{occurrence}"
            metadata = st.session_state.classification_metadata.get(metadata_key, {})
            method = metadata.get("method", "Manual")
            rationale = metadata.get("rationale", "")
            
            data.append({
                'Classification': 'OI',
                'Sentence': highlighted_sentence,
                'Keyword Instance': keyword_instance,
                'Method': method,
                'Rationale': rationale
            })
    
    if data:
        for row in data:
            for key in row:
                row[key] = str(row[key])
        
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True)
    else:
        st.info("No raw data available for this keyword.")