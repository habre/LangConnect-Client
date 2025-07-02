import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
IS_TESTING = os.getenv("IS_TESTING", "").lower() == "true"
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
    data: Optional[dict] = None,
    files: Optional[dict] = None,
    json_data: Optional[dict] = None,
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
        return False, f"Request failed: {e!s}"


# Collections tab has been moved to pages/1_Collections.py


# API tester tab has been moved to pages/4_API_Tester.py

# Document upload tab has been moved to pages/2_Documents.py

# Vector search tab has been moved to pages/3_Search.py

# Document management tab has been moved to pages/2_Documents.py


def auth_page():
    """Display authentication page."""
    st.title("🔗 LangConnect Client")
    st.subheader("Authentication")

    # Testing mode - simple authentication
    if IS_TESTING:
        st.info("🧪 Testing Mode - Use simple credentials")

        with st.form("testing_signin_form"):
            st.write("**Testing Users:**")
            st.write("- user1")
            st.write("- user2")

            username = st.text_input("Username", placeholder="user1 or user2")
            submitted = st.form_submit_button("Sign In (Testing)", type="primary")

            if submitted:
                if username in ["user1", "user2"]:
                    st.session_state.authenticated = True
                    st.session_state.access_token = (
                        username  # Use username as token in testing
                    )
                    st.session_state.user_email = f"{username}@test.com"
                    # Save to file
                    save_auth_to_file(username, f"{username}@test.com")
                    st.success(f"Successfully signed in as {username}!")
                    st.rerun()
                else:
                    st.error("Please use 'user1' or 'user2' for testing")

        st.divider()
        st.subheader("Production Authentication")
        st.write(
            "*For production use, configure SUPABASE_URL and SUPABASE_KEY, then set IS_TESTING=false*"
        )
        return

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

    st.markdown(
        """
    Welcome to **LangConnect** - A powerful document management and search system powered by LangChain and PostgreSQL.
    
    ## 🚀 Features
    
    This application provides a comprehensive interface for managing documents with advanced search capabilities:
    """
    )

    # Page navigation
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📚 Collections Management")
        st.markdown(
            """
        - Create and manage document collections
        - View collection statistics
        - Bulk delete collections
        """
        )
        st.page_link("pages/1_Collections.py", label="Go to Collections", icon="📚")

        st.markdown("### 📄 Document Management")
        st.markdown(
            """
        - Upload multiple documents (PDF, TXT, MD, DOCX)
        - View and manage document chunks
        - Delete individual chunks or entire documents
        """
        )
        st.page_link("pages/2_Documents.py", label="Go to Documents", icon="📄")

    with col2:
        st.markdown("### 🔍 Search")
        st.markdown(
            """
        - **Semantic Search**: AI-powered similarity search
        - **Keyword Search**: Traditional full-text search
        - **Hybrid Search**: Best of both approaches
        - Advanced metadata filtering
        """
        )
        st.page_link("pages/3_Search.py", label="Go to Search", icon="🔍")

        st.markdown("### 🧪 API Tester")
        st.markdown(
            """
        - Test all API endpoints directly
        - Explore the API functionality
        - Debug and develop integrations
        """
        )
        st.page_link("pages/4_API_Tester.py", label="Go to API Tester", icon="🧪")

    st.divider()

    # Project information
    st.markdown("## 📌 About This Project")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
        **LangConnect** is an open-source project that combines the power of:
        - 🦜 **LangChain** for document processing and embeddings
        - 🐘 **PostgreSQL** with pgvector extension for vector storage
        - ⚡ **FastAPI** for high-performance API backend
        - 🎨 **Streamlit** for interactive user interface
        
        Perfect for building RAG (Retrieval-Augmented Generation) applications!
        """
        )

    with col2:
        st.markdown("### 🔗 Links")
        st.markdown(
            """
        - 📦 [GitHub Repository](https://github.com/teddynote-lab/LangConnect-Client)
        - 👨‍💻 [TeddyNote LAB](https://github.com/teddynote-lab)
        - 📚 [Documentation](https://github.com/teddynote-lab/LangConnect-Client#readme)
        """
        )

    st.divider()

    # Footer
    st.markdown(
        """
    <div style='text-align: center; color: #666; padding: 20px;'>
        Made with ❤️ by <a href='https://github.com/teddynote-lab' target='_blank'>TeddyNote LAB</a>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Configuration")

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


if __name__ == "__main__":
    main()
