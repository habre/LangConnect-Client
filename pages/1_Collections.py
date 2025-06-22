import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

st.set_page_config(
    page_title="Collections - LangConnect", page_icon="📚", layout="wide"
)


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


# Check authentication
if not st.session_state.get("authenticated", False):
    st.error("Please sign in first")
    st.stop()

st.title("📚 Collections Management")

# Create tabs
tab1, tab2 = st.tabs(["List", "Create"])

with tab2:
    st.header("➕ Create New Collection")

    col1, col2 = st.columns(2)

    with col1:
        new_collection_name = st.text_input(
            "Collection Name",
            placeholder="Enter collection name",
            key="new_collection_name",
        )

    with col2:
        new_collection_metadata = st.text_area(
            "Metadata (JSON)",
            value="{}",
            height=100,
            key="new_collection_metadata",
            help="Enter metadata as a JSON object",
        )

    if st.button("Create Collection", type="primary", key="create_collection_btn"):
        if not new_collection_name:
            st.error("Please enter a collection name")
        else:
            try:
                metadata = (
                    json.loads(new_collection_metadata)
                    if new_collection_metadata
                    else {}
                )

                with st.spinner("Creating collection..."):
                    success, result = make_request(
                        "POST",
                        "/collections",
                        json_data={
                            "name": new_collection_name,
                            "metadata": metadata,
                        },
                    )

                if success:
                    st.success(
                        f"Collection '{new_collection_name}' created successfully!"
                    )
                    st.json(result)
                    # Force refresh of collections list
                    if "collections_list" in st.session_state:
                        del st.session_state["collections_list"]
                else:
                    st.error(f"Failed to create collection: {result}")

            except json.JSONDecodeError:
                st.error("Invalid JSON in metadata")

with tab1:
    st.header("📋 Existing Collections")

    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_collections"):
            if "collections_list" in st.session_state:
                del st.session_state["collections_list"]

    # Fetch collections
    if "collections_list" not in st.session_state:
        with st.spinner("Loading collections..."):
            success, collections = make_request("GET", "/collections")

            if success:
                st.session_state["collections_list"] = collections
            else:
                st.error(f"Failed to fetch collections: {collections}")
                st.stop()

    collections = st.session_state.get("collections_list", [])

    if not collections:
        st.info("No collections found. Create one to get started!")
    else:
        # Display collections count
        st.write(f"**Total Collections:** {len(collections)}")
        
        # Pre-fetch all collection stats at once to improve performance
        collection_stats = {}
        with st.spinner("Loading collection statistics..."):
            for collection in collections:
                # Fetch all documents using pagination
                all_documents = []
                offset = 0
                limit = 100
                
                while True:
                    success, documents = make_request(
                        "GET",
                        f"/collections/{collection['uuid']}/documents",
                        data={"limit": limit, "offset": offset}
                    )
                    
                    if not success:
                        break
                        
                    if not documents:
                        break
                        
                    all_documents.extend(documents)
                    
                    # If we got less than the limit, we've reached the end
                    if len(documents) < limit:
                        break
                        
                    offset += limit
                
                if all_documents:
                    total_chunks = len(all_documents)
                    
                    # Count unique documents by file_id
                    unique_file_ids = set()
                    for doc in all_documents:
                        file_id = doc.get("metadata", {}).get("file_id")
                        if file_id:
                            unique_file_ids.add(file_id)
                    
                    total_documents = len(unique_file_ids)
                    collection_stats[collection['uuid']] = {
                        "documents": total_documents,
                        "chunks": total_chunks
                    }
                else:
                    collection_stats[collection['uuid']] = {
                        "documents": 0,
                        "chunks": 0
                    }

        # Add column headers
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([3, 1.5, 1.5, 3, 2, 1])
        with header_col1:
            st.markdown("**Collection Name**")
        with header_col2:
            st.markdown("**Documents**")
        with header_col3:
            st.markdown("**Chunks**")
        with header_col4:
            st.markdown("**UUID**")
        with header_col5:
            st.markdown("**Metadata**")
        with header_col6:
            st.markdown("**Action**")

        st.divider()

        # Display collections
        for idx, collection in enumerate(collections):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1.5, 1.5, 3, 2, 1])

            with col1:
                st.write(f"**{collection['name']}**")

            # Display document stats for this collection
            stats = collection_stats.get(collection['uuid'], {"documents": 0, "chunks": 0})
            with col2:
                st.metric("", stats["documents"])
            with col3:
                st.metric("", stats["chunks"])

            with col4:
                st.code(collection["uuid"], language=None)

            with col5:
                metadata_str = (
                    json.dumps(collection.get("metadata", {}), ensure_ascii=False)
                    if collection.get("metadata")
                    else "{}"
                )
                st.text(metadata_str)

            with col6:
                if st.button(
                    "🗑️",
                    key=f"delete_collection_{collection['uuid']}",
                    help="Delete collection",
                ):
                    st.session_state[f'confirm_delete_{collection["uuid"]}'] = True

            # Confirmation dialog
            if st.session_state.get(f'confirm_delete_{collection["uuid"]}', False):
                st.warning(
                    f"⚠️ Are you sure you want to delete '{collection['name']}'? This will also delete all documents in the collection."
                )
                confirm_col1, confirm_col2 = st.columns(2)

                with confirm_col1:
                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_yes_{collection['uuid']}",
                        type="primary",
                    ):
                        with st.spinner("Deleting collection..."):
                            success, result = make_request(
                                "DELETE", f"/collections/{collection['uuid']}"
                            )

                        if success:
                            st.success(
                                f"Collection '{collection['name']}' deleted successfully!"
                            )
                            # Clear session state
                            del st.session_state[f'confirm_delete_{collection["uuid"]}']
                            if "collections_list" in st.session_state:
                                del st.session_state["collections_list"]
                            st.rerun()
                        else:
                            st.error(f"Failed to delete collection: {result}")

                with confirm_col2:
                    if st.button("Cancel", key=f"confirm_no_{collection['uuid']}"):
                        del st.session_state[f'confirm_delete_{collection["uuid"]}']
                        st.rerun()

            if idx < len(collections) - 1:
                st.divider()

