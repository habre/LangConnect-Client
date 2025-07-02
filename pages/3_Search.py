import json
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

st.set_page_config(page_title="Search - LangConnect", page_icon="🔍", layout="wide")


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
                        st.error(
                            "Your authentication token has expired. Please sign in again."
                        )
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

st.title("🔍 Vector Search")

success, collections = make_request("GET", "/collections")

if not success:
    st.error(f"Failed to fetch collections: {collections}")
    st.stop()

if not collections:
    st.warning("No collections found. Please create a collection first.")
    st.stop()

collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
selected_collection = st.selectbox(
    "Select Collection",
    list(collection_options.keys()),
    key="vector_search_collection_select",
)
collection_id = collection_options[selected_collection]

# Show available sources for filtering
with st.expander("📋 View available sources in this collection"):
    if st.button("Load sources", key="load_sources_for_filter"):
        with st.spinner("Loading sources..."):
            success, documents = make_request(
                "GET", f"/collections/{collection_id}/documents?limit=100"
            )
            if success and documents:
                # Extract unique sources
                sources = set()
                for doc in documents:
                    source = doc.get("metadata", {}).get("source")
                    if source:
                        sources.add(source)

                if sources:
                    st.write("**Available sources:**")
                    for source in sorted(sources):
                        st.code(f'{{"source": "{source}"}}')
                else:
                    st.info("No source metadata found in documents")
            else:
                st.warning("Could not load documents")

query = st.text_input("Search Query", placeholder="Enter your search query...")

col1, col2, col3 = st.columns(3)
with col1:
    limit = st.number_input("Number of Results", min_value=1, max_value=50, value=5)

with col2:
    search_type = st.selectbox(
        "Search Type",
        ["semantic", "keyword", "hybrid"],
        help="Semantic: Vector similarity search\nKeyword: Full-text search\nHybrid: Combination of both",
    )

with col3:
    # Add helper text for metadata filter
    st.markdown("**Metadata Filter**")
    st.caption("Filter by metadata fields")
    filter_json = st.text_area(
        "Enter filter as JSON",
        placeholder='{"source": "sample.pdf"}\n\n# Other examples:\n{"file_id": "abc123"}\n{"source": "document.pdf", "type": "report"}',
        height=100,
        help='Enter a JSON object to filter results by metadata. Example: {"source": "filename.pdf"}',
    )

if st.button("Search", type="primary"):
    if not query:
        st.warning("Please enter a search query")
    else:
        try:
            search_data = {"query": query, "limit": limit, "search_type": search_type}

            if filter_json and filter_json != "{}":
                search_data["filter"] = json.loads(filter_json)

            with st.spinner("Searching..."):
                success, results = make_request(
                    "POST",
                    f"/collections/{collection_id}/documents/search",
                    json_data=search_data,
                )

            if success:
                if results:
                    st.success(f"Found {len(results)} results")

                    for i, result in enumerate(results):
                        with st.expander(
                            f"Result {i + 1} - Score: {result['score']:.4f}"
                        ):
                            st.write("**Content:**")
                            st.write(result["page_content"])

                            if result.get("metadata"):
                                st.write("**Metadata:**")
                                st.json(result["metadata"])

                            st.write(f"**Document ID:** {result['id']}")
                else:
                    st.info("No results found")
            else:
                st.error(f"Search failed: {results}")

        except json.JSONDecodeError:
            st.error("Invalid JSON in filter")
        except Exception as e:
            st.error(f"Error: {e!s}")
