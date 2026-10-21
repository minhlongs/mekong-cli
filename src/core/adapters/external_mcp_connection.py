# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Connection lifecycle manager for external MCP client sessions."""

from __future__ import annotations

import logging
import os
from concurrent.futures import Future
from typing import Any, Optional

import anyio

from .external_mcp_types import (
    ExternalMcpTransportError,
    HttpConfig,
    StdioConfig,
    load_http,
    load_stdio,
)

logger = logging.getLogger(__name__)


class ExternalMcpConnectionManager:
    """Manages the lifecycle of an external MCP session background task."""

    def __init__(self, transport: str, config: Any) -> None:
        self.transport = transport
        self.config = config
        self.portal_cm: Optional[Any] = None
        self.portal: Optional[Any] = None
        self.close_event: Optional[Any] = None
        self.loop_future: Optional[Any] = None
        self.session: Optional[Any] = None

    def ensure_connected(self) -> Any:
        """Establish connection if not already active."""
        if self.session is not None:
            return self.session

        if self.transport == "stdio":
            load_stdio()
        else:
            load_http()

        from anyio.from_thread import start_blocking_portal

        self.portal_cm = start_blocking_portal()
        self.portal = self.portal_cm.__enter__()

        if self.transport == "stdio":
            self.session = self._connect_stdio()
        else:
            self.session = self._connect_http()
        return self.session

    def _connect_stdio(self) -> Any:
        stdio_client, StdioServerParameters, ClientSession = load_stdio()
        cfg: StdioConfig = self.config

        params = StdioServerParameters(
            command=cfg.command,
            args=cfg.args,
            env=cfg.env or {**os.environ},
            cwd=cfg.cwd,
        )

        self.close_event = anyio.Event()
        session_future: Future[Any] = Future()

        async def _session_loop() -> None:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    if not session_future.done():
                        session_future.set_result(session)
                    await self.close_event.wait()

        try:
            self.loop_future = self.portal.start_task_soon(_session_loop)
            return session_future.result()
        except Exception as exc:
            self.signal_close()
            if self.loop_future is not None:
                try:
                    self.loop_future.result()
                except Exception:
                    logger.debug("session loop cleanup failed", exc_info=True)
            raise ExternalMcpTransportError(
                f"failed to connect to stdio MCP server {cfg.command!r}: {exc}"
            ) from exc

    def _connect_http(self) -> Any:
        streamablehttp_client, ClientSession = load_http()
        cfg: HttpConfig = self.config

        self.close_event = anyio.Event()
        session_future: Future[Any] = Future()

        async def _session_loop() -> None:
            async with streamablehttp_client(
                url=cfg.url,
                headers=cfg.headers,
                timeout=cfg.timeout,
                sse_read_timeout=cfg.sse_read_timeout,
            ) as (read, write, _get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    if not session_future.done():
                        session_future.set_result(session)
                    await self.close_event.wait()

        try:
            self.loop_future = self.portal.start_task_soon(_session_loop)
            return session_future.result()
        except Exception as exc:
            self.signal_close()
            if self.loop_future is not None:
                try:
                    self.loop_future.result()
                except Exception:
                    logger.debug("session loop cleanup failed", exc_info=True)
            raise ExternalMcpTransportError(
                f"failed to connect to HTTP MCP server {cfg.url!r}: {exc}"
            ) from exc

    def signal_close(self) -> None:
        """Fire close event in the background task loop."""
        if self.close_event is not None and self.portal is not None:
            try:
                self.portal.call(self.close_event.set)
            except Exception:
                logger.debug("close event set failed", exc_info=True)

    def close(self) -> None:
        """Tear down loop and blocking portal."""
        self.signal_close()
        if self.loop_future is not None:
            try:
                self.loop_future.result()
            except Exception:
                logger.debug("session loop shutdown failed", exc_info=True)
        self.loop_future = None
        self.close_event = None
        self.session = None
        if self.portal_cm is not None:
            try:
                self.portal_cm.__exit__(None, None, None)
            except Exception:
                logger.debug("portal cleanup failed", exc_info=True)
        self.portal_cm = None
        self.portal = None


__all__ = ["ExternalMcpConnectionManager"]
