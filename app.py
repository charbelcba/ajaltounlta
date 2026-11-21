from pathlib import Path
import sqlite3
import time
import streamlit as st
from auth import init_db, has_users, create_first_admin, authenticate, current_user, allowed, LEVELS

st.set_page_config(page_title='Ajaltoun LTA', page_icon='🎓', layout='wide')
BASE = Path(__file__).resolve().parent
DB_PATH = BASE / 'ajaltoun.sqlite'
logo = BASE / 'ajaltoun.png'
init_db()


def find_student(student_number):
    """Return a student only for an exact matching student number."""
    number = student_number.strip()
    if not number or not number.isdecimal():
        return None
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT NUM, NAME, CLASS FROM student WHERE CAST(NUM AS TEXT) = ?',
            (number,),
        ).fetchone()
    return dict(row) if row else None


def student_session_user(student):
    return {
        'username': 'student',
        'level': 1,
        'student_num': str(student['NUM']),
        'student_name': student['NAME'],
        'student_class': student['CLASS'],
        'student_login': True,
    }


if not has_users():
    st.title('Ajaltoun LTA — First Administrator Setup')
    st.info('This setup appears only while the users table is empty. Choose a strong password.')
    with st.form('setup'):
        username = st.text_input('Administrator username')
        password = st.text_input('New password (12+ characters)', type='password')
        confirm = st.text_input('Confirm password', type='password')
        submitted = st.form_submit_button('Create administrator')
    if submitted:
        if password != confirm:
            st.error('Passwords do not match.')
        else:
            try:
                create_first_admin(username, password)
                st.success('Administrator created. Log in below.')
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    st.stop()

# Student sessions are handled explicitly; staff sessions keep using auth.py.
student_user = st.session_state.get('student_portal_user')
user = student_user if student_user else current_user()

if not user:
    left, center, right = st.columns([1, 2, 1])
    with center:
        if logo.exists():
            st.image(str(logo), width=225, caption='TEL: 09 236075')
        st.title('Ajaltoun LTA Login')
        with st.form('login'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            submitted = st.form_submit_button('Login')
        if submitted:
            if username.strip().lower() == 'student':
                student = find_student(password)
                if student:
                    st.session_state['student_portal_user'] = student_session_user(student)
                    # Keep these keys available to existing exam.py integrations.
                    st.session_state['student_num'] = str(student['NUM'])
                    st.rerun()
                else:
                    st.error('Invalid username or password.')
            else:
                result = authenticate(username, password)
                if result:
                    st.session_state['user'] = result
                    st.session_state.pop('student_portal_user', None)
                    st.session_state.pop('student_num', None)
                    st.rerun()
                else:
                    st.error('Invalid username or password.')
    st.stop()

if logo.exists():
    st.logo(str(logo))

is_student = bool(user.get('student_login')) and user.get('level') == 1
with st.sidebar:
    if is_student:
        st.write(f"Student: **{user['student_name']}**")
        st.caption(f"Class: {user['student_class']}")
        st.caption('Role: Student (1)')
    else:
        st.write(f"Logged in: **{user['username']}**")
        st.caption(f"Role: {LEVELS.get(user['level'], 'User')} ({user['level']})")
    if st.button('Logout'):
        st.session_state.pop('user', None)
        st.session_state.pop('student_portal_user', None)
        st.session_state.pop('student_num', None)
        st.rerun()
#('mygrades', 'mygrades.py', 'MY GRADES', '📊'),
page_definitions = [
    ('hello', 'hello.py', 'WELCOME TO AJALTOUN LTA', '👋'),
    ('app2', 'app2.py', 'Ajaltoun Student', '🎓'),
    ('exam', 'exam.py', 'EXAM', '✏️'),
    ('stdnote', 'stdnote.py', 'STUDENT NOTE', '📖'),
    ('stdnote_view', 'stdnote_view.py', 'VIEW STUDENT NOTE', '🔍'),
    ('attendance', 'attendance.py', 'VIEW ATTENDANCE', '🕐'),
    ('attendanceall', 'attendanceall.py', 'VIEW ATTENDANCE ALL', '✅'),    
    ('users', 'users.py', 'USER MANAGEMENT', '🔐'),
]
pages = []
for key, filename, title, icon in page_definitions:
    # Student login is restricted to EXAM; staff permissions stay in auth.py.
    authorized = (key == 'exam') if is_student else allowed(key, user)
    if authorized:
        if (BASE / filename).is_file():
            pages.append(st.Page(str(BASE / filename), title=title, icon=icon))
        else:
            st.sidebar.warning(f'Missing page: {filename}')
if not pages:
    st.error('No authorized pages are available.')
    st.stop()
st.navigation(pages).run()
