"""Turn an OpenAPI 3.x / Swagger 2.0 dict into a normalized Inventory."""
from __future__ import annotations

from typing import Any

from .models import Endpoint, Inventory, Param

METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")
MAX_REF_DEPTH = 20


class RefResolver:
    """Resolves local '#/...' refs; stops on cycles/depth to stay safe."""

    def __init__(self, doc: dict[str, Any], warnings: list[str]):
        self.doc, self.warnings = doc, warnings

    def _lookup(self, ref: str) -> Any:
        if not ref.startswith("#/"):
            self.warnings.append(f"External $ref not resolved: {ref}")
            return {"$ref": ref}
        node: Any = self.doc
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                self.warnings.append(f"Broken $ref: {ref}")
                return {"$ref": ref, "broken": True}
            node = node[part]
        return node

    def resolve(self, node: Any, seen: tuple[str, ...] = ()) -> Any:
        if isinstance(node, list):
            return [self.resolve(n, seen) for n in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node and isinstance(node["$ref"], str):
            ref = node["$ref"]
            if ref in seen or len(seen) >= MAX_REF_DEPTH:
                return {"$ref": ref, "circular": True}
            target = self._lookup(ref)
            if "$ref" in target and target.get("$ref") == ref:
                return target
            return self.resolve(target, seen + (ref,))
        return {k: self.resolve(v, seen) for k, v in node.items()}


def normalize(doc: dict[str, Any]) -> Inventory:
    warnings: list[str] = []
    r = RefResolver(doc, warnings)
    v2 = "swagger" in doc
    info = doc.get("info") or {}
    global_sec = doc.get("security", [])
    global_consumes = doc.get("consumes", ["application/json"])
    global_produces = doc.get("produces", ["application/json"])

    endpoints: list[Endpoint] = []
    for path, item in doc["paths"].items():
        item = r.resolve(item) if isinstance(item, dict) else {}
        shared = item.get("parameters", [])
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            ep_id = f"{method.upper()} {path}"
            params, body = _params(shared, op.get("parameters", []), v2,
                                   op.get("consumes", global_consumes))
            if not v2:
                body = _body_v3(op.get("requestBody"))
            endpoints.append(Endpoint(
                id=ep_id,
                method=method.upper(),
                path=path,
                operation_id=op.get("operationId"),
                summary=op.get("summary") or op.get("description") or "",
                tags=op.get("tags", []),
                params=params,
                request_body=body,
                responses=_responses(op.get("responses", {}), v2,
                                     op.get("produces", global_produces)),
                security=op.get("security", global_sec) or [],
                deprecated=bool(op.get("deprecated")),
            ))
    if not endpoints:
        warnings.append("Spec contains no operations")

    return Inventory(
        title=info.get("title", "Untitled"),
        version=str(info.get("version", "")),
        spec_version="2.0" if v2 else str(doc["openapi"]),
        servers=_servers(doc, v2),
        security_schemes=r.resolve(
            doc.get("securityDefinitions", {}) if v2
            else (doc.get("components") or {}).get("securitySchemes", {})),
        endpoints=endpoints,
        warnings=sorted(set(warnings)),
    )


def _params(shared, own, v2, consumes):
    merged = {(p.get("name"), p.get("in")): p for p in shared + own if isinstance(p, dict)}
    params, body = [], None
    form_props: dict[str, Any] = {}
    for p in merged.values():
        loc = p.get("in")
        if v2 and loc == "body":
            body = {"required": bool(p.get("required")), "content_types": consumes,
                    "schema": p.get("schema", {})}
        elif v2 and loc == "formData":
            form_props[p["name"]] = {k: v for k, v in p.items() if k not in ("name", "in", "required")}
        else:
            schema = p.get("schema") or {k: p[k] for k in ("type", "format", "enum", "items") if k in p}
            params.append(Param(name=p.get("name", ""), location=loc or "query",
                                required=bool(p.get("required")) or loc == "path", schema=schema))
    if form_props:
        body = {"required": False, "content_types": consumes,
                "schema": {"type": "object", "properties": form_props}}
    return params, body


def _body_v3(rb):
    if not isinstance(rb, dict):
        return None
    content = rb.get("content") or {}
    first = next(iter(content.values()), {}) or {}
    return {"required": bool(rb.get("required")), "content_types": list(content),
            "schema": first.get("schema", {})}


def _responses(resps, v2, produces):
    out = {}
    for status, resp in (resps or {}).items():
        if not isinstance(resp, dict):
            continue
        if v2:
            schema = resp.get("schema", {})
        else:
            content = resp.get("content") or {}
            schema = (next(iter(content.values()), {}) or {}).get("schema", {})
        out[str(status)] = {"description": resp.get("description", ""), "schema": schema}
    return out


def _servers(doc, v2):
    if v2:
        host = doc.get("host")
        if not host:
            return []
        return [f"{s}://{host}{doc.get('basePath', '')}" for s in doc.get("schemes", ["https"])]
    return [s.get("url", "") for s in doc.get("servers", []) if isinstance(s, dict)]
