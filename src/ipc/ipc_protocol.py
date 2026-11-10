# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, Optional
import json


def _ipc_default(obj: Any) -> Any:
    """Fast serializer fallback for NumPy scalars/arrays and arbitrary objects."""
    item_fn = getattr(obj, "item", None)
    if callable(item_fn) and getattr(obj, "ndim", 0) == 0:
        return item_fn()
    tolist_fn = getattr(obj, "tolist", None)
    if callable(tolist_fn):
        return tolist_fn()
    return str(obj)


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
        payload_data = asdict(self.data) if (is_dataclass(self.data) and not isinstance(self.data, type)) else self.data
        return json.dumps(
            {"event": self.event, "data": payload_data, "type": self.type},
            ensure_ascii=False,
            default=_ipc_default,
        )


@dataclass
class IpcResponse:
    """Represents a response to a correlated command."""
    id: Optional[str]
    success: bool
    result: Any = None
    error: Optional[str] = None
    type: str = "response"

    def to_json(self) -> str:
        res = asdict(self.result) if (is_dataclass(self.result) and not isinstance(self.result, type)) else self.result
        return json.dumps(
            {"id": self.id, "success": self.success, "result": res, "error": self.error, "type": self.type},
            ensure_ascii=False,
            default=_ipc_default,
        )
