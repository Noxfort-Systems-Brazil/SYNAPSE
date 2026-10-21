# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import json


@dataclass
class IpcMessage:
    """Represents an incoming command from the UI/Tauri process via STDIN."""
    action: str
    id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, raw: str) -> Optional['IpcMessage']:
        try:
            data = json.loads(raw.strip())
            return cls(
                action=data.get("action", ""),
                id=data.get("id"),
                payload=data.get("payload", {})
            )
        except Exception:
            return None


@dataclass
class IpcEvent:
    """Represents an asynchronous domain event emitted to STDOUT."""
    event: str
    data: Any = None
    type: str = "event"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


@dataclass
class IpcResponse:
    """Represents a response to a correlated command."""
    id: Optional[str]
    success: bool
    result: Any = None
    error: Optional[str] = None
    type: str = "response"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)
