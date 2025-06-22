# LangConnect MCP Servers

This directory contains Model Context Protocol (MCP) server implementations for LangConnect.

## Authentication

Both MCP servers use Supabase JWT authentication. You need to provide a valid access token to use these servers.

### How to Get Your Access Token

#### Option 1: Using the Helper Script (Recommended)

Run the provided helper script:
```bash
cd mcp
python get_access_token.py
```

Enter your email and password when prompted. The script will:
- Sign you in
- Test the token
- Display the access token for you to copy

#### Option 2: From the Streamlit UI

1. **Sign in to the Streamlit UI** at http://localhost:8501
2. **Open Developer Tools** in your browser (F12)
3. **Go to the Application/Storage tab**
4. **Find Session Storage** for localhost:8501
5. **Look for the `access_token` key**
6. **Copy the JWT token value**

### Using the Access Token

#### For Standard MCP Server (stdio)

Update `mcp_config.json`:
```json
{
  "mcpServers": {
    "langconnect-rag-mcp": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_langconnect_server.py"
      ],
      "env": {
        "API_BASE_URL": "http://localhost:8080",
        "SUPABASE_ACCESS_TOKEN": "YOUR_JWT_TOKEN_HERE"
      }
    }
  }
}
```

#### For SSE Server

Set the environment variable:
```bash
export SUPABASE_ACCESS_TOKEN="YOUR_JWT_TOKEN_HERE"
docker compose up -d mcp-sse
```

Or add it to your `.env` file:
```
SUPABASE_ACCESS_TOKEN=YOUR_JWT_TOKEN_HERE
```

## Token Expiration

Supabase JWT tokens expire after a certain period (typically 1 hour). When your token expires:

1. Sign in again through the Streamlit UI
2. Get the new access token
3. Update your configuration with the new token

## Security Notes

- **Never commit tokens** to version control
- Keep your `.env` file in `.gitignore`
- Tokens are user-specific and grant access to that user's data
- Always use HTTPS in production environments