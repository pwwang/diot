"""
Python dictionary with dot notation
"""
import re
import keyword
import inflection

def safe_transform(item):
	"""
	Transform an arbitrary key into a safe key for dot notation
	"""
	item = re.sub(r'[^\w_]+', '.', item)
	item = re.sub(r'_?\.+|\.+_?', '_', item)
	if not item:
		return ''
	return '_' + item if item[0] in '0123456789' or item in keyword.kwlist else item

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
	safe           = safe_transform,
	safe_transform = safe_transform,
	camel_case     = camel_case,
	camelCase      = camel_case,
	snake_case     = snake_case,
	upper          = upper_case,
	lower          = lower_case,
	upper_case     = upper_case,
	lower_case     = lower_case,
	uppercase      = upper_case,
	lowercase      = lower_case,
	UPPERCASE      = upper_case,
	UPPER_CASE     = upper_case,
)

__all__ = ['Diot', 'CamelDiot', 'SnakeDiot', 'OrderedDiot']

def _nest(value, types, dest_type):
	"""Convert values with certain types recursively"""
	if not types:
		return value
	if not isinstance(value, tuple(types)):
		return value
	if list in types and isinstance(value, list):
		return [_nest(val, types, dest_type) for val in value]
	if tuple in types and isinstance(value, tuple):
		return tuple((_nest(val, types, dest_type) for val in value))
	if dict in types and isinstance(value, dict):
		return dest_type([(key, _nest(val, types, dest_type)) for key, val in value.items()])
	return value

class Diot(dict):
	"""Dictionary with dot notation"""
	def __init__(self, *args, **kwargs):
		self._diot_keymaps   = {}
		self._diot_nest      = kwargs.pop('diot_nest') if 'diot_nest' in kwargs else False
		self._diot_nest      = [dict, list, tuple] if self._diot_nest is True \
			else [] if self._diot_nest is False \
			else list(self._diot_nest) if isinstance(self._diot_nest, tuple) \
			else self._diot_nest if isinstance(self._diot_nest, list) \
			else [self._diot_nest]
		self._diot_transform = kwargs.pop('diot_transform') if 'diot_transform' in kwargs \
			else safe_transform
		if isinstance(self._diot_transform, str):
			self._diot_transform = TRANSFORMS[self._diot_transform]

		super().__init__(*args, **kwargs)
		for key in self:
			transformed_key = self._diot_transform(str(key))
			if transformed_key in self._diot_keymaps:
				raise KeyError(f"Keys {self._diot_keymaps[transformed_key]!r} and {key!r} "
					"will be transformed to the same attribute. Either change one of them "
					"or use a different diot_transform function.")
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
		transformed_key = self._diot_transform(str(name))
		if transformed_key in self._diot_keymaps \
			and transformed_key != name and self._diot_keymaps[transformed_key] != name:
			raise KeyError(f"{name!r} will be transformed to the same attribute as "
				f"{self._diot_keymaps[transformed_key]!r}. Either use a different name "
				"or a different diot_transform function.")
		self._diot_keymaps[transformed_key] = name
		super().__setitem__(name, _nest(value, self._diot_nest, self.__class__))

	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			raise AttributeError(name) from None

	def __getitem__(self, name):
		original_key = self._diot_keymaps.get(name, name)
		return super().__getitem__(original_key)

	def pop(self, name, *value):
		name = self._diot_keymaps.get(name, name)
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
		for val in value:
			super().update(_nest(val, self._diot_nest, self.__class__))
		super().update(_nest(kwargs, self._diot_nest, self.__class__))

	def __delitem__(self, name):
		if name in self._diot_keymaps:
			super().__delitem__(self._diot_keymaps[name])
			del self._diot_keymaps[name]
		else:
			super().__delitem__(name)
			del self._diot_keymaps[self._diot_transform(name)]

	__delattr__ = __delitem__

	def __repr__(self):
		idot_transform = self._diot_transform
		for key, val in TRANSFORMS.items():
			if val == idot_transform:
				idot_transform = key
				break
		return '{}({}, diot_nest = {}, diot_transform = {!r})'.format(
			self.__class__.__name__, list(self.items()),
			[dn.__name__ for dn in self._diot_nest], idot_transform)

	def __str__(self):
		return repr(dict(self))

	def setdefault(self, name, value):
		name = self._diot_keymaps.get(name, name)
		return super().setdefault(name, _nest(value, self._diot_nest, self.__class__))

	def accessible_keys(self):
		"""Get the converted keys"""
		return self._diot_keymaps.keys()

	def get(self, name, value = None):
		name = self._diot_keymaps.get(name, name)
		return super().get(name, _nest(value, self._diot_nest, self.__class__))

	def __contains__(self, name):
		if name in self._diot_keymaps:
			return True
		return super().__contains__(name)

	def clear(self):
		super().clear()
		self._diot_keymaps.clear()

	def copy(self):
		return self.__class__(
			self.items(), diot_nest = self._diot_nest, diot_transform = self._diot_transform)

	__copy__ = copy

class NestDiot(Diot):
	"""With recursive dict/list/tuple conversion"""
	def __init__(self, *args, **kwargs):
		kwargs['diot_nest'] = [list, dict, tuple]
		super().__init__(*args, **kwargs)

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
		self._diot_orderedkeys = [key[0] if isinstance(key, tuple) else key
			for arg in args for key in arg] + [key for key in kwargs if not key.startswith('diot_')]
		super().__init__(*args, **kwargs)

	def __setitem__(self, name, value):
		super().__setitem__(name, value)
		if name not in self._diot_orderedkeys:
			self._diot_orderedkeys.append(name)

	def items(self):
		return ((key, self[key]) for key in self._diot_orderedkeys)

	def insert(self, position, name, value):
		"""Insert an item to certain position"""
		self._diot_orderedkeys.insert(position, name)
		self[name] = value

	def keys(self):
		return (key for key in self._diot_orderedkeys)

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
		ret._diot_orderedkeys = self._diot_orderedkeys[:]
		return ret
