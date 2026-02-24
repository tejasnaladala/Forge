from __future__ import annotations

import inspect
from typing import Any, get_type_hints


PYTHON_TO_JSON_TYPE = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class ToolSchema:
    @staticmethod
    def from_function(func) -> dict[str, Any]:
        sig = inspect.signature(func)
        try:
            hints = get_type_hints(func)
        except Exception:
            hints = {}

        properties: dict[str, Any] = {}
        required: list[str] = []

        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue

            hint = hints.get(name, str)
            origin = getattr(hint, "__origin__", None)
            if origin is not None:
                hint = origin

            json_type = PYTHON_TO_JSON_TYPE.get(hint, "string")
            prop: dict[str, Any] = {"type": json_type}

            if param.default is not inspect.Parameter.empty:
                prop["default"] = param.default
            else:
                required.append(name)

            properties[name] = prop

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        return schema
