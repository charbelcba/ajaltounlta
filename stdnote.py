"""Student Notes: Streamlit + SQLite (ajaltoun.sqlite)."""
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "ajaltoun.sqlite"


def connect():
    return sqlite3.connect(DB_PATH)


def initialize():
    """Create notes table; migrate the old one-note-per-student schema safely."""
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='stdnote'").fetchone()
        if not exists:
            conn.execute('''CREATE TABLE stdnote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL, num INTEGER NOT NULL,
                name TEXT, class TEXT, description TEXT)''')
        else:
            columns = {r[1] for r in conn.execute('PRAGMA table_info("stdnote")')}
            if 'id' not in columns:
                conn.execute('''CREATE TABLE stdnote_migrating (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL, num INTEGER NOT NULL,
                    name TEXT, class TEXT, description TEXT)''')
                conn.execute('''INSERT INTO stdnote_migrating (date,num,name,class,description)
                    SELECT date,num,name,class,description FROM stdnote''')
                conn.execute('DROP TABLE stdnote')
                conn.execute('ALTER TABLE stdnote_migrating RENAME TO stdnote')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_stdnote_student ON stdnote(num,date)')


def students():
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='student'").fetchone():
            return None
        return conn.execute('SELECT num,name,class FROM student ORDER BY name,num').fetchall()


def notes_for_student(num):
    with connect() as conn:
        return conn.execute('''SELECT id,date,description FROM stdnote
            WHERE num=? ORDER BY date DESC,id DESC''', (num,)).fetchall()


def get_note(note_id, num):
    with connect() as conn:
        return conn.execute('''SELECT id,date,description FROM stdnote
            WHERE id=? AND num=?''', (note_id, num)).fetchone()


def all_notes():
    with connect() as conn:
        return conn.execute('''SELECT date,num,name,class,description FROM stdnote
            ORDER BY date DESC,id DESC''').fetchall()


def reset_editor():
    st.session_state['record_date'] = date.today()
    st.session_state['record_description'] = ''


def new_note():
    st.session_state['mode'] = 'new'
    st.session_state['note_choice'] = None
    reset_editor()
    st.session_state['notice'] = None


def class_changed():
    # Runs before widgets are instantiated on the next rerun.
    st.session_state['student_choice'] = None
    st.session_state['selected_student'] = None
    st.session_state['note_choice'] = None
    st.session_state['pending_note_id'] = None
    st.session_state['mode'] = 'view'
    reset_editor()


def student_changed():
    st.session_state['selected_student'] = st.session_state['student_choice']
    st.session_state['mode'] = 'view'
    st.session_state['note_choice'] = None
    reset_editor()


def note_changed():
    st.session_state['mode'] = 'view'
    note_id = st.session_state['note_choice']
    num = st.session_state['selected_student']
    note = get_note(note_id, num) if note_id is not None else None
    if note:
        try:
            st.session_state['record_date'] = date.fromisoformat(note[1])
        except (TypeError, ValueError):
            st.session_state['record_date'] = date.today()
        st.session_state['record_description'] = note[2] or ''
    else:
        reset_editor()


def begin_modify():
    if st.session_state['note_choice'] is not None:
        st.session_state['mode'] = 'edit'


def delete_selected():
    note_id = st.session_state['note_choice']
    num = st.session_state['selected_student']
    if note_id is None or num is None:
        st.session_state['notice'] = ('error', 'Select an existing note to delete.')
        return
    try:
        with connect() as conn:
            cur = conn.execute('DELETE FROM stdnote WHERE id=? AND num=?', (note_id, num))
            deleted = cur.rowcount
        st.session_state['note_choice'] = None
        st.session_state['mode'] = 'view'
        reset_editor()
        st.session_state['notice'] = ('success', 'Note deleted successfully.') if deleted else ('error', 'Note not found.')
    except sqlite3.Error as exc:
        st.session_state['notice'] = ('error', f'Could not delete note: {exc}')


st.set_page_config(page_title='Student Notes', layout='wide')
try:
    initialize()
    student_rows = students()
except (sqlite3.Error, ValueError) as exc:
    st.error(f'Database error: {exc}')
    st.stop()

st.title('Student Notes')
#st.caption('Database: ajaltoun.sqlite | Student lookup: student | Notes: stdnote')
if student_rows is None:
    st.error('The student table was not found in ajaltoun.sqlite.')
    st.stop()
if not student_rows:
    st.warning('The student table is empty.')
    st.stop()

