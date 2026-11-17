import streamlit as st

#st.write("Welcome to Ajaltoun LTA 👋")
c1,c2,c3= st.columns(3)
with c2:
     st.success("WELCOME TO AJALTOUN LTA")
     
#st.sidebar.success("Select")
col1,col2,col3 = st.columns(3)
#with col1:
      #st.image("aj_qrcode.png",width=250)
with col2:
     st.image("ajaltoun.png",caption="TEL:09 236075",width=225)
     #st.image("ajaltoun.png",caption="Ecole Technique Ajaltoun TEL:09 236075",width=150)
#with col3:
      #st.image("tiktok3.png",width=250)

st.markdown(
    """
     Ecole Technique Ajaltoun , Mont-Liban, Lebanon
    - INSTAGRAM : (https://www.instagram.com/ajaltoun_lta?utm_source=qr)
    - TIKTOK :https://www.tiktok.com/@ajaltoun_lta?_r=1&_t=ZS-9BTlJ44lHso)
    
"""
)
#col1,col2,col3 = st.columns(3)

#with col2:
     #st.image("pic1.png",caption="TEL:09 236075",width=300)
     #st.image("ajaltoun.png",caption="Ecole Technique Ajaltoun TEL:09 236075",width=150)

