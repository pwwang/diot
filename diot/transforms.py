"""Key transforms for diot

@Attribute:
    TRANSFORMS: Builtin transforms
"""
from typing import Dict, Callable
import re
import keyword
import inflection

def safe_transform(item: str) -> str:
    """
    Transform an arbitrary key into a safe key for dot notation

    Examples:
    >>> safe_transform("a,b")   # a_b
    >>> safe_transform("a_,_b") # a__b
    >>> safe_transform("in")    # _in

    Args:
        item: The item to be transformed

    Returns:
        The safely-transformed item
    """
    # // support bytes transform to keys in bytes?
    if isinstance(item, bytes):
        item = item.decode("utf-8")
    item = str(item)
    item = re.sub(r'[^A-Za-z0-9_]+', '.', item)
    item = re.sub(r'_?\.+|\.+_?', '_', item)
    if not item:
        return ''
    return ('_' + item
            if item[0] in '0123456789' or item in keyword.kwlist
            else item)

def camel_case(item: str) -> str:
    """Transform item to camel case format

    The item will be first safely-transformed.

    Examples:
    >>> camel_case('one_two')   # oneTwo
    >>> camel_case('_one')      # _one
    >>> camel_case('o_one')     # oOne

    Args:
        item: The item to be transformed

    Returns:
        The camel_case-transformed item
    """
    item = safe_transform(item)
    return inflection.camelize(item, False)


def snake_case(item: str) -> str:
    """Transform item to snake case

    The item will be first safely-transformed.

    Examples:
    >>> snake_case('oneTwo')   # one_two
    >>> snake_case('One')      # one
    >>> snake_case('1One')     # _1_one

    Args:
        item: The item to be transformed

    Returns:
        The snake_case-transformed item
    """
    item = safe_transform(item)
    return inflection.underscore(item)

def upper_case(item: str) -> str:
    """Transform item to upper case

    The item will be first safely-transformed.

    Examples:
    >>> upper_case('oneTwo')   # ONETWO
    >>> upper_case('One')      # ONE
    >>> upper_case('1One')     # _1ONE

    Args:
        item: The item to be transformed

    Returns:
        The uppercase-transformed item
    """
    item = safe_transform(item)
    return item.upper()

def lower_case(item: str) -> str:
    """Transform item to lower case

    The item will be first safely-transformed.

    Examples:
    >>> lower_case('ONETWO')   # onetwo
    >>> lower_case('One')      # one
    >>> lower_case('1One')     # _1one

    Args:
        item: The item to be transformed

    Returns:
        The lowercase-transformed item
    """
    item = safe_transform(item)
    return item.lower()

TRANSFORMS: Dict[str, Callable[[str], str]] = dict(
    safe=safe_transform,
    safe_transform=safe_transform,
    camel_case=camel_case,
    camelCase=camel_case,
    snake_case=snake_case,
    upper=upper_case,
    lower=lower_case,
    upper_case=upper_case,
    lower_case=lower_case,
    uppercase=upper_case,
    lowercase=lower_case,
    UPPERCASE=upper_case,
    UPPER_CASE=upper_case,
)
