# analyzer.py
# This module contains the analysis functions such as splitting text into sentences,
# finding keyword matches, and calculating analysis metrics.

import re
import streamlit as st
from config import KEYWORDS_SETS

class Analyzer:
    @staticmethod
    def find_sentences_with_keyword(text, keyword):
        """Find sentences that contain the specified keyword including context."""
        # Split text into sentences based on period followed by whitespace or newline.
        sentences = re.split(r'\.(?:\s|\n|$)', text)
        # Remove empty sentences and add period back.
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        matching_sentences = []
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for i, sentence in enumerate(sentences):
            matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
            before_context = sentences[i-1] if i > 0 else ""
            after_context = sentences[i+1] if i < len(sentences)-1 else ""
            if matches:
                for match in matches:
                    matching_sentences.append({
                        'sentence': sentence,
                        'start': match.start(),
                        'end': match.end(),
                        'match_text': match.group(),
                        'before_context': before_context,
                        'after_context': after_context
                    })
        return matching_sentences

    @staticmethod
    def calculate_metrics(isp_id, isps, language):
        """Calculate analysis metrics for a given ISP."""
        keywords = KEYWORDS_SETS.get(language, {})
        if isp_id not in isps:
            return None
        isp_data = isps[isp_id]
        
        keyword_aa_counts = {}
        keyword_oi_counts = {}
        
        for keyword, data in isp_data.get('analysis_results', {}).items():
            aa_count = len(data.get('AA', []))
            oi_count = len(data.get('OI', []))
            keyword_aa_counts[keyword] = aa_count
            keyword_oi_counts[keyword] = oi_count
        
        total_aa = sum(keyword_aa_counts.values())
        total_oi = sum(keyword_oi_counts.values())
        total_all = total_aa + total_oi
        
        print(f"\n=== DEBUG FÖR ISP {isp_id} ===")
        print(f"Total AA: {total_aa}, Total OI: {total_oi}, Total: {total_all}")
        print("Per nyckelord:")

        metrics = {
            'total_aa': total_aa,
            'total_oi': total_oi,
            'total_count': total_all,
            'total_loss_specificity': (total_oi / total_all * 100) if total_all > 0 else 0,
            'aa_count': {kw: keyword_aa_counts.get(kw, 0) for kw in keywords.keys()},
            'oi_count': {kw: keyword_oi_counts.get(kw, 0) for kw in keywords.keys()},
            'keyword_loss_specificity': {}
        }
        
        for kw in keywords.keys():
            aa = keyword_aa_counts.get(kw, 0)
            oi = keyword_oi_counts.get(kw, 0)
            tot = aa + oi
            loss = (oi / tot * 100) if tot > 0 else None
            print(f"  {kw}: AA={aa}, OI={oi}, Tot={tot}, Loss={loss}%")
            metrics['keyword_loss_specificity'][kw] = (oi / tot * 100) if tot > 0 else None
        
        return metrics

    @staticmethod
    def calculate_all_metrics(isps, language):
        """Calculate metrics for all ISPs."""
        all_metrics = {}
        for isp_id in isps:
            all_metrics[isp_id] = Analyzer.calculate_metrics(isp_id, isps, language)
        return all_metrics
