import streamlit as st


def render_turns(turns):

    for turn in turns:

        with st.chat_message(
            "user",
            avatar="👤"
        ):
            st.markdown(
                turn["question"]
            )

        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):
            st.markdown(
                turn["answer"]
            )

            if turn.get("sources"):

                with st.expander(
                    "Sources"
                ):

                    for source in turn["sources"]:

                        st.markdown(
                            f"**{source['citation']}**"
                        )