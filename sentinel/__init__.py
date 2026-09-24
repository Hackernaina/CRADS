from .ingest import SpecError, load_spec
from .models import Endpoint, Inventory, Param
from .normalize import normalize


def ingest(raw: bytes | str) -> Inventory:
    """OpenAPI/Swagger text -> normalized Inventory. Raises SpecError."""
    return normalize(load_spec(raw))


__all__ = ["ingest", "load_spec", "normalize", "SpecError", "Endpoint", "Inventory", "Param"]
