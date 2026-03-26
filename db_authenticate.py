import streamlit as st

def check_password():
    """Simple password protection without secrets.toml"""

    APP_PASSWORD = "radcalnettest"  # 🔴 change this later

    def password_entered():
        if st.session_state.get("password", "") == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Login Required")
        st.text_input(
            "Enter password",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False

    if not st.session_state["password_correct"]:
        st.title("🔒 Login Required")
        st.text_input(
            "Enter password",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("❌ Incorrect password")
        return False

    return True