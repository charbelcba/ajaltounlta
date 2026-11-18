import sqlite3
import streamlit as st
import pandas as pd

DB_PATH = "ajaltoun.sqlite"
#col1,col2,col3 = st.columns([1,1,1])
#with col2:
     #st.image("ajaltoun.png",caption="TEL:09 236075",width=100)
     #st.image("ajaltoun.png",caption="Ecole Technique Ajaltoun TEL:09 236075",width=150)

st.title("AJALTOUN STUDENT")

search = st.text_input("Search Number رقم الطالب",type="default")
search2 = 999999999999999999
conn = sqlite3.connect(DB_PATH)
if search :
    if search=="Ajaltoun@1234":
        df = pd.read_sql("""
            select nom as "اسم الطالب",class as "الصف",subject as "اسم المادة",
            rate as "العلامة النهائية /20",result as "النتيجة"
            from exam 
            """, conn)
    else:
        df = pd.read_sql("""
             select nom as "اسم الطالب",class as "الصف",subject as "اسم المادة",
             rate as "العلامة النهائية /20",result as "النتيجة"
             from exam where 
             CAST(num AS TEXT) LIKE ?
            """, conn, params=(f"{search}",))
        
        if len(df)>0:
            df["FullCode"] = df["اسم الطالب"].astype(str)+"---"+df["الصف"].astype(str)
            st.caption(df["FullCode"][1])
            df=df.drop(columns=["اسم الطالب","الصف","FullCode"])
            
else:
     df = pd.read_sql("""
        select nom as "اسم الطالب",class as "الصف",subject as "اسم المادة",
        rate as "العلامة النهائية /20",result as "النتيجة"
        from exam where 
        CAST(num AS TEXT) LIKE ?
        """, conn, params=(f"{search2}",))
     
   
conn.close()
#st.caption(f"Showing {len(df)} rows")


#df["FullCode"] = df["اسم الطالب"].astype(str)+"---" + df["الصف"].astype(str)
#st.caption(df["FullCode"][1])
#df=df.drop(columns=["اسم الطالب","الصف"])
st.dataframe(df, use_container_width=True)

#select * from exam where num=="651227" or num=="رقم الطالب"