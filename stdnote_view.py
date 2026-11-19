"""Read-only Student Notes report filtered by date and class."""
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "ajaltoun.sqlite"
st.set_page_config(page_title="Student Notes by Date and Class", layout="wide")
st.title("Student Notes — Date and Class")

if not DB_PATH.is_file():
    st.error(f"Database not found: {DB_PATH}. Put this program in the same folder as ajaltoun.sqlite.")
    st.stop()

try:
    with sqlite3.connect(DB_PATH) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "stdnote" not in tables:
            st.error("Table 'stdnote' was not found in ajaltoun.sqlite.")
            st.stop()
        note_cols = {r[1] for r in conn.execute('PRAGMA table_info("stdnote")')}
        required = {"date", "num", "description"}
        if not required.issubset(note_cols):
            st.error("stdnote must contain date, num, and description columns.")
            st.stop()

        # Prefer the current student class/name; use the saved note fields as fallback.
        student_ok = False
        if "student" in tables:
            student_cols = {r[1] for r in conn.execute('PRAGMA table_info("student")')}
            student_ok = {"num", "name", "class"}.issubset(student_cols)
        if student_ok:
            name_expr = 'COALESCE(NULLIF(s.name, ""), n.name)' if 'name' in note_cols else 's.name'
            class_expr = 'COALESCE(NULLIF(s."class", ""), n."class")' if 'class' in note_cols else 's."class"'
            from_clause = 'FROM stdnote n LEFT JOIN student s ON s.num = n.num'
        else:
            name_expr = 'n.name' if 'name' in note_cols else "''"
            class_expr = 'n."class"' if 'class' in note_cols else "''"
            from_clause = 'FROM stdnote n'

        # Pull just the fields needed; filtering and display are read-only.
        records = pd.read_sql_query(
            f'''SELECT n.date AS note_date, n.num AS student_num,
                {name_expr} AS student_name, {class_expr} AS student_class,
                n.description AS description
                {from_clause}''', conn
        )
except (sqlite3.Error, pd.errors.DatabaseError) as exc:
    st.error(f"Unable to read the database: {exc}")
    st.stop()

if records.empty:
    st.info("There are no student notes to display yet.")
    st.stop()

records['parsed_date'] = pd.to_datetime(records['note_date'], errors='coerce').dt.date
records['student_class'] = records['student_class'].fillna('').astype(str)
records['student_name'] = records['student_name'].fillna('').astype(str)
records['description'] = records['description'].fillna('').astype(str)

valid_dates = sorted(records['parsed_date'].dropna().unique(), reverse=True)
if not valid_dates:
    st.warning("No valid dates were found in stdnote. Dates should use YYYY-MM-DD format.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input("Choose note date", value=valid_dates[0])
with col2:
    classes_for_date = sorted(records.loc[records['parsed_date'] == selected_date, 'student_class'].unique().tolist())
    selected_class = st.selectbox("Choose class", ["All classes"] + classes_for_date)

filtered = records[records['parsed_date'] == selected_date].copy()
if selected_class != "All classes":
    filtered = filtered[filtered['student_class'] == selected_class]
filtered = filtered.sort_values(['student_class', 'student_name', 'student_num'])

st.subheader(f"Notes for {selected_date.strftime('%d/%m/%Y')}")
st.write(f"**{len(filtered)} note(s)** found")
if filtered.empty:
    st.info("No notes found for the selected date and class.")
else:
    display = filtered.rename(columns={
        'student_num': 'Number', 'student_name': 'Name',
        'student_class': 'Class', 'description': 'Description'
    })[['Number', 'Name', 'Class', 'Description']]
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download results as CSV",
        data=display.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"student_notes_{selected_date.isoformat()}.csv",
        mime="text/csv",
    )

st.caption("Read-only report: this program does not change or delete database records.")
