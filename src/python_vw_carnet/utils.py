from dataclasses import asdict, is_dataclass
from typing import Any

from python_vw_carnet.models import DTOModel


def serialize_for_json(value: Any) -> Any:
    if isinstance(value, DTOModel):
        return {key: serialize_for_json(item) for key, item in value.to_dict().items()}
    if is_dataclass(value):
        return {key: serialize_for_json(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    return value
