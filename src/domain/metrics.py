# src/domain/metrics.py
from typing import Dict, List, Any, Optional

class MetricsCalculator:
    """Responsible for calculating analysis metrics."""
    
    @staticmethod
    def calculate_metrics(isp_id: int, isps: Dict[int, Dict], keywords: Dict[str, str]) -> Dict[str, Any]:
        """Calculate analysis metrics for a given ISP."""
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
            metrics['keyword_loss_specificity'][kw] = (oi / tot * 100) if tot > 0 else None
        
        return metrics
    
    @staticmethod
    def calculate_all_metrics(isps: Dict[int, Dict], keywords: Dict[str, str]) -> Dict[int, Dict]:
        """Calculate metrics for all ISPs."""
        all_metrics = {}
        for isp_id in isps:
            all_metrics[isp_id] = MetricsCalculator.calculate_metrics(isp_id, isps, keywords)
        return all_metrics