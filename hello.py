import streamlit as st

#st.write("Welcome to Ajaltoun LTA 👋")
#c1,c2,c3= st.columns(3)
#with c2:
     #st.success("WELCOME TO AJALTOUN LTA")
     
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
          """
          )
     st.markdown(
         """
          Follow Us & Stay Updated ❤️
         """
     )

     st.markdown("""
          <a href="https://www.instagram.com/ajaltoun_lta" target="_blank">
          <img src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png" width="50">
          </a>
          &nbsp;&nbsp;&nbsp;
          <a href="https://www.tiktok.com/@ajaltoun_lta" target="_blank">
         <img src="https://cdn-icons-png.flaticon.com/512/3046/3046121.png" width="50">
         </a>
         &nbsp;&nbsp;&nbsp;
         <a href="https://www.facebook.com/share/1Mj6pc4TWN/?mibextid=wwXIfr" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/733/733547.png" width="50">
        </a>
        """, unsafe_allow_html=True)
     
#col1,col2,col3 = st.columns(3)

#with col2:
     #st.image("pic1.png",caption="TEL:09 236075",width=300)
     #st.image("ajaltoun.png",caption="Ecole Technique Ajaltoun TEL:09 236075",width=150)

