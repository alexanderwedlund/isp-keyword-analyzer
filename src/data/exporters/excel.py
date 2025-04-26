import pandas as pd
import base64
import datetime
from io import BytesIO
from typing import Dict, List, Any
from src.domain.metrics import MetricsCalculator
from src.config.settings import KeywordSets

class ExcelExporter:
    """Responsible for exporting analysis results to Excel format."""
    
    def __init__(self, isps: Dict[int, Dict[str, Any]], language: str, classification_metadata: Dict = None):
        """Initialize the exporter with ISP data and language."""
        self.isps = isps
        self.language = language
        self.keywords = KeywordSets.get_keywords(language)
        self.all_metrics = MetricsCalculator.calculate_all_metrics(isps, self.keywords)
        self.sorted_isps = sorted(isps.items(), key=lambda x: x[0])
        self.isp_ids = [isp_id for isp_id, _ in self.sorted_isps]
        self.classification_metadata = classification_metadata or {}
    
    def generate_excel(self) -> BytesIO:
        """Generate an Excel file with the analysis results."""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            title_format = workbook.add_format({'bold': True})
            
            self._create_total_loss_worksheet(workbook, title_format)
            self._create_aa_keywords_worksheet(workbook, title_format)
            self._create_oi_keywords_worksheet(workbook, title_format)
            self._create_keyword_loss_worksheet(workbook, title_format)
            self._create_raw_data_worksheet(workbook, title_format)
            
        return output
    
    def _create_total_loss_worksheet(self, workbook, title_format):
        """Create the total keyword loss of specificity worksheet."""
        worksheet = workbook.add_worksheet('Table 1')
        worksheet.write(0, 0, 'Table 1. Total keyword loss of specificity', title_format)
        headers = ['ISP', 'Actionable advice', 'Other information', 
                  'Total', 'Total keyword loss of specificity (%)']
        
        for col, header in enumerate(headers):
            worksheet.write(1, col, header)
            
        row = 2
        total_aa = 0
        total_oi = 0
        total_all = 0
        percent_format = workbook.add_format({'num_format': '0.0'})
        
        for isp_id in self.isp_ids:
            metrics = self.all_metrics.get(isp_id)
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
    
    def _create_aa_keywords_worksheet(self, workbook, title_format):
        """Create the actionable advice keywords worksheet."""
        worksheet = workbook.add_worksheet('Table 2')
        worksheet.write(0, 0, 'Table 2. Number of keywords for actionable advice', title_format)
        headers = ['ISP'] + list(self.keywords.keys())
        
        for col, header in enumerate(headers):
            worksheet.write(1, col, header)
            
        row = 2
        keyword_sums_aa = {kw: 0 for kw in self.keywords}
        
        for isp_id in self.isp_ids:
            metrics = self.all_metrics.get(isp_id)
            if metrics:
                worksheet.write(row, 0, isp_id)
                for col, kw in enumerate(self.keywords.keys(), start=1):
                    count = metrics['aa_count'].get(kw, 0)
                    worksheet.write(row, col, count)
                    keyword_sums_aa[kw] += count
                row += 1
                
        worksheet.write(row, 0, 'Sum')
        total_aa_count = 0
        
        for col, kw in enumerate(self.keywords.keys(), start=1):
            worksheet.write(row, col, keyword_sums_aa[kw])
            total_aa_count += keyword_sums_aa[kw]
            
        row += 1
        worksheet.write(row, 0, '% of all AA')
        percent_format_pct = workbook.add_format({'num_format': '0.0%'})
        
        for col, kw in enumerate(self.keywords.keys(), start=1):
            percent = (keyword_sums_aa[kw] / total_aa_count) if total_aa_count > 0 else 0
            worksheet.write(row, col, percent, percent_format_pct)
    
    def _create_oi_keywords_worksheet(self, workbook, title_format):
        """Create the other information keywords worksheet."""
        worksheet = workbook.add_worksheet('Table 3')
        worksheet.write(0, 0, 'Table 3. Number of keywords for other information', title_format)
        headers = ['ISP'] + list(self.keywords.keys())
        
        for col, header in enumerate(headers):
            worksheet.write(1, col, header)
            
        row = 2
        keyword_sums_oi = {kw: 0 for kw in self.keywords}
        
        for isp_id in self.isp_ids:
            metrics = self.all_metrics.get(isp_id)
            if metrics:
                worksheet.write(row, 0, isp_id)
                for col, kw in enumerate(self.keywords.keys(), start=1):
                    count = metrics['oi_count'].get(kw, 0)
                    worksheet.write(row, col, count)
                    keyword_sums_oi[kw] += count
                row += 1
                
        worksheet.write(row, 0, 'Sum')
        total_oi_count = 0
        
        for col, kw in enumerate(self.keywords.keys(), start=1):
            worksheet.write(row, col, keyword_sums_oi[kw])
            total_oi_count += keyword_sums_oi[kw]
            
        row += 1
        worksheet.write(row, 0, '% of all OI')
        percent_format_pct = workbook.add_format({'num_format': '0.0%'})
        
        for col, kw in enumerate(self.keywords.keys(), start=1):
            percent = (keyword_sums_oi[kw] / total_oi_count) if total_oi_count > 0 else 0
            worksheet.write(row, col, percent, percent_format_pct)
    
    def _create_keyword_loss_worksheet(self, workbook, title_format):
        """Create the keyword loss of specificity worksheet."""
        worksheet = workbook.add_worksheet('Table 4')
        worksheet.write(0, 0, 'Table 4. Keyword loss of specificity', title_format)
        headers = ['ISP'] + [f"{kw} (%)" for kw in self.keywords.keys()]
        
        for col, header in enumerate(headers):
            worksheet.write(1, col, header)
            
        row = 2
        valid_metrics = {kw: [] for kw in self.keywords}
        
        for isp_id in self.isp_ids:
            metrics = self.all_metrics.get(isp_id)
            if metrics:
                worksheet.write(row, 0, isp_id)
                for col, kw in enumerate(self.keywords.keys(), start=1):
                    loss = metrics['keyword_loss_specificity'].get(kw)
                    if loss is not None:
                        worksheet.write(row, col, loss, workbook.add_format({'num_format': '0'}))
                        valid_metrics[kw].append(loss)
                    else:
                        worksheet.write(row, col, '-')
                row += 1
                
        aa_sums = {kw: sum(metrics['aa_count'].get(kw, 0) for isp_id, metrics in self.all_metrics.items() if metrics)
                  for kw in self.keywords.keys()}
        oi_sums = {kw: sum(metrics['oi_count'].get(kw, 0) for isp_id, metrics in self.all_metrics.items() if metrics)
                  for kw in self.keywords.keys()}
        
        worksheet.write(row, 0, 'Sum*')
        for col, kw in enumerate(self.keywords.keys(), start=1):
            aa_sum = aa_sums[kw]
            oi_sum = oi_sums[kw]
            total = aa_sum + oi_sum
            if total > 0:
                loss_specificity = (oi_sum / total) * 100
                worksheet.write(row, col, loss_specificity, workbook.add_format({'num_format': '0'}))
            else:
                worksheet.write(row, col, '-')
                
        row += 1
        worksheet.write(row, 0, 'Note: *Calculated using the sums in Tables 2 and 3')
    
    def _create_raw_data_worksheet(self, workbook, title_format):
        """Create the raw data worksheet with all occurrences."""
        worksheet = workbook.add_worksheet('Raw Data')
        headers = ['ISP ID', 'ISP Name', 'Keyword', 'Classification', 
                'Sentence', 'Keyword Instance', 'Position', 'Method', 'Rationale']
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
            
        row = 1
        
        for isp_id, isp_data in sorted(self.isps.items(), key=lambda x: x[0]):
            analysis_results = isp_data.get('analysis_results', {})
            isp_name = isp_data.get('name', f"ISP {isp_id}")
            
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
                        
                        metadata_key = f"{isp_id}::{keyword}::{occurrence}"
                        metadata = self.classification_metadata.get(metadata_key, {})
                        method = metadata.get("method", "Manual")
                        rationale = metadata.get("rationale", "")
                        
                        worksheet.write(row, 0, isp_id)
                        worksheet.write(row, 1, isp_name)
                        worksheet.write(row, 2, keyword)
                        worksheet.write(row, 3, 'AA')
                        worksheet.write(row, 4, highlighted_sentence)
                        worksheet.write(row, 5, keyword_instance)
                        worksheet.write(row, 6, f"{start_pos}-{end_pos}")
                        worksheet.write(row, 7, method)
                        worksheet.write(row, 8, rationale)
                        row += 1
                        
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
                        
                        metadata_key = f"{isp_id}::{keyword}::{occurrence}"
                        metadata = self.classification_metadata.get(metadata_key, {})
                        method = metadata.get("method", "Manual")
                        rationale = metadata.get("rationale", "")
                        
                        worksheet.write(row, 0, isp_id)
                        worksheet.write(row, 1, isp_name)
                        worksheet.write(row, 2, keyword)
                        worksheet.write(row, 3, 'OI')
                        worksheet.write(row, 4, highlighted_sentence)
                        worksheet.write(row, 5, keyword_instance)
                        worksheet.write(row, 6, f"{start_pos}-{end_pos}")
                        worksheet.write(row, 7, method)
                        worksheet.write(row, 8, rationale)
                        row += 1
    
    def get_download_link(self) -> str:
        """Generate a download link for the Excel file."""
        excel_data = self.generate_excel().getvalue()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        b64 = base64.b64encode(excel_data).decode()
        return (
            f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;'
            f'base64,{b64}" download="isp_analysis_{timestamp}.xlsx">Download Excel file</a>'
        )