"""
Python dictionary with dot notation
"""
import re
import keyword
from copy import deepcopy
import inflection

__version__ = "0.0.10"

def safe_transform(item):
    """
    Transform an arbitrary key into a safe key for dot notation
    """
    if isinstance(item, bytes):
        item = item.decode("utf-8")
    item = str(item)
    item = re.sub(r'[^A-Za-z0-9_]+', '.', item)
    item = re.sub(r'_?\.+|\.+_?', '_', item)
    if not item:
        return ''
    return '_' + item \
           if item[0] in '0123456789' or item in keyword.kwlist \
           else item

def camel_case(item):
    """
    Transform keys to camel case
    For example:
    one_two => oneTwo
    _one => One
    """
    item = safe_transform(item)
    return inflection.camelize(item, False)


def snake_case(item):
    """
    Transform keys to snake case
    For example:
    oneTwo => one_tow
    One => _one
    """
    item = safe_transform(item)
    return inflection.underscore(item)

def upper_case(item):
    """
    oneTwo => ONETWO
    """
    item = safe_transform(item)
    return item.upper()

def lower_case(item):
    """
    ONETWO => onetwo
    """
    item = safe_transform(item)
    return item.lower()

TRANSFORMS = dict(
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

__all__ = ['Diot', 'CamelDiot', 'SnakeDiot', 'OrderedDiot']

def _nest(value, types, dest_type):
    """Convert values with certain types recursively"""
    if not types:
        return value
    if not isinstance(value, tuple(types)):
        return value
    if ((list in types and isinstance(value, list)) or
            (tuple in types and isinstance(value, tuple))):
        return value.__class__([_nest(val, types, dest_type) for val in value])
    if dict in types and isinstance(value, dict):
        return dest_type([(key, _nest(val, types, dest_type))
                          for key, val in value.items()])
    return value

def _dict(value):
    """Convert converted Diot objects back to dict"""
    if isinstance(value, dict):
        return {key: _dict(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return tuple((_dict(val) for val in value))
    if isinstance(value, list):
        return [_dict(val) for val in value]
    return value

class Diot(dict):
    """Dictionary with dot notation"""
    def __new__(cls, *args, **kwargs):
        ret = super().__new__(cls)
        # unpickling will not call __init__
        # we use a flag '__inited__' to tell if __init__ has been called
        # is there a better way?
        ret.__init__(*args, **kwargs)
        return ret

    @classmethod
    def from_namespace(cls, namespace, recursive=True):
        """Get a Diot object from a namespace"""
        ret = cls({key: val
                   for key, val in vars(namespace).items()
                   if not key.startswith('__')})
        if not recursive:
            return ret
        for key, value in ret.items():
            if isinstance(value, namespace.__class__):
                ret[key] = cls.from_namespace(value)
        return ret

    def __init__(self, *args, **kwargs):
        if self.__dict__.get('__inited__'):
            return

        self.__dict__['__inited__'] = True
        self._diot_keymaps = {}
        self._diot_nest = kwargs.pop('diot_nest', True)
        self._diot_nest = ([dict, list, tuple]
                           if self._diot_nest is True
                           else []
                           if self._diot_nest is False
                           else list(self._diot_nest)
                           if isinstance(self._diot_nest, tuple)
                           else self._diot_nest
                           if isinstance(self._diot_nest, list)
                           else [self._diot_nest])
        self._diot_transform = kwargs.pop('diot_transform', 'safe')
        if isinstance(self._diot_transform, str):
            self._diot_transform = TRANSFORMS[self._diot_transform]

        super().__init__(*args, **kwargs)
        for key in self:
            transformed_key = self._diot_transform(key)
            if transformed_key in self._diot_keymaps:
                raise KeyError(
                    f"Keys {self._diot_keymaps[transformed_key]!r} and {key!r}"
                    " will be transformed to the same attribute. "
                    "Either change one of them or use a different "
                    "diot_transform function."
                )
            self._diot_keymaps[transformed_key] = key

        # nest values
        for key in self:
            self[key] = _nest(self[key], self._diot_nest, self.__class__)

    def __setattr__(self, name, value):
        if name.startswith('_diot_'):
            self.__dict__[name] = value
        else:
            self[name] = _nest(value, self._diot_nest, self.__class__)

    def __setitem__(self, name, value):
        transformed_key = self._diot_transform(name)
        if (transformed_key in self._diot_keymaps and
                transformed_key != name and
                self._diot_keymaps[transformed_key] != name):
            raise KeyError(
                f"{name!r} will be transformed to the same attribute as "
                f"{self._diot_keymaps[transformed_key]!r}. "
                "Either use a different name or "
                "a different diot_transform function."
            )
        self._diot_keymaps[transformed_key] = name
        super().__setitem__(name, _nest(value,
                                        self._diot_nest,
                                        self.__class__))

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name):
        original_key = self._diot_keymaps.get(name, name)
        return super().__getitem__(original_key)

    def pop(self, name, *value):
        if name in self._diot_keymaps:
            name = self._diot_keymaps[name]
            del self._diot_keymaps[name]
        if value:
            return super().pop(name, value[0])
        return super().pop(name)

    def popitem(self):
        key, val = super().popitem()
        if key in self._diot_keymaps:
            del self._diot_keymaps[key]
        else:
            del self._diot_keymaps[self._diot_transform(key)]
        return key, val

    def update(self, *value, **kwargs):
        dict_to_update = dict(*value, **kwargs)
        for key, val in dict_to_update.items():
            if (key not in self or
                    not isinstance(self[key], dict) or
                    not isinstance(val, dict)):
                self[key] = _nest(val, self._diot_nest, self.__class__)
            else:
                self[key].update(val)

    def __or__(self, other):
        ret = self.copy()
        ret.update(other)
        return ret

    def __ior__(self, other):
        self.update(other)
        return self

    def __delitem__(self, name):
        if name in self._diot_keymaps:
            super().__delitem__(self._diot_keymaps[name])
            del self._diot_keymaps[name]
        else:
            super().__delitem__(name)
            del self._diot_keymaps[self._diot_transform(name)]

    __delattr__ = __delitem__

    def __repr__(self):
        diot_transform = self._diot_transform
        for key, val in TRANSFORMS.items():
            if val == diot_transform:
                diot_transform = key
                break
        return '{}({}, diot_nest = [{}], diot_transform = {!r})'.format(
            self.__class__.__name__,
            list(self.items()),
            ', '.join(dn.__name__ for dn in self._diot_nest),
            diot_transform
        )

    def __str__(self):
        return repr(dict(self))

    def setdefault(self, name, value):
        if name in self:
            return self[name]
        self[name] = value
        return self[name]

    def accessible_keys(self):
        """Get the converted keys"""
        return self._diot_keymaps.keys()

    def get(self, name, value=None):
        name = self._diot_keymaps.get(name, name)
        return super().get(name, _nest(value,
                                       self._diot_nest,
                                       self.__class__))

    def __contains__(self, name):
        if name in self._diot_keymaps:
            return True
        return super().__contains__(name)

    def clear(self):
        super().clear()
        self._diot_keymaps.clear()

    def copy(self):
        return self.__class__(list(self.items()),
                              diot_nest=self._diot_nest,
                              diot_transform=self._diot_transform)

    __copy__ = copy

    def __deepcopy__(self, memo=None):
        out = self.__class__(diot_nest=self._diot_nest,
                             diot_transform=self._diot_transform)
        memo = memo or {}
        memo[id(self)] = out
        for key, value in self.items():
            out[key] = deepcopy(value, memo)
        return out

    # for pickling and unpickling
    def __getstate__(self):
        return {}

    def __getnewargs_ex__(self):
        return ((list(self.items()), ),
                {'diot_transform': self._diot_transform,
                 'diot_nest': self._diot_nest})

    def to_dict(self):
        """
        Turn the Box and sub Boxes back into a native
        python dictionary.
        """
        return _dict(self)

    dict = as_dict = to_dict

    def to_json(self,
                filename=None,
                encoding="utf-8",
                errors="strict",
                **json_kwargs):
        """Convert to a json string or save it to json file"""
        import json
        json_dump = json.dumps(self.to_dict(),
                               ensure_ascii=False,
                               **json_kwargs)
        if not filename:
            return json_dump
        with open(filename, 'w', encoding=encoding, errors=errors) as fjs:
            fjs.write(json_dump)
        return None

    json = as_json = to_json

    def to_yaml(self,
                filename=None,
                default_flow_style=False,
                encoding="utf-8",
                errors="strict",
                **yaml_kwargs):
        """Convert to a yaml string or save it to yaml file"""
        try:
            import yaml
        except ImportError as exc: # pragma: no cover
            raise ImportError(
                'You need pyyaml installed to export Diot as yaml.'
            ) from exc
        yaml_dump = self.to_dict()
        if not filename:
            return yaml.dump(yaml_dump,
                             default_flow_style=default_flow_style,
                             **yaml_kwargs)
        with open(filename, 'w', encoding=encoding, errors=errors) as fyml:
            yaml.dump(yaml_dump,
                      stream=fyml,
                      default_flow_style=default_flow_style,
                      **yaml_kwargs)
        return None

    yaml = as_yaml = to_yaml

    def to_toml(self, filename=None, encoding="utf-8", errors="strict"):
        """Convert to a toml string or save it to toml file"""
        try:
            import toml
        except ImportError as exc: # pragma: no cover
            raise ImportError(
                "You need toml installed to export Diot as toml."
            ) from exc
        toml_dump = self.to_dict()
        if not filename:
            return toml.dumps(toml_dump)
        with open(filename, 'w', encoding=encoding, errors=errors) as ftml:
            toml.dump(toml_dump, ftml)
        return None

    toml = as_toml = to_toml

class CamelDiot(Diot):
    """With camel case conversion"""
    def __init__(self, *args, **kwargs):
        kwargs['diot_transform'] = camel_case
        super().__init__(*args, **kwargs)

class SnakeDiot(Diot):
    """With snake case conversion"""
    def __init__(self, *args, **kwargs):
        kwargs['diot_transform'] = snake_case
        super().__init__(*args, **kwargs)

class OrderedDiot(Diot):
    """With key order preserved"""
    def __init__(self, *args, **kwargs):
        self._diot_orderedkeys = [
            key[0] if isinstance(key, tuple) else key
            for arg in args for key in arg
        ] + [
            key for key in kwargs if not key.startswith('diot_')
        ]
        super().__init__(*args, **kwargs)

    def __setitem__(self, name, value):
        super().__setitem__(name, value)
        if name not in self._diot_orderedkeys:
            self._diot_orderedkeys.append(name)

    def items(self):
        return ((key, self[key]) for key in self._diot_orderedkeys)

    def insert(self, position, name, value=None):
        """Insert an item to certain position"""
        if position is None:
            position = len(self)

        if isinstance(name, tuple): # key-value pair
            if value is not None:
                raise ValueError(
                    'Unnecessary value provided when key-value pair is passed.'
                )
            if len(name) != 2:
                raise ValueError(
                    'Expecting a key-value pair (tuple with 2 elements).'
                )
            name, value = name
            self._diot_orderedkeys.insert(position, name)
            self[name] = value

        elif isinstance(name, dict):
            if value is not None:
                raise ValueError(
                    'Unnecessary value provided when '
                    'a ordered-dictionary passed.'
                )
            self._diot_orderedkeys[position:position] = list(name.keys())
            for key, val in name.items():
                self[key] = val

        else:
            self._diot_orderedkeys.insert(position, name)
            self[name] = value

    def insert_before(self, existing_key, name, value=None):
        """Insert items before the specified key"""
        try:
            position = self._diot_orderedkeys.index(existing_key)
        except ValueError as vex:
            raise KeyError("No such key: %s" % existing_key) from vex
        if name in self._diot_orderedkeys:
            raise KeyError("Key already exists: %s" % name)
        self.insert(position, name, value)

    def insert_after(self, existing_key, name, value=None):
        """Insert items after the specified key"""
        try:
            position = self._diot_orderedkeys.index(existing_key)
        except ValueError as vex:
            raise KeyError("No such key: %s" % existing_key) from vex
        if name in self._diot_orderedkeys:
            raise KeyError("Key already exists: %s" % name)
        self.insert(position + 1, name, value)

    def keys(self):
        return (key for key in self._diot_orderedkeys)

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return (self[key] for key in self._diot_orderedkeys)

    def __delitem__(self, name):
        super().__delitem__(name)
        name = self._diot_keymaps.get(name, name)
        del self._diot_orderedkeys[self._diot_orderedkeys.index(name)]

    __delattr__ = __delitem__

    def pop(self, name, *value):
        ret = super().pop(name, *value)
        name = self._diot_keymaps.get(name, name)
        del self._diot_orderedkeys[self._diot_orderedkeys.index(name)]
        return ret

    def __reversed__(self):
        return reversed(self._diot_orderedkeys)

    def clear(self):
        super().clear()
        del self._diot_orderedkeys[:]

    def copy(self):
        ret = super().copy()
        # pylint: disable=protected-access
        ret._diot_orderedkeys = self._diot_orderedkeys
        return ret
