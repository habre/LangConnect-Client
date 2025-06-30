import json
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

st.set_page_config(page_title="API Tester - LangConnect", page_icon="🧪", layout="wide")


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
    data=None,
    files=None,
    json_data=None,
):
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
            # Check for authentication errors (401 Unauthorized or token expiry)
            if response.status_code == 401:
                # Clear authentication state
                st.session_state.authenticated = False
                st.session_state.access_token = None
                st.session_state.user = None
                st.error("Your authentication token has expired. Please sign in again.")
                st.switch_page("Main.py")

            # Check for token expiry in 500 errors
            elif response.status_code == 500:
                try:
                    error_text = response.text.lower()
                    if "token" in error_text and (
                        "expired" in error_text or "invalid" in error_text
                    ):
                        # Clear authentication state
                        st.session_state.authenticated = False
                        st.session_state.access_token = None
                        st.session_state.user = None
                        st.error("인증 토큰이 만료되었습니다. 다시 로그인해주세요.")
                        st.switch_page("Main.py")
                except:
                    pass

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


# Check authentication
if not st.session_state.get("authenticated", False):
    st.error("Please sign in first")
    st.stop()

st.title("🧪 API Tester")
st.markdown("Test LangConnect API endpoints directly")

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
            and "search" not in endpoint
        ):
            st.info("Use the Document Upload tab for uploading documents")
        else:
            if (
                method == "GET"
                and endpoint_group == "Documents"
                and "documents" in endpoint
                and "search" not in endpoint
            ):
                params = {}
                if "limit" in locals():
                    params["limit"] = 10
                if "offset" in locals():
                    params["offset"] = 0
                success, result = make_request(method, endpoint, data=params)
            else:
                success, result = make_request(method, endpoint, json_data=request_data)

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
