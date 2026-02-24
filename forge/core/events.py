from __future__ import annotations

import asyncio
import fnmatch

import structlog

from forge.core.types import ForgeEvent

logger = structlog.get_logger()


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}
        self._global_handlers: list = []

    def on(self, event_type: str, handler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def on_all(self, handler) -> None:
        self._global_handlers.append(handler)

    async def emit(self, event: ForgeEvent) -> None:
        handlers = list(self._global_handlers)

        for pattern, pattern_handlers in self._handlers.items():
            if fnmatch.fnmatch(event.type, pattern) or pattern == event.type:
                handlers.extend(pattern_handlers)

        if not handlers:
            return

        tasks = []
        for handler in handlers:
            tasks.append(self._safe_call(handler, event))

        await asyncio.gather(*tasks)

    async def _safe_call(self, handler, event: ForgeEvent) -> None:
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            logger.error("event_handler_error", event_type=event.type, exc_info=True)


event_bus = EventBus()
