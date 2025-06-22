import os
import json
from typing import List, Dict, Any, Optional
import asyncio

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import httpx
import datetime

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
# For Supabase authentication, we need to get the access token from environment
# This should be set when initializing the MCP server with a valid JWT token
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")

# Create MCP server
mcp = FastMCP(
    name="LangConnect",
    version="0.0.1",
    description="""LangConnect RAG Service - A comprehensive document management and vector search system.

Available Tools:
1. search_documents - Perform semantic, keyword, or hybrid search on documents with metadata filtering
2. list_collections - List all available document collections
3. get_collection - Get detailed information about a specific collection
4. create_collection - Create a new collection for storing documents
5. update_collection - Update an existing collection's name or metadata
6. delete_collection - Delete a collection and all its documents
7. list_documents - List documents within a specific collection
8. add_documents - Add text documents to a collection with metadata
9. delete_document - Delete a specific document from a collection
10. get_health_status - Check the health status of the LangConnect API

This service provides:
- Multiple search types: semantic (vector similarity), keyword (full-text), and hybrid (combined)
- Metadata filtering for precise document retrieval (e.g., filter by source, type, date)
- Collection management for organizing documents by topic or purpose
- Document management for controlling stored content
- RESTful API integration with authentication support

Example usage:
- Semantic search: Find conceptually similar documents
- Keyword search: Find documents containing exact terms
- Hybrid search: Combine both approaches for best results
- Filter example: '{"source": "report.pdf"}' to search only in specific documents
- Add documents: add_documents("collection-id", "Document text", '{"source": "article", "topic": "AI"}')
""",
)


