import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
API_TOKEN = os.getenv("API_TOKEN", "user1")

st.set_page_config(page_title="LangConnect Client", page_icon="🔗", layout="wide")


def get_headers(include_content_type=True):
    headers = {
        "Accept": "application/json",
    }
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
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
                filter_json = st.text_area("Filter (JSON, optional)", "{}")
                try:
                    filter_dict = json.loads(filter_json) if filter_json else None
                    request_data = {"query": query, "limit": limit}
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


def document_upload_tab():
    st.header("Document Upload & Embedding")

    success, collections = make_request("GET", "/collections")

    if not success:
        st.error(f"Failed to fetch collections: {collections}")
        return

    if not collections:
        st.warning(
            "No collections found. Please create a collection first in the API Tester tab."
        )
        return

    collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
    selected_collection = st.selectbox(
        "Select Collection",
        list(collection_options.keys()),
        key="upload_collection_select",
    )
    collection_id = collection_options[selected_collection]

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
    )

    metadata_input = st.text_area(
        "Metadata for files (JSON array, one object per file)",
        value='[{"source": "upload", "timestamp": "'
        + datetime.now().isoformat()
        + '"}]',
    )

    if st.button("Upload and Embed Documents", type="primary"):
        if not uploaded_files:
            st.warning("Please select files to upload")
            return

        try:
            metadata_list = json.loads(metadata_input) if metadata_input else []

            files_data = []
            for i, file in enumerate(uploaded_files):
                file_content = file.read()
                files_data.append(
                    (
                        "files",
                        (
                            file.name,
                            file_content,
                            file.type or "application/octet-stream",
                        ),
                    )
                )

            data = {}
            if metadata_list:
                data["metadatas_json"] = json.dumps(metadata_list)

            with st.spinner("Uploading and embedding documents..."):
                success, result = make_request(
                    "POST",
                    f"/collections/{collection_id}/documents",
                    data=data,
                    files=files_data,
                )

            if success:
                st.success("Documents uploaded and embedded successfully!")
                st.json(result)
            else:
                st.error("Upload failed")
                if isinstance(result, str):
                    st.code(result)

        except json.JSONDecodeError:
            st.error("Invalid JSON in metadata")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    st.divider()

    st.subheader("View Documents in Collection")

    if st.button("Fetch Documents"):
        success, documents = make_request(
            "GET", f"/collections/{collection_id}/documents?limit=100"
        )

        if success:
            if documents:
                df = pd.DataFrame(documents)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No documents found in this collection")
        else:
            st.error(f"Failed to fetch documents: {documents}")


def vector_search_tab():
    st.header("Vector Search")

    success, collections = make_request("GET", "/collections")

    if not success:
        st.error(f"Failed to fetch collections: {collections}")
        return

    if not collections:
        st.warning("No collections found. Please create a collection first.")
        return

    collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
    selected_collection = st.selectbox(
        "Select Collection",
        list(collection_options.keys()),
        key="vector_search_collection_select",
    )
    collection_id = collection_options[selected_collection]

    query = st.text_input("Search Query", placeholder="Enter your search query...")

    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("Number of Results", min_value=1, max_value=50, value=5)

    with col2:
        filter_json = st.text_area("Metadata Filter (JSON)", "{}", height=100)

    if st.button("Search", type="primary"):
        if not query:
            st.warning("Please enter a search query")
            return

        try:
            search_data = {"query": query, "limit": limit}

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
                            f"Result {i+1} - Score: {result['score']:.4f}"
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
            st.error(f"Error: {str(e)}")


def main():
    st.title("🔗 LangConnect Client")

    with st.sidebar:
        st.header("Configuration")
        st.write(f"**API Base URL:** {API_BASE_URL}")
        st.write(f"**Auth Token:** {'Configured' if API_TOKEN else 'Not configured'}")

        if not API_TOKEN:
            st.warning(
                "⚠️ No API token configured. Most endpoints require authentication."
            )

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

        with st.expander("Debug Info"):
            st.code(f"Headers being sent:\n{json.dumps(get_headers(), indent=2)}")

        st.divider()

        st.info(
            "To configure the API connection, create a `.env` file with:\n\n"
            "```\n"
            "API_BASE_URL=http://localhost:8080\n"
            "API_TOKEN=your-token-here\n"
            "```"
        )

    tab1, tab2, tab3 = st.tabs(["API Tester", "Document Upload", "Vector Search"])

    with tab1:
        api_tester_tab()

    with tab2:
        document_upload_tab()

    with tab3:
        vector_search_tab()


if __name__ == "__main__":
    main()
