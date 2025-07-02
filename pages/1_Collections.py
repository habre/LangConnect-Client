import json
import os
import time

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

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


@st.dialog("삭제 확인")
def confirm_delete_collections(selected_names, selected_uuids):
    st.warning(
        "⚠️ 정말로 선택한 컬렉션을 삭제하시겠습니까? **이 작업은 복구할 수 없습니다.**"
    )

    st.write(f"삭제할 컬렉션 ({len(selected_names)}개):")
    for name in selected_names:
        st.write(f"• {name}")

    st.write("")
    st.info("삭제된 컬렉션의 모든 문서도 함께 삭제됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("삭제", type="primary", use_container_width=True):
            # Delete each selected collection
            deleted_count = 0
            failed_count = 0

            progress_text = st.empty()
            progress_bar = st.progress(0)

            for i, (uuid, name) in enumerate(zip(selected_uuids, selected_names, strict=False)):
                progress_text.text(
                    f"컬렉션 삭제 중 {i + 1}/{len(selected_uuids)}: {name}..."
                )
                progress_bar.progress((i + 1) / len(selected_uuids))

                success, result = make_request("DELETE", f"/collections/{uuid}")

                if success:
                    deleted_count += 1
                else:
                    failed_count += 1

            progress_text.empty()
            progress_bar.empty()

            if deleted_count > 0:
                st.success(
                    f"✅ {deleted_count}개의 컬렉션이 성공적으로 삭제되었습니다."
                )

            if failed_count > 0:
                st.error(f"❌ {failed_count}개의 컬렉션 삭제에 실패했습니다.")

            # Clear session state to force refresh
            st.session_state.collections_df = None
            st.session_state.collections_stats = None
            if "collections_list" in st.session_state:
                del st.session_state["collections_list"]
            st.session_state.delete_confirmed = True
            time.sleep(1)
            st.rerun()

    with col2:
        if st.button("취소", use_container_width=True):
            st.rerun()


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

    # Initialize session state for collections dataframe
    if "collections_df" not in st.session_state:
        st.session_state.collections_df = None
    if "collections_stats" not in st.session_state:
        st.session_state.collections_stats = None

    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_collections"):
            st.session_state.collections_df = None
            st.session_state.collections_stats = None

    # Fetch collections and stats if not in session state
    if st.session_state.collections_df is None:
        with st.spinner("Loading collections..."):
            success, collections = make_request("GET", "/collections")

            if not success:
                st.error(f"Failed to fetch collections: {collections}")
                with st.expander("에러 상세 정보"):
                    st.code(collections)
                    st.info("API 서버가 실행 중인지 확인하세요.")
                    st.info(f"API URL: {API_BASE_URL}")
                st.stop()

            st.session_state["collections_list"] = collections

            if not collections:
                st.info("No collections found. Create one to get started!")
                st.session_state.collections_df = pd.DataFrame()
                st.session_state.collections_stats = {}
            else:
                # Pre-fetch all collection stats at once to improve performance
                if st.session_state.collections_stats is None:
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
                                    data={"limit": limit, "offset": offset},
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
                                collection_stats[collection["uuid"]] = {
                                    "documents": total_documents,
                                    "chunks": total_chunks,
                                }
                            else:
                                collection_stats[collection["uuid"]] = {
                                    "documents": 0,
                                    "chunks": 0,
                                }

                        st.session_state.collections_stats = collection_stats
                else:
                    collection_stats = st.session_state.collections_stats

                # Create DataFrame for collections
                df_data = []
                for collection in collections:
                    stats = collection_stats.get(
                        collection["uuid"], {"documents": 0, "chunks": 0}
                    )
                    df_data.append(
                        {
                            "Name": collection["name"],
                            "Documents": stats["documents"],
                            "Chunks": stats["chunks"],
                            "UUID": collection["uuid"],
                            "Metadata": (
                                json.dumps(
                                    collection.get("metadata", {}), ensure_ascii=False
                                )
                                if collection.get("metadata")
                                else "{}"
                            ),
                            "_uuid": collection["uuid"],  # Hidden column for operations
                        }
                    )

                df = pd.DataFrame(df_data)
                st.session_state.collections_df = df

    # Display collections dataframe
    if (
        st.session_state.collections_df is not None
        and len(st.session_state.collections_df) > 0
    ):
        st.write(f"**Total Collections:** {len(st.session_state.collections_df)}")

        # Display selectable dataframe
        event = st.dataframe(
            st.session_state.collections_df[
                ["Name", "Documents", "Chunks", "UUID", "Metadata"]
            ],  # Show only visible columns
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="collections_list_df",
        )

        # Process selection
        if event.selection:
            selected_indices = event.selection.rows
            if len(selected_indices) > 0:
                st.write(f"**Selected {len(selected_indices)} collection(s)**")

                # Show delete button
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button(
                        "🗑️ Delete Selected",
                        type="secondary",
                        key="delete_selected_collections",
                    ):
                        # Get UUIDs of selected collections
                        selected_uuids = []
                        selected_names = []
                        for idx in selected_indices:
                            if idx < len(st.session_state.collections_df):
                                uuid = st.session_state.collections_df.iloc[idx][
                                    "_uuid"
                                ]
                                name = st.session_state.collections_df.iloc[idx]["Name"]
                                selected_uuids.append(uuid)
                                selected_names.append(name)

                        # Show confirmation dialog
                        confirm_delete_collections(selected_names, selected_uuids)
