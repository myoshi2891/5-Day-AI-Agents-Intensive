"""Image agent builder that integrates MCP servers with cost approvals."""

from __future__ import annotations

import asyncio
import base64
import importlib
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Iterable, List, Optional, Protocol, Type, cast

try:
    from ..agents import FallbackAgent
    from ..config import build_model
    from ..tool_types import AgentToolType, Tool
except ImportError:
    if __package__:
        raise
    import sys

    pkg_root = Path(__file__).resolve().parents[2]
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))
    from day_2.Agent_Tools_Best_Practices.agents import FallbackAgent  # type: ignore
    from day_2.Agent_Tools_Best_Practices.config import build_model  # type: ignore
    from day_2.Agent_Tools_Best_Practices.tool_types import (  # type: ignore
        AgentToolType,
        Tool,
    )

from google.adk.agents.base_agent import BaseAgent as GoogleBaseAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)

BULK_IMAGE_THRESHOLD = 1  # Single image auto-approves; >1 requires approval

MCP_IMAGE_SERVERS = {
    "everything": {
        "package": "@modelcontextprotocol/server-everything",
        "tool_filter": ["getTinyImage"],
        "description": "Reference server exposing sample image tools like getTinyImage.",
    },
    "shroominic": {
        "package": "@shroominic/image-tool",
        "tool_filter": ["generateImage"],
        "description": "Playful Flux-based server suitable for quick sketches.",
    },
    "stabilityai": {
        "package": "@modelcontextprotocol/server-stabilityai",
        "tool_filter": ["text_to_image"],
        "description": "Stability AI integration (requires API key configured).",
    },
}

MCP_IMAGE_SERVER_KEY = os.getenv("MCP_IMAGE_SERVER", "everything").lower()
if MCP_IMAGE_SERVER_KEY not in MCP_IMAGE_SERVERS:
    logger.warning(
        "Unknown MCP_IMAGE_SERVER=%s. Falling back to 'everything'.",
        MCP_IMAGE_SERVER_KEY,
    )
    MCP_IMAGE_SERVER_KEY = "everything"

SELECTED_MCP_SERVER = MCP_IMAGE_SERVERS[MCP_IMAGE_SERVER_KEY]
logger.info(
    "Using MCP image server '%s' (%s)",
    MCP_IMAGE_SERVER_KEY,
    SELECTED_MCP_SERVER["package"],
)


def _noop_display(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover
    return None


class _DummyImage:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


try:
    from IPython.display import Image as IPImage, display  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    display = _noop_display  # type: ignore[assignment]
    IPImage = _DummyImage  # type: ignore[assignment,misc]

CAN_DISPLAY_INLINE = display is not _noop_display and IPImage is not _DummyImage


def _write_inline_bytes(
    data: bytes,
    mime_type: Optional[str],
    *,
    event_idx: int,
    part_idx: int,
) -> Path:
    """Persist inline tool output to disk for manual inspection."""
    suffix = mimetypes.guess_extension(mime_type or "") or ".bin"
    output_dir = Path("debug_outputs")
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / f"event_{event_idx}_{part_idx}{suffix}"
    file_path.write_bytes(data)
    return file_path


def display_events(events: Iterable[Any]) -> None:
    """Display or persist inline MCP outputs."""
    for idx, event in enumerate(events):
        content = getattr(event, "content", None)
        if not content:
            continue
        for part_idx, part in enumerate(content.parts or []):
            inline = getattr(part, "inline_data", None)
            file_data = getattr(part, "file_data", None)
            function_resp = getattr(part, "function_response", None)

            if getattr(part, "text", None):
                print(f"[event {idx}] {part.text}")
            elif inline:
                payload = base64.b64decode(inline.data)
                saved = _write_inline_bytes(
                    payload, inline.mime_type, event_idx=idx, part_idx=part_idx
                )
                print(f"[event {idx}] inline data saved to {saved}")
                if CAN_DISPLAY_INLINE:
                    display(IPImage(data=payload, format=inline.mime_type))
            elif file_data and file_data.file_uri:
                file_path = file_data.file_uri.replace("file://", "")
                try:
                    if CAN_DISPLAY_INLINE:
                        display(IPImage(filename=file_path))
                except Exception:
                    logger.warning("Unable to display file data at %s", file_path)
                else:
                    print(f"[event {idx}] file data available at {file_path}")
            elif function_resp:
                for item in function_resp.response.get("content", []):
                    inline_block = item.get("inline_data")
                    if inline_block:
                        payload = base64.b64decode(inline_block["data"])
                        saved = _write_inline_bytes(
                            payload,
                            inline_block.get("mime_type"),
                            event_idx=idx,
                            part_idx=part_idx,
                        )
                        print(f"[event {idx}] inline data saved to {saved}")
                        if CAN_DISPLAY_INLINE:
                            display(
                                IPImage(
                                    data=payload,
                                    format=inline_block.get("mime_type"),
                                )
                            )
                    elif item.get("type") == "image" and "data" in item:
                        payload = base64.b64decode(item["data"])
                        saved = _write_inline_bytes(
                            payload, None, event_idx=idx, part_idx=part_idx
                        )
                        print(f"[event {idx}] inline image saved to {saved}")
                        if CAN_DISPLAY_INLINE:
                            display(IPImage(data=payload))


print("✅ ADK components imported successfully.")

MCP_IMAGE_SERVER = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                SELECTED_MCP_SERVER["package"],
            ],
        ),
        timeout=30,
    ),
    tool_filter=SELECTED_MCP_SERVER["tool_filter"],
)


