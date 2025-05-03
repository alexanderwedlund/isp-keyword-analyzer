import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Callable
from src.config.settings import KeywordSets

def render_total_loss_table(all_metrics, create_safe_dataframe):
    """Render Table 1: Total Keyword Loss of Specificity."""
    st.subheader("Table 1: Total Keyword Loss of Specificity")
    table1_data = []
    
    for isp_id, metrics in all_metrics.items():
        if metrics:
            isp_data = st.session_state.isps[isp_id]
            table1_data.append({
                'ISP': str(isp_id),
                'ISP Name': isp_data.get('name', f"ISP {isp_id}"),
                'Actionable advice': str(metrics['total_aa']),
                'Other information': str(metrics['total_oi']),
                'Total': str(metrics['total_count']),
                'Total keyword loss of specificity (%)': f"{metrics['total_loss_specificity']:.1f}%"
            })
    
    if table1_data:
        df1 = create_safe_dataframe(table1_data)
        st.dataframe(df1, hide_index=True)

def render_aa_keywords_table(all_metrics, create_safe_dataframe):
    """Render Table 2: Number of Keywords for Actionable Advice."""
    st.subheader("Table 2: Number of Keywords for Actionable Advice")
    keywords = KeywordSets.get_keywords(st.session_state.language)
    table2_data = []
    
    for isp_id in sorted(st.session_state.isps.keys()):
        metrics = all_metrics.get(isp_id)
        if metrics:
            row_data = {'ISP': str(isp_id)}
            for kw in keywords.keys():
                row_data[kw] = str(metrics['aa_count'].get(kw, 0))
            table2_data.append(row_data)
    
    if table2_data:
        keyword_sums = {kw: 0 for kw in keywords.keys()}
        for row in table2_data:
            for kw in keywords.keys():
                try:
                    keyword_sums[kw] += int(row[kw])
                except (ValueError, TypeError):
                    pass
        
        sum_row = {'ISP': 'Sum'}
        total_aa_count = 0
        for kw in keywords.keys():
            sum_row[kw] = str(keyword_sums[kw])
            total_aa_count += keyword_sums[kw]
        table2_data.append(sum_row)
        
        if total_aa_count > 0:
            percent_row = {'ISP': '% of all AA'}
            for kw in keywords.keys():
                percent = (keyword_sums[kw] / total_aa_count) * 100 if total_aa_count > 0 else 0
                percent_row[kw] = f"{percent:.1f}%"
            table2_data.append(percent_row)
        
        df2 = create_safe_dataframe(table2_data)
        st.dataframe(df2, hide_index=True)

def render_oi_keywords_table(all_metrics, create_safe_dataframe):
    """Render Table 3: Number of Keywords for Other Information."""
    st.subheader("Table 3: Number of Keywords for Other Information")
    keywords = KeywordSets.get_keywords(st.session_state.language)
    table3_data = []
    
    for isp_id in sorted(st.session_state.isps.keys()):
        metrics = all_metrics.get(isp_id)
        if metrics:
            row_data = {'ISP': str(isp_id)}
            for kw in keywords.keys():
                row_data[kw] = str(metrics['oi_count'].get(kw, 0))
            table3_data.append(row_data)
    
    if table3_data:
        keyword_sums = {kw: 0 for kw in keywords.keys()}
        for row in table3_data:
            for kw in keywords.keys():
                try:
                    keyword_sums[kw] += int(row[kw])
                except (ValueError, TypeError):
                    pass
        
        sum_row = {'ISP': 'Sum'}
        total_oi_count = 0
        for kw in keywords.keys():
            sum_row[kw] = str(keyword_sums[kw])
            total_oi_count += keyword_sums[kw]
        table3_data.append(sum_row)
        
        if total_oi_count > 0:
            percent_row = {'ISP': '% of all OI'}
            for kw in keywords.keys():
                percent = (keyword_sums[kw] / total_oi_count) * 100 if total_oi_count > 0 else 0
                percent_row[kw] = f"{percent:.1f}%"
            table3_data.append(percent_row)
        
        df3 = create_safe_dataframe(table3_data)
        st.dataframe(df3, hide_index=True)

