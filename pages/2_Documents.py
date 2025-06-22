import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import time

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
tab1, tab2 = st.tabs(["Upload", "List"])

with tab1:
    st.header("📤 Document Upload & Embedding")

    # Add clear button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🧹 Clear", key="clear_upload_form"):
            # Clear all upload-related session state
            keys_to_clear = [
                "file_uploader",
                "metadata_input",
                "upload_collection_select",
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

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
        key="file_uploader",
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
            key="metadata_input",
        )
    else:
        metadata_input = st.text_area(
            "Metadata for files (JSON array, one object per file)",
            value='[{"source": "filename.pdf", "timestamp": "'
            + datetime.now().isoformat()
            + '"}]',
            height=100,
            key="metadata_input",
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

    # Add refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_documents"):
            st.session_state.list_tab_df = None
            st.session_state.list_tab_collection_id = None

    collection_options = {f"{c['name']} ({c['uuid']})": c["uuid"] for c in collections}
    selected_collection = st.selectbox(
        "Select Collection",
        list(collection_options.keys()),
        key="list_collection_select",
    )
    collection_id = collection_options[selected_collection]

    # Initialize session state for this tab
    if "list_tab_df" not in st.session_state:
        st.session_state.list_tab_df = None
    if "list_tab_collection_id" not in st.session_state:
        st.session_state.list_tab_collection_id = None

    # Auto-fetch documents when collection changes
    if st.session_state.list_tab_collection_id != collection_id:
        with st.spinner("Loading documents..."):
            # Fetch all documents using pagination
            all_documents = []
            offset = 0
            limit = 100

            while True:
                success, documents = make_request(
                    "GET",
                    f"/collections/{collection_id}/documents",
                    data={"limit": limit, "offset": offset},
                )

                if not success:
                    st.error(f"Failed to fetch documents: {documents}")
                    st.session_state.list_tab_df = None
                    break

                if not documents:
                    break

                all_documents.extend(documents)

                # If we got less than the limit, we've reached the end
                if len(documents) < limit:
                    break

                offset += limit

            documents = all_documents

            if success:
                if documents:
                    # Create DataFrame with full document data
                    df_data = []
                    for idx, doc in enumerate(documents):
                        metadata = doc.get("metadata", {})
                        content = doc.get("content", "")
                        df_data.append(
                            {
                                "ID": doc.get("id", "N/A")[:8] + "...",
                                "Content Preview": content,
                                "Count": len(content),
                                "Source": metadata.get("source", "N/A"),
                                "File ID": metadata.get("file_id", "N/A"),
                                "Timestamp": metadata.get("timestamp", "N/A"),
                                "_full_id": doc.get(
                                    "id", "N/A"
                                ),  # Hidden column with full ID
                                "_file_id": metadata.get(
                                    "file_id", doc.get("id")
                                ),  # Hidden column with file_id for deletion
                            }
                        )

                    df = pd.DataFrame(df_data)

                    # Store documents in session state for persistence
                    st.session_state.list_tab_df = df
                    st.session_state.list_tab_collection_id = collection_id
                else:
                    st.session_state.list_tab_df = pd.DataFrame()  # Empty DataFrame
                    st.session_state.list_tab_collection_id = collection_id

    # Display dataframe
    if st.session_state.list_tab_df is not None:
        if len(st.session_state.list_tab_df) > 0:
            st.success(f"Found {len(st.session_state.list_tab_df)} documents")

            # Calculate and display source statistics
            source_stats = (
                st.session_state.list_tab_df.groupby("Source")
                .agg(
                    {
                        "ID": "count",  # Count of chunks per source
                        "Count": "mean",  # Average character count per source
                    }
                )
                .round(0)
                .astype(int)
            )

            source_stats.columns = ["Chunks", "Avg Characters"]
            source_stats = source_stats.reset_index()

            # Create markdown table
            markdown_table = "| Source | Chunks | Avg Characters |\n"
            markdown_table += "|--------|--------|----------------|\n"

            for _, row in source_stats.iterrows():
                markdown_table += f"| {row['Source']} | {row['Chunks']} | {row['Avg Characters']:,} |\n"

            # Display the summary table
            st.markdown("### 📊 Document Summary")
            st.markdown(markdown_table)

            # Display dataframe with selection
            event = st.dataframe(
                st.session_state.list_tab_df[
                    ["ID", "Content Preview", "Count", "Source", "Timestamp", "File ID"]
                ],  # Show only visible columns
                use_container_width=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="doc_list_df",
            )

            # Process selection
            if event.selection:
                selected_indices = event.selection.rows
                if len(selected_indices) > 0:
                    st.write(f"**Selected {len(selected_indices)} document(s)**")

                    # Show delete button
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button(
                            "🗑️ Delete Selected",
                            type="secondary",
                            key="delete_selected_list",
                        ):
                            # Get document IDs of selected documents
                            selected_doc_ids = []
                            for idx in selected_indices:
                                if idx < len(st.session_state.list_tab_df):
                                    doc_id = st.session_state.list_tab_df.iloc[idx][
                                        "_full_id"
                                    ]
                                    selected_doc_ids.append(doc_id)

                            # Delete each selected document
                            deleted_count = 0
                            failed_count = 0

                            progress_text = st.empty()
                            progress_bar = st.progress(0)

                            for i, doc_id in enumerate(selected_doc_ids):
                                progress_text.text(
                                    f"Deleting document {i+1} of {len(selected_doc_ids)}..."
                                )
                                progress_bar.progress((i + 1) / len(selected_doc_ids))

                                success, result = make_request(
                                    "DELETE",
                                    f"/collections/{collection_id}/documents/{doc_id}?delete_by=document_id",
                                )

                                if success:
                                    deleted_count += 1
                                else:
                                    failed_count += 1

                            progress_text.empty()
                            progress_bar.empty()

                            if deleted_count > 0:
                                st.success(
                                    f"✅ Successfully deleted {deleted_count} document(s)"
                                )

                            if failed_count > 0:
                                st.error(
                                    f"❌ Failed to delete {failed_count} document(s)"
                                )

                            # Clear session state to force refresh
                            st.session_state.list_tab_df = None
                            st.session_state.list_tab_collection_id = (
                                None  # Force re-fetch
                            )
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("No documents found in this collection")
