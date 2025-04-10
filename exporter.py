# exporter.py v2.0
# This module handles the export of analysis results to an Excel file.

import pandas as pd
import base64
import datetime
from io import BytesIO
import streamlit as st
from analyzer import Analyzer
from config import KEYWORDS_SETS

class Exporter:
    @staticmethod
    def to_excel(isps, language):
        """Generate a downloadable Excel file with the analysis results."""
        output = BytesIO()
        all_metrics = Analyzer.calculate_all_metrics(isps, language)
        sorted_isps = sorted(isps.items(), key=lambda x: x[0])
        isp_ids = [isp_id for isp_id, _ in sorted_isps]
        keywords = KEYWORDS_SETS.get(language, {})
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            title_format = workbook.add_format({'bold': True})
            
            # Table 1: Total keyword loss of specificity
            worksheet = workbook.add_worksheet('Table 1')
            worksheet.write(0, 0, 'Table 1. Total keyword loss of specificity', title_format)
            headers = ['ISP', 'Actionable advice', 'Other information', 'Total', 'Total keyword loss of specificity (%)']
            for col, header in enumerate(headers):
                worksheet.write(1, col, header)
            row = 2
            total_aa = 0
            total_oi = 0
            total_all = 0
            percent_format = workbook.add_format({'num_format': '0.0'})
            for isp_id in isp_ids:
                metrics = all_metrics.get(isp_id)
                if metrics:
                    worksheet.write(row, 0, isp_id)
                    worksheet.write(row, 1, metrics['total_aa'])
                    worksheet.write(row, 2, metrics['total_oi'])
                    worksheet.write(row, 3, metrics['total_count'])
                    worksheet.write(row, 4, metrics['total_loss_specificity'], percent_format)
                    total_aa += metrics['total_aa']
                    total_oi += metrics['total_oi']
                    total_all += metrics['total_count']
                    row += 1
            worksheet.write(row, 0, 'Sum')
            worksheet.write(row, 1, total_aa)
            worksheet.write(row, 2, total_oi)
            worksheet.write(row, 3, total_all)
            if total_all > 0:
                total_loss = (total_oi / total_all) * 100
                worksheet.write(row, 4, total_loss, percent_format)
            
            # Table 2: Number of keywords for actionable advice
            worksheet = workbook.add_worksheet('Table 2')
            worksheet.write(0, 0, 'Table 2. Number of keywords for actionable advice', title_format)
            headers = ['ISP'] + list(keywords.keys())
            for col, header in enumerate(headers):
                worksheet.write(1, col, header)
            row = 2
            keyword_sums_aa = {kw: 0 for kw in keywords}
            for isp_id in isp_ids:
                metrics = all_metrics.get(isp_id)
                if metrics:
                    worksheet.write(row, 0, isp_id)
                    for col, kw in enumerate(keywords.keys(), start=1):
                        count = metrics['aa_count'].get(kw, 0)
                        worksheet.write(row, col, count)
                        keyword_sums_aa[kw] += count
                    row += 1
            worksheet.write(row, 0, 'Sum')
            total_aa_count = 0
            for col, kw in enumerate(keywords.keys(), start=1):
                worksheet.write(row, col, keyword_sums_aa[kw])
                total_aa_count += keyword_sums_aa[kw]
            row += 1
            worksheet.write(row, 0, '% of all AA')
            percent_format_pct = workbook.add_format({'num_format': '0.0%'})
            for col, kw in enumerate(keywords.keys(), start=1):
                percent = (keyword_sums_aa[kw] / total_aa_count) if total_aa_count > 0 else 0
                worksheet.write(row, col, percent, percent_format_pct)
            
            # Table 3: Number of keywords for other information
            worksheet = workbook.add_worksheet('Table 3')
            worksheet.write(0, 0, 'Table 3. Number of keywords for other information', title_format)
            headers = ['ISP'] + list(keywords.keys())
            for col, header in enumerate(headers):
                worksheet.write(1, col, header)
            row = 2
            keyword_sums_oi = {kw: 0 for kw in keywords}
            for isp_id in isp_ids:
                metrics = all_metrics.get(isp_id)
                if metrics:
                    worksheet.write(row, 0, isp_id)
                    for col, kw in enumerate(keywords.keys(), start=1):
                        count = metrics['oi_count'].get(kw, 0)
                        worksheet.write(row, col, count)
                        keyword_sums_oi[kw] += count
                    row += 1
            worksheet.write(row, 0, 'Sum')
            total_oi_count = 0
            for col, kw in enumerate(keywords.keys(), start=1):
                worksheet.write(row, col, keyword_sums_oi[kw])
                total_oi_count += keyword_sums_oi[kw]
            row += 1
            worksheet.write(row, 0, '% of all OI')
            for col, kw in enumerate(keywords.keys(), start=1):
                percent = (keyword_sums_oi[kw] / total_oi_count) if total_oi_count > 0 else 0
                worksheet.write(row, col, percent, percent_format_pct)
            
            # Table 4: Keyword loss of specificity
            worksheet = workbook.add_worksheet('Table 4')
            worksheet.write(0, 0, 'Table 4. Keyword loss of specificity', title_format)
            headers = ['ISP'] + [f"{kw} (%)" for kw in keywords.keys()]
            for col, header in enumerate(headers):
                worksheet.write(1, col, header)
            row = 2
            valid_metrics = {kw: [] for kw in keywords}
            for isp_id in isp_ids:
                metrics = all_metrics.get(isp_id)
                if metrics:
                    worksheet.write(row, 0, isp_id)
                    for col, kw in enumerate(keywords.keys(), start=1):
                        loss = metrics['keyword_loss_specificity'].get(kw)
                        if loss is not None:
                            worksheet.write(row, col, loss, workbook.add_format({'num_format': '0'}))
                            valid_metrics[kw].append(loss)
                        else:
                            worksheet.write(row, col, '-')
                    row += 1
            worksheet.write(row, 0, 'Sum*')
            for col, kw in enumerate(keywords.keys(), start=1):
                aa_sum = keyword_sums_aa[kw]  # Från Tabell 2
                oi_sum = keyword_sums_oi[kw]  # Från Tabell 3
                total = aa_sum + oi_sum
                if total > 0:
                    loss_specificity = (oi_sum / total) * 100
                    worksheet.write(row, col, loss_specificity, workbook.add_format({'num_format': '0'}))
                else:
                    worksheet.write(row, col, '-')
            row += 1
            worksheet.write(row, 0, 'Note: *Calculated using the sums in Tables 2 and 3')
            
            # Raw Data worksheet
            worksheet = workbook.add_worksheet('Raw Data')
            headers = ['ISP ID', 'ISP Name', 'Keyword', 'Classification', 'Sentence', 'Keyword Instance', 'Position']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            row = 1
            for isp_id, isp_data in sorted(isps.items(), key=lambda x: x[0]):
                analysis_results = isp_data.get('analysis_results', {})
                isp_name = isp_data.get('name', f"ISP {isp_id}")
                for keyword, data in analysis_results.items():
                    # Process AA occurrences
                    for occurrence in data.get('AA', []):
                        parts = occurrence.split("::")
                        if len(parts) >= 3:
                            sentence = parts[0]
                            start_pos = int(parts[1])
                            end_pos = int(parts[2])
                            keyword_instance = sentence[start_pos:end_pos]
                            worksheet.write(row, 0, isp_id)
                            worksheet.write(row, 1, isp_name)
                            worksheet.write(row, 2, keyword)
                            worksheet.write(row, 3, 'AA')
                            worksheet.write(row, 4, sentence)
                            worksheet.write(row, 5, keyword_instance)
                            worksheet.write(row, 6, f"{start_pos}-{end_pos}")
                            row += 1
                    # Process OI occurrences
                    for occurrence in data.get('OI', []):
                        parts = occurrence.split("::")
                        if len(parts) >= 3:
                            sentence = parts[0]
                            start_pos = int(parts[1])
                            end_pos = int(parts[2])
                            keyword_instance = sentence[start_pos:end_pos]
                            worksheet.write(row, 0, isp_id)
                            worksheet.write(row, 1, isp_name)
                            worksheet.write(row, 2, keyword)
                            worksheet.write(row, 3, 'OI')
                            worksheet.write(row, 4, sentence)
                            worksheet.write(row, 5, keyword_instance)
                            worksheet.write(row, 6, f"{start_pos}-{end_pos}")
                            row += 1
        excel_data = output.getvalue()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        b64 = base64.b64encode(excel_data).decode()
        return (
            f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;'
            f'base64,{b64}" download="isp_analysis_{timestamp}.xlsx">Download Excel file</a>'
        )
