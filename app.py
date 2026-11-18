import streamlit as st
import pandas as pd

# --- 1. Iza ba3edna ma fetna, farji l box ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1,col2,col3 = st.columns(3)
    with col2:
        st.image("ajaltoun.png",caption="TEL:09 236075",width=225)
    password = st.text_input("PASSWORD", type="password")

    if password == "Ajaltoun@1234":
        st.session_state.logged_in = True
        st.rerun()

    elif password != "":
        st.error("Wrong Password !")

    st.stop()  # Wa2af hon, ma tfarji shi tene

# --- 2. Iza fetna, kammel l app hon, MA FI BOX BA2A ---
#st.success("Welcome to Ajaltoun LTA 👋")
# ... hon btebda l logo, l QR, l search, kello

page = st.navigation(
    [
         st.Page("hello.py", title="WELCOME TO AJALTOUN LTA" ),
        #st.Page("C:/python/ajaltoun/hello.py", title="Hello", icon="👋"),
        #st.Page("C:/python/ajaltoun/hello.py", title="Hello", icon="ajaltoun.png"),
        st.Page("app2.py", title="Ajaltoun Student", icon="📈"),
        st.Page("exam.py", title="EXAM", icon="🌍"),
        #st.Page("C:/python/ajaltoun/dataframe_demo.py", title="DataFrame", icon="📊"),
    ]
)
page.run()
