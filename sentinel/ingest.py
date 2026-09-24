"""Load raw bytes (JSON/YAML) into a validated OpenAPI/Swagger dict."""
from __future__ import annotations

import json
from typing import Any

import yaml

MAX_BYTES = 5 * 1024 * 1024


class SpecError(ValueError):
    """Raised for any spec that cannot be ingested."""


def load_spec(raw: bytes | str) -> dict[str, Any]:
    if isinstance(raw, bytes):
        if len(raw) > MAX_BYTES:
            raise SpecError("Spec exceeds 5 MB limit")
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise SpecError("Spec is not valid UTF-8 text") from None
    if not raw.strip():
        raise SpecError("Spec is empty")

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise SpecError(f"Not valid JSON or YAML: {e}") from None

    if not isinstance(doc, dict):
        raise SpecError("Spec root must be an object")
    if "openapi" in doc:
        if not str(doc["openapi"]).startswith("3."):
            raise SpecError(f"Unsupported OpenAPI version: {doc['openapi']}")
    elif str(doc.get("swagger")) != "2.0":
        raise SpecError("Missing 'openapi: 3.x' or 'swagger: 2.0' field")
    if not isinstance(doc.get("paths"), dict):
        raise SpecError("Spec has no 'paths' object")
    return doc
