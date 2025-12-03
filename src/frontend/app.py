import streamlit as st
import requests
from streamlit_pills import pills
# from ..api.dataSchemas import Query


API_BASE_URL = "http://127.0.0.1:8000" 
ENDPOINT = "/api/query"
API_URL = f"{API_BASE_URL}{ENDPOINT}"

st.set_page_config(
    page_title="Test1",
    page_icon="Test2",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

st.title("Test3")
st.info(
    "Test4",
    icon="ℹ️",
)

# add pills
selected = pills(
    "Test5",
    [
        "Test6",
        "Test7",
    ],
    clearable=True,
    index=None,
)

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Test8"}
    ]

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
        return "Error: Could not retrieve data from the backend."

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

        # # check agent_ids again
        # # if it doesn't match, add to directory and refresh
        # agent_ids = current_state.agent_registry.get_agent_ids()
        # # check diff between agent_ids and cur agent ids
        # diff_ids = list(set(agent_ids) - set(st.session_state.cur_agent_ids))
        # if len(diff_ids) > 0:
        #     # # clear streamlit cache, to allow you to generate a new agent
        #     # st.cache_resource.clear()
        #     st.session_state.has_rerun = True
        #     st.rerun()

else:
    # TODO: set has_rerun to False
    st.session_state.has_rerun = False