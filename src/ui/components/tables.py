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

def render_raw_data_table(current_isp_id, isps, create_safe_dataframe):
    """Render a table showing Raw Data for the current ISP."""
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
    
    raw_data = []
    
    for keyword, data in analysis_results.items():
        for occurrence in data.get('AA', []):
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
                    'Keyword': keyword,
                    'Classification': 'AA',
                    'Sentence': highlighted_sentence,
                    'Keyword Instance': keyword_instance,
                    'Position': f"{start_pos}-{end_pos}",
                    'Method': method,
                    'Rationale': rationale
                })
                
        for occurrence in data.get('OI', []):
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
                    'Keyword': keyword,
                    'Classification': 'OI',
                    'Sentence': highlighted_sentence,
                    'Keyword Instance': keyword_instance,
                    'Position': f"{start_pos}-{end_pos}",
                    'Method': method,
                    'Rationale': rationale
                })
    
    if raw_data:
        df = create_safe_dataframe(raw_data)
        st.dataframe(df, hide_index=True)
    else:
        st.info("No raw data available for this ISP.")