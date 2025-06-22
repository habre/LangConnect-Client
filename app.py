import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime
import time
import pickle
from pathlib import Path

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
# Check for saved auth credentials in environment variables
SAVED_TOKEN = os.getenv("LANGCONNECT_TOKEN", "")
SAVED_EMAIL = os.getenv("LANGCONNECT_EMAIL", "")

st.set_page_config(page_title="LangConnect Client", page_icon="🔗", layout="wide")

# Define auth cache file path
AUTH_CACHE_FILE = Path.home() / ".langconnect_auth_cache"


# Function to save auth data to file
def save_auth_to_file(token: str, email: str):
    """Save authentication data to a local file."""
    try:
        auth_data = {"token": token, "email": email, "timestamp": time.time()}
        with open(AUTH_CACHE_FILE, "wb") as f:
            pickle.dump(auth_data, f)
    except Exception as e:
        print(f"Failed to save auth data: {e}")


# Function to load auth data from file
def load_auth_from_file():
    """Load authentication data from a local file."""
    try:
        if AUTH_CACHE_FILE.exists():
            with open(AUTH_CACHE_FILE, "rb") as f:
                auth_data = pickle.load(f)
                # Check if auth data is not too old (e.g., 7 days)
                if time.time() - auth_data.get("timestamp", 0) < 7 * 24 * 3600:
                    return auth_data.get("token"), auth_data.get("email")
    except Exception as e:
        print(f"Failed to load auth data: {e}")
    return None, None


# Function to clear auth file
def clear_auth_file():
    """Clear the authentication cache file."""
    try:
        if AUTH_CACHE_FILE.exists():
            AUTH_CACHE_FILE.unlink()
    except Exception as e:
        print(f"Failed to clear auth file: {e}")


# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "auth_loaded" not in st.session_state:
    st.session_state.auth_loaded = False

# Try to load auth from file or environment on first load
if not st.session_state.auth_loaded:
    # First try to load from file
    token, email = load_auth_from_file()

    # If not found in file, try environment variables
    if not token and SAVED_TOKEN and SAVED_EMAIL:
        token = SAVED_TOKEN
        email = SAVED_EMAIL

    # If we have valid credentials, set them
    if token and email:
        st.session_state.authenticated = True
        st.session_state.access_token = token
        st.session_state.user_email = email

    st.session_state.auth_loaded = True


def get_headers(include_content_type=True):
    headers = {
        "Accept": "application/json",
    }
    # Use access_token from SUPABASE
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
) -> tuple[bool, Any]:
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            headers = get_headers()
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            if files:
                headers = get_headers(include_content_type=False)
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                headers = get_headers()
                response = requests.post(url, headers=headers, json=json_data)
        elif method == "DELETE":
            headers = get_headers()
            response = requests.delete(url, headers=headers)
        elif method == "PATCH":
            headers = get_headers()
            response = requests.patch(url, headers=headers, json=json_data)
        else:
            return False, f"Unsupported method: {method}"

        if response.status_code in [200, 201, 204]:
            if response.status_code == 204:
                return True, "Success (No content)"
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            try:
                error_detail = response.json()
                return (
                    False,
                    f"Error {response.status_code}: {json.dumps(error_detail, indent=2)}",
                )
            except:
                return False, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return (
            False,
            f"Connection failed. Please check if the API is running at {API_BASE_URL}",
        )
    except Exception as e:
        return False, f"Request failed: {str(e)}"


# Collections tab has been moved to pages/1_Collections.py


