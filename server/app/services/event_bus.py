"""In-memory event broadcaster for SSE request streams."""

import asyncio
from collections import defaultdict
from typing import AsyncGenerator, Dict, List
import uuid
from server.app.schemas.request import RequestEventResponse


class RequestEventBus:
    """Pub/sub queue registry for real-time SSE streaming per request ID."""

    def __init__(self):
        self._subscribers: Dict[uuid.UUID, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, request_id: uuid.UUID) -> asyncio.Queue:
        """Register a subscriber queue for a specific request."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[request_id].append(queue)
        return queue

    async def unsubscribe(self, request_id: uuid.UUID, queue: asyncio.Queue):
        """Remove a subscriber queue when the client disconnects."""
        async with self._lock:
            if request_id in self._subscribers:
                if queue in self._subscribers[request_id]:
                    self._subscribers[request_id].remove(queue)
                if not self._subscribers[request_id]:
                    del self._subscribers[request_id]

    async def publish(self, request_id: uuid.UUID, event: RequestEventResponse):
        """Broadcast an event to all active SSE subscribers of a request."""
        async with self._lock:
            queues = list(self._subscribers.get(request_id, []))
        for q in queues:
            await q.put(event)


event_bus = RequestEventBus()