def render_keyword_loss_table(all_metrics, create_safe_dataframe):
    """Render Table 4: Keyword Loss of Specificity."""
    st.subheader("Table 4: Keyword Loss of Specificity (%)")
    keywords = KeywordSets.get_keywords(st.session_state.language)
    table4_data = []
    
    for isp_id in sorted(st.session_state.isps.keys()):
        metrics = all_metrics.get(isp_id)
        if metrics:
            row_data = {'ISP': str(isp_id)}
            for kw in keywords.keys():
                loss = metrics['keyword_loss_specificity'].get(kw)
                if loss is not None:
                    row_data[kw] = f"{loss:.1f}%"
                else:
                    row_data[kw] = '-'
            table4_data.append(row_data)
    
    if table4_data:
        aa_sums = {kw: 0 for kw in keywords.keys()}
        oi_sums = {kw: 0 for kw in keywords.keys()}
        
        for isp_id in sorted(st.session_state.isps.keys()):
            metrics = all_metrics.get(isp_id)
            if metrics:
                for kw in keywords.keys():
                    aa_sums[kw] += metrics['aa_count'].get(kw, 0)
                    oi_sums[kw] += metrics['oi_count'].get(kw, 0)
        
        sum_row = {'ISP': 'Sum*'}
        for kw in keywords.keys():
            total = aa_sums[kw] + oi_sums[kw]
            if total > 0:
                loss_specificity = (oi_sums[kw] / total) * 100
                sum_row[kw] = f"{loss_specificity:.1f}%"
            else:
                sum_row[kw] = '-'
        table4_data.append(sum_row)
        
        note_row = {'ISP': 'Note: *Calculated using the sums in Tables 2 and 3'}
        for kw in keywords.keys():
            note_row[kw] = ''
        table4_data.append(note_row)
        
        df4 = create_safe_dataframe(table4_data)
        st.dataframe(df4, hide_index=True)

def switch_classification(isp_id, keyword, occurrence, current_classification):
    """Switch a classification between AA and OI and update all related data."""
    if isp_id not in st.session_state.isps:
        st.error(f"ISP with ID {isp_id} not found.")
        return False
        
    current_isp = st.session_state.isps[isp_id]
    if 'analysis_results' not in current_isp or keyword not in current_isp['analysis_results']:
        st.error(f"Analysis results for keyword '{keyword}' not found.")
        return False
        
    target_classification = "OI" if current_classification == "AA" else "AA"
    
    current_list = current_isp['analysis_results'][keyword][current_classification]
    target_list = current_isp['analysis_results'][keyword][target_classification]
    
    if occurrence not in current_list:
        st.error(f"Occurrence not found in {current_classification} list.")
        return False
        
    current_list.remove(occurrence)
    if occurrence not in target_list:
        target_list.append(occurrence)
        
    metadata_key = f"{isp_id}::{keyword}::{occurrence}"
    if metadata_key in st.session_state.classification_metadata:
        metadata = st.session_state.classification_metadata[metadata_key]
        metadata["method"] = "Manual (Switched)"
        if "original_classification" not in metadata:
            metadata["original_classification"] = current_classification
        st.session_state.classification_metadata[metadata_key] = metadata
    
    # Move?
    st.session_state.skip_congratulations = True
    
    st.success(f"Classification switched from {current_classification} to {target_classification}")
    return True

def synchronize_classifications(current_isp_id: int, target_classification: str, duplicate_group: List[Dict[str, Any]]) -> None:
    """Synchronize the classification of all duplicated sentences to the same classification.
    
    Args:
        current_isp_id: ID of the current ISP
        target_classification: Target classification ('AA' or 'OI')
        duplicate_group: List of all duplicates of a sentence
    """
    if current_isp_id not in st.session_state.isps:
        st.error(f"ISP with ID {current_isp_id} not found.")
        return
        
    current_isp = st.session_state.isps[current_isp_id]
    sync_count = 0
    
    for row in duplicate_group:
        if row['Classification'] != target_classification:
            if switch_classification(
                current_isp_id,
                row['Keyword'],
                row['Occurrence'],
                row['Classification']
            ):
                sync_count += 1
    
    if sync_count > 0:
        st.session_state.skip_congratulations = True
        st.success(f"Classification synchronized for {sync_count} duplicates.")

