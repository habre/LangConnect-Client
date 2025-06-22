#!/usr/bin/env python3
"""
Create MCP configuration with automatic Supabase authentication.

This script generates the mcp_config.json file and automatically obtains
a Supabase access token by prompting for credentials.
"""

import os
import json
import sys
from pathlib import Path
from getpass import getpass
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")


def sign_in(email: str, password: str):
    """Sign in to Supabase and get access token."""
    try:
        # Call the LangConnect API signin endpoint
        response = requests.post(
            f"{API_BASE_URL}/auth/signin",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token"), data.get("refresh_token")
        else:
            error = response.json()
            print(f"Sign in failed: {error.get('detail', 'Unknown error')}")
            return None, None
            
    except Exception as e:
        print(f"Error during sign in: {str(e)}")
        return None, None


def test_token(token: str):
    """Test if the token works by calling the collections endpoint."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/collections",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except:
        return False


def get_access_token():
    """Get Supabase access token through user authentication."""
    print("\n🔐 Authentication Required")
    print("=" * 40)
    print("Please sign in to generate your MCP configuration")
    print()
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return None
    
    # Get credentials
    email = input("Enter your email: ")
    password = getpass("Enter your password: ")
    
    print("\nSigning in...")
    access_token, refresh_token = sign_in(email, password)
    
    if access_token:
        print("✅ Sign in successful!")
        print("Testing token...")
        
        if test_token(access_token):
            print("✅ Token is valid and working!")
            return access_token
        else:
            print("❌ Token validation failed.")
            return None
    else:
        print("❌ Sign in failed. Please check your credentials.")
        return None


def get_env_variables():
    """
    Load environment variables and return required variables as a dictionary.
    
    Returns:
        dict: Dictionary containing environment variables
    """
    # Get access token
    access_token = get_access_token()
    
    if not access_token:
        print("\n⚠️  Warning: No access token obtained. MCP server may not work properly.")
        access_token = ""
    
    env_dict = {
        "API_BASE_URL": API_BASE_URL,
        "SUPABASE_ACCESS_TOKEN": access_token
    }
    
    return env_dict


def create_mcp_json():
    """
    Create a Model Context Protocol (MCP) server configuration JSON file.
    
    This function generates a configuration file that defines how the MCP server
    should be launched, including the Python interpreter path, server script location,
    and necessary environment variables including the Supabase access token.
    
    Returns:
        str: Path to the created JSON configuration file
    """
    
    project_root = Path(__file__).parent.absolute()
    
    # .venv python executable path
    if os.name == "nt":  # Windows
        python_path = str(project_root.parent / ".venv" / "Scripts" / "python.exe")
    else:  # Mac, Ubuntu etc
        python_path = str(project_root.parent / ".venv" / "bin" / "python")
    
    server_script = project_root / "mcp_langconnect_server.py"
    
    # Get environment variables including access token
    env_vars = get_env_variables()
    
    config = {
        "mcpServers": {
            "langconnect-rag-mcp": {
                "command": python_path,
                "args": [str(server_script)],
                "env": env_vars,
            }
        }
    }
    
    json_path = project_root / "mcp_config.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ MCP configuration file has been created: {json_path}")
    print(f"📋 Configuration includes:")
    print(f"   - API Base URL: {env_vars['API_BASE_URL']}")
    print(f"   - Access Token: {'Configured' if env_vars['SUPABASE_ACCESS_TOKEN'] else 'Not configured'}")
    
    if env_vars['SUPABASE_ACCESS_TOKEN']:
        print("\n⚠️  Important Notes:")
        print("   - The access token will expire in about 1 hour")
        print("   - Run this script again to generate a new configuration with a fresh token")
        print("   - Keep your mcp_config.json file secure and don't commit it to version control")
    
    return str(json_path)


if __name__ == "__main__":
    print("🚀 LangConnect MCP Configuration Generator")
    print("=" * 50)
    
    try:
        create_mcp_json()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)