import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

st.set_page_config(page_title="الحضور - Ajaltoun", layout="wide")
st.title("Ajaltoun LTA - الحضور Attendance")

DB = "ajaltoun.sqlite"

# --- HEIK MNOFTOH W MNSEKKER DEGHE - MA BA2A FI LOCKED ---
def get_conn():
    c = sqlite3.connect(DB, check_same_thread=False, timeout=10)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout = 5000")
    return c

def run_query(q, params=()):
    c = get_conn()
    try:
        df = pd.read_sql(q, c, params=params)
        return df
    finally:
        c.close()

def run_exec(q, params=()):
    c = get_conn()
    try:
        c.execute(q, params)
        c.commit()
    finally:
        c.close()

# Khol2o l table marra
c0 = get_conn()
c0.execute("""CREATE TABLE IF NOT EXISTS attendance (
  date TEXT, num TEXT, nom TEXT, class TEXT, period TEXT, status TEXT
)""")
c0.commit()
c0.close()

if 'reset_counter' not in st.session_state:
    st.session_state['reset_counter'] = 0
VER = st.session_state['reset_counter']

# --- 1. DATE + CLASS ---
c1, c2 = st.columns(2)
with c1:
    d = st.date_input("Date / التاريخ", date.today())
with c2:
    classes = run_query("SELECT DISTINCT CLASS FROM student ORDER BY CLASS")['CLASS'].tolist()
    selected_class = st.selectbox("Class / الصف", classes)

exists = run_query("SELECT * FROM attendance WHERE date=? AND class=? AND period='الحصة 1'", (str(d), selected_class))
if not exists.empty:
    st.info("⚠️ هيدا اليوم موجود قبل - عم تعمل Modify")
else:
    st.success("✨ يوم جديد - عم تعمل New")

# --- 2. KABSET ---
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("➕ New / جديد", use_container_width=True):
        run_exec("DELETE FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
        st.session_state['reset_counter'] += 1
        st.rerun()
with b2:
    save_clicked = st.button("💾 Save / حفظ", type="primary", use_container_width=True)
with b3:
    if st.button("🗑️ Delete / حذف", use_container_width=True):
        run_exec("DELETE FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
        st.session_state['reset_counter'] += 1
        st.success("Enmaha! - Raja3 kello ✅")
        st.rerun()

# --- 3. L JADWAL - 8 7ESAS, BALA NUM ---
students = run_query("SELECT NUM, NAME FROM student WHERE CLASS=? ORDER BY NAME", (selected_class,))
st.write(f"الصف: **{selected_class}** | {d} | عدد التلاميذ: **{len(students)}** | ✅ = حاضر | ❌ = غايب")

periods = ["الحصة 1","الحصة 2","الحصة 3","الحصة 4","الحصة 5","الحصة 6","الحصة 7","الحصة 8"]

h = st.columns([2.2] + [1.1]*8)
h[0].write("**اسم الطالب**")
for i, p in enumerate(periods):
    h[1+i].write(f"**{p}**")

all_to_save = []

for _, row in students.iterrows():
    cols = st.columns([2.2] + [1.1]*8)
    cols[0].write(row['NAME'])
    row_data = {}
    for i, p in enumerate(periods):
        old = run_query("SELECT status FROM attendance WHERE date=? AND num=? AND period=?", (str(d), str(row['NUM']), p))
        old_val = str(old.iloc[0,0]) if not old.empty else ""
        idx = 1 if ("غايب" in old_val or old_val.strip() in ["X", "❌"]) else 0
        s = cols[1+i].selectbox(f"{p}_{row['NUM']}", ["✅", "❌"], index=idx, key=f"V{VER}_{d}_{row['NUM']}_{i}", label_visibility="collapsed")
        row_data[p] = s
    all_to_save.append((row['NUM'], row['NAME'], row_data))

if save_clicked:
    c = get_conn()
    try:
        for num, name, row_data in all_to_save:
            for p in periods:
                c.execute("DELETE FROM attendance WHERE date=? AND num=? AND period=?", (str(d), str(num), p))
                c.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, p, row_data[p]))
        c.commit()
    finally:
        c.close()
    st.success("T7afaz - Saved ✅")
    st.rerun()

# --- DOWNLOAD ---
st.divider()
df_all = run_query("SELECT date as التاريخ, class as الصف, nom as 'اسم الطالب', period as الحصة, status as الحالة FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
if not df_all.empty:
    pivot = df_all.pivot_table(index=['التاريخ','الصف','اسم الطالب'], columns='الحصة', values='الحالة', aggfunc='first')
    pivot = pivot.reindex(columns=periods).reset_index()
    pivot.columns = ["التاريخ", "الصف", "اسم الطالب"] + periods
    st.dataframe(pivot, use_container_width=True)
    csv_data = pivot.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 تحميل Excel / CSV", data=csv_data, file_name=f"attendance_{selected_class}_{d}.csv", mime="text/csv")