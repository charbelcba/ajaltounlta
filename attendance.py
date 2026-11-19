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

# --- 1. ENTA BTNA22E BAS DATE + CLASS ---
c1, c2 = st.columns(2)
with c1:
    d = st.date_input("Date / التاريخ", date.today())
with c2:
    classes = pd.read_sql("SELECT DISTINCT CLASS FROM student ORDER BY CLASS", conn)['CLASS'].tolist()
    selected_class = st.selectbox("Class / الصف", classes)

# Chouf iza mawjoud abl walla la2
exists = pd.read_sql(f"SELECT * FROM attendance WHERE date='{d}' AND class='{selected_class}'", conn)
if not exists.empty:
    st.info(f"⚠️ هيدا اليوم موجود قبل - عم تعمل Modify - عدّل و اعمل Save")
else:
    st.success(f"✨ يوم جديد - عم تعمل New - حط الحضور و اعمل Save")

# --- 2. L KABSET ---
b1, b2, b3 = st.columns(3)
with b1:
    new_clicked = st.button("➕ New / جديد", use_container_width=True)
with b2:
    save_clicked = st.button("💾 Save / حفظ", type="primary", use_container_width=True)
with b3:
    delete_clicked = st.button("🗑️ Delete / حذف", use_container_width=True)

if delete_clicked:
    conn.execute("DELETE FROM attendance WHERE date=? AND class=?", (str(d), selected_class))
    conn.commit()
    st.warning("Enmaha! - Deleted! 3mol New la terja3 tkhle2a")
    st.rerun()

if new_clicked:
    # New = iza mawjoud, ma byem7e, bas byefarjiik yeha la t3addel
    # Iza baddak New ndif 100%, 3mol Delete abl
    st.rerun()

# --- 3. L JADWAL - BYEKBOLAK KELLO DEGHRE ---
students = pd.read_sql(f"SELECT NUM, NAME FROM student WHERE CLASS='{selected_class}' ORDER BY NAME", conn)
st.write(f"الصف: **{selected_class}** | عدد التلاميذ: **{len(students)}** | {d}")

h = st.columns([0.5, 1.5] + [0.8]*8 + [1.5])
h[0].write("**Num**"); h[1].write("**اسم الطالب**")
for i in range(8): h[2+i].write(f"**الحصة {i+1}**")
h[10].write("**التبرير**")

for _, row in students.iterrows():
    cols = st.columns([0.5, 1.5] + [0.8]*8 + [1.5])
    cols[0].write(row['NUM']); cols[1].write(row['NAME'])
    statuses = []
    for p in range(1, 9):
        period = f"الحصة {p}"
        old = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='{period}'", conn)
        idx = 1 if not old.empty and "غايب" in old.iloc[0,0] else 0
        s = cols[1+p].selectbox(f"p{p}_{row['NUM']}", ["حاضر ✅", "غايب ❌"], index=idx, key=f"{d}_{row['NUM']}_{p}", label_visibility="collapsed")
        statuses.append((period, s))

    old_j = pd.read_sql(f"SELECT status FROM attendance WHERE date='{d}' AND num='{row['NUM']}' AND period='التبرير'", conn)
    old_j_val = old_j.iloc[0,0] if not old_j.empty else ""
    justification = cols[10].text_input(f"j_{row['NUM']}", value=old_j_val, placeholder="التبرير...", key=f"just_{d}_{row['NUM']}", label_visibility="collapsed")

    if save_clicked:
        for period, s in statuses:
            conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period=?", (str(d), str(row['NUM']), period))
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(row['NUM']), row['NAME'], selected_class, period, s))
        conn.execute("DELETE FROM attendance WHERE date=? AND num=? AND period='التبرير'", (str(d), str(row['NUM'])))
        if justification.strip() != "":
            conn.execute("INSERT INTO attendance VALUES (?,?,?,?,?,?)", (str(d), str(row['NUM']), row['NAME'], selected_class, "التبرير", justification))
        conn.commit()

if save_clicked:
    st.success("T7afaz - Saved ✅")
    st.rerun()

# --- EXCEL ---
st.divider()
df_all = pd.read_sql(f"SELECT date as التاريخ, class as الصف, nom as 'اسم الطالب', period as الحصة, status as الحالة FROM attendance WHERE date='{d}' AND class='{selected_class}'", conn)
if not df_all.empty:
    pivot = df_all.pivot_table(index=['التاريخ','الصف','اسم الطالب'], columns='الحصة', values='الحالة', aggfunc='first')
    pivot = pivot.reindex(columns=[f"الحصة {i}" for i in range(1,9)] + ["التبرير"]).reset_index()
    st.dataframe(pivot, use_container_width=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, index=False)
    st.download_button("📥 تحميل Excel", data=output.getvalue(), file_name=f"attendance_{selected_class}_{d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")