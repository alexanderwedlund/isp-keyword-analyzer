# db.py
# This module encapsulates all database operations (using SQLite) for session state management.

import sqlite3
import json
import datetime
import streamlit as st

class SessionDB:
    DATABASE_FILE = "session_state.db"

    @staticmethod
    def init_db():
        """Initialize SQLite database and create sessions table if it does not exist."""
        conn = sqlite3.connect(SessionDB.DATABASE_FILE, check_same_thread=False)
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

    @staticmethod
    def save_session():
        """Save the current session state to the SQLite database."""
        session_data = {
            'isps': st.session_state.isps,
            'current_isp_id': st.session_state.current_isp_id,
            'next_isp_id': st.session_state.next_isp_id,
            'analyzed_keywords': {str(k): list(v) for k, v in st.session_state.analyzed_keywords.items()},
            'language': st.session_state.language
        }
        json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(SessionDB.DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (timestamp, session_data) VALUES (?, ?)", (timestamp, json_data))
        conn.commit()
        conn.close()
        return timestamp

    @staticmethod
    def get_sessions():
        """Retrieve a list of saved sessions (id and timestamp) from the database."""
        conn = sqlite3.connect(SessionDB.DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp FROM sessions ORDER BY id DESC")
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    @staticmethod
    def load_session(session_id):
        """Load a session from the database using the provided session ID."""
        conn = sqlite3.connect(SessionDB.DATABASE_FILE, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT session_data FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            session_data = json.loads(row[0])
            st.session_state.isps = session_data.get('isps', {})
            st.session_state.current_isp_id = session_data.get('current_isp_id')
            st.session_state.next_isp_id = session_data.get('next_isp_id', 1)
            
            # Convert analyzed keywords from list to set
            analyzed_keywords = session_data.get('analyzed_keywords', {})
            st.session_state.analyzed_keywords = {k: set(v) for k, v in analyzed_keywords.items()}
            
            st.session_state.language = session_data.get('language', 'Swedish')
            
            # Reset temporary analysis state
            st.session_state.current_keyword = None
            st.session_state.current_sentences = []
            st.session_state.current_index = 0
            st.session_state.classifications = []
            st.session_state.show_context = False

            # Ensure that ISP IDs are of type integer
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
        else:
            st.error("Session not found")
            return False
