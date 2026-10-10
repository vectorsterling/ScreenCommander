"""Run Screen Commander MCP over SSE (bind 0.0.0.0 for LAN clients)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import anyio
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "action_executor"))

from mcp_server.server import create_server, transport_security_settings


async def _main() -> None:
    load_dotenv()
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8080"))
    sse_path = os.getenv("MCP_SSE_PATH", "/sse")
    message_path = os.getenv("MCP_MESSAGE_PATH", "/messages/")

    server = create_server()
    security = transport_security_settings()

    print(f"Screen Commander MCP listening on http://{host}:{port}{sse_path}")
    print(f"POST client messages to http://{host}:{port}{message_path}")

    await server.run_sse_async(
        host=host,
        port=port,
        sse_path=sse_path,
        message_path=message_path,
        transport_security=security,
    )


def main() -> None:
    anyio.run(_main)


if __name__ == "__main__":
    main()
