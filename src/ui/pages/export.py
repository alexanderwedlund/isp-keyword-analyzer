import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.domain.metrics import MetricsCalculator
from src.data.exporters.excel import ExcelExporter
from src.config.settings import KeywordSets
from src.ui.components.tables import (
    render_total_loss_table,
    render_aa_keywords_table,
    render_oi_keywords_table,
    render_keyword_loss_table,
    render_raw_data_table
)

def render_export_ui(isps: Dict[int, Dict[str, Any]], language: str) -> None:
    """Render the export UI with analysis results."""
    st.header("Analysis Results")
    
    if st.button("Refresh Metrics", key="refresh_metrics_btn"):
        st.success("Metrics refreshed!")
        st.rerun()
    
    all_metrics = MetricsCalculator.calculate_all_metrics(
        isps, 
        KeywordSets.get_keywords(language)
    )
    
    if all_metrics:
        def create_safe_dataframe(data):
            for row in data:
                for key in row:
                    row[key] = str(row[key])
            return pd.DataFrame(data)
        
        render_total_loss_table(all_metrics, create_safe_dataframe)
        render_aa_keywords_table(all_metrics, create_safe_dataframe)
        render_oi_keywords_table(all_metrics, create_safe_dataframe)
        render_keyword_loss_table(all_metrics, create_safe_dataframe)
        
        if st.session_state.current_isp_id is not None:
            if "last_displayed_isp" not in st.session_state or st.session_state.last_displayed_isp != st.session_state.current_isp_id:
                st.session_state.raw_data_page = 0
                st.session_state.last_displayed_isp = st.session_state.current_isp_id
                
            render_raw_data_table(st.session_state.current_isp_id, isps, create_safe_dataframe)
        
        st.subheader("Export Results")
        exporter = ExcelExporter(
            isps=isps, 
            language=language, 
            classification_metadata=st.session_state.classification_metadata
        )
        st.markdown(exporter.get_download_link(), unsafe_allow_html=True)