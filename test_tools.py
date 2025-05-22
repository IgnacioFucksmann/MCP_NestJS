import asyncio
import logging
from fastmcp import Client
import sys
from rich.logging import RichHandler

# Set up pretty logging with rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp-client")

# Disable other loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("fastmcp").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)


async def test_tools():
    logger.info("🚀 Starting MCP client test...")

    try:
        async with Client("http://localhost:8000/sse") as client:
            try:
                # List available tools
                logger.info("🔍 Requesting available tools...")
                tools = await client.list_tools()
                logger.info(f"✨ Found {len(tools)} tools:")
                for tool in tools:
                    logger.info(f"   • {tool.name}")
                    logger.debug(f"     Description: {tool.description}")

                if not tools:
                    logger.warning(
                        "⚠️  No tools found! Make sure the MCP server is running."
                    )
                    return

                # Test POST /usuarios
                logger.info("\n📝 Testing user creation...")
                test_user_data = {
                    "nombre": "Test User",
                    "email": "test@example.com",
                    "password": "test123",
                }
                logger.info(f"   Sending data: {test_user_data}")
                result = await client.call_tool(
                    "api_UsuariosController_create", test_user_data
                )
                logger.info(f"   ✅ Created user: {result}")

                # Extract user ID from the created user
                created_user = eval(result[0].text)
                user_id = created_user["id"]
                logger.info(f"\n🎯 Using user_id: {user_id}")

                # Test PUT /usuarios/{id}
                logger.info("\n✏️  Testing user update...")
                update_data = {"id": user_id, "nombre": "Updated Name"}
                logger.info(f"   Sending update: {update_data}")
                updated = await client.call_tool(
                    "api_UsuariosController_update", update_data
                )
                logger.info(f"   ✅ Updated user: {updated}")

                # Test DELETE /usuarios/{id}
                logger.info("\n🗑️  Testing user deletion...")
                deleted = await client.call_tool(
                    "api_UsuariosController_remove", {"id": user_id}
                )
                logger.info(f"   ✅ Delete response: {deleted}")

            except Exception as e:
                logger.error(f"❌ Error during tool operations: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"❌ Error connecting to MCP server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(test_tools())
        logger.info("✨ Test script completed successfully")
    except KeyboardInterrupt:
        logger.info("\n🛑 Test script interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test script failed: {str(e)}")
        sys.exit(1)
