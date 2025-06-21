import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import httpx

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
API_TOKEN = os.getenv("API_TOKEN", "user1")

# Create MCP server
mcp = FastMCP(
    name="LangConnect",
    version="0.0.1",
    description="LangConnect RAG Service - Vector search and document management via MCP",
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
    ) -> Dict[str, Any]:
        """Make HTTP request to LangConnect API"""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    params=params,
                    timeout=30.0,
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
client = LangConnectClient(API_BASE_URL, API_TOKEN)


def format_search_results(results: List[Dict]) -> str:
    """Format search results as markdown"""
    if not results:
        return "No results found."

    markdown = "## Search Results\n\n"

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
    collection_id: str, query: str, limit: int = 5, filter_json: Optional[str] = None
) -> str:
    """
    Perform vector similarity search on documents in a collection.

    Args:
        collection_id: UUID of the collection to search in
        query: Search query text
        limit: Maximum number of results to return (default: 5)
        filter_json: Optional JSON string containing metadata filters

    Returns:
        Formatted search results
    """
    try:
        search_data = {"query": query, "limit": limit}

        if filter_json:
            try:
                search_data["filter"] = json.loads(filter_json)
            except json.JSONDecodeError:
                return "Error: Invalid JSON in filter parameter"

        results = await client.request(
            "POST",
            f"/collections/{collection_id}/documents/search",
            json_data=search_data,
        )

        return format_search_results(results)
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
            f"- **Authentication:** {'Configured' if API_TOKEN else 'Not configured'}\n"
        )

        return markdown
    except Exception as e:
        return f"Health check failed: {str(e)}"


if __name__ == "__main__":
    import sys
    try:
        print("Starting LangConnect MCP server...", file=sys.stderr)
        print(f"API_BASE_URL: {API_BASE_URL}", file=sys.stderr)
        print(f"API_TOKEN configured: {'Yes' if API_TOKEN else 'No'}", file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
