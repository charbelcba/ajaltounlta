import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(page_title="الحضور - Ajaltoun", layout="wide")
st.title("Ajaltoun LTA - الحضور Attendance")

conn = sqlite3.connect("ajaltoun.sqlite", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
  date TEXT, num TEXT, nom TEXT, class TEXT, period TEXT, status TEXT
)""")
conn.commit()

# --- HAYDA L SERRR: VERSION COUNTER ---
# Kell ma tekbos New / Delete, mnzid l ra2em, w Streamlit byensa kell l 2adim
if 'reset_counter' not in st.session_state:
    st.session_state['reset_counter'] = 0
VER = st.session_state['reset_counter']

# --- 1. DATE + CLASS ---
c1, c2 = st.columns(2)
with c1:
    d = st.date_input("Date / التاريخ", date.today())
with c2:
    classes = pd.read_sql("SELECT DISTINCT CLASS FROM student ORDER BY CLASS", conn)['CLASS'].tolist()
    selected_class = st.selectbox("Class / الصف", classes)

exists = pd.read_sql(f"SELECT * FROM attendance WHERE date='{d}' AND class='{selected_class}'", conn)
if not exists.empty:
    st.info("⚠️ هيدا اليوم موجود قبل - عم تعمل Modify")
else:
    st.success("✨ يوم جديد - عم تعمل New")

# --- 2. KABSET ---
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("➕ New / جديد", use_container_width=True):
        conn.execute("DELETE FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
        conn.commit()
        st.session_state['reset_counter'] += 1
        st.rerun()
with b2:
    save_clicked = st.button("💾 Save / حفظ", type="primary", use_container_width=True)
with b3:
    if st.button("🗑️ Delete / حذف", use_container_width=True):
        conn.execute("DELETE FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
        conn.commit()
        st.session_state['reset_counter'] += 1
        st.success("Enmaha! - Deleted! - Raja3 kello حاضر")
        st.rerun()

# --- 3. L JADWAL ---
students = pd.read_sql(f"SELECT NUM, NAME FROM student WHERE CLASS='{selected_class}' ORDER BY NAME", conn)
st.write(f"الصف: **{selected_class}** | عدد التلاميذ: **{len(students)}** | {d}")

h = st.columns([0.6, 1.8, 1.2, 1.2, 1.8])
h[0].write("**Num**"); h[1].write("**اسم الطالب**"); h[2].write("**الحضور / الغياب**"); h[3].write("**برر؟**"); h[4].write("**شو التبرير؟**")

all_to_save = []

for _, row in students.iterrows():
    cols = st.columns([0.6, 1.8, 1.2, 1.2, 1.8])
    cols[0].write(row['NUM']); cols[1].write(row['NAME'])

    # 1. الحضور - DEFAULT: حاضر
    old = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='اليوم'", conn)
    idx = 1 if not old.empty and "غايب" in str(old.iloc[0,0]) else 0
    # L KEY FIHA VER - heik lamma tekbos New/Delete, l key btetsghayyar w Streamlit byensa l 2adim
    s = cols[2].selectbox(f"p_{row['NUM']}", ["حاضر ✅", "غايب ❌"], index=idx, key=f"V{VER}_{d}_{row['NUM']}_att", label_visibility="collapsed")

    # 2. برر؟ - DEFAULT: لم يبرر
    old_b = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='التبرير - برر'", conn)
    idx_b = 1 if not old_b.empty and "برر ✅" in str(old_b.iloc[0,0]) else 0
    b = cols[3].selectbox(f"b_{row['NUM']}", ["لم يبرر ❌", "برر ✅"], index=idx_b, key=f"V{VER}_{d}_{row['NUM']}_barar", label_visibility="collapsed")

    # 3. شو التبرير؟
    old_j = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='التبرير - شو'", conn)
    old_j_val = old_j.iloc[0,0] if not old_j.empty else ""
    justification = cols[4].text_input(f"j_{row['NUM']}", value=old_j_val, placeholder="مريض، ورقة طبيب...", key=f"V{VER}_{d}_{row['NUM']}_just", label_visibility="collapsed")

    all_to_save.append((row['NUM'], row['NAME'], s, b, justification))

if save_clicked:
    for num, name, s, b, justification in all_to_save:
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='اليوم'", (str(d), str(num)))
        conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "اليوم", s))
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='التبرير - برر'", (str(d), str(num)))
        if "غايب" in s:
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "التبرير - برر", b))
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='التبرير - شو'", (str(d), str(num)))
        if justification.strip() != "":
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "التبرير - شو", justification))
    conn.commit()
    st.success(f"T7afaz - Saved ✅")
    st.rerun()

# --- EXCEL ---
st.divider()
df_all = pd.read_sql(f"SELECT date as التاريخ, class as الصف, nom as 'اسم الطالب', period as الحصة, status as الحالة FROM attendance WHERE date='{d}' AND class='{selected_class}'", conn)
if not df_all.empty:
    pivot = df_all.pivot_table(index=['التاريخ','الصف','اسم الطالب'], columns='الحصة', values='الحالة', aggfunc='first')
    pivot = pivot.reindex(columns=["اليوم", "التبرير - برر", "التبرير - شو"]).reset_index()
    pivot.columns = ["التاريخ", "الصف", "اسم الطالب", "الحضور / الغياب", "برر؟", "شو التبرير؟"]
    st.dataframe(pivot, use_container_width=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, index=False)
    st.download_button("📥 تحميل Excel", data=output.getvalue(), file_name=f"attendance_{selected_class}_{d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")