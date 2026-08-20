"""Polls OpenF1's REST API for real-time car telemetry while an F1 session
is live, buffers the latest reading per driver, and fans it out to
WebSocket subscribers.

OpenF1 was chosen over FastF1's raw SignalR feed: it's a plain REST API
(poll on an asyncio task, no threaded SignalR client needed), historical
data is free/no-auth, and real-time access is a simple API key rather than
an F1TV subscription plus an interactive browser login.
"""
import asyncio
from datetime import datetime, timezone

import httpx

OPENF1_BASE = "https://api.openf1.org/v1"
POLL_INTERVAL_SECONDS = 3
IDLE_POLL_INTERVAL_SECONDS = 60
NO_DATA_TIMEOUT_SECONDS = 30
ERROR_RETRY_SECONDS = 15


class LiveTelemetryManager:
    """Status states: idle | no_session | connecting | connected | no_data | error.

    'idle' is only the pre-start state; once started it always settles into
    one of the other five, so the frontend never has to guess why nothing's
    happening.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.status = "idle"
        self.status_detail = None
        self.current_session = None
        self.buffer: dict[int, dict] = {}
        self._subscribers: set = set()
        self._poll_task: asyncio.Task | None = None
        self._last_data_at: datetime | None = None
        self._since: datetime | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def _fetch_latest_session(self, client: httpx.AsyncClient) -> dict | None:
        try:
            resp = await client.get(f"{OPENF1_BASE}/sessions", params={"session_key": "latest"})
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None
        except Exception as e:
            print(f"[live_timing] Failed to fetch latest session: {e}")
            return None

    @staticmethod
    def _is_session_live(session: dict) -> bool:
        try:
            start = datetime.fromisoformat(session["date_start"])
            end = datetime.fromisoformat(session["date_end"])
            return start <= datetime.now(timezone.utc) <= end
        except Exception:
            return False

    async def _set_status(self, status: str, detail=None, extra: dict | None = None):
        self.status = status
        self.status_detail = detail
        message = {"type": "status", "status": status, "detail": detail, "session": self.current_session}
        if extra:
            message.update(extra)
        await self._broadcast(message)

    async def _fetch_car_data_window(
        self, client: httpx.AsyncClient, session_key, since: datetime, until: datetime
    ) -> list:
        """One request for every driver's data in a narrow time window.

        OpenF1 rejects an open-ended date>= query outright ("too much data
        at once") for a multi-hour session, even without a driver_number
        filter — an EXPLICIT upper bound is required to keep the window
        small. A single request covering ~one poll interval across all
        drivers is what actually works reliably (verified: a 5s window
        returns all 22 drivers' data in one call, no per-driver looping or
        concurrency needed, which also avoids OpenF1's aggressive rate
        limiting on many simultaneous requests).
        """
        try:
            # OpenF1 only recognizes strict date>/date< (verified empirically
            # — date>=/date<= silently returns "No results found").
            resp = await client.get(
                f"{OPENF1_BASE}/car_data",
                params={
                    "session_key": session_key,
                    "date>": since.isoformat(),
                    "date<": until.isoformat(),
                },
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[live_timing] car_data fetch failed: {e}")
            return []

    async def _fetch_location_window(
        self, client: httpx.AsyncClient, session_key, since: datetime, until: datetime
    ) -> list:
        """Same narrow-window approach as car_data — x/y/z track coordinates
        for every driver, used to draw a live position map."""
        try:
            resp = await client.get(
                f"{OPENF1_BASE}/location",
                params={
                    "session_key": session_key,
                    "date>": since.isoformat(),
                    "date<": until.isoformat(),
                },
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[live_timing] location fetch failed: {e}")
            return []

    async def _poll_loop(self):
        async with httpx.AsyncClient(timeout=10) as client:
            while True:
                try:
                    session = await self._fetch_latest_session(client)
                    session_changed = (
                        session is not None
                        and (self.current_session is None
                             or session["session_key"] != self.current_session.get("session_key"))
                    )
                    self.current_session = session

                    if session is None or not self._is_session_live(session):
                        self._since = None
                        await self._set_status("no_session")
                        await asyncio.sleep(IDLE_POLL_INTERVAL_SECONDS)
                        continue

                    session_key = session["session_key"]

                    if session_changed or self._since is None:
                        if self.status not in ("connected", "no_data"):
                            await self._set_status("connecting")
                        self._since = datetime.now(timezone.utc)
                        self.buffer = {}

                    poll_started_at = datetime.now(timezone.utc)
                    readings, positions = await asyncio.gather(
                        self._fetch_car_data_window(client, session_key, self._since, poll_started_at),
                        self._fetch_location_window(client, session_key, self._since, poll_started_at),
                    )
                    self._since = poll_started_at

                    if readings or positions:
                        self._last_data_at = datetime.now(timezone.utc)
                        for reading in readings:
                            self.buffer[reading["driver_number"]] = reading
                        self.status = "connected"
                        await self._broadcast({"type": "telemetry", "readings": readings, "positions": positions})
                    elif self._last_data_at and (
                        datetime.now(timezone.utc) - self._last_data_at
                    ).total_seconds() > NO_DATA_TIMEOUT_SECONDS:
                        await self._set_status("no_data")

                    await asyncio.sleep(POLL_INTERVAL_SECONDS)

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"[live_timing] Poll error: {e}")
                    await self._set_status("error", detail=str(e))
                    await asyncio.sleep(ERROR_RETRY_SECONDS)

    def start(self):
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_loop())

    def stop(self):
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None

    def subscribe(self, websocket):
        self._subscribers.add(websocket)

    def unsubscribe(self, websocket):
        self._subscribers.discard(websocket)

    async def _broadcast(self, message: dict):
        dead = set()
        for ws in self._subscribers:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._subscribers -= dead

    def snapshot(self) -> dict:
        return {
            "type": "status",
            "status": self.status,
            "detail": self.status_detail,
            "session": self.current_session,
        }
