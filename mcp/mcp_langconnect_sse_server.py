#!/usr/bin/env python3
"""
LangConnect MCP SSE Server

A Server-Sent Events (SSE) implementation of the LangConnect MCP server.
This provides the same tools as the standard MCP server but uses SSE transport
for web-based integrations.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from aiohttp import web
import httpx

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
# For Supabase authentication, we need to get the access token from environment
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")
SSE_PORT = int(os.getenv("SSE_PORT", "8765"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                    timeout=60.0,
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


class MCPSSEServer:
    """MCP SSE Server implementation"""

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()

    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/sse", self.handle_sse)
        self.app.router.add_post("/tools/{tool_name}", self.handle_tool_call)
        self.app.router.add_get("/tools", self.list_tools)
        
        # OAuth discovery endpoints (return empty responses to avoid 404s)
        self.app.router.add_get("/.well-known/oauth-protected-resource", self.oauth_protected_resource)
        self.app.router.add_get("/.well-known/oauth-authorization-server", self.oauth_authorization_server)

    def setup_cors(self):
        """Setup CORS middleware"""
        async def cors_middleware(app, handler):
            async def middleware_handler(request):
                if request.method == "OPTIONS":
                    return web.Response(headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Accept",
                    })
                
                response = await handler(request)
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
                return response
            
            return middleware_handler
        
        self.app.middlewares.append(cors_middleware)

    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "service": "langconnect-mcp-sse",
            "port": SSE_PORT,
            "api_base_url": API_BASE_URL,
            "timestamp": datetime.now().isoformat()
        })
    
    async def oauth_protected_resource(self, request):
        """OAuth protected resource discovery endpoint"""
        # Return minimal OAuth discovery response
        return web.json_response({
            "resource": "langconnect-mcp-sse",
            "oauth_enabled": False
        })
    
    async def oauth_authorization_server(self, request):
        """OAuth authorization server discovery endpoint"""
        # Return minimal OAuth discovery response
        return web.json_response({
            "issuer": "langconnect-mcp-sse",
            "authorization_endpoint": None,
            "token_endpoint": None
        })

    async def list_tools(self, request):
        """List available tools"""
        tools = [
            {
                "name": "search_documents",
                "description": "Perform semantic, keyword, or hybrid search on documents",
                "parameters": {
                    "collection_id": "UUID of the collection to search in",
                    "query": "Search query text",
                    "limit": "Maximum number of results (default: 5)",
                    "search_type": "Type of search - semantic, keyword, or hybrid",
                    "filter_json": "Optional JSON string containing metadata filters"
                }
            },
            {
                "name": "list_collections",
                "description": "List all available document collections"
            },
            {
                "name": "get_collection",
                "description": "Get detailed information about a specific collection",
                "parameters": {
                    "collection_id": "UUID of the collection"
                }
            },
            {
                "name": "create_collection",
                "description": "Create a new collection for storing documents",
                "parameters": {
                    "name": "Name of the collection",
                    "metadata_json": "Optional JSON string containing metadata"
                }
            },
            {
                "name": "update_collection",
                "description": "Update an existing collection's name or metadata",
                "parameters": {
                    "collection_id": "UUID of the collection to update",
                    "name": "New name for the collection (optional)",
                    "metadata_json": "New metadata as JSON string (optional)"
                }
            },
            {
                "name": "delete_collection",
                "description": "Delete a collection and all its documents",
                "parameters": {
                    "collection_id": "UUID of the collection to delete"
                }
            },
            {
                "name": "list_documents",
                "description": "List documents within a specific collection",
                "parameters": {
                    "collection_id": "UUID of the collection",
                    "limit": "Maximum number of documents to return (default: 20)",
                    "offset": "Number of documents to skip (default: 0)"
                }
            },
            {
                "name": "add_documents",
                "description": "Add text documents to a collection with metadata",
                "parameters": {
                    "collection_id": "UUID of the collection",
                    "text": "Text content to add as a document"
                }
            },
            {
                "name": "delete_document",
                "description": "Delete a specific document from a collection",
                "parameters": {
                    "collection_id": "UUID of the collection",
                    "document_id": "ID of the document to delete"
                }
            },
            {
                "name": "get_health_status",
                "description": "Check the health status of the LangConnect API"
            }
        ]
        
        return web.json_response({"tools": tools})

    async def handle_tool_call(self, request):
        """Handle tool execution requests"""
        tool_name = request.match_info["tool_name"]
        
        try:
            data = await request.json()
            arguments = data.get("arguments", {})
            
            # Execute the appropriate tool
            if tool_name == "search_documents":
                result = await self.search_documents(**arguments)
            elif tool_name == "list_collections":
                result = await self.list_collections()
            elif tool_name == "get_collection":
                result = await self.get_collection(**arguments)
            elif tool_name == "create_collection":
                result = await self.create_collection(**arguments)
            elif tool_name == "update_collection":
                result = await self.update_collection(**arguments)
            elif tool_name == "delete_collection":
                result = await self.delete_collection(**arguments)
            elif tool_name == "list_documents":
                result = await self.list_documents(**arguments)
            elif tool_name == "add_documents":
                result = await self.add_documents(**arguments)
            elif tool_name == "delete_document":
                result = await self.delete_document(**arguments)
            elif tool_name == "get_health_status":
                result = await self.get_health_status()
            else:
                return web.json_response(
                    {"error": f"Unknown tool: {tool_name}"},
                    status=404
                )
            
            return web.json_response({
                "success": True,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_sse(self, request):
        """Handle SSE connections"""
        response = web.StreamResponse()
        response.headers["Content-Type"] = "text/event-stream"
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        await response.prepare(request)

        # Send initial connection message
        await response.write(f"data: {json.dumps({'type': 'connected', 'message': 'Connected to LangConnect MCP SSE Server'})}\n\n".encode())

        try:
            # Keep connection alive
            while True:
                # Send heartbeat every 30 seconds
                await asyncio.sleep(30)
                await response.write(f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n".encode())
        except asyncio.CancelledError:
            pass
        finally:
            await response.write_eof()
            
        return response

    # Tool implementations
    async def search_documents(
        self,
        collection_id: str,
        query: str,
        limit: int = 5,
        search_type: str = "semantic",
        filter_json: Optional[str] = None,
    ) -> str:
        """Perform search on documents in a collection"""
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

            header = f"## Search Results ({search_type.capitalize()} Search)\n\n"
            if filter_json:
                header += f"**Filter Applied:** `{filter_json}`\n\n"

            return header + format_search_results(results)
        except Exception as e:
            return f"Search failed: {str(e)}"

    async def list_collections(self) -> str:
        """List all available collections"""
        try:
            collections = await client.request("GET", "/collections")
            return format_collections(collections)
        except Exception as e:
            return f"Failed to list collections: {str(e)}"

    async def get_collection(self, collection_id: str) -> str:
        """Get details of a specific collection"""
        try:
            collection = await client.request("GET", f"/collections/{collection_id}")
            return format_collections([collection])
        except Exception as e:
            return f"Failed to get collection: {str(e)}"

    async def create_collection(self, name: str, metadata_json: Optional[str] = None) -> str:
        """Create a new collection"""
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

    async def update_collection(
        self, collection_id: str, name: Optional[str] = None, metadata_json: Optional[str] = None
    ) -> str:
        """Update an existing collection"""
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

    async def delete_collection(self, collection_id: str) -> str:
        """Delete a collection"""
        try:
            await client.request("DELETE", f"/collections/{collection_id}")
            return f"Collection {collection_id} deleted successfully!"
        except Exception as e:
            return f"Failed to delete collection: {str(e)}"

    async def list_documents(self, collection_id: str, limit: int = 20, offset: int = 0) -> str:
        """List documents in a collection"""
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

    async def add_documents(self, collection_id: str, text: str) -> str:
        """Add documents to a collection"""
        try:
            metadata = {
                "source": "text-input",
                "author": "MCP-SSE-Server",
                "timestamp": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }

            # Create file data for upload
            filename = "document.txt"
            content = text.encode("utf-8")
            mimetype = "text/plain"

            files_list = [("files", (filename, content, mimetype))]
            form_data = {"metadatas_json": json.dumps([metadata])}

            result = await client.request(
                "POST",
                f"/collections/{collection_id}/documents",
                files=files_list,
                data=form_data,
            )

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

                return markdown
            else:
                return f"Failed to add document: {message}"

        except Exception as e:
            return f"Failed to add document: {str(e)}"

    async def delete_document(self, collection_id: str, document_id: str) -> str:
        """Delete a document from a collection"""
        try:
            await client.request(
                "DELETE", f"/collections/{collection_id}/documents/{document_id}"
            )
            return f"Document {document_id} deleted successfully from collection {collection_id}!"
        except Exception as e:
            return f"Failed to delete document: {str(e)}"

    async def get_health_status(self) -> str:
        """Get health status of the API"""
        try:
            result = await client.request("GET", "/health")

            markdown = "## LangConnect API Health Status\n\n"
            markdown += f"- **Status:** {result.get('status', 'Unknown')}\n"
            markdown += f"- **API Base URL:** {API_BASE_URL}\n"
            markdown += f"- **Authentication:** {'Configured' if SUPABASE_ACCESS_TOKEN else 'Not configured'}\n"

            return markdown
        except Exception as e:
            return f"Health check failed: {str(e)}"

    async def start(self):
        """Start the SSE server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", SSE_PORT)
        await site.start()
        
        logger.info(f"LangConnect MCP SSE Server started on port {SSE_PORT}")
        logger.info(f"SSE endpoint: http://localhost:{SSE_PORT}/sse")
        logger.info(f"Health check: http://localhost:{SSE_PORT}/health")
        logger.info(f"Tools endpoint: http://localhost:{SSE_PORT}/tools")
        logger.info(f"API_BASE_URL: {API_BASE_URL}")
        logger.info(f"SUPABASE_ACCESS_TOKEN configured: {'Yes' if SUPABASE_ACCESS_TOKEN else 'No'}")
        
        if not SUPABASE_ACCESS_TOKEN:
            logger.warning("No SUPABASE_ACCESS_TOKEN provided. API calls will likely fail.")
            logger.warning("Please set SUPABASE_ACCESS_TOKEN environment variable with a valid JWT token.")
        
        # Keep the server running
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Shutting down SSE server...")
        finally:
            await runner.cleanup()


async def main():
    """Main entry point"""
    server = MCPSSEServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error starting MCP SSE server: {e}")
        import traceback
        traceback.print_exc()
        exit(1)