"""SQLite persistence for inventories (swap for any backend later)."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import Inventory


class Store:
    def __init__(self, path: str = "sentinel.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS inventories "
                        "(id TEXT PRIMARY KEY, created TEXT, title TEXT, data TEXT)")

    def save(self, inv: Inventory) -> str:
        sid = uuid.uuid4().hex[:12]
        self.db.execute("INSERT INTO inventories VALUES (?,?,?,?)",
                        (sid, datetime.now(timezone.utc).isoformat(), inv.title,
                         json.dumps(inv.to_dict())))
        self.db.commit()
        return sid

    def get(self, sid: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT data FROM inventories WHERE id=?", (sid,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT id, created, title FROM inventories ORDER BY created DESC")
        return [{"id": i, "created": c, "title": t} for i, c, t in rows]