class LangConnectClient:
    """HTTP client for LangConnect API"""

    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to LangConnect API"""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                # Adjust headers for file upload
                headers = self.headers.copy()
                if files:
                    # Remove Content-Type for multipart/form-data
                    headers.pop("Content-Type", None)

                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data if not files else None,
                    params=params,
                    files=files,
                    data=data,
                    timeout=60.0,  # Increased timeout for file uploads
                )
                response.raise_for_status()

                if response.status_code == 204:
                    return {"status": "success", "message": "No content"}

                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    error_json = e.response.json()
                    error_detail = json.dumps(error_json, indent=2)
                except:
                    pass
                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")
            except httpx.RequestError as e:
                raise Exception(f"Connection error: {str(e)}")


# Initialize client
client = LangConnectClient(API_BASE_URL, SUPABASE_ACCESS_TOKEN)


def format_search_results(results: List[Dict]) -> str:
    """Format search results as markdown"""
    if not results:
        return "No results found.\n\nTips:\n- Try different search types (semantic, keyword, hybrid)\n- Check your metadata filter syntax\n- Ensure the collection contains documents matching your criteria"

    markdown = ""

    for i, result in enumerate(results, 1):
        score = result.get("score", 0)
        content = result.get("page_content", "")
        metadata = result.get("metadata", {})
        doc_id = result.get("id", "Unknown")

        markdown += f"### Result {i} (Score: {score:.4f})\n\n"
        markdown += f"{content}\n\n"

        if metadata:
            markdown += "**Metadata:**\n"
            for key, value in metadata.items():
                markdown += f"- {key}: {value}\n"

        markdown += f"\n**Document ID:** {doc_id}\n"
        markdown += "\n---\n\n"

    return markdown


def format_collections(collections: List[Dict]) -> str:
    """Format collections list as markdown"""
    if not collections:
        return "No collections found."

    markdown = "## Collections\n\n"

    for coll in collections:
        name = coll.get("name", "Unnamed")
        uuid = coll.get("uuid", "Unknown")
        metadata = coll.get("metadata", {})

        markdown += f"### {name}\n"
        markdown += f"- **ID:** {uuid}\n"

        if metadata:
            markdown += "- **Metadata:**\n"
            for key, value in metadata.items():
                markdown += f"  - {key}: {value}\n"

        markdown += "\n"

    return markdown


@mcp.tool()
async def search_documents(
    collection_id: str,
    query: str,
    limit: int = 5,
    search_type: str = "semantic",
    filter_json: Optional[str] = None,
) -> str:
    """
    Perform search on documents in a collection.

    Args:
        collection_id: UUID of the collection to search in
        query: Search query text
        limit: Maximum number of results to return (default: 5)
        search_type: Type of search - "semantic", "keyword", or "hybrid" (default: "semantic")
        filter_json: Optional JSON string containing metadata filters (e.g., '{"source": "document.pdf"}')

    Returns:
        Formatted search results
    """
    try:
        # Validate search type
        valid_search_types = ["semantic", "keyword", "hybrid"]
        if search_type not in valid_search_types:
            return f"Error: Invalid search_type '{search_type}'. Must be one of: {', '.join(valid_search_types)}"

        search_data = {"query": query, "limit": limit, "search_type": search_type}

        if filter_json:
            try:
                search_data["filter"] = json.loads(filter_json)
            except json.JSONDecodeError:
                return 'Error: Invalid JSON in filter parameter. Example: \'{"source": "document.pdf"}\''

        results = await client.request(
            "POST",
            f"/collections/{collection_id}/documents/search",
            json_data=search_data,
        )

        # Add search type info to the output
        header = f"## Search Results ({search_type.capitalize()} Search)\n\n"
        if filter_json:
            header += f"**Filter Applied:** `{filter_json}`\n\n"

        return header + format_search_results(results)
    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool()
async def list_collections() -> str:
    """
    List all available collections.

    Returns:
        Formatted list of collections with their metadata
    """
    try:
        collections = await client.request("GET", "/collections")
        return format_collections(collections)
    except Exception as e:
        return f"Failed to list collections: {str(e)}"


@mcp.tool()
async def get_collection(collection_id: str) -> str:
    """
    Get details of a specific collection.

    Args:
        collection_id: UUID of the collection

    Returns:
        Collection details including metadata
    """
    try:
        collection = await client.request("GET", f"/collections/{collection_id}")
        return format_collections([collection])
    except Exception as e:
        return f"Failed to get collection: {str(e)}"


@mcp.tool()
async def create_collection(name: str, metadata_json: Optional[str] = None) -> str:
    """
    Create a new collection for storing documents.

    Args:
        name: Name of the collection
        metadata_json: Optional JSON string containing metadata

    Returns:
        Details of the created collection
    """
    try:
        data = {"name": name}

        if metadata_json:
            try:
                data["metadata"] = json.loads(metadata_json)
            except json.JSONDecodeError:
                return "Error: Invalid JSON in metadata parameter"

        result = await client.request("POST", "/collections", json_data=data)
        return f"Collection created successfully!\n\n{format_collections([result])}"
    except Exception as e:
        return f"Failed to create collection: {str(e)}"


@mcp.tool()
async def update_collection(
    collection_id: str, name: Optional[str] = None, metadata_json: Optional[str] = None
) -> str:
    """
    Update an existing collection.

    Args:
        collection_id: UUID of the collection to update
        name: New name for the collection (optional)
        metadata_json: New metadata as JSON string (optional)

    Returns:
        Updated collection details
    """
    try:
        data = {}

        if name:
            data["name"] = name

        if metadata_json:
            try:
                data["metadata"] = json.loads(metadata_json)
            except json.JSONDecodeError:
                return "Error: Invalid JSON in metadata parameter"

        if not data:
            return "Error: No updates provided"

        result = await client.request(
            "PATCH", f"/collections/{collection_id}", json_data=data
        )
        return f"Collection updated successfully!\n\n{format_collections([result])}"
    except Exception as e:
        return f"Failed to update collection: {str(e)}"


@mcp.tool()
async def delete_collection(collection_id: str) -> str:
    """
    Delete a collection and all its documents.

    Args:
        collection_id: UUID of the collection to delete

    Returns:
        Confirmation message
    """
    try:
        await client.request("DELETE", f"/collections/{collection_id}")
        return f"Collection {collection_id} deleted successfully!"
    except Exception as e:
        return f"Failed to delete collection: {str(e)}"


@mcp.tool()
async def list_documents(collection_id: str, limit: int = 20, offset: int = 0) -> str:
    """
    List documents in a collection.

    Args:
        collection_id: UUID of the collection
        limit: Maximum number of documents to return
        offset: Number of documents to skip

    Returns:
        List of documents with their metadata
    """
    try:
        params = {"limit": limit, "offset": offset}
        documents = await client.request(
            "GET", f"/collections/{collection_id}/documents", params=params
        )

        if not documents:
            return "No documents found in this collection."

        markdown = f"## Documents in Collection (showing {len(documents)} items)\n\n"

        for i, doc in enumerate(documents, 1):
            doc_id = doc.get("id", "Unknown")
            content = (
                doc.get("page_content", "")[:200] + "..."
                if len(doc.get("page_content", "")) > 200
                else doc.get("page_content", "")
            )
            metadata = doc.get("metadata", {})

            markdown += f"### Document {i}\n"
            markdown += f"- **ID:** {doc_id}\n"
            markdown += f"- **Content Preview:** {content}\n"

            if metadata:
                markdown += "- **Metadata:**\n"
                for key, value in metadata.items():
                    markdown += f"  - {key}: {value}\n"

            markdown += "\n"

        return markdown
    except Exception as e:
        return f"Failed to list documents: {str(e)}"


@mcp.tool()
async def delete_document(collection_id: str, document_id: str) -> str:
    """
    Delete a specific document from a collection.

    Args:
        collection_id: UUID of the collection
        document_id: ID of the document to delete

    Returns:
        Confirmation message
    """
    try:
        await client.request(
            "DELETE", f"/collections/{collection_id}/documents/{document_id}"
        )
        return f"Document {document_id} deleted successfully from collection {collection_id}!"
    except Exception as e:
        return f"Failed to delete document: {str(e)}"


@mcp.tool()
async def add_documents(collection_id: str, text: str) -> str:
    """
    Add text documents to a collection.

    Args:
        collection_id: UUID of the collection to add documents to
        text: Text content to add as a document

    Returns:
        Summary of added documents

    Examples:
        # More examples with proper formatting:
        add_documents(
            collection_id="uuid-here",
            text="contents to be added..."
        )
    """
    try:
        # Parse metadata if provided
        metadata = dict()
        metadata["source"] = "text-input"
        metadata["author"] = "MCP-Server"
        metadata["timestamp"] = datetime.datetime.now().isoformat()
        metadata["created_at"] = datetime.datetime.now().isoformat()

        # Create file data for upload
        filename = "document.txt"
        content = text.encode("utf-8")
        mimetype = "text/plain"

        files_list = [("files", (filename, content, mimetype))]

        # Prepare form data with metadata
        form_data = {"metadatas_json": json.dumps([metadata])}

        # Upload document
        result = await client.request(
            "POST",
            f"/collections/{collection_id}/documents",
            files=files_list,
            data=form_data,
        )

        # Format response
        success = result.get("success", False)
        message = result.get("message", "Unknown response")

        if success:
            added_ids = result.get("added_chunk_ids", [])
            markdown = f"## Document Added Successfully\n\n"
            markdown += f"- **Message:** {message}\n"
            markdown += f"- **Number of chunks created:** {len(added_ids)}\n"
            markdown += f"- **Text length:** {len(text)} characters\n"

            if metadata:
                markdown += f"\n**Metadata:**\n"
                for key, value in metadata.items():
                    markdown += f"- {key}: {value}\n"

            if result.get("warnings"):
                markdown += f"\n**Warnings:** {result['warnings']}\n"

            return markdown
        else:
            return f"Failed to add document: {message}"

    except Exception as e:
        return f"Failed to add document: {str(e)}"


@mcp.tool()
async def get_health_status() -> str:
    """
    Check the health status of the LangConnect API.

    Returns:
        API health information
    """
    try:
        result = await client.request("GET", "/health")

        markdown = "## LangConnect API Health Status\n\n"
        markdown += f"- **Status:** {result.get('status', 'Unknown')}\n"
        markdown += f"- **API Base URL:** {API_BASE_URL}\n"
        markdown += (
            f"- **Authentication:** {'Configured' if SUPABASE_ACCESS_TOKEN else 'Not configured'}\n"
        )

        return markdown
    except Exception as e:
        return f"Health check failed: {str(e)}"


if __name__ == "__main__":
    import sys

    try:
        print("Starting LangConnect MCP server...", file=sys.stderr)
        print(f"API_BASE_URL: {API_BASE_URL}", file=sys.stderr)
        print(f"SUPABASE_ACCESS_TOKEN configured: {'Yes' if SUPABASE_ACCESS_TOKEN else 'No'}", file=sys.stderr)
        
        if not SUPABASE_ACCESS_TOKEN:
            print("WARNING: No SUPABASE_ACCESS_TOKEN provided. API calls will likely fail.", file=sys.stderr)
            print("Please set SUPABASE_ACCESS_TOKEN environment variable with a valid JWT token.", file=sys.stderr)
        
        mcp.run()
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
