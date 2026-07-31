import streamlit as st

from utils.pdf_utils import save_uploaded_pdfs


def render_pdf_library(db):

    st.markdown("## 📚 My PDFs")
    st.caption("Upload PDFs and start chatting")

    # -----------------------------
    # Upload PDF
    # -----------------------------

    upload_key = f"pdf_upload_{st.session_state.sidebar_upload_counter}"

    uploaded_files = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        accept_multiple_files=True,
        key=upload_key,
    )

    # -----------------------------
    # Automatically save PDF
    # -----------------------------

    if uploaded_files:

        with st.spinner("Uploading PDF..."):

            new_pdf_ids = save_uploaded_pdfs(
                uploaded_files,
                st.session_state.user_id,
                db
            )

        # Automatically select uploaded PDFs
        st.session_state.active_pdf_ids = list(
            dict.fromkeys(
                [
                    *st.session_state.active_pdf_ids,
                    *new_pdf_ids
                ]
            )
        )

        # Reset uploader
        st.session_state.sidebar_upload_counter += 1

        st.success(
            f"✅ {len(new_pdf_ids)} PDF(s) uploaded successfully!"
        )

        st.rerun()

    # -----------------------------
    # Get PDFs from database
    # -----------------------------

    pdf_rows = db.get_pdfs_for_user(
        st.session_state.user_id
    )

    if not pdf_rows:

        st.info(
            "📄 No PDFs uploaded yet."
        )

        return []

    # -----------------------------
    # Existing PDF Library
    # -----------------------------

    default_selection = [
        row
        for row in pdf_rows
        if row[0] in st.session_state.active_pdf_ids
    ]

    selected_pdf_rows = st.multiselect(
        "Your Documents",
        options=pdf_rows,
        default=default_selection,
        format_func=lambda row: row[1],
        key="library_multiselect",
    )

    # Store selected PDFs
    st.session_state.active_pdf_ids = [
        row[0]
        for row in selected_pdf_rows
    ]

    if selected_pdf_rows:

        st.success(
            f"✅ {len(selected_pdf_rows)} document(s) ready to chat"
        )

    # -----------------------------
    # Delete PDFs
    # -----------------------------

    if selected_pdf_rows:

        if st.button(
            "🗑️ Delete Selected PDFs",
            use_container_width=True
        ):

            for pdf_row in selected_pdf_rows:

                db.delete_pdf(
                    pdf_row[0],
                    st.session_state.user_id
                )

            st.session_state.active_pdf_ids = []

            st.success(
                "PDF(s) deleted."
            )

            st.rerun()

    return selected_pdf_rows