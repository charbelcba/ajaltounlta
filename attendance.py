import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os
from io import BytesIO

st.set_page_config(page_title="الحضور - Ajaltoun", layout="wide")
st.title("Ajaltoun LTA - الحضور Attendance")

conn = sqlite3.connect("ajaltoun.sqlite", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
  date TEXT, num TEXT, nom TEXT, class TEXT, period TEXT, status TEXT
)""")
conn.commit()

# --- LISTET L TBRIRAT MEN L FILE ---
if os.path.exists("justifications.txt"):
    with open("justifications.txt", encoding="utf-8") as f:
        just_list = [l.strip() for l in f if l.strip() != ""]
else:
    just_list = ["مريض", "ورقة طبيب", "سفر", "ظرف عائلي", "تأخر", "غيره..."]
if "غيره..." not in just_list:
    just_list.append("غيره...")

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

exists = pd.read_sql(f"SELECT * FROM attendance WHERE date='{d}' AND class='{selected_class}' AND period='الحصة 1'", conn)
if not exists.empty:
    st.info("⚠️ هيدا اليوم موجود قبل - عم تعمل Modify")
else:
    st.success("✨ يوم جديد - عم تعمل New")

# --- 2. KABSET ---
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("➕ New / جديد", use_container_width=True):
        conn.execute("DELETE FROM attendance WHERE date=? AND class=? AND period IN ('الحصة 1','التبرير - برر','التبرير - شو')", (str(d), selected_class))
        conn.commit()
        st.session_state['reset_counter'] += 1
        st.rerun()
with b2:
    save_clicked = st.button("💾 Save / حفظ", type="primary", use_container_width=True)
with b3:
    if st.button("🗑️ Delete / حذف", use_container_width=True):
        conn.execute("DELETE FROM attendance WHERE date=? AND class=? AND period IN ('الحصة 1','التبرير - برر','التبرير - شو')", (str(d), selected_class))
        conn.commit()
        st.session_state['reset_counter'] += 1
        st.success("Enmaha! - Raja3 kello ✅")
        st.rerun()

# --- 3. L JADWAL - BALA NUM ---
students = pd.read_sql(f"SELECT NUM, NAME FROM student WHERE CLASS='{selected_class}' ORDER BY NAME", conn)
st.write(f"الصف: **{selected_class}** | {d} | عدد التلاميذ: **{len(students)}**")

h = st.columns([1.8, 1.1, 1.1, 1.8])
h[0].write("**اسم الطالب**")
h[1].write("**الحضور / الغياب**")
h[2].write("**برر؟**")
h[3].write("**شو التبرير؟**")

all_to_save = []

for _, row in students.iterrows():
    cols = st.columns([1.8, 1.1, 1.1, 1.8])
    cols[0].write(row['NAME'])

    # 1. الحضور - الحصة 1 - ✅ / ❌ BAS
    old = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='الحصة 1'", conn)
    old_val = str(old.iloc[0,0]) if not old.empty else ""
    idx = 1 if ("غايب" in old_val or old_val.strip() in ["X", "❌"]) else 0
    s = cols[1].selectbox(f"p_{row['NUM']}", ["✅", "❌"], index=idx, key=f"V{VER}_{d}_{row['NUM']}_att", label_visibility="collapsed")

    # 2. برر؟ - METEL MA HIYE
    old_b = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='التبرير - برر'", conn)
    idx_b = 1 if not old_b.empty and "برر ✅" in str(old_b.iloc[0,0]) else 0
    b = cols[2].selectbox(f"b_{row['NUM']}", ["لم يبرر ❌", "برر ✅"], index=idx_b, key=f"V{VER}_{d}_{row['NUM']}_barar", label_visibility="collapsed")

    # 3. شو التبرير؟ - LISTE MEN L FILE
    old_j = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='التبرير - شو'", conn)
    old_j_val = old_j.iloc[0,0] if not old_j.empty else ""
    if old_j_val in just_list:
        idx_j = just_list.index(old_j_val)
        custom_val = ""
    elif old_j_val != "":
        idx_j = just_list.index("غيره...")
        custom_val = old_j_val
    else:
        idx_j = 0
        custom_val = ""

    # L LISTE
    just_choice = cols[3].selectbox(f"j_{row['NUM']}", just_list, index=idx_j, key=f"V{VER}_{d}_{row['NUM']}_just", label_visibility="collapsed")
    # Iza na2a غيره, byebayyan m3a7al ktebe
    if just_choice == "غيره...":
        justification = st.text_input(f"ktob tbrir jdid la {row['NAME']}", value=custom_val, placeholder="ktob l tbrir hon...", key=f"V{VER}_{d}_{row['NUM']}_custom")
    else:
        justification = just_choice

    all_to_save.append((row['NUM'], row['NAME'], s, b, justification))

if save_clicked:
    for num, name, s, b, justification in all_to_save:
        # الحصة 1 - HEIK BYERBAT MA3 L FORM L 8 7ESAS
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='الحصة 1'", (str(d), str(num)))
        conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "الحصة 1", s))
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='التبرير - برر'", (str(d), str(num)))
        if "❌" in s:
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "التبرير - برر", b))
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='التبرير - شو'", (str(d), str(num)))
        if justification.strip() != "" and justification.strip() != "غيره...":
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(num), str(name), selected_class, "التبرير - شو", justification))
    conn.commit()
    st.success("T7afaz - Saved ✅")
    st.rerun()

# --- DOWNLOAD ---
st.divider()
df_all = pd.read_sql(f"SELECT date as التاريخ, class as الصف, nom as 'اسم الطالب', period as الحصة, status as الحالة FROM attendance WHERE date='{d}' AND class='{selected_class}'", conn)
if not df_all.empty:
    pivot = df_all.pivot_table(index=['التاريخ','الصف','اسم الطالب'], columns='الحصة', values='الحالة', aggfunc='first')
    pivot = pivot.reindex(columns=["الحصة 1", "التبرير - برر", "التبرير - شو"]).reset_index()
    pivot.columns = ["التاريخ", "الصف", "اسم الطالب", "الحضور / الغياب", "برر؟", "شو التبرير؟"]
    st.dataframe(pivot, use_container_width=True)
    csv_data = pivot.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 تحميل Excel / CSV", data=csv_data, file_name=f"attendance_{selected_class}_{d}.csv", mime="text/csv")