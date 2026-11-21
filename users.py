import sqlite3
import streamlit as st
from auth import connect, hash_password, require_page, LEVELS, current_user

require_page('users')
st.title('User Management')
st.caption('Administrator only. Passwords are stored as secure hashes.')
STAFF_LEVELS = [99, 50, 20, 10]

with st.form('create_user', clear_on_submit=True):
    st.subheader('Add user')
    username = st.text_input('Username')
    password = st.text_input('Password (at least 12 characters)', type='password')
    level = st.selectbox('Level', STAFF_LEVELS, format_func=lambda n: f'{n} — {LEVELS[n]}')
    create = st.form_submit_button('Create user')
if create:
    if not username.strip() or len(password) < 12:
        st.error('Enter a username and password of at least 12 characters.')
    elif username.strip().casefold() == 'student':
        st.error('The username student is reserved for student login.')
    else:
        try:
            with connect() as con:
                con.execute('INSERT INTO users(username,password_hash,level,student_num,active) VALUES(?,?,?,NULL,1)',
                            (username.strip(), hash_password(password), level))
            st.success('User created successfully.')
            st.rerun()
        except sqlite3.IntegrityError:
            st.error('Username already exists.')
        except sqlite3.Error as exc:
            st.error(f'Database error: {exc}')

with connect() as con:
    users = [dict(r) for r in con.execute('SELECT id, username, level, active FROM users ORDER BY username')]
st.subheader('Existing users')
st.dataframe([{'Username': u['username'], 'Level': LEVELS.get(u['level'], str(u['level'])),
               'Active': bool(u['active'])} for u in users], use_container_width=True)

if users:
    user_ids = [u['id'] for u in users]
    by_id = {u['id']: u for u in users}
    selected_id = st.selectbox('Select user to edit', user_ids,
                               format_func=lambda uid: by_id[uid]['username'])
    selected = by_id[selected_id]
    st.subheader(f"Edit: {selected['username']}")
    with st.form(f'edit_user_{selected_id}'):
        new_level = st.selectbox('Level', STAFF_LEVELS,
                                 index=STAFF_LEVELS.index(selected['level']) if selected['level'] in STAFF_LEVELS else 0,
                                 format_func=lambda n: f'{n} — {LEVELS[n]}')
        active = st.checkbox('Active', value=bool(selected['active']))
        new_password = st.text_input('New password (leave blank to keep)', type='password')
        update = st.form_submit_button('Update user')
    if update:
        if new_password and len(new_password) < 12:
            st.error('New password must have at least 12 characters.')
        elif selected_id == current_user()['id'] and (new_level != 99 or not active):
            st.error('You cannot remove your own administrator access. Use another administrator account.')
        else:
            try:
                with connect() as con:
                    # Read the current database state, not a stale widget value.
                    row = con.execute('SELECT level,active FROM users WHERE id=?', (selected_id,)).fetchone()
                    if row is None:
                        st.error('User no longer exists.')
                    elif row['level'] == 99 and (new_level != 99 or not active) and con.execute(
                        'SELECT COUNT(*) FROM users WHERE level=99 AND active=1'
                    ).fetchone()[0] <= 1:
                        st.error('At least one active administrator must remain.')
                    else:
                        if new_password:
                            con.execute('UPDATE users SET level=?,student_num=NULL,active=?,password_hash=? WHERE id=?',
                                        (new_level, int(active), hash_password(new_password), selected_id))
                        else:
                            con.execute('UPDATE users SET level=?,student_num=NULL,active=? WHERE id=?',
                                        (new_level, int(active), selected_id))
                        st.session_state['user_update_notice'] = f"Updated {selected['username']} to {LEVELS[new_level]}."
                if 'user_update_notice' in st.session_state:
                    st.rerun()
            except sqlite3.Error as exc:
                st.error(f'Database error: {exc}')

if st.session_state.pop('user_update_notice', None):
    st.success('User updated successfully. The list now reflects the saved database values.')