class BaseAgent(Protocol):
    """Structural Agent interface used for typing regardless of dependency availability."""

    tools: List[AgentToolType]

    def __init__(
        self,
        *,
        name: str,
        model: Any,
        instruction: str,
        tools: Optional[Iterable[AgentToolType]] = None,
        **kwargs: Any,
    ) -> None:
        ...


def _load_agent_class() -> Type[BaseAgent]:
    """Return the real google-adk Agent if available, otherwise fallback."""
    try:
        module = importlib.import_module("google.adk.agents")
        agent_cls = getattr(module, "Agent")
        logger.info("google.adk.agents.Agent successfully loaded")
        return cast(Type[BaseAgent], agent_cls)
    except (ImportError, AttributeError) as e:
        logger.warning(
            "google-adk Agent not available, using fallback. reason=%s", e
        )
        return FallbackAgent


Agent: Type[BaseAgent] = _load_agent_class()
_root_agent: Optional[BaseAgent] = None


def cost_aware_image_request(
    prompt: str,
    num_images: int,
    approval_decision: Optional[str] = None,
) -> dict[str, Any]:
    """Request approval before issuing bulk image generations."""
    if num_images <= 0:
        return {
            "status": "rejected",
            "message": (
                f"Invalid num_images: {num_images}. "
                "Please provide a positive integer."
            ),
        }

    if num_images <= BULK_IMAGE_THRESHOLD:
        return {
            "status": "approved",
            "message": (
                f"Auto-approved single image request for '{prompt}'. "
                "Feel free to call the MCP image tool."
            ),
        }

    decision = (approval_decision or "").strip().lower()
    if not decision:
        return {
            "status": "pending",
            "message": (
                f"Bulk image request ({num_images}) detected. Ask the user to respond "
                "with 'APPROVE BULK' or 'REJECT BULK', then call this tool again "
                "passing the response via the approval_decision argument."
            ),
        }

    if decision in {"approve bulk", "approve", "approved", "yes"}:
        return {
            "status": "approved",
            "message": (
                f"Approved {num_images} images for '{prompt}'. "
                "You may now call the MCP tool."
            ),
        }

    if decision in {"reject bulk", "reject", "rejected", "no"}:
        return {
            "status": "rejected",
            "message": (
                f"Rejected {num_images} images for '{prompt}'. "
                "Do not call the MCP server."
            ),
        }

    return {
        "status": "pending",
        "message": (
            "Invalid approval_decision provided. Please ask the user to reply with "
            "'APPROVE BULK' or 'REJECT BULK' and call the tool again with that text."
        ),
    }


def get_root_agent() -> BaseAgent:
    """Get or create the root agent instance."""
    global _root_agent
    if _root_agent is None:
        instruction = (
            "You are an image-generation specialist with access to multiple MCP "
            "servers. Always call the cost_aware_image_request tool first when "
            "users request more than one image so that expensive bulk requests "
            "can be approved. If the tool returns status 'pending', ask the user "
            "to respond with 'APPROVE BULK' or 'REJECT BULK' and call the tool "
            "again with that text via the approval_decision argument. Once "
            "approved, use the MCP image tool to create the images."
        )
        _root_agent = Agent(
            model=build_model(),
            name="image_agent",
            instruction=instruction,
            tools=[
                FunctionTool(func=cost_aware_image_request),
                MCP_IMAGE_SERVER,
            ],
        )
    return _root_agent


root_agent = get_root_agent()


def run_debug_session(
    prompt: str = "Provide a sample tiny image", *, verbose: bool = True
) -> Optional[Iterable[Any]]:
    """Run the image agent via InMemoryRunner for quick, local debugging."""
    if not isinstance(root_agent, GoogleBaseAgent):
        print(
            "⚠️ Skipping InMemoryRunner debug run because fallback agent is active."
        )
        return None

    runner = InMemoryRunner(agent=cast(GoogleBaseAgent, root_agent))
    return asyncio.run(runner.run_debug(prompt, verbose=verbose))


__all__ = [
    "cost_aware_image_request",
    "display_events",
    "get_root_agent",
    "root_agent",
    "run_debug_session",
]
