# src/data/repository.py
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

class SessionRepository(ABC):
    """Abstract interface for session data storage."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the repository."""
        pass
    
    @abstractmethod
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save session data and return timestamp."""
        pass
    
    @abstractmethod
    def get_sessions(self) -> List[Tuple[int, str]]:
        """Get list of saved sessions (id, timestamp)."""
        pass
    
    @abstractmethod
    def load_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Load session data by ID."""
        pass