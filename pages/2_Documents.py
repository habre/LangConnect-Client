import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

st.set_page_config(page_title="Documents - LangConnect", page_icon="📄", layout="wide")


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

st.title("📄 Document Management")

# Get collections first
success, collections = make_request("GET", "/collections")

if not success:
    st.error(f"Failed to fetch collections: {collections}")
    st.stop()

if not collections:
    st.warning(
        "No collections found. Please create a collection first in the Collections page."
    )
    st.stop()

# Create tabs
tab1, tab2, tab3 = st.tabs(["Upload", "List", "Management"])

with tab1:
    st.header("📤 Document Upload & Embedding")
    
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

    # Show uploaded files and auto-generate metadata
    if uploaded_files:
        st.write(f"**Selected {len(uploaded_files)} file(s):**")
        default_metadata = []
        for file in uploaded_files:
            default_metadata.append(
                {"source": file.name, "timestamp": datetime.now().isoformat()}
            )

        metadata_input = st.text_area(
            "Metadata for files (JSON array, one object per file)",
            value=json.dumps(default_metadata, indent=2),
            height=200,
        )
    else:
        metadata_input = st.text_area(
            "Metadata for files (JSON array, one object per file)",
            value='[{"source": "filename.pdf", "timestamp": "'
            + datetime.now().isoformat()
            + '"}]',
            height=100,
        )

    if st.button("Upload and Embed Documents", type="primary"):
        if not uploaded_files:
            st.warning("Please select files to upload")
        else:
            try:
                metadata_list = json.loads(metadata_input) if metadata_input else []

                # Ensure metadata list matches number of files
                if len(metadata_list) < len(uploaded_files):
                    # Add default metadata for missing files
                    for i in range(len(metadata_list), len(uploaded_files)):
                        metadata_list.append(
                            {
                                "source": uploaded_files[i].name,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                elif len(metadata_list) > len(uploaded_files):
                    # Trim excess metadata
                    metadata_list = metadata_list[: len(uploaded_files)]

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

with tab2:
    st.header("📋 View Documents")
    
    collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
    selected_collection = st.selectbox(
        "Select Collection",
        list(collection_options.keys()),
        key="list_collection_select",
    )
    collection_id = collection_options[selected_collection]

    if st.button("Fetch Documents", type="primary"):
        with st.spinner("Fetching documents..."):
            success, documents = make_request(
                "GET", f"/collections/{collection_id}/documents?limit=100"
            )

        if success:
            if documents:
                st.success(f"Found {len(documents)} documents")
                
                # Create DataFrame
                df_data = []
                for doc in documents:
                    metadata = doc.get("metadata", {})
                    df_data.append({
                        "ID": doc.get("id", "N/A")[:8] + "...",
                        "Source": metadata.get("source", "N/A"),
                        "File ID": metadata.get("file_id", "N/A"),
                        "Timestamp": metadata.get("timestamp", "N/A"),
                        "Content Preview": doc.get("page_content", "")[:100] + "..."
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No documents found in this collection")
        else:
            st.error(f"Failed to fetch documents: {documents}")

with tab3:
    st.header("🔧 Document Management")
    
    # Collection selector
    collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
    selected_collection = st.selectbox(
        "Select Collection",
        list(collection_options.keys()),
        key="doc_mgmt_collection_select",
    )
    collection_id = collection_options[selected_collection]

    # Fetch documents button
    if st.button("Fetch Documents", type="primary", key="fetch_docs_button"):
        with st.spinner("Fetching documents..."):
            success, documents = make_request(
                "GET", f"/collections/{collection_id}/documents?limit=100"
            )

        if success:
            if documents:
                st.session_state["doc_mgmt_documents"] = documents
                st.session_state["doc_mgmt_collection_id"] = collection_id
            else:
                st.info("No documents found in this collection")
                if "doc_mgmt_documents" in st.session_state:
                    del st.session_state["doc_mgmt_documents"]
        else:
            st.error(f"Failed to fetch documents: {documents}")

    # Display documents if they exist in session state
    if (
        "doc_mgmt_documents" in st.session_state
        and st.session_state.get("doc_mgmt_collection_id") == collection_id
    ):
        documents = st.session_state["doc_mgmt_documents"]

        st.divider()
        st.subheader(f"Documents in Collection ({len(documents)} items)")

        # Prepare data for display
        display_data = []
        for idx, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            row_data = {
                "index": idx + 1,
                "source": metadata.get("source", "N/A"),
                "file_id": metadata.get("file_id", "N/A"),
                "timestamp": metadata.get("timestamp", "N/A"),
                "document_id": doc.get("id", "N/A"),
                "metadata": (
                    json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
                ),
            }

            display_data.append(row_data)

        # Display as dataframe
        if display_data:
            df = pd.DataFrame(display_data)

            # Configure column order and display
            column_order = [
                "index",
                "source",
                "file_id",
                "document_id",
                "timestamp",
                "metadata",
            ]
            df = df[column_order]

            # Show the dataframe with custom column config
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "index": st.column_config.NumberColumn("Index", width="small"),
                    "source": st.column_config.TextColumn("Source", width="medium"),
                    "file_id": st.column_config.TextColumn("File ID", width="medium"),
                    "document_id": st.column_config.TextColumn(
                        "Document ID", width="medium"
                    ),
                    "timestamp": st.column_config.TextColumn(
                        "Timestamp", width="medium"
                    ),
                    "metadata": st.column_config.TextColumn(
                        "Metadata (JSON)", width="large"
                    ),
                },
            )

            st.divider()

            # Document actions section
            st.subheader("Document Actions")

            # Group documents by source for better organization
            sources = {}
            for idx, doc in enumerate(documents):
                source = doc.get("metadata", {}).get("source", "Unknown")
                if source not in sources:
                    sources[source] = []
                sources[source].append((idx, doc))

            # Display documents grouped by source
            for source, doc_list in sources.items():
                with st.expander(f"📄 {source} ({len(doc_list)} chunks)"):
                    for idx, doc in doc_list:
                        col1, col2 = st.columns([8, 2])

                        with col1:
                            st.write(f"**Chunk {idx + 1}**")
                            metadata = doc.get("metadata", {})

                            # Display key metadata
                            meta_cols = st.columns(3)
                            with meta_cols[0]:
                                st.caption(f"File ID: {metadata.get('file_id', 'N/A')}")
                            with meta_cols[1]:
                                st.caption(f"Doc ID: {doc.get('id', 'N/A')[:8]}...")
                            with meta_cols[2]:
                                if "timestamp" in metadata:
                                    try:
                                        ts = datetime.fromisoformat(
                                            metadata["timestamp"].replace("Z", "+00:00")
                                        )
                                        st.caption(
                                            f"Time: {ts.strftime('%Y-%m-%d %H:%M')}"
                                        )
                                    except:
                                        st.caption(f"Time: {metadata['timestamp']}")

                        with col2:
                            # Delete button
                            if st.button(
                                "🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"
                            ):
                                # Get file_id from metadata if available
                                file_id = metadata.get("file_id", doc.get("id"))

                                with st.spinner("Deleting document..."):
                                    success, result = make_request(
                                        "DELETE",
                                        f"/collections/{collection_id}/documents/{file_id}",
                                    )

                                if success:
                                    st.success("Document deleted successfully!")
                                    # Clear the cached documents to force refresh
                                    if "doc_mgmt_documents" in st.session_state:
                                        del st.session_state["doc_mgmt_documents"]
                                    # Refresh the page
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete document: {result}")

        # Refresh button at the bottom
        if st.button("🔄 Refresh Document List", key="refresh_docs"):
            # Clear the cached documents to force a fresh fetch
            if "doc_mgmt_documents" in st.session_state:
                del st.session_state["doc_mgmt_documents"]
            st.rerun()