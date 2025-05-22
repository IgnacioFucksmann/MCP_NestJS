import logging
import requests
from fastmcp import FastMCP
from httpx import AsyncClient
import sys
import json
from rich.logging import RichHandler
from fastmcp.server.openapi import RouteMap, RouteType

# Set up pretty logging with rich
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp-server")

# Set other loggers to DEBUG as well
logging.getLogger("httpcore").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.DEBUG)


def main():
    try:
        # Download OpenAPI JSON from Swagger
        logger.info("🔍 Fetching OpenAPI spec from NestJS API...")
        response = requests.get("http://localhost:3000/api-json")
        response.raise_for_status()
        openapi_spec = response.json()

        # Create FastMCP instance
        logger.info("🚀 Initializing MCP server...")
        mcp = FastMCP(
            title="Usuario MCP Server",
            description="MCP Server para gestionar usuarios",
            version="1.0",
        )

        # Create httpx AsyncClient with base URL
        client = AsyncClient(base_url="http://localhost:3000")

        # Define custom route maps to include GET endpoints
        custom_maps = [
            RouteMap(
                methods=["GET"], pattern=r"^/usuarios.*", route_type=RouteType.TOOL
            )
        ]

        # Generate FastMCP server from OpenAPI
        logger.info("🛠️  Generating tools from OpenAPI spec...")
        openapi_server = mcp.from_openapi(
            openapi_spec=openapi_spec, client=client, route_maps=custom_maps
        )

        # Mount the OpenAPI server
        logger.info("📝 Mounting OpenAPI server...")
        mcp.mount("api", openapi_server)

        # Run the server
        logger.info("✨ Starting MCP server on http://localhost:8000/sse")
        mcp.run(transport="sse", port=8000)

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to NestJS API: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
