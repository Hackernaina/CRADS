"""Normalized endpoint model — the contract Phase 2 consumes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Param:
    name: str
    location: str  # path | query | header | cookie
    required: bool = False
    schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Endpoint:
    id: str  # "METHOD /path"
    method: str
    path: str
    operation_id: str | None = None
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    params: list[Param] = field(default_factory=list)
    request_body: dict[str, Any] | None = None  # {"required", "content_types", "schema"}
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)  # status -> {"description", "schema"}
    security: list[dict[str, list[str]]] = field(default_factory=list)  # [] = no auth
    deprecated: bool = False

    @property
    def requires_auth(self) -> bool:
        return any(req for req in self.security)  # [{}] means optional/anonymous


@dataclass
class Inventory:
    title: str
    version: str
    spec_version: str  # "2.0" | "3.x"
    servers: list[str]
    security_schemes: dict[str, Any]
    endpoints: list[Endpoint]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for e, ep in zip(d["endpoints"], self.endpoints):
            e["requires_auth"] = ep.requires_auth
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Inventory":
        eps = []
        for e in d.get("endpoints", []):
            e = {k: v for k, v in e.items() if k != "requires_auth"}
            e["params"] = [Param(**p) for p in e.get("params", [])]
            eps.append(Endpoint(**e))
        return cls(
            title=d["title"], version=d["version"], spec_version=d["spec_version"],
            servers=d.get("servers", []), security_schemes=d.get("security_schemes", {}),
            endpoints=eps, warnings=d.get("warnings", []),
        )
