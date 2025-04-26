from typing import Dict, Any, Optional

class KeywordSets:
    """Manages the sets of keywords for different languages."""
    
    _DEFAULT_SETS = {
        "Swedish": {
            "Aldrig": "Never",
            "Behöver": "Need",
            "Bör": "Should",
            "Ej": "Not",
            "Förbjuden": "Forbidden",
            "Inte": "Not",
            "Måste": "Must",
            "Ska": "Shall",
            "Skall": "Shall"
        },
        "English": {
            "Never": "Never",
            "Need": "Need",
            "Should": "Should",
            "Not": "Not",
            "Forbidden": "Forbidden",
            "Must": "Must",
            "Shall": "Shall"
        }
    }
    
    @classmethod
    def get_keywords(cls, language: str) -> Dict[str, str]:
        """Get keywords for a specific language."""
        return cls._DEFAULT_SETS.get(language, {}).copy()
    
    @classmethod
    def get_available_languages(cls) -> list:
        """Get a list of available languages."""
        return list(cls._DEFAULT_SETS.keys())
    
    @classmethod
    def is_valid_language(cls, language: str) -> bool:
        """Check if a language is supported."""
        return language in cls._DEFAULT_SETS