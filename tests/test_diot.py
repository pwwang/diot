import pytest
from copy import deepcopy
from collections import OrderedDict
from diot import Diot, CamelDiot, SnakeDiot, _nest, OrderedDiot, NestDiot

@pytest.mark.parametrize('value, types, dest_type, expected, expectedtype', [
	({'a': 1}, [], dict, {'a': 1}, dict),
	({'a': 1}, [list], dict, {'a': 1}, dict),
	([{'a': 1}], [list], dict, [{'a': 1}], list),
	({'a': 1}, [dict], OrderedDict, {'a': 1}, OrderedDict),
])
def test_nest(value, types, dest_type, expected, expectedtype):
	out = _nest(value, types, dest_type)
	assert out == expected
	assert type(out) == expectedtype

def test_safe():

	diot = Diot(a__b = 1)
	assert diot.a__b == 1
	assert diot['a__b'] == 1

	diot.a_b = 2
	assert diot.a_b == 2
	diot['a_@_c'] = 3
	assert diot.a__c == 3

	diot2 = eval(repr(diot))
	assert diot2.a_b == 2
	assert diot2.a__c == 3
	assert diot2['a_@_c'] == 3

	with pytest.raises(KeyError):
		Diot({'a__b': 1, 'a_@_b': 2})

	with pytest.raises(KeyError):
		diot['a_@b'] = 1

	assert diot._diot_keymaps == {'a__b': 'a__b', 'a_b': 'a_b', 'a__c': 'a_@_c'}

	diot = Diot(a = {'b': {'c': 1}, 'd': ({'e':2}, {'f':3}), 'g': lambda:True}, diot_nest = True, diot_transform = 'safe')
	assert diot.a.b.c == 1
	assert diot.a.d[0].e == 2
	assert diot.a.d[1].f == 3
	assert diot.a.g()

	diot = Diot(a = Diot({'b': {'c': 1}, 'd': ({'e':2}, {'f':3}), 'g': lambda:True, 'h': Diot(a=1, b=2)}), diot_nest = Diot)
	assert diot.a.h.a == 1
	assert diot.a.h.b == 2
	assert diot.a.g()

	with pytest.raises(AttributeError):
		diot.a.b.c
	with pytest.raises(AttributeError):
		diot.a.d[0].e
	with pytest.raises(AttributeError):
		diot.a.d[1].f

	diot = Diot({'': 1})
	assert diot[''] == 1

	assert diot.pop('') == 1
	assert diot == {}

	diot.update({'': 1})
	assert diot[''] == 1

	diot = Diot({'__': 1})
	assert diot.__ == 1

def test_camel():

	diot = CamelDiot(a_b = 1)
	assert diot.aB == 1

def test_snake():
	diot = SnakeDiot(oneTwo = 1)
	assert diot.one_two == 1

def test_ordered():

	diot = OrderedDiot([('c', 1), ('b', 2), ('a', 3)])
	assert list(diot.keys()) == ['c', 'b', 'a']

	diot.insert(0, 'x', 9)
	assert list(diot.items()) == [('x', 9),('c', 1), ('b', 2), ('a', 3)]

	diot._ = 8
	assert list(diot.keys()) == ['x', 'c', 'b', 'a', '_']
	assert list(diot.values()) == [9, 1, 2, 3, 8]

	dt = OrderedDiot(OrderedDict([('b',1), ('a',2), ('c',3)]))
	assert list(dt.keys()) == ['b', 'a', 'c']


def test_upper_lower():
	dt = Diot(a=1, diot_transform = 'upper')
	assert dt.A == dt['a'] == dt['A'] == 1

	dt = Diot(A=1, diot_transform = 'lower')
	assert dt.a == dt['a'] == dt['A'] == 1

def test_nest_diot():
	dt = NestDiot(a = {'b': {'c': [{'d': 1}]}})
	assert isinstance(dt.a, NestDiot)
	assert isinstance(dt.a.b, NestDiot)
	assert isinstance(dt.a.b.c[0], NestDiot)
	assert dt.a.b.c[0].d == 1

def test_unicode_key():
	dt = Diot({u'a键值b': 1})
	assert dt.a_b == 1

def test_bytes_key():
	dt = Diot({b'a_@_b': 1})
	assert dt.a__b == 1

def test_to_dict():
	dt = NestDiot(a = {'b': {'c': [{'d': 1}], 'e': ({'f': 2},)}})
	assert isinstance(dt.a, NestDiot)
	assert isinstance(dt.a.b, NestDiot)
	assert isinstance(dt.a.b.c[0], NestDiot)
	assert isinstance(dt.a.b.e[0], NestDiot)
	assert dt.a.b.c[0].d == 1
	assert dt.a.b.e[0].f == 2

	d = dt.dict()
	assert not isinstance(d['a'], NestDiot)
	assert not isinstance(d['a']['b'], NestDiot)
	assert not isinstance(d['a']['b']['c'][0], NestDiot)
	assert not isinstance(d['a']['b']['e'][0], NestDiot)

	assert d == {'a': {'b': {'c': [{'d': 1}], 'e': ({'f': 2}, )}}}

def test_deepcopy():
	dt = NestDiot(a = {'b': {'c': [{'d': 1}], 'e': ({'f': 2},)}})
	dt2 = deepcopy(dt)
	assert dt == dt2
	assert dt is not dt2
	assert dt.a is not dt2.a
	assert dt.a.b is not dt2.a.b
	assert dt.a.b.c is not dt2.a.b.c
	assert dt.a.b.c[0] is not dt2.a.b.c[0]
	assert dt.a.b.e is not dt2.a.b.e
	assert dt.a.b.e[0] is not dt2.a.b.e[0]


def test_trydeepcopy():

	def tryDeepCopy(obj, _recurvise = True):
		"""
		Try do deepcopy an object. If fails, just do a shallow copy.
		@params:
			obj (any): The object
			_recurvise (bool): A flag to avoid deep recursion
		@returns:
			The copied object
		"""
		if _recurvise and isinstance(obj, dict):
			# do a shallow copy first
			# we don't start with an empty dictionary, because obj may be
			# an object from a class extended from dict
			ret = obj.copy()
			for key, value in obj.items():
				ret[key] = tryDeepCopy(value, False)
			return ret
		if _recurvise and isinstance(obj, list):
			ret = obj[:]
			for i, value in enumerate(obj):
				ret[i] = tryDeepCopy(value, False)
			return ret
		try:
			return deepcopy(obj)
		except TypeError:
			return obj

	dt = NestDiot(a = Diot(b = Diot(c=1)))
	dt3 = tryDeepCopy(dt)
	assert dt3 == dt
