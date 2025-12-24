import streamlit as st
import requests
from config import API_BASE_URL
import time

def add_to_message_history(role: str, content: str) -> None:
    """Adds a message to the Streamlit session state chat history."""
    message = {"role": role, "content": str(content)}
    st.session_state.messages.append(message)    

def answer_question(question: str, session_id: str) -> dict:
    """Calls the backend API and returns the response data."""
    api_endpoint = f"{API_BASE_URL}/api/query"
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"query": question, "session_id": session_id}
        
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        return response.json()
        
    except requests.exceptions.Timeout:
        st.error("Request timed out. The backend server took too long to respond.")
        return {"answer": "❌ Error: The request to the backend timed out."}
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the backend API: {e}")
        return {"answer": "❌ Error: Could not retrieve data from the backend."}

def check_server_status() -> tuple[bool, str]:
    """Fetches the status from the FastAPI health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/status", timeout=5) # 5 second timeout
        data = response.json()
        if response.status_code == 200:
          message = data.get('message', 'Connected.')
          status = data.get('status', 'Unknown')
          return True, f"{message} (Status: {status})"
        else:
          # Server is up but returned a non-200 code (e.g., 503 Service Unavailable)
          return False, f"Server Error: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return False, "Server Offline: Connection refused/host unreachable."
    except requests.exceptions.Timeout:
        return False, "Server Timeout: Request took too long to respond."
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"
    
def send_delete_history(uuid: str):
    """Calls the backend API and delete the history for the session with uuid."""
    delete_url = f"{API_BASE_URL}/delete_History/{uuid}"
    del_res = requests.delete(delete_url)
            
    if del_res.status_code == 200:
        print(f"✅ Session with ID:{uuid} removed!")
    else:
        print("❌ Failed to delete.")

    
def update_UI_server_status(placeholder):
    try:
        is_up, text = check_server_status()
        placeholder.success(text, icon="✅") if is_up else st.error(text, icon="❌")
    except requests.exceptions.RequestException:
        placeholder.warning("Backend server may be offline or unreachable.", icon="⚠️")
