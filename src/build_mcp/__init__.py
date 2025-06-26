import argparse
import asyncio

from build_mcp.common.logger import get_logger
from build_mcp.services.server import mcp


def main():
    """Main function to run the MCP server."""
    logger = get_logger('app')

    parser = argparse.ArgumentParser(description="Amap MCP Server")
    parser.add_argument(
        'transport',
        nargs='?',
        default='stdio',
        choices=['stdio', 'sse', 'streamable-http'],
        help='Transport type (stdio, sse, or streamable-http)'
    )
    args = parser.parse_args()

    logger.info(f"🚀 Starting MCP server with transport type: %s", args.transport)

    try:
        mcp.run(transport=args.transport)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("🛑 MCP Server received shutdown signal. Cleaning up...")
    except Exception as e:
        logger.exception("❌ MCP Server crashed with unhandled exception: %s", e)
    else:
        logger.info("✅ MCP Server shut down cleanly.")


if __name__ == "__main__":
    main()
