import sqlite3
import pandas as pd
from pathlib import Path
import streamlit as st

DB_PATH = Path(__file__).parent.parent / "IDX-API" / "data" / "database.sqlite"

@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=3600)
def query_db(query: str, params: tuple = ()):
    conn = get_connection()
    if conn:
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            st.error(f"Error querying database: {e}")
            return pd.DataFrame()
    else:
        st.warning(f"Database not found at {DB_PATH}. Please ensure data sync has been run.")
        return pd.DataFrame()
