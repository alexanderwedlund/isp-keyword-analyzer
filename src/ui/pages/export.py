# src/ui/pages/export.py
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
    render_keyword_loss_table
)

def render_export_ui(isps: Dict[int, Dict[str, Any]], language: str) -> None:
    """Render the export UI with analysis results."""
    st.header("Analysis Results")
    
    # Calculate metrics
    all_metrics = MetricsCalculator.calculate_all_metrics(
        isps, 
        KeywordSets.get_keywords(language)
    )
    
    if all_metrics:
        # Function to create safe dataframes without type conversion problems
        def create_safe_dataframe(data):
            # Convert all values to strings to avoid type conversion problems
            for row in data:
                for key in row:
                    row[key] = str(row[key])
            return pd.DataFrame(data)
        
        # Create and display tables
        render_total_loss_table(all_metrics, create_safe_dataframe)
        render_aa_keywords_table(all_metrics, create_safe_dataframe)
        render_oi_keywords_table(all_metrics, create_safe_dataframe)
        render_keyword_loss_table(all_metrics, create_safe_dataframe)
        
        # Export button
        st.subheader("Export Results")
        exporter = ExcelExporter(isps, language)
        st.markdown(exporter.get_download_link(), unsafe_allow_html=True)