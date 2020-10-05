"""diot module"""
from os import PathLike
from typing import (
    Any, Callable, Dict, Iterable, Iterator, Optional, Tuple, Union
)
from copy import deepcopy
from argparse import Namespace
from .transforms import TRANSFORMS

class DiotFrozenError(Exception):
    """When try to modify a frozen diot"""

def _nest(value: Any,
          types: Union[type],
          dest_type: type,
          frozen: bool) -> Any:
    """Convert values with certain types recursively"""
    # nothing to convert
    if not types or not isinstance(value, tuple(types)):
        return value

    if ((list in types and isinstance(value, list)) or
            (tuple in types and isinstance(value, tuple))):
        # use value.__class__ to keep user-subclassed list or tuple
        return value.__class__([
            _nest(val, types, dest_type, frozen) for val in value
        ])

    if dict in types and isinstance(value, dict):
        return dest_type([(key, _nest(val, types, dest_type, frozen))
                          for key, val in value.items()])
    return value

def _dict(value: "Diot") -> dict:
    """Convert converted Diot objects back to dict"""
    if isinstance(value, dict):
        return {key: _dict(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return tuple((_dict(val) for val in value))
    if isinstance(value, list):
        return [_dict(val) for val in value]
    return value

class Diot(dict):
    """Dictionary with dot notation

    Examples:
    >>> d = Diot(a=1, b=2)
    >>> d.a = 2
    >>> d['a'] = 2
    >>> d.a        # 2
    >>> d['a']     # 2
    >>> d.pop('a') # 2
    >>> d.pop('x', 1) # 1
    >>> d.popitem()   # ('b', 2)
    >>> d.update(a=3, b=4)    # {'a': 3, 'b': 4}
    >>> d | {'a': 1, 'b': 2}  # {'a': 1, 'b': 2} (d unchanged)
    >>> d |= {'a': 1, 'b': 2} # d == {'a': 1, 'b': 2}
    >>> del d.a
    >>> del d['b']
    >>> d.freeze()
    >>> d.a = 1  # DiotFrozenError
    >>> d.unfreeze()
    >>> d.a = 1  # ok
    >>> d.setdefault('b', 2)
    >>> 'b' in d
    >>> d.copy()
    >>> d.deepcopy()

    Args:
        *args: Anything that can be sent to dict construct
        **kwargs: keyword argument that can be sent to dict construct
            Some diot configurations can also be passed, including:
            diot_nest: Types to nestly convert values
            diot_transform: The transforms for keys
            diot_frozen: Whether to generate a frozen diot.
                True: freeze the object recursively if there are Diot objects
                in descendants
                False: Don'f freeze
                'shallow': Only freeze at depth = 1

    """
    __slots__ = ('__diot__', '__dict__')

    def __new__(cls, *args, **kwargs):
        ret = super().__new__(cls)
        # unpickling will not call __init__
        # we use a flag '__inited__' to tell if __init__ has been called
        # is there a better way?
        ret.__init__(*args, **kwargs)
        return ret

    @classmethod
    def from_namespace(
            cls,
            namespace: Namespace,
            recursive: bool = True,
            diot_nest: Union[bool, Iterable[type]] = True,
            diot_transform: Union[Callable[[str], str], str] = 'safe',
            diot_frozen: Union[bool, str] = False
    ) -> "Diot":
        """Get a Diot object from an argparse namespace

        Example:
        >>> from argparse import Namespace
        >>> Diot.from_namespace(Namespace(a=1, b=2))

        Args:
            namespace: The namespace object
            recursive: Do it recursively?
            diot_nest: Types to nestly convert values
            diot_transform: The transforms for keys
            diot_frozen: Whether to generate a frozen diot.
                True: freeze the object recursively if there are Diot objects
                in descendants
                False: Don'f freeze
                'shallow': Only freeze at depth = 1
        Returns:
            The converted diot object.
        """
        ret = cls({key: val
                   for key, val in vars(namespace).items()
                   if not key.startswith('__')},
                  diot_nest=diot_nest,
                  diot_transform=diot_transform,
                  diot_frozen=diot_frozen)
        if not recursive:
            return ret

        for key, value in ret.items():
            if isinstance(value, Namespace):
                ret[key] = cls.from_namespace(value)
        return ret

    def __init__(self, *args, **kwargs):
        if self.__dict__.get('__inited__'):
            return

        self.__dict__['__inited__'] = True
        self.__dict__.setdefault('__diot__', {})
        self.__diot__['keymaps'] = {}
        self.__diot__['nest'] = kwargs.pop('diot_nest', True)
        self.__diot__['nest'] = (
            [dict, list, tuple] if self.__diot__['nest'] is True
            else [] if self.__diot__['nest'] is False
            else list(self.__diot__['nest'])
            if isinstance(self.__diot__['nest'], tuple)
            else self.__diot__['nest']
            if isinstance(self.__diot__['nest'], list)
            else [self.__diot__['nest']]
        )
        self.__diot__['transform'] = kwargs.pop('diot_transform', 'safe')
        self.__diot__['frozen'] = False
        diot_frozen = kwargs.pop('diot_frozen', False)
        if isinstance(self.__diot__['transform'], str):
            self.__diot__['transform'] = TRANSFORMS[self.__diot__['transform']]

        super().__init__(*args, **kwargs)

        for key in self:
            transformed_key = self.__diot__['transform'](key)
            if transformed_key in self.__diot__['keymaps']:
                raise KeyError(
                    f"Keys {self.__diot__['keymaps'][transformed_key]!r} and "
                    f"{key!r} will be transformed to the same attribute. "
                    "Either change one of them or use a different "
                    "diot_transform function."
                )
            self.__diot__['keymaps'][transformed_key] = key

        # nest values
        for key in self:
            self[key] = _nest(self[key],
                              self.__diot__['nest'],
                              self.__class__,
                              self.__diot__['frozen'] is True)

        self.__diot__['frozen'] = diot_frozen

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot set attribute to a frozen diot.')
        self[name] = _nest(value,
                           self.__diot__['nest'],
                           self.__class__,
                           self.__diot__['frozen'])

    def __setitem__(self, name: str, value: Any) -> None:
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot set item to a frozen diot.')
        transformed_key = self.__diot__['transform'](name)
        if (transformed_key in self.__diot__['keymaps'] and
                transformed_key != name and
                self.__diot__['keymaps'][transformed_key] != name):
            raise KeyError(
                f"{name!r} will be transformed to the same attribute as "
                f"{self.__diot__['keymaps'][transformed_key]!r}. "
                "Either use a different name or "
                "a different diot_transform function."
            )
        self.__diot__['keymaps'][transformed_key] = name
        super().__setitem__(name, _nest(value,
                                        self.__diot__['nest'],
                                        self.__class__,
                                        self.__diot__['frozen'] is True))

    def __getattr__(self, name: str) -> Any:
        if name == '__diot__':
            return self.__dict__['__diot__']
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name: str) -> Any:
        original_key = self.__diot__['keymaps'].get(name, name)
        return super().__getitem__(original_key)

    def pop(self, name: str, *value) -> Any:
        """Pop a key from the object and return the value. If key does not
        exist, return the given default value

        Args:
            name: The key
            value: The default value to return if the key does not exist

        Returns:
            The value corresponding to the name or the default value

        Raises:
            DiotFrozenError: when try to pop from a frozen diot
        """
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot pop a frozen diot.')
        if name in self.__diot__['keymaps']:
            name = self.__diot__['keymaps'][name]
            del self.__diot__['keymaps'][name]
        if value:
            return super().pop(name, value[0])
        return super().pop(name)

    def popitem(self) -> Tuple[str, Any]:
        """Pop last item from the object

        Returns:
            A tuple of key and value

        Raises:
            DiotFrozenError: when try to pop from a frozen diot
        """
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot popitem of a frozen diot.')
        key, val = super().popitem()
        if key in self.__diot__['keymaps']:
            del self.__diot__['keymaps'][key]
        else:
            del self.__diot__['keymaps'][self.__diot__['transform'](key)]
        return key, val

    def update(self, *value, **kwargs) -> None:
        """Update the object. Shortcut: `|=`

        Args:
            args: args that can be sent to dict to update the object
            kwargs: kwargs that can be sent to dict to update the object

        Raises:
            DiotFrozenError: when try to update a frozen diot
        """
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot update a frozen diot.')
        dict_to_update = dict(*value, **kwargs)
        for key, val in dict_to_update.items():
            if (key not in self or
                    not isinstance(self[key], dict) or
                    not isinstance(val, dict)):
                self[key] = _nest(val,
                                  self.__diot__['nest'],
                                  self.__class__,
                                  self.__diot__['frozen'] is True)
            else:
                self[key].update(val)

    def __or__(self, other: Dict[str, Any]) -> "Diot":
        ret = self.copy()
        ret.update(other)
        return ret

    def __ior__(self, other: Dict[str, Any]) -> "Diot":
        self.update(other)
        return self

    def __delitem__(self, name: str) -> None:
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot delete from a frozen diot.')
        if name in self.__diot__['keymaps']:
            super().__delitem__(self.__diot__['keymaps'][name])
            del self.__diot__['keymaps'][name]
        else:
            super().__delitem__(name)
            del self.__diot__['keymaps'][self.__diot__['transform'](name)]

    __delattr__ = __delitem__

    def _repr(self, hide=None, items='dict'):
        """Compose the repr for the object. If the config item is default, hide
        it. If argument hide is specified, hide that item anyway"""
        diot_class = self.__class__.__name__
        diot_transform = self.__diot__['transform']
        for key, val in TRANSFORMS.items():
            if val is diot_transform:
                diot_transform = key
                break
        diot_transform = (None
                          if diot_transform == 'safe' or hide == 'transform'
                          else diot_transform)
        diot_transform = ('' if diot_transform is None else
                          f', diot_transform={diot_transform}')
        diot_nest = ','.join(sorted(dn.__name__
                                    for dn in self.__diot__['nest']))
        diot_nest = (None if diot_nest == 'dict,list,tuple' or hide == 'next'
                     else diot_nest)
        diot_nest = '' if diot_nest is None else f', diot_nest={diot_nest}'
        diot_frozen = (None
                       if self.__diot__['frozen'] is False or hide == 'frozen'
                       else self.__diot__['frozen'])
        diot_frozen = ('' if diot_frozen is None
                       else f', diot_frozen={diot_frozen}')
        diot_items = self if items == 'dict' else list(self.items())
        return (f'{diot_class}({diot_items}'
                f'{diot_transform}{diot_nest}{diot_frozen})')

    def __repr__(self) -> str:
        return self._repr()

    def __str__(self) -> str:
        return repr(dict(self))

    def freeze(self, frozen: Union[str, bool] = 'shallow') -> None:
        """Freeze the diot object

        Args:
            frozen: The frozen argument indicating how to freeze:
                shallow: only freeze at depth=1
                True: freeze recursively if there are diot objects in children
                False: Disable freezing
        """
        self.__diot__['frozen'] = frozen
        if frozen is True:
            for val in self.values():
                if isinstance(val, Diot):
                    val.freeze(True)

    def unfreeze(self, recursive: bool = False) -> None:
        """Unfreeze the diot object

        Args:
            recursive: Whether unfreeze all diot objects recursively
        """
        self.__diot__['frozen'] = False
        if recursive:
            for val in self.values():
                if isinstance(val, Diot):
                    val.unfreeze(True)

    def setdefault(self, name: str, value: Any) -> Any:
        """Set a default value to a key

        Args:
            name: The key name
            value: The default value

        Returns:
            The existing value or the value passed in

        Raises:
            DiotFrozenError: when try to set default to a frozen diot
        """
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot setdefault to a frozen diot.')
        if name in self:
            return self[name]
        self[name] = value
        return self[name]

    def accessible_keys(self) -> Iterable[str]:
        """Get the converted keys

        Returns:
            The accessible (transformed) keys
        """
        return self.__diot__['keymaps'].keys()

    def get(self, name: str, value: Any = None) -> Any:
        """Get the value of a key name

        Args:
            name: The key name
            value: The value to return if the key does not exist

        Returns:
            The corresponding value or the value passed in if the key does
            not exist
        """
        name = self.__diot__['keymaps'].get(name, name)
        return super().get(name, _nest(value,
                                       self.__diot__['nest'],
                                       self.__class__,
                                       self.__diot__['frozen'] is True))

    def __contains__(self, name: str) -> bool:
        if name in self.__diot__['keymaps']:
            return True
        return super().__contains__(name)

    def clear(self) -> None:
        """Clear the object"""
        if self.__diot__['frozen']:
            raise DiotFrozenError('Cannot clear a frozen diot.')
        super().clear()
        self.__diot__['keymaps'].clear()

    def copy(self) -> "Diot":
        """Shallow copy the object

        Returns:
            The copied object
        """
        return self.__class__(list(self.items()),
                              diot_nest=self.__diot__['nest'],
                              diot_transform=self.__diot__['transform'],
                              diot_frozen=self.__diot__['frozen'])

    __copy__ = copy

    def __deepcopy__(self, memo: Optional[Dict[int, Any]] = None) -> "Diot":
        out = self.__class__(diot_nest=self.__diot__['nest'],
                             diot_transform=self.__diot__['transform'],
                             diot_frozen=self.__diot__['frozen'])
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
                {'diot_transform': self.__diot__['transform'],
                 'diot_nest': self.__diot__['nest'],
                 'diot_frozen': self.__diot__['frozen']})

    def to_dict(self) -> Dict[str, Any]:
        """
        Turn the Box and sub Boxes back into a native
        python dictionary.

        Returns:
            The converted python dictionary
        """
        return _dict(self)

    dict = as_dict = to_dict

    def to_json(self,
                filename: Optional[Union[str, PathLike]] = None,
                encoding: str = "utf-8",
                errors: str = "strict",
                **json_kwargs) -> Optional[str]:
        """Convert to a json string or save it to json file

        Args:
            filename: The filename to save the json to, if not given a json
                string will be returned
            encoding: The encoding for saving to file
            errors: The errors handling for saveing to file
                See python's open function
            **json_kwargs: Other kwargs for json.dumps

        Returns:
            The json string with filename is not given
        """
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
                filename: Optional[Union[str, PathLike]] = None,
                default_flow_style: bool = False,
                encoding: str = "utf-8",
                errors: str = "strict",
                **yaml_kwargs) -> Optional[str]:
        """Convert to a yaml string or save it to yaml file

        Args:
            filename: The filename to save the yaml to, if not given a yaml
                string will be returned
            default_flow_style: The default flow style for yaml dumping
                See `yaml.dump`
            encoding: The encoding for saving to file
            errors: The errors handling for saveing to file
                See python's open function
            **yaml_kwargs: Other kwargs for `yaml.dump`

        Returns:
            The yaml string with filename is not given
        """
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

    def to_toml(self,
                filename: Optional[Union[str, PathLike]] = None,
                encoding: str = "utf-8",
                errors: str = "strict") -> Optional[str]:
        """Convert to a toml string or save it to toml file

        Args:
            filename: The filename to save the toml to, if not given a toml
                string will be returned
            encoding: The encoding for saving to file
            errors: The errors handling for saveing to file
                See python's open function

        Returns:
            The toml string with filename is not given
        """
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
        kwargs['diot_transform'] = TRANSFORMS['camel_case']
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return self._repr(hide='transform')

