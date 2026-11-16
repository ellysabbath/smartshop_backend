from datetime import date, datetime
from decimal import Decimal
import uuid as uuid_lib


def to_json_safe(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid_lib.UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_safe(v) for v in value]
    return str(value)


def model_to_dict(instance) -> dict:
    data = {}
    for field in instance._meta.concrete_fields:
        name = field.name
        value = getattr(instance, name, None)
        if field.is_relation and field.many_to_one:
            data[f"{name}_id"] = str(value.pk) if value is not None else None
            continue
        data[name] = to_json_safe(value)
    data["id"] = str(instance.pk)
    return data