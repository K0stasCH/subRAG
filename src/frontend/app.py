import streamlit as st
import requests
from streamlit_pills import pills
# from ..api.dataSchemas import Query


# API_BASE_URL = "http://127.0.0.1:8000" 
# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = "http://backend:8000"
# API_BASE_URL = ""
ENDPOINT = "/api/query"
API_URL = f"{API_BASE_URL}{ENDPOINT}"


def add_to_message_history(role: str, content: str) -> None:
    message = {"role": role, "content": str(content)}
    st.session_state.messages.append(message)  # Add response to message history

def get_data_from_backend(question:str):
    """Calls the backend API and returns the message."""
    try:        
        payload = {"query": question}
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the backend API: {e}")
        return {"answer": "❌ Error: Could not retrieve data from the backend."}

st.set_page_config(
    page_title="SubRag - A RAG system given subtiltes of a movie",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

st.title("SubRag")
st.header("A RAG system that replies based on the subtiltes of a movie")
st.info(
    "Test4",
    icon="ℹ️",
)

# add pills
selected_pill= pills(
    "Test5",
    [
        "Who is the main character?",
        "Make a summary of the plot.",
    ],
    clearable=True,
    index=None,
)

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Test8"}
    ]


for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])


# TODO: this is really hacky, only because st.rerun is jank
if prompt := st.chat_input(
    "Your question",
):  # Prompt for user input and save to chat history
    # TODO: hacky
    if "has_rerun" in st.session_state.keys() and st.session_state.has_rerun:
        # if this is true, skip the user input
        st.session_state.has_rerun = False
    else:
        add_to_message_history("user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

        # If last message is not from assistant, generate a new response
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_data_from_backend(prompt)["answer"]
                    st.write(str(response))
                    add_to_message_history("assistant", str(response))

        else:
            pass

else:
    # TODO: set has_rerun to False
    st.session_state.has_rerun = False