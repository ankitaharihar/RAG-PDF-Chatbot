import streamlit as st

from auth.password_reset import request_password_reset
from auth.validators import is_valid_email


def render_forgot_password():
    st.markdown("## 🔐 Forgot Password")
    st.caption(
        "Enter your registered email address and we'll send you a password reset link."
    )

    with st.form("forgot_password_page_form"):
        email = st.text_input(
            "Email Address",
            placeholder="you@example.com",
        )

        submitted = st.form_submit_button(
            "Send Reset Link",
            width="stretch",
        )

    if submitted:
        email_value = email.strip().lower()

        if not email_value:
            st.error("❌ Please enter your email address.")
            return

        if not is_valid_email(email_value):
            st.error("❌ Please enter a valid email address.")
            return

        with st.spinner("Sending reset link..."):
            success, message = request_password_reset(email_value)

        if not success:
            st.error(f"❌ {message}")
            return

        st.success(
            "📧 Password reset link sent! Please check your email."
        )

        st.info(
            "The link expires in 20 minutes and can only be used once."
        )

    st.markdown("---")

    if st.button(
        "← Back to Login",
        width="stretch",
        key="forgot_back_login",
    ):
        st.session_state.auth_page = "login"
        st.rerun()