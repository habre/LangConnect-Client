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
                search_type = st.selectbox(
                    "Search Type", 
                    ["semantic", "keyword", "hybrid"],
                    help="Semantic: Vector similarity search\nKeyword: Full-text search\nHybrid: Combination of both"
                )
                filter_json = st.text_area(
                    "Filter (JSON, optional)", 
                    placeholder='{"source": "SPRi AI Brief_6월호.pdf"}\n\n# Other examples:\n{"file_id": "abc123"}\n{"source": "document.pdf", "type": "report"}',
                    help="Enter a JSON object to filter results by metadata"
                )
                try:
                    filter_dict = json.loads(filter_json) if filter_json and filter_json != "{}" else None
                    request_data = {"query": query, "limit": limit, "search_type": search_type}
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

    # Show uploaded files and auto-generate metadata
    if uploaded_files:
        st.write(f"**Selected {len(uploaded_files)} file(s):**")
        default_metadata = []
        for file in uploaded_files:
            default_metadata.append({
                "source": file.name,
                "timestamp": datetime.now().isoformat()
            })
        
        metadata_input = st.text_area(
            "Metadata for files (JSON array, one object per file)",
            value=json.dumps(default_metadata, indent=2),
            height=200
        )
    else:
        metadata_input = st.text_area(
            "Metadata for files (JSON array, one object per file)",
            value='[{"source": "filename.pdf", "timestamp": "'
            + datetime.now().isoformat()
            + '"}]',
            height=100
        )

    if st.button("Upload and Embed Documents", type="primary"):
        if not uploaded_files:
            st.warning("Please select files to upload")
            return

        try:
            metadata_list = json.loads(metadata_input) if metadata_input else []
            
            # Ensure metadata list matches number of files
            if len(metadata_list) < len(uploaded_files):
                # Add default metadata for missing files
                for i in range(len(metadata_list), len(uploaded_files)):
                    metadata_list.append({
                        "source": uploaded_files[i].name,
                        "timestamp": datetime.now().isoformat()
                    })
            elif len(metadata_list) > len(uploaded_files):
                # Trim excess metadata
                metadata_list = metadata_list[:len(uploaded_files)]

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
                        source = doc.get('metadata', {}).get('source')
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
            help="Semantic: Vector similarity search\nKeyword: Full-text search\nHybrid: Combination of both"
        )
    
    with col3:
        # Add helper text for metadata filter
        st.markdown("**Metadata Filter**")
        st.caption("Filter by metadata fields")
        filter_json = st.text_area(
            "Enter filter as JSON",
            placeholder='{"source": "SPRi AI Brief_6월호.pdf"}\n\n# Other examples:\n{"file_id": "abc123"}\n{"source": "document.pdf", "type": "report"}',
            height=100,
            help="Enter a JSON object to filter results by metadata. Example: {\"source\": \"filename.pdf\"}"
        )

    if st.button("Search", type="primary"):
        if not query:
            st.warning("Please enter a search query")
            return

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


def document_management_tab():
    st.header("Document Management")
    
    # Get collections
    success, collections = make_request("GET", "/collections")
    
    if not success:
        st.error(f"Failed to fetch collections: {collections}")
        return
    
    if not collections:
        st.warning("No collections found. Please create a collection first.")
        return
    
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
                st.session_state['doc_mgmt_documents'] = documents
                st.session_state['doc_mgmt_collection_id'] = collection_id
            else:
                st.info("No documents found in this collection")
                if 'doc_mgmt_documents' in st.session_state:
                    del st.session_state['doc_mgmt_documents']
        else:
            st.error(f"Failed to fetch documents: {documents}")
    
    # Display documents if they exist in session state
    if 'doc_mgmt_documents' in st.session_state and st.session_state.get('doc_mgmt_collection_id') == collection_id:
        documents = st.session_state['doc_mgmt_documents']
        
        st.divider()
        st.subheader(f"Documents in Collection ({len(documents)} items)")
        
        # Create a table-like view for documents
        # Prepare data for display
        display_data = []
        for idx, doc in enumerate(documents):
            metadata = doc.get('metadata', {})
            row_data = {
                'index': idx + 1,
                'source': metadata.get('source', 'N/A'),
                'file_id': metadata.get('file_id', 'N/A'),
                'timestamp': metadata.get('timestamp', 'N/A'),
                'document_id': doc.get('id', 'N/A'),
                'metadata': json.dumps(metadata, ensure_ascii=False) if metadata else '{}'
            }
            
            display_data.append(row_data)
        
        # Display as dataframe
        if display_data:
            df = pd.DataFrame(display_data)
            
            # Configure column order and display
            column_order = ['index', 'source', 'file_id', 'document_id', 'timestamp', 'metadata']
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
                    "document_id": st.column_config.TextColumn("Document ID", width="medium"),
                    "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                    "metadata": st.column_config.TextColumn("Metadata (JSON)", width="large")
                }
            )
            
            st.divider()
            
            # Document actions section
            st.subheader("Document Actions")
            
            # Group documents by source for better organization
            sources = {}
            for idx, doc in enumerate(documents):
                source = doc.get('metadata', {}).get('source', 'Unknown')
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
                            metadata = doc.get('metadata', {})
                            
                            # Display key metadata
                            meta_cols = st.columns(3)
                            with meta_cols[0]:
                                st.caption(f"File ID: {metadata.get('file_id', 'N/A')}")
                            with meta_cols[1]:
                                st.caption(f"Doc ID: {doc.get('id', 'N/A')[:8]}...")
                            with meta_cols[2]:
                                if 'timestamp' in metadata:
                                    try:
                                        ts = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                                        st.caption(f"Time: {ts.strftime('%Y-%m-%d %H:%M')}")
                                    except:
                                        st.caption(f"Time: {metadata['timestamp']}")
                        
                        with col2:
                            # Delete button
                            if st.button("🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                                # Get file_id from metadata if available
                                file_id = metadata.get('file_id', doc.get('id'))
                                
                                with st.spinner("Deleting document..."):
                                    success, result = make_request(
                                        "DELETE",
                                        f"/collections/{collection_id}/documents/{file_id}"
                                    )
                                
                                if success:
                                    st.success("Document deleted successfully!")
                                    # Refresh the document list
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete document: {result}")
        
        # Refresh button at the bottom
        if st.button("🔄 Refresh Document List", key="refresh_docs"):
            st.rerun()


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

    tab1, tab2, tab3, tab4 = st.tabs(["API Tester", "Document Upload", "Vector Search", "Document Management"])

    with tab1:
        api_tester_tab()

    with tab2:
        document_upload_tab()

    with tab3:
        vector_search_tab()
    
    with tab4:
        document_management_tab()


if __name__ == "__main__":
    main()
