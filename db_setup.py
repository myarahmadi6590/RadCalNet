import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="RadCalNet",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            "Get Help": "https://example.com/help",
            "Report a Bug": "https://example.com/bug",
            "About": "This app analyzes sensor vs RadCalNet data."
        }
    )

    st.markdown(
        "<h1 style='text-align: center;'>RadCalNet Sensor Analysis Dashboard</h1>",
        unsafe_allow_html=True
    )

    st.markdown("""
        <hr>
        <div style='text-align: center; font-size: 20px; color: gray;'>
            &copy; 2025 | Developed by Mehran Yarahmadi |
            <a href='mailto:mehran.yarahmadi@nasa.gov' style='color: gray; text-decoration: none;'>
                mehran.yarahmadi@nasa.gov
            </a>
            <br>
            With support from NASA Goddard Space Flight Center: 
            Kurt Thome, Brian Wenny
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <hr>
        <div style='text-align: center; font-size: 14px; color: gray;'>
        </div>
    """, unsafe_allow_html=True)