student_by_num = {r[0]: r for r in student_rows}
defaults = {
    'student_choice': None, 'selected_student': None,
    'note_choice': None, 'mode': 'view',
    'record_date': date.today(), 'record_description': '', 'notice': None,
    'pending_note_id': None, 'class_filter': 'All Classes',
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Filter students by class before creating the student lookup widget.
classes = sorted({str(r[2]).strip() for r in student_rows if r[2] is not None and str(r[2]).strip()}, key=str.casefold)
class_options = ['All Classes'] + classes
if st.session_state['class_filter'] not in class_options:
    st.session_state['class_filter'] = 'All Classes'

c1,c2 = st.columns(2)
with c1:
    st.selectbox('Choose Class', class_options, key='class_filter', on_change=class_changed)


chosen_class = st.session_state['class_filter']


filtered_students = {
    n: row for n, row in student_by_num.items()
    if chosen_class == 'All Classes' or str(row[2] or '').strip() == chosen_class
    }

# Guard against stale selection if the database has changed.
if st.session_state['student_choice'] not in filtered_students:
   st.session_state['student_choice'] = None
   st.session_state['selected_student'] = None

with c2:
     st.selectbox('Find student number or name', list(filtered_students),
       format_func=lambda n: f'{n} - {filtered_students[n][1]}',
       index=None, placeholder='Search student number or name...',
       key='student_choice', on_change=student_changed)
st.caption(f'{len(filtered_students)} student(s) in selected class.')

num = st.session_state['selected_student']
if num is None or num not in student_by_num:
    st.info('Select a student to view or create notes.')
else:
    _, student_name, student_class = student_by_num[num]
    d1,d2,d3 = st.columns(3)
    with d1:
        st.text_input('Student Number', value=str(num), disabled=True)
    with d2:
        st.text_input('Name', value=student_name or '', disabled=True)
    with d3:
        st.text_input('Class', value=student_class or '', disabled=True)

    existing = notes_for_student(num)
    note_options = [r[0] for r in existing]
    note_labels = {r[0]: f'{r[1]} | Note #{r[0]} | {(r[2] or "")[:60]}' for r in existing}
    # Apply post-save selection before instantiating the note_choice widget.
    pending_id = st.session_state.pop('pending_note_id', None)
    if pending_id is not None and pending_id in note_options:
        st.session_state['note_choice'] = pending_id
        saved_note = get_note(pending_id, num)
        if saved_note:
            try:
                st.session_state['record_date'] = date.fromisoformat(saved_note[1])
            except (TypeError, ValueError):
                st.session_state['record_date'] = date.today()
            st.session_state['record_description'] = saved_note[2] or ''
    if st.session_state['note_choice'] not in note_options:
        st.session_state['note_choice'] = None
        if st.session_state['mode'] == 'edit':
            st.session_state['mode'] = 'view'
    st.selectbox('Existing notes', note_options,
        format_func=lambda i: note_labels[i], index=None,
        placeholder='Choose a note to view, modify, or delete',
        key='note_choice', on_change=note_changed)

    selected = st.session_state['note_choice'] is not None
    c1, c2, c3 = st.columns(3)
    c1.button('New', on_click=new_note, use_container_width=True)
    c2.button('Modify', on_click=begin_modify, disabled=not selected,
              use_container_width=True)
    c3.button('Delete', on_click=delete_selected, disabled=not selected,
              use_container_width=True)

    notice = st.session_state.pop('notice', None)
    if notice:
        if notice[0] == 'success':
            st.success(notice[1])
        else:
            st.error(notice[1])

    mode = st.session_state['mode']
    st.caption({'view': 'View mode: click New or select a note and click Modify.',
                'new': 'New mode: enter a date and description, then click Save.',
                'edit': 'Modify mode: change the note, then click Save.'}[mode])
    with st.form('note_form'):
        dt = st.date_input('Date', key='record_date', disabled=(mode == 'view'))
        description = st.text_area('Description', key='record_description',
                                   height=140, disabled=(mode == 'view'))
        save = st.form_submit_button('Save', type='primary', disabled=(mode == 'view'))

    if save:
        try:
            with connect() as conn:
                if mode == 'new':
                    cur = conn.execute('''INSERT INTO stdnote (date,num,name,class,description)
                        VALUES (?,?,?,?,?)''', (dt.isoformat(), num, student_name,
                                               student_class, description))
                    saved_id = cur.lastrowid
                    success_message = 'New student note saved successfully.'
                elif mode == 'edit' and selected:
                    cur = conn.execute('''UPDATE stdnote SET date=?,name=?,class=?,description=?
                        WHERE id=? AND num=?''', (dt.isoformat(), student_name,
                        student_class, description, st.session_state['note_choice'], num))
                    if cur.rowcount == 0:
                        raise ValueError('Note not found.')
                    saved_id = st.session_state['note_choice']
                    success_message = 'Student note updated successfully.'
                else:
                    raise ValueError('Click New or Modify before saving.')
            st.session_state['mode'] = 'view'
            st.session_state['pending_note_id'] = saved_id
            st.session_state['notice'] = ('success', success_message)
            st.rerun()
        except (sqlite3.Error, ValueError) as exc:
            st.error(f'Could not save note: {exc}')

st.subheader('Student Notes Records')
records = all_notes()
if records:
    st.dataframe(pd.DataFrame(records,
        columns=['date', 'num', 'name', 'class', 'description']),
        use_container_width=True, hide_index=True)
else:
    st.info('No notes yet.')
