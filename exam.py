from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd
from auth import current_user, allowed

DB_PATH = Path(__file__).resolve().parent / 'ajaltoun.sqlite'
student = st.session_state.get('student_portal_user')
user = student if student else current_user()
if not user:
    st.error('Please log in first.')
    st.stop()

is_student = bool(student) and user.get('student_login') and user.get('level') == 1
if not is_student and not allowed('exam', user):
    st.error('You do not have permission to view this page.')
    st.stop()

st.title('AJALTOUN STUDENT')
if is_student:
    number = str(user['student_num'])
    st.write(f"**Student:** {user['student_name']}")
    st.write(f"**Class:** {user['student_class']}")
else:
    number = st.text_input('Search Number رقم الطالب').strip()

columns = ['اسم الطالب', 'الصف', 'اسم المادة', 'العلامة النهائية /20', 'النتيجة']
if number:
    with sqlite3.connect(str(DB_PATH)) as conn:
        df = pd.read_sql_query('''
            SELECT nom AS "اسم الطالب", class AS "الصف",
                   subject AS "اسم المادة", rate AS "العلامة النهائية /20",
                   result AS "النتيجة"
            FROM exam WHERE CAST(num AS TEXT) = ?
        ''', conn, params=(number,))
    if not df.empty:
        if not is_student:
            st.caption(f"{df.iloc[0]['اسم الطالب']} — {df.iloc[0]['الصف']}")
        df = df.drop(columns=['اسم الطالب', 'الصف'])
    else:
        st.info('No exam results found for this student.')
else:
    df = pd.DataFrame(columns=columns)
st.dataframe(df, use_container_width=True)
