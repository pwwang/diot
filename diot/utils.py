"""Utilities for diot"""
from typing import TYPE_CHECKING, Any, Union


if TYPE_CHECKING:
    from .diot import Diot


class DiotFrozenError(Exception):
    """When try to modify a frozen diot"""


def nest(
    value: Any,
    types: Union[type],
    dest_type: type,
    frozen: bool,
) -> Any:
    """Convert values with certain types recursively"""
    # nothing to convert
    if not types or not isinstance(value, tuple(types)):  # type: ignore
        return value

    if (list in types and isinstance(value, list)) or (  # type: ignore
        tuple in types and isinstance(value, tuple)  # type: ignore
    ):
        # use value.__class__ to keep user-subclassed list or tuple
        return value.__class__(
            [nest(val, types, dest_type, frozen) for val in value]
        )

    if dict in types and isinstance(value, dict):  # type: ignore
        return dest_type(
            [
                (key, nest(val, types, dest_type, frozen))
                for key, val in value.items()
            ]
        )
    return value


def to_dict(value: "Diot") -> dict:
    """Convert converted Diot objects back to dict"""
    if isinstance(value, dict):
        return {key: to_dict(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return tuple((to_dict(val) for val in value))
    if isinstance(value, list):
        return [to_dict(val) for val in value]
    return value
