import streamlit as st


def header_home():

    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f"""
        <div style = "display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: 30px; margin-bottom: 30px;">
        <img src='{logo_url}' style = 'height:100px;' />
        <h1 style = "text-align: center; color: #E0E3FF;">SNAP</br>CLASS</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def header_dashboard():

    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"

    st.markdown(
        """
    <style>
    .snap-title {
        color: #5865f2 !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style = "display: flex; align-items: center; justify-content: center; gap: 10px;">
        <img src='{logo_url}' style = 'height:85px;' />
        <h2 class = "snap-title">SNAP</br>CLASS</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
