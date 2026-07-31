import streamlit as st

from auth.auth import is_valid_email, validate_password, password_strength_level
from auth.password_reset import reset_user_password


def render_reset_password():
    st.markdown("## 🔑 Create New Password")
    st.caption("Enter a new password for your account.")

    # Get reset information from URL
    email = st.query_params.get("email", "")
    token = st.query_params.get("token", "")

    if not email or not token:
        st.error("❌ This password reset link is invalid.")

        if st.button(
            "Request New Reset Link",
            width="stretch",
            key="invalid_reset_link",
        ):
            st.query_params.clear()
            st.session_state.auth_page = "forgot"
            st.rerun()

        return

    with st.form("reset_password_page_form"):

        st.text_input(
            "Email",
            value=email,
            disabled=True,
        )

        show_password = st.checkbox(
            "Show Password",
            key="reset_page_show_password",
        )

        new_password = st.text_input(
            "New Password",
            type="default" if show_password else "password",
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="default" if show_password else "password",
        )

        if new_password:
            strength_label, strength_ratio, _ = (
                password_strength_level(new_password)
            )

            st.markdown(
                f"**Password Strength: {strength_label}**"
            )

            st.progress(strength_ratio)

        submitted = st.form_submit_button(
            "Update Password",
            width="stretch",
        )

    if not submitted:
        return

    email_value = email.strip().lower()
    token_value = token.strip()

    if not is_valid_email(email_value):
        st.error("❌ Invalid email address.")
        return

    if not new_password or not confirm_password:
        st.error("❌ Please enter and confirm your new password.")
        return

    if new_password != confirm_password:
        st.error("❌ Passwords do not match.")
        return

    password_errors = validate_password(new_password)

    if password_errors:
        st.error(
            "❌ " + "; ".join(password_errors)
        )
        return

    success, message = reset_user_password(
        email_value,
        token_value,
        new_password,
    )

    if not success:
        st.error(f"❌ {message}")
        return

    # Reset successful
    st.query_params.clear()

    st.session_state.auth_page = "login"
    st.session_state.auth_mode = "Login"

    st.session_state.auth_notice = (
        "✅ Password updated successfully. "
        "Please login with your new password."
    )

    st.success("✅ Password updated successfully!")

    st.rerun()