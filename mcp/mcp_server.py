#!/usr/bin/env python3
"""LangConnect MCP Server using FastMCP (stdio)
"""

import json
import os
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from fastmcp import FastMCP

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Create FastMCP server
mcp = FastMCP(name="LangConnect")


# Output parser for multi-query generation
class LineListOutputParser(BaseOutputParser[list[str]]):
    """Output parser for a list of lines."""

    def parse(self, text: str) -> list[str]:
        # Split into lines, strip whitespace, and remove empties
        lines = [line.strip() for line in text.strip().split("\n")]
        return [line for line in lines if line]


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

    output = f'<search_results type="{search_type}">\n'
    for i, result in enumerate(results, 1):
        output += "  <document>\n"
        output += f"    <content>{result.get('page_content', '')}</content>\n"
        output += f"    <metadata>{json.dumps(result.get('metadata', {}), ensure_ascii=False)}</metadata>\n"
        output += f"    <score>{result.get('score', 0):.4f}</score>\n"
        output += f"    <id>{result.get('id', 'Unknown')}</id>\n"
        output += "  </document>\n"
    output += "</search_results>"

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


@mcp.tool
async def multi_query(question: str) -> str:
    """Generate multiple queries (3-5) for better vector search results from a single user question."""
    if not OPENAI_API_KEY:
        return json.dumps({"error": "OpenAI API key not configured"})

    try:
        # Initialize LLM
        llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY)

        # Create prompt template
        query_prompt = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI language model assistant. Your task is to generate 3 to 5 
different versions of the given user question to retrieve relevant documents from a vector 
database. By generating multiple perspectives on the user question, your goal is to help
the user overcome some of the limitations of the distance-based similarity search. 
Provide these alternative questions separated by newlines. Do not number them.
Original question: {question}""",
        )

        # Create parser
        output_parser = LineListOutputParser()

        # Create chain
        chain = query_prompt | llm | output_parser

        # Generate queries
        queries = await chain.ainvoke({"question": question})

        # Return as JSON array
        return json.dumps(queries, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Failed to generate queries: {e!s}"})


def main():
    """Entry point for the MCP server"""
    import sys

    print("Starting LangConnect MCP server...", file=sys.stderr)
    print(f"API_BASE_URL: {API_BASE_URL}", file=sys.stderr)
    print(
        f"SUPABASE_JWT_SECRET configured: {'Yes' if SUPABASE_JWT_SECRET else 'No'}",
        file=sys.stderr,
    )
    print(
        f"OPENAI_API_KEY configured: {'Yes' if OPENAI_API_KEY else 'No'}",
        file=sys.stderr,
    )

    if not SUPABASE_JWT_SECRET:
        print(
            "WARNING: No SUPABASE_JWT_SECRET provided. API calls will likely fail.",
            file=sys.stderr,
        )
        print(
            "Please set SUPABASE_JWT_SECRET environment variable with a valid JWT token.",
            file=sys.stderr,
        )

    if not OPENAI_API_KEY:
        print(
            "WARNING: No OPENAI_API_KEY provided. Multi-query generation will not work.",
            file=sys.stderr,
        )

    # Run stdio mode (default for Claude Desktop)
    mcp.run()


if __name__ == "__main__":
    main()
