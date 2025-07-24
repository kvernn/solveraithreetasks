import streamlit as st
from libsql_client import create_client
from datetime import datetime

class CoachingCRM:
    @staticmethod
    def _get_client():
        """
        Helper to create a client
        """
        url = st.secrets["TURSO_DATABASE_URL"]
        auth_token = st.secrets["TURSO_AUTH_TOKEN"]
        https_url = url.replace("libsql://", "https://")
        return create_client(url=https_url, auth_token=auth_token)

    @staticmethod
    async def ensure_tables_exist():
        """
        Creates tables if they don't exist
        """
        client = CoachingCRM._get_client()
        await client.batch([
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT,
                phone TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, session_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT, response_time_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ])
        await client.close()

    @staticmethod
    async def create_user(email: str, name: str = None, phone: str = None) -> int:
        """
        Creates a new user or gets the ID if they already exist
        """
        client = CoachingCRM._get_client()
        try:
            await CoachingCRM.ensure_tables_exist()
            rs = await client.execute("SELECT id FROM users WHERE email = ?", (email,))
            if len(rs.rows) > 0:
                return rs.rows[0][0]

            rs_insert = await client.execute(
                "INSERT INTO users (email, name, phone) VALUES (?, ?, ?)",
                (email, name, phone)
            )
            return rs_insert.last_insert_rowid
        except Exception as e:
            print(f"ERROR in create_user: {e}")
            st.error(f"CRM Error creating user: {e}")
            return None
        finally:
            await client.close()

    @staticmethod
    async def log_conversation(user_id: int, session_id: str, role: str, content: str, response_time_ms: int = None):
        """
        Logs a single message to the database
        """
        if user_id is None:
            st.warning("Cannot log conversation, user_id is None.")
            return

        client = CoachingCRM._get_client()
        try:
            await client.execute(
                "INSERT INTO conversations (user_id, session_id, role, content, response_time_ms) VALUES (?, ?, ?, ?, ?)",
                (user_id, session_id, role, content, response_time_ms)
            )
        except Exception as e:
            print(f"ERROR in log_conversation: {e}")
            st.error(f"CRM Error logging conversation: {e}")
        finally:
            await client.close()