import sqlite3
import streamlit as st
import pandas as pd

DB_PATH = "ajaltoun.sqlite"
col1,col2 = st.columns(2)
with col1:
     st.image("ajaltoun.png",caption="TEL:09 236075",width=100)
     #st.title("AJALTOUN STUDENT NAME",width="stretch")
     #st.image("ajaltoun.png",caption="Ecole Technique Ajaltoun TEL:09 236075",width=150)
with col2:
    st.title("AJALTOUN STUDENT NAME",width="stretch")

search = st.text_input("SEARCH")

conn = sqlite3.connect(DB_PATH)
if search:
    df = pd.read_sql("""
        SELECT NAME, PHONE, PARENT_PH as PARENT_PHONE,CLASS,ADDRESS
        FROM ajaltoun
        WHERE CAST(NAME AS TEXT) LIKE ? OR CAST(CLASS AS TEXT) LIKE ?
    """, conn, params=(f"%{search}%", f"%{search}%"))
else:
    df = pd.read_sql("""
        SELECT NAME, PHONE, PARENT_PH as PARENT_PHONE,CLASS,ADDRESS
        FROM ajaltoun
    """, conn)
conn.close()
st.caption(f"Showing {len(df)} rows")
st.dataframe(df, use_container_width=True)