class SnakeDiot(Diot):
    """With snake case conversion"""
    def __init__(self, *args, **kwargs):
        kwargs['diot_transform'] = TRANSFORMS['snake_case']
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return self._repr(hide='transform')

class FrozenDiot(Diot):
    """The frozen diot"""
    def __init__(self, *args, **kwargs):
        kwargs['diot_frozen'] = True
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return self._repr(hide='frozen')

class OrderedDiot(Diot):
    """With key order preserved"""
    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('__diot__', {})
        self.__diot__['orderedkeys'] = [
            key[0] if isinstance(key, tuple) else key
            for arg in args for key in arg
        ] + [
            key for key in kwargs if not key.startswith('diot_')
        ]
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return self._repr(items='items')

    def __setitem__(self, name: str, value: Any) -> None:
        super().__setitem__(name, value)
        if name not in self.__diot__['orderedkeys']:
            self.__diot__['orderedkeys'].append(name)

    def items(self) -> Iterator[Tuple[str, Any]]:
        """Get the items in the order of the keys

        Returns:
            The items (key-value) of the object
        """
        return ((key, self[key]) for key in self.__diot__['orderedkeys'])

    def insert(self,
               position: int,
               name: Union[str, Tuple[str, Any]],
               value: Any = None) -> None:
        """Insert an item to certain position

        Args:
            position: The position where the name-value pair to be inserted
            name: The key name to be inserted
                It could also be a tuple of key-value pair. In such a case,
                value is ignored.
                It could be an ordered dictionary as well
            value: The value to be inserted

        Raises:
            ValueError: when try to pass a value if name is key-value pair or
                a dictonary.
            ValueError: when name is a tuple but not with 2 elements
        """
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
            self.__diot__['orderedkeys'].insert(position, name)
            self[name] = value

        elif isinstance(name, dict):
            if value is not None:
                raise ValueError(
                    'Unnecessary value provided when '
                    'a ordered-dictionary passed.'
                )
            self.__diot__['orderedkeys'][position:position] = list(name.keys())
            for key, val in name.items():
                self[key] = val

        else:
            self.__diot__['orderedkeys'].insert(position, name)
            self[name] = value

    def insert_before(self,
                      existing_key: str,
                      name: str,
                      value: Any = None) -> None:
        """Insert items before the specified key

        Args:
            existing_key: The key where the new elements to be inserted before
            name: The key name to be inserted
            value: The value to be inserted
                Same as name and value arguments for `insert`

        Raises:
            KeyError: when existing key does not exist
            KeyError: when name is an existing key
        """
        try:
            position = self.__diot__['orderedkeys'].index(existing_key)
        except ValueError as vex:
            raise KeyError("No such key: %s" % existing_key) from vex
        if name in self.__diot__['orderedkeys']:
            raise KeyError("Key already exists: %s" % name)
        self.insert(position, name, value)

    def insert_after(self,
                     existing_key: str,
                     name: str,
                     value: Any = None) -> None:
        """Insert items after the specified key

        Args:
            existing_key: The key where the new elements to be inserted after
            name: The key name to be inserted
            value: The value to be inserted
                Same as name and value arguments for `insert`

        Raises:
            KeyError: when existing key does not exist
            KeyError: when name is an existing key
        """
        try:
            position = self.__diot__['orderedkeys'].index(existing_key)
        except ValueError as vex:
            raise KeyError("No such key: %s" % existing_key) from vex
        if name in self.__diot__['orderedkeys']:
            raise KeyError("Key already exists: %s" % name)
        self.insert(position + 1, name, value)

    def keys(self) -> Iterable[str]:
        """Get the keys in the order they are added

        Returns:
            The keys (untransformed)
        """
        return (key for key in self.__diot__['orderedkeys'])

    def __iter__(self) -> Iterable[str]:
        return iter(self.keys())

    def values(self) -> Iterable[Any]:
        """Get the values in the order they are added

        Returns:
            The values of the object
        """
        return (self[key] for key in self.__diot__['orderedkeys'])

    def __delitem__(self, name: str) -> None:
        super().__delitem__(name)
        name = self.__diot__['keymaps'].get(name, name)
        del self.__diot__['orderedkeys'][
            self.__diot__['orderedkeys'].index(name)
        ]

    __delattr__ = __delitem__

    def pop(self, name: str, *value) -> Any:
        ret = super().pop(name, *value)
        name = self.__diot__['keymaps'].get(name, name)
        del self.__diot__['orderedkeys'][
            self.__diot__['orderedkeys'].index(name)
        ]
        return ret

    def __reversed__(self) -> Iterable[str]:
        return reversed(self.__diot__['orderedkeys'])

    def clear(self) -> None:
        super().clear()
        del self.__diot__['orderedkeys'][:]

    def copy(self) -> "OrderedDiot":
        ret = super().copy()
        self.__diot__['orderedkeys'] = self.__diot__['orderedkeys'][:]
        return ret
