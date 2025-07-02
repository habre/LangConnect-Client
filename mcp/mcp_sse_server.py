#!/usr/bin/env python3
"""LangConnect MCP Server using FastMCP
"""

import json
import os
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

from fastmcp import FastMCP

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SSE_PORT = int(os.getenv("SSE_PORT", "8765"))

# Create FastMCP server
mcp = FastMCP(name="LangConnect")


# HTTP client
class LangConnectClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def request(self, method: str, endpoint: str, **kwargs):
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}{endpoint}"
            response = await client.request(
                method, url, headers=self.headers, timeout=60.0, **kwargs
            )
            response.raise_for_status()
            return (
                response.json()
                if response.status_code != 204
                else {"status": "success"}
            )


# Initialize client
client = LangConnectClient(API_BASE_URL, SUPABASE_JWT_SECRET)


@mcp.tool
async def search_documents(
    collection_id: str,
    query: str,
    limit: int = 5,
    search_type: str = "semantic",
    filter_json: Optional[str] = None,
) -> str:
    """Search documents in a collection using semantic, keyword, or hybrid search."""
    search_data = {"query": query, "limit": limit, "search_type": search_type}

    if filter_json:
        try:
            search_data["filter"] = json.loads(filter_json)
        except json.JSONDecodeError:
            return "Error: Invalid JSON in filter parameter"

    results = await client.request(
        "POST", f"/collections/{collection_id}/documents/search", json=search_data
    )

    if not results:
        return "No results found."

    output = f"## Search Results ({search_type})\n\n"
    for i, result in enumerate(results, 1):
        output += f"### Result {i} (Score: {result.get('score', 0):.4f})\n"
        output += f"{result.get('page_content', '')}\n"
        output += f"Document ID: {result.get('id', 'Unknown')}\n\n"

    return output


@mcp.tool
async def list_collections() -> str:
    """List all available document collections."""
    collections = await client.request("GET", "/collections")

    if not collections:
        return "No collections found."

    output = "## Collections\n\n"
    for coll in collections:
        output += (
            f"- **{coll.get('name', 'Unnamed')}** (ID: {coll.get('uuid', 'Unknown')})\n"
        )

    return output


@mcp.tool
async def get_collection(collection_id: str) -> str:
    """Get details of a specific collection."""
    collection = await client.request("GET", f"/collections/{collection_id}")
    return f"**{collection.get('name', 'Unnamed')}**\nID: {collection.get('uuid', 'Unknown')}"


@mcp.tool
async def create_collection(name: str, metadata_json: Optional[str] = None) -> str:
    """Create a new collection."""
    data = {"name": name}

    if metadata_json:
        try:
            data["metadata"] = json.loads(metadata_json)
        except json.JSONDecodeError:
            return "Error: Invalid JSON in metadata"

    result = await client.request("POST", "/collections", json=data)
    return f"Collection '{result.get('name')}' created with ID: {result.get('uuid')}"


@mcp.tool
async def delete_collection(collection_id: str) -> str:
    """Delete a collection and all its documents."""
    await client.request("DELETE", f"/collections/{collection_id}")
    return f"Collection {collection_id} deleted successfully!"


@mcp.tool
async def list_documents(collection_id: str, limit: int = 20) -> str:
    """List documents in a collection."""
    docs = await client.request(
        "GET", f"/collections/{collection_id}/documents", params={"limit": limit}
    )

    if not docs:
        return "No documents found."

    output = f"## Documents ({len(docs)} items)\n\n"
    for i, doc in enumerate(docs, 1):
        content_preview = doc.get("page_content", "")[:200]
        if len(doc.get("page_content", "")) > 200:
            content_preview += "..."
        output += f"{i}. {content_preview}\n   ID: {doc.get('id', 'Unknown')}\n\n"

    return output


@mcp.tool
async def add_documents(collection_id: str, text: str) -> str:
    """Add a text document to a collection."""
    metadata = {"source": "mcp-input", "created_at": datetime.now().isoformat()}

    files = [("files", ("document.txt", text.encode("utf-8"), "text/plain"))]
    data = {"metadatas_json": json.dumps([metadata])}

    # Remove Content-Type for multipart
    headers = client.headers.copy()
    headers.pop("Content-Type", None)

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            f"{client.base_url}/collections/{collection_id}/documents",
            headers=headers,
            files=files,
            data=data,
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()

    if result.get("success"):
        return f"Document added successfully! Created {len(result.get('added_chunk_ids', []))} chunks."
    return f"Failed to add document: {result.get('message', 'Unknown error')}"


@mcp.tool
async def delete_document(collection_id: str, document_id: str) -> str:
    """Delete a document from a collection."""
    await client.request(
        "DELETE", f"/collections/{collection_id}/documents/{document_id}"
    )
    return f"Document {document_id} deleted successfully!"


@mcp.tool
async def get_health_status() -> str:
    """Check API health status."""
    result = await client.request("GET", "/health")
    return f"Status: {result.get('status', 'Unknown')}\nAPI: {API_BASE_URL}\nAuth: {'✓' if SUPABASE_JWT_SECRET else '✗'}"


if __name__ == "__main__":
    # SSE server mode
    print(f"Starting MCP SSE server on http://127.0.0.1:{SSE_PORT}")
    print(
        "This server is for MCP clients only and cannot be accessed directly in a browser."
    )
    print("Use the configuration in the Streamlit UI to connect MCP clients.")
    mcp.run(transport="sse", port=SSE_PORT)
