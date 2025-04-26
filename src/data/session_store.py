import sqlite3
import json
import datetime
from typing import Dict, List, Tuple, Any, Optional
import streamlit as st
from src.data.repository import SessionRepository

class SQLiteSessionRepository(SessionRepository):
    """SQLite implementation of session repository."""
    
    def __init__(self, database_file: str = "session_state.db"):
        self.database_file = database_file
    
    def initialize(self) -> None:
        """Initialize SQLite database and create sessions table if it does not exist."""
        conn = sqlite3.connect(self.database_file, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_data TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save the session data to the SQLite database."""
        json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.database_file, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (timestamp, session_data) VALUES (?, ?)", 
                      (timestamp, json_data))
        conn.commit()
        conn.close()
        return timestamp
    
    def get_sessions(self) -> List[Tuple[int, str]]:
        """Retrieve a list of saved sessions (id and timestamp) from the database."""
        conn = sqlite3.connect(self.database_file, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp FROM sessions ORDER BY id DESC")
        sessions = cursor.fetchall()
        conn.close()
        return sessions
    
    def load_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Load a session from the database using the provided session ID."""
        conn = sqlite3.connect(self.database_file, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT session_data FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None


class SessionManager:
    """Manages session state in the application."""
    
    def __init__(self, repository: SessionRepository):
        self.repository = repository
        self.repository.initialize()
    
    def save_current_session(self) -> str:
        """Save the current session state."""
        session_data = {
            'isps': st.session_state.isps,
            'current_isp_id': st.session_state.current_isp_id,
            'next_isp_id': st.session_state.next_isp_id,
            'analyzed_keywords': {str(k): list(v) for k, v in st.session_state.analyzed_keywords.items()},
            'language': st.session_state.language,
            'context_mode': st.session_state.context_mode,
            'classification_metadata': st.session_state.classification_metadata,
            'selected_model': st.session_state.selected_model
        }
        return self.repository.save_session(session_data)
    
    def get_available_sessions(self) -> List[Tuple[int, str]]:
        """Get list of available sessions."""
        return self.repository.get_sessions()
    
    def load_session(self, session_id: int) -> bool:
        """Load a session and update app state."""
        session_data = self.repository.load_session(session_id)
        if not session_data:
            return False
            
        st.session_state.isps = session_data.get('isps', {})
        st.session_state.current_isp_id = session_data.get('current_isp_id')
        st.session_state.next_isp_id = session_data.get('next_isp_id', 1)
        st.session_state.context_mode = session_data.get('context_mode', 'normal')
        st.session_state.classification_metadata = session_data.get('classification_metadata', {})
        analyzed_keywords = session_data.get('analyzed_keywords', {})
        st.session_state.analyzed_keywords = {k: set(v) for k, v in analyzed_keywords.items()}
        st.session_state.language = session_data.get('language', 'Swedish')
        st.session_state.selected_model = session_data.get('selected_model')
        st.session_state.current_keyword = None
        st.session_state.current_sentences = []
        st.session_state.current_index = 0
        st.session_state.classifications = []
        st.session_state.show_context = False

        if st.session_state.isps:
            old_isps = st.session_state.isps.copy()
            st.session_state.isps = {}
            for isp_id, isp_data in old_isps.items():
                st.session_state.isps[int(isp_id)] = isp_data
            if st.session_state.current_isp_id is not None:
                st.session_state.current_isp_id = int(st.session_state.current_isp_id)
            old_analyzed_keywords = st.session_state.analyzed_keywords.copy()
            st.session_state.analyzed_keywords = {}
            for isp_id, keywords in old_analyzed_keywords.items():
                st.session_state.analyzed_keywords[int(isp_id)] = keywords
        return True