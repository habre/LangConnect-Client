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

        # Add column headers
        header_col1, header_col2, header_col3, header_col4 = st.columns([3, 4, 4, 1])
        with header_col1:
            st.markdown("**Collection Name**")
        with header_col2:
            st.markdown("**UUID**")
        with header_col3:
            st.markdown("**Metadata**")
        with header_col4:
            st.markdown("**Action**")

        st.divider()

        # Display collections
        for idx, collection in enumerate(collections):
            col1, col2, col3, col4 = st.columns([3, 4, 4, 1])

            with col1:
                st.write(f"**{collection['name']}**")

            with col2:
                st.code(collection["uuid"], language=None)

            with col3:
                metadata_str = (
                    json.dumps(collection.get("metadata", {}), ensure_ascii=False)
                    if collection.get("metadata")
                    else "{}"
                )
                st.text(metadata_str)

            with col4:
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

    # Collection details section
    if collections:
        st.divider()
        st.subheader("📊 Collection Details")

        collection_options = {f"{c['name']} ({c['uuid']})": c for c in collections}
        selected = st.selectbox(
            "Select a collection to view details",
            list(collection_options.keys()),
            key="collection_details_select",
        )

        if selected:
            selected_collection = collection_options[selected]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Collection Information:**")
                st.write(f"- **Name:** {selected_collection['name']}")
                st.write(f"- **UUID:** `{selected_collection['uuid']}`")

            with col2:
                st.write("**Metadata:**")
                metadata = selected_collection.get("metadata", {})
                if metadata:
                    st.json(metadata)
                else:
                    st.write("No metadata")

            # Quick stats
            if st.button(
                "📈 Get Collection Stats", key=f"stats_{selected_collection['uuid']}"
            ):
                with st.spinner("Fetching documents..."):
                    success, documents = make_request(
                        "GET",
                        f"/collections/{selected_collection['uuid']}/documents?limit=100",
                    )

                if success and documents:
                    st.write("**Collection Statistics:**")

                    # Chunk count
                    total_chunks = len(documents)
                    st.write(f"- Total chunks: {total_chunks}")
                    if total_chunks == 100:
                        st.caption("Note: Showing stats for first 100 chunks only")

                    # Debug: Show first few chunks to understand structure
                    with st.expander("Debug: First 3 chunks (click to expand)"):
                        for i, doc in enumerate(documents[:3]):
                            st.write(f"Chunk {i+1}:")
                            st.json(
                                {
                                    "id": doc.get("id", "N/A")[:8] + "...",
                                    "metadata": doc.get("metadata", {}),
                                    "content_preview": doc.get("page_content", "")[:100]
                                    + "...",
                                }
                            )

                    # Document analysis by file_id
                    documents_by_file_id = {}
                    for chunk in documents:
                        metadata = chunk.get("metadata", {})
                        file_id = metadata.get("file_id")
                        if file_id:
                            if file_id not in documents_by_file_id:
                                documents_by_file_id[file_id] = {
                                    "source": metadata.get("source", "Unknown"),
                                    "chunks": 0,
                                }
                            documents_by_file_id[file_id]["chunks"] += 1

                    # Show document count
                    st.write(f"- Total documents: {len(documents_by_file_id)}")

                    if documents_by_file_id:
                        st.write("\n**Documents and their chunks:**")
                        # Show documents with most chunks first
                        sorted_docs = sorted(
                            documents_by_file_id.items(),
                            key=lambda x: x[1]["chunks"],
                            reverse=True,
                        )
                        for file_id, info in sorted_docs[:10]:  # Show top 10
                            source_name = info["source"]
                            chunk_count = info["chunks"]
                            st.write(f"  - {source_name}: {chunk_count} chunks")

                        if len(sorted_docs) > 10:
                            st.caption(
                                f"... and {len(sorted_docs) - 10} more documents"
                            )
                elif success:
                    st.info("No documents in this collection")
                else:
                    st.error(f"Failed to fetch documents: {documents}")
