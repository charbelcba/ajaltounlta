import streamlit as st
from auth import require_page, current_user
require_page('mygrades')
user = current_user()
st.title('My Grades')
if user['level'] == 1:
    st.info(f"Student number: {user['student_num']}")
else:
    st.info('Administrator preview: student selection not configured.')
st.warning('Grade display is not yet connected. The exam table schema must be checked before implementing student-specific queries. Do not use an unfiltered exam query here.')