def render_raw_data_table(current_isp_id, isps, create_safe_dataframe):
    """Render a table showing raw data for the current ISP with functionality to switch classification."""
    st.subheader("Raw Data for Current ISP")
    
    if current_isp_id not in isps:
        st.info("No data available for this ISP.")
        return
        
    current_isp = isps[current_isp_id]
    analysis_results = current_isp.get('analysis_results', {})
    isp_name = current_isp.get('name', f"ISP {current_isp_id}")
    
    if not analysis_results:
        st.info("No analysis data available for this ISP.")
        return
    
    if "raw_data_order" not in st.session_state:
        st.session_state.raw_data_order = {}
    
    isp_key = f"isp_{current_isp_id}_order"
    
    if isp_key not in st.session_state.raw_data_order:
        st.session_state.raw_data_order[isp_key] = {}
    
    raw_data = []
    row_counter = 0
    
    for keyword in sorted(analysis_results.keys()):
        aa_occurrences = analysis_results[keyword].get('AA', [])
        oi_occurrences = analysis_results[keyword].get('OI', [])
        
        all_occurrences = []
        
        for occurrence in aa_occurrences:
            all_occurrences.append((keyword, occurrence, "AA"))
            
        for occurrence in oi_occurrences:
            all_occurrences.append((keyword, occurrence, "OI"))
            
        for keyword, occurrence, classification in all_occurrences:
            occ_key = f"{keyword}::{occurrence}"
            
            if occ_key not in st.session_state.raw_data_order[isp_key]:
                st.session_state.raw_data_order[isp_key][occ_key] = row_counter
                row_counter += 1
                
            order_index = st.session_state.raw_data_order[isp_key][occ_key]
            
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
                
                metadata_key = f"{current_isp_id}::{keyword}::{occurrence}"
                metadata = st.session_state.classification_metadata.get(metadata_key, {})
                method = metadata.get("method", "Manual") 
                rationale = metadata.get("rationale", "") 
                
                raw_data.append({
                    'Order': order_index, 
                    'Keyword': keyword,
                    'Classification': classification,
                    'Sentence': highlighted_sentence,
                    'BaseSentence': sentence,
                    'Keyword Instance': keyword_instance,
                    'Position': f"{start_pos}-{end_pos}",
                    'Method': method,
                    'Rationale': rationale,
                    'Occurrence': occurrence, 
                    'Switch': f"Switch to {'OI' if classification == 'AA' else 'AA'}"
                })
    
    if raw_data:
        raw_data.sort(key=lambda x: x['Order'])
        
        sentence_map = {}
        for i, row in enumerate(raw_data):
            base_sentence = row['BaseSentence']
            if base_sentence not in sentence_map:
                sentence_map[base_sentence] = []
            sentence_map[base_sentence].append(i)
        
        for base_sentence, indices in sentence_map.items():
            if len(indices) > 1:
                classifications = set(raw_data[idx]['Classification'] for idx in indices)
                
                for idx in indices:
                    raw_data[idx]['IsDuplicate'] = True
                    raw_data[idx]['DuplicateCount'] = len(indices)
                    raw_data[idx]['DuplicateIndices'] = indices
                    
                    if len(classifications) > 1:
                        raw_data[idx]['InconsistentClassification'] = True
                    else:
                        raw_data[idx]['InconsistentClassification'] = False
        
        keywords_in_data = sorted(set(item['Keyword'] for item in raw_data))
        
        keyword_filter = st.selectbox(
            "Filter by Keyword:", 
            ["All Keywords"] + keywords_in_data,
            key="raw_data_keyword_filter"
        )
        
        classification_filter = st.radio(
            "Filter by Classification:",
            ["All", "AA", "OI"],
            horizontal=True,
            key="raw_data_classification_filter"
        )
        
        consistency_filter = st.radio(
            "Filter by Classification Consistency:",
            ["All", "Show only inconsistent", "Show only consistent"],
            horizontal=True,
            key="raw_data_consistency_filter"
        )
        
        filtered_data = raw_data
        if keyword_filter != "All Keywords":
            filtered_data = [item for item in filtered_data if item['Keyword'] == keyword_filter]
            
        if classification_filter != "All":
            filtered_data = [item for item in filtered_data if item['Classification'] == classification_filter]
            
        if consistency_filter == "Show only inconsistent":
            filtered_data = [item for item in filtered_data if 
                           item.get('IsDuplicate', False) and 
                           item.get('InconsistentClassification', False)]
        elif consistency_filter == "Show only consistent":
            filtered_data = [item for item in filtered_data if 
                           item.get('IsDuplicate', False) and 
                           not item.get('InconsistentClassification', False)]
        
        if filtered_data:
            if "view_all_raw_data" not in st.session_state:
                st.session_state.view_all_raw_data = False
                
            view_all = st.checkbox("Show all data on single page", 
                                  value=st.session_state.view_all_raw_data,
                                  key="view_all_checkbox")
            
            if view_all != st.session_state.view_all_raw_data:
                st.session_state.view_all_raw_data = view_all
                st.rerun()
            
            chunk_size = 20
            total_chunks = (len(filtered_data) + chunk_size - 1) // chunk_size
            
            if "raw_data_page" not in st.session_state:
                st.session_state.raw_data_page = 0
            
            if total_chunks > 1 and not st.session_state.view_all_raw_data:
                st.write(f"Showing page {st.session_state.raw_data_page + 1} of {total_chunks}")
                
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if st.button("Previous Page", key="prev_page", disabled=st.session_state.raw_data_page <= 0):
                        st.session_state.raw_data_page -= 1
                        st.rerun()
                        
                with col3:
                    if st.button("Next Page", key="next_page", disabled=st.session_state.raw_data_page >= total_chunks - 1):
                        st.session_state.raw_data_page += 1
                        st.rerun()
                        
                with col2:
                    page_options = list(range(1, total_chunks + 1))
                    selected_page = st.selectbox(
                        "Go to page:",
                        page_options,
                        index=st.session_state.raw_data_page,
                        key="page_selector"
                    )
                    if selected_page - 1 != st.session_state.raw_data_page:
                        st.session_state.raw_data_page = selected_page - 1
                        st.rerun()
                        
            if st.session_state.view_all_raw_data:
                current_chunk = filtered_data
                if len(filtered_data) > 50:
                    st.warning(f"Showing all {len(filtered_data)} items. This may cause slower performance.")
            else:
                start_idx = st.session_state.raw_data_page * chunk_size
                end_idx = min(start_idx + chunk_size, len(filtered_data))
                current_chunk = filtered_data[start_idx:end_idx]
            
            if st.session_state.view_all_raw_data:
                search_term = st.text_input("Search in sentences:", key="raw_data_search")
                if search_term:
                    st.info(f"Searching for '{search_term}' in {len(current_chunk)} items")
                    current_chunk = [item for item in current_chunk if search_term.lower() in item['Sentence'].lower()]
                    if not current_chunk:
                        st.warning(f"No results found for '{search_term}'")
                    else:
                        st.success(f"Found {len(current_chunk)} matches")
            
            for i, row in enumerate(current_chunk):
                with st.container():
                    if row.get('IsDuplicate', False):
                        if row.get('InconsistentClassification', False):
                            duplicate_notification = f"⚠️ **This sentence appears {row.get('DuplicateCount', 0)} times with DIFFERENT classifications!**"
                            st.markdown(duplicate_notification)
                        else:
                            duplicate_notification = f"✅ **This sentence appears {row.get('DuplicateCount', 0)} times with the same classification**"
                            st.markdown(duplicate_notification)
                    
                    cols = st.columns([3, 1, 8, 1])
                    with cols[0]:
                        st.write(f"**Keyword:** {row['Keyword']}")
                        st.write(f"**Classification:** {row['Classification']}")
                        
                    with cols[1]:
                        if st.button(f"Switch to {'OI' if row['Classification'] == 'AA' else 'AA'}", 
                                   key=f"switch_{row['Order']}_{i}", 
                                   use_container_width=True):
                            if switch_classification(
                                current_isp_id, 
                                row['Keyword'], 
                                row['Occurrence'], 
                                row['Classification']
                            ):
                                st.rerun()
                                
                        if row.get('IsDuplicate', False) and row.get('InconsistentClassification', False):
                            if st.button("Sync all duplicates", 
                                       key=f"sync_{row['Order']}_{i}", 
                                       help=f"Apply {row['Classification']} classification to all duplicates of this sentence",
                                       use_container_width=True):
                                duplicate_rows = [raw_data[idx] for idx in row.get('DuplicateIndices', [])]
                                synchronize_classifications(
                                    current_isp_id, 
                                    row['Classification'], 
                                    duplicate_rows
                                )
                                st.rerun()
                                
                    with cols[2]:
                        st.write("**Sentence:**")
                        st.markdown(f"{row['Sentence']}")
                        if row['Rationale']:
                            with st.expander("Show rationale"):
                                st.write(f"{row['Rationale']}")
                        
                    with cols[3]:
                        st.write(f"**Method:** {row['Method']}")
                    
                    st.markdown("---")
        else:
            st.info("No data matches the current filters.")
    else:
        st.info("No raw data available for this ISP.")