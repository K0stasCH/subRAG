import streamlit as st
from utils import add_to_message_history, answer_question, update_UI_server_status
import threading


st.set_page_config(
    page_title="SubRag - A subtiltes RAG system",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/K0stasCH/subRAG',
        'Report a bug': 'https://github.com/K0stasCH/subRAG/issues',
        'About': 'A Retrieval-Augmented Generation (RAG) system built with Streamlit and a custom backend for repling based on movie subtitles.',
    },
)

st.title("SubRag")
st.header("A RAG system that replies based on the subtiltes of a movie")

status_placeholder = st.empty()
update_UI_server_status(status_placeholder)

if "messages" not in st.session_state:  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey, you can ask me anything!"}
    ]

for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt:= st.chat_input("Ask your question here..."):
    add_to_message_history("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = answer_question(prompt)
                answer = response_data.get("answer", "❌ Error: No answer key found in API response.")
                st.markdown(str(answer))
                add_to_message_history("assistant", str(answer))
        st.rerun()