def api_tester_tab():
    st.header("API Tester")

    col1, col2 = st.columns([1, 2])

    with col1:
        endpoint_group = st.selectbox(
            "Select Endpoint Group",
            ["Health", "Collections", "Documents"],
            key="api_endpoint_group",
        )

        if endpoint_group == "Health":
            endpoint = st.selectbox("Endpoint", ["/health"], key="health_endpoint")
            method = "GET"

        elif endpoint_group == "Collections":
            endpoint_options = {
                "List Collections": ("GET", "/collections"),
                "Create Collection": ("POST", "/collections"),
                "Get Collection": ("GET", "/collections/{collection_id}"),
                "Update Collection": ("PATCH", "/collections/{collection_id}"),
                "Delete Collection": ("DELETE", "/collections/{collection_id}"),
            }
            selected = st.selectbox(
                "Endpoint", list(endpoint_options.keys()), key="collections_endpoint"
            )
            method, endpoint = endpoint_options[selected]

        elif endpoint_group == "Documents":
            endpoint_options = {
                "List Documents": ("GET", "/collections/{collection_id}/documents"),
                "Create Documents": ("POST", "/collections/{collection_id}/documents"),
                "Delete Document": (
                    "DELETE",
                    "/collections/{collection_id}/documents/{document_id}",
                ),
                "Search Documents": (
                    "POST",
                    "/collections/{collection_id}/documents/search",
                ),
            }
            selected = st.selectbox(
                "Endpoint", list(endpoint_options.keys()), key="documents_endpoint"
            )
            method, endpoint = endpoint_options[selected]

        st.write(f"**Method:** {method}")
        st.write(f"**Endpoint:** {endpoint}")

    with col2:
        st.subheader("Parameters")

        if "{collection_id}" in endpoint:
            collection_id = st.text_input("Collection ID (UUID)")
            endpoint = endpoint.replace("{collection_id}", collection_id)

        if "{document_id}" in endpoint:
            document_id = st.text_input("Document ID")
            endpoint = endpoint.replace("{document_id}", document_id)

        request_data = None
        files = None

        if method in ["POST", "PATCH"]:
            if "collections" in endpoint and method == "POST":
                name = st.text_input("Collection Name")
                metadata = st.text_area("Metadata (JSON)", "{}")
                try:
                    metadata_dict = json.loads(metadata) if metadata else {}
                    request_data = {"name": name, "metadata": metadata_dict}
                except json.JSONDecodeError:
                    st.error("Invalid JSON in metadata")

            elif "collections" in endpoint and method == "PATCH":
                name = st.text_input("New Collection Name (optional)")
                metadata = st.text_area("New Metadata (JSON, optional)", "{}")
                try:
                    request_data = {}
                    if name:
                        request_data["name"] = name
                    if metadata:
                        request_data["metadata"] = json.loads(metadata)
                except json.JSONDecodeError:
                    st.error("Invalid JSON in metadata")

            elif "search" in endpoint:
                query = st.text_input("Search Query")
                limit = st.number_input("Limit", min_value=1, max_value=100, value=10)
                search_type = st.selectbox(
                    "Search Type",
                    ["semantic", "keyword", "hybrid"],
                    help="Semantic: Vector similarity search\nKeyword: Full-text search\nHybrid: Combination of both",
                )
                filter_json = st.text_area(
                    "Filter (JSON, optional)",
                    placeholder='{"source": "SPRi AI Brief_6월호.pdf"}\n\n# Other examples:\n{"file_id": "abc123"}\n{"source": "document.pdf", "type": "report"}',
                    help="Enter a JSON object to filter results by metadata",
                )
                try:
                    filter_dict = (
                        json.loads(filter_json)
                        if filter_json and filter_json != "{}"
                        else None
                    )
                    request_data = {
                        "query": query,
                        "limit": limit,
                        "search_type": search_type,
                    }
                    if filter_dict:
                        request_data["filter"] = filter_dict
                except json.JSONDecodeError:
                    st.error("Invalid JSON in filter")

        if st.button("Send Request", type="primary"):
            if "{collection_id}" in endpoint and not collection_id:
                st.error("Please provide Collection ID")
            elif "{document_id}" in endpoint and not document_id:
                st.error("Please provide Document ID")
            elif (
                endpoint_group == "Documents"
                and "documents" in endpoint
                and method == "POST"
                and not "search" in endpoint
            ):
                st.info("Use the Document Upload tab for uploading documents")
            else:
                if (
                    method == "GET"
                    and endpoint_group == "Documents"
                    and "documents" in endpoint
                    and not "search" in endpoint
                ):
                    params = {}
                    if "limit" in locals():
                        params["limit"] = 10
                    if "offset" in locals():
                        params["offset"] = 0
                    success, result = make_request(method, endpoint, data=params)
                else:
                    success, result = make_request(
                        method, endpoint, json_data=request_data
                    )

                if success:
                    st.success("Request successful!")
                    if isinstance(result, (dict, list)):
                        st.json(result)
                    else:
                        st.write(result)
                else:
                    st.error("Request failed")
                    if isinstance(result, str):
                        st.code(result)


# Document upload tab has been moved to pages/2_Documents.py


# Vector search tab has been moved to pages/3_Search.py


# Document management tab has been moved to pages/2_Documents.py


def auth_page():
    """Display authentication page."""
    st.title("🔗 LangConnect Client")
    st.subheader("Authentication")

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab1:
        with st.form("signin_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", type="primary")

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    with st.spinner("Signing in..."):
                        success, result = make_request(
                            "POST",
                            "/auth/signin",
                            json_data={"email": email, "password": password},
                        )

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.access_token = result["access_token"]
                        st.session_state.user_email = result["email"]
                        # Save to file
                        save_auth_to_file(result["access_token"], result["email"])
                        st.success("Successfully signed in!")
                        st.rerun()
                    else:
                        st.error(f"Sign in failed: {result}")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", placeholder="user@example.com")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up", type="primary")

            if submitted:
                if not new_email or not new_password:
                    st.error("Please enter both email and password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        success, result = make_request(
                            "POST",
                            "/auth/signup",
                            json_data={"email": new_email, "password": new_password},
                        )

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.access_token = result["access_token"]
                        st.session_state.user_email = result["email"]
                        # Save to file
                        save_auth_to_file(result["access_token"], result["email"])
                        st.success("Account created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Sign up failed: {result}")


def main():
    # Check if user is authenticated
    if not st.session_state.authenticated:
        auth_page()
        return

    st.title("🔗 LangConnect Client")

    with st.sidebar:
        st.header("Configuration")
        st.write(f"**API Base URL:** {API_BASE_URL}")

        if st.session_state.authenticated:
            st.write(f"**User:** {st.session_state.user_email}")
            if st.button("Sign Out", key="signout_btn"):
                st.session_state.authenticated = False
                st.session_state.access_token = None
                st.session_state.user_email = None
                # Clear auth file
                clear_auth_file()
                st.rerun()
        st.divider()

        st.subheader("Connection Status")
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                success, result = make_request("GET", "/health")
                if success:
                    st.success("✅ API is healthy")
                    st.json(result)
                else:
                    st.error("❌ Connection failed")
                    st.error(result)

    # Welcome message
    st.markdown("""
    Welcome to **LangConnect Client**! 🔗
    
    Navigate to different features using the sidebar:
    - **📚 Collections**: Create and manage collections
    - **📄 Documents**: Upload, view, and manage documents
    - **🔍 Search**: Perform vector searches across your documents
    
    The API Tester below allows you to directly interact with the LangConnect API.
    """)
    
    st.divider()
    
    # Main content - API Tester
    api_tester_tab()


if __name__ == "__main__":
    main()
