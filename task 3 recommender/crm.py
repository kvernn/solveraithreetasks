# D:\...\task 3 recommender\crm.py

import streamlit as st
import json
import datetime
from libsql_client import create_client

class ShoeCRM:
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
    async def log_event(event_type: str, event_data: dict, user_message: str = None, bot_response: str = None):
        """
        Creates a client, logs a single event to the database, and closes the client
        """
        client = ShoeCRM._get_client()
        try:
            await client.execute("""
            CREATE TABLE IF NOT EXISTS crm_events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                event_data TEXT,
                user_message TEXT,
                bot_response TEXT
            )
            """)

            await client.execute(
                "INSERT INTO crm_events (timestamp, event_type, event_data, user_message, bot_response) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.datetime.now().isoformat(),
                    event_type,
                    json.dumps(event_data),
                    user_message,
                    bot_response
                )
            )
            print(f"[DB LOG] Successfully logged event: {event_type}")

        except Exception as e:
            print(f"ERROR in CRM log_event: {e}")
            st.error(f"CRM Logging Failed: {e}")
        finally:
            await client.close()