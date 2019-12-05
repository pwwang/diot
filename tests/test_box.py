# grab some test from box
import pytest
from multiprocessing import Process, Queue
from diot import Diot, CamelDiot, SnakeDiot, OrderedDiot
test_dict = {'key1': 'value1',
			 'diot_nest': [dict, list],
             'not$allowed': 'fine_value',
             'BigCamel': 'hi',
             'alist': [{'a': 1}],
             "Key 2": {"Key 3": "Value 3",
                       "Key4": {"Key5": "Value5"}}}
extended_test_dict = {
    3: 'howdy',
    'not': 'true',
    '_box_config': True,
    'CamelCase': '21',
    '321CamelCase': 321,
    False: 'tree',
    'tuples_galore': ({'item': 3}, ({'item': 4}, 5))}
extended_test_dict.update(test_dict)

def test_box():
	bx = Diot(**test_dict)
	assert bx.key1 == test_dict['key1']
	assert dict(getattr(bx, 'Key 2')) == test_dict['Key 2']
	setattr(bx, 'TEST_KEY', 'VALUE')
	assert bx.TEST_KEY == 'VALUE'

	delattr(bx, 'TEST_KEY')
	assert 'TEST_KEY' not in bx
	assert isinstance(bx['Key 2'].Key4, Diot)
	assert "'key1': 'value1'" in str(bx)
	assert repr(bx).startswith("Diot([")

	bx3 = Diot(a=4)
	setattr(bx3, 'key', 2)
	assert bx3.key == 2
	bx3.__setattr__("Test", 3)
	assert bx3.Test == 3

def test_box_modify_at_depth():
	bx = Diot(**test_dict)
	assert 'key1' in bx
	assert 'key2' not in bx
	bx['Key 2'].new_thing = "test"
	assert bx['Key 2'].new_thing == "test"
	bx['Key 2'].new_thing += "2"
	assert bx['Key 2'].new_thing == "test2"
	assert bx['Key 2']['new_thing'] == "test2"
	bx.__setattr__('key1', 1)
	assert bx['key1'] == 1
	bx.__delattr__('key1')
	assert 'key1' not in bx

def test_error_box():
	bx = Diot(**test_dict)
	with pytest.raises(AttributeError):
		getattr(bx, 'hello')

def test_box_from_dict():
	ns = Diot({"k1": "v1", "k2": {"k3": "v2"}}, diot_nest = dict)
	assert ns.k2.k3 == "v2"

def test_box_from_bad_dict():
	with pytest.raises(ValueError):
		Diot('{"k1": "v1", "k2": {"k3": "v2"}}')

def test_basic_box():
	a = Diot(one=1, two=2, three=3)
	b = Diot({'one': 1, 'two': 2, 'three': 3})
	c = Diot((zip(['one', 'two', 'three'], [1, 2, 3])))
	d = Diot(([('two', 2), ('one', 1), ('three', 3)]))
	e = Diot(({'three': 3, 'one': 1, 'two': 2}))
	assert a == b == c == d == e

def test_bad_args():
	with pytest.raises(TypeError):
		Diot('123', '432')

def test_box_inits():
	a = Diot({'data': 2, 'count': 5})
	b = Diot(data=2, count=5)
	c = Diot({'data': 2, 'count': 1}, count=5)
	d = Diot([('data', 2), ('count', 5)])
	e = Diot({'a': [{'item': 3}, {'item': []}]}, diot_nest = [dict, list])
	assert e.a[1].item == []
	assert a == b == c == d

def test_create_subdicts():
	a = Diot({'data': 2, 'count': 5}, diot_nest = [dict, list])
	a.brand_new = {'subdata': 1}
	assert a.brand_new.subdata == 1
	a.new_list = [{'sub_list_item': 1}]
	assert a.new_list[0].sub_list_item == 1
	assert isinstance(a.new_list, list)
	a.new_list2 = [[{'sub_list_item': 2}]]
	assert a.new_list2[0][0].sub_list_item == 2

def test_update():
	a = Diot(**test_dict)
	a.grand = 1000
	a.update({'key1': {'new': 5}, 'Key 2': {"add_key": 6},
				'lister': ['a']})
	a.update([('asdf', 'fdsa')])
	a.update(testkey=66)
	a.update({'items': {'test': 'pme'}})
	a.update({'key1': {'gg': 4}})
	b = Diot(diot_nest = [list, dict])
	b.update(item=1)

	assert a.grand == 1000
	assert a['grand'] == 1000
	assert isinstance(a['items'], Diot)
	assert a['items'].test == 'pme'
	assert a['Key 2'].add_key == 6
	assert isinstance(a.key1, Diot)
	assert isinstance(a.lister, list)
	assert a.asdf == 'fdsa'
	assert a.testkey == 66
	assert a.key1.gg == 4

	c = Diot(diot_nest=[dict])
	c.a = [1, 2]
	c.update({'b': [3, 4]})

	assert c.a == [1, 2]
	assert isinstance(c.b, list)

def test_set_default():
	a = Diot(**test_dict)

	new = a.setdefault("key3", {'item': 2})
	new_list = a.setdefault("lister", [{'gah': 7}])
	assert a.setdefault("key1", False) == 'value1'

	assert new == Diot(item=2)
	assert new_list == [{'gah': 7}]
	assert a.key3.item == 2
	assert a.lister[0].gah == 7

	# without default_box we would get an error
	a = Diot()
	a.setdefault('b', [])
	a.b.append({})
	with pytest.raises(AttributeError):
		a.b[0].c.d = 1

	a = Diot()
	a.setdefault('b', {})
	with pytest.raises(AttributeError):
		a.b.c.d = 1

def test_conversion_box():
	bx = Diot(extended_test_dict, diot_nest = [dict, list])
	assert list(bx.accessible_keys()) == ['_3', '_not', '_box_config', 'CamelCase', '_321CamelCase', '_False', 'tuples_galore', 'key1', 'diot_nest', 'not_allowed', 'BigCamel', 'alist', 'Key_2']
	assert bx.Key_2.Key_3 == "Value 3"
	assert bx._3 == 'howdy'
	assert bx._not == 'true'
	with pytest.raises(AttributeError):
		getattr(bx, "(3, 4)")

def test_camel_killer_box():
	td = extended_test_dict.copy()
	td['CamelCase'] = 'Item'
	td['321CamelCaseFever!'] = 'Safe'

	kill_box = SnakeDiot(td)
	assert kill_box.camel_case == 'Item'
	assert kill_box['321CamelCaseFever!'] == 'Safe'

	con_kill_box = SnakeDiot(td)
	assert con_kill_box.camel_case == 'Item'
	assert con_kill_box._321_camel_case_fever_ == 'Safe'

def test_get():
	bx = Diot(diot_nest = [dict, list])
	bx["c"] = {}
	assert isinstance(bx.get("c"), Diot)
	assert isinstance(bx.get("b", {}), Diot)
	assert "a" in bx.get("a", Diot(a=1))
	assert isinstance(bx.get("a", [{"a":1}])[0], Diot)

def test_is_in():
	bx = Diot()
	dbx = Diot()
	assert "a" not in bx
	assert "a" not in dbx
	bx["b"] = 1
	dbx["b"] = {}
	assert "b" in bx
	assert "b" in dbx
	bx["a_@_b"] = 1
	assert "a__b" in bx
	assert "a_@_b" in bx
	delattr(bx, "a_@_b")

# def mp_queue_test(q):
#     bx = q.get(timeout=1)
#     try:
#         assert isinstance(bx, Diot)
#         assert bx.a == 4
#     except AssertionError:
#         q.put(False)
#     else:
#         q.put(True)

# def test_through_queue():
# 	my_box = Diot(a=4, c={"d": 3})

# 	queue = Queue()
# 	queue.put(my_box)

# 	p = Process(target=mp_queue_test, args=(queue,))
# 	p.start()
# 	p.join()

# 	assert queue.get(timeout=1)

def test_update_with_integer():
	bx = Diot()
	bx[1] = 4
	assert bx[1] == 4
	bx.update({1: 2})
	assert bx[1] == 2

def test_ordered_box():
	bx = OrderedDiot(h=1)
	bx.a = 1
	bx.c = 4
	bx['g'] = 7
	bx.d = 2
	assert list(bx.keys()) == ['h', 'a', 'c', 'g', 'd']
	del bx.a
	bx.pop('c')
	bx.__delattr__('g')
	assert list(bx.keys()) == ['h', 'd']

def test_pop():
	bx = Diot(a=4, c={"d": 3}, b={"h": {"y": 2}}, diot_nest = [dict, list])
	assert bx.pop('a') == 4
	assert bx.pop('b').h.y == 2
	with pytest.raises(KeyError):
		bx.pop('b')
	assert bx.pop('a', None) is None
	assert bx.pop('a', True) is True
	assert bx == {'c': {"d": 3}}
	assert bx.pop('c', True) is not True

def test_pop_items():
	bx = Diot(a=4)
	assert bx.popitem() == ('a', 4)
	with pytest.raises(KeyError):
		assert bx.popitem()

	bx = Diot({'a_@_b':1})
	assert bx.popitem() == ('a_@_b', 1)


def test_iter():
	bx = OrderedDiot()
	bx.a = 1
	bx.c = 2
	assert list(bx.__iter__()) == ['a', 'c']

def test_revesed():
	bx = OrderedDiot()
	bx.a = 1
	bx.c = 2
	assert list(reversed(bx)) == ['c', 'a']

def test_clear():
	bx = OrderedDiot()
	bx.a = 1
	bx.c = 4
	bx['g'] = 7
	bx.d = 2
	assert list(bx.keys()) == ['a', 'c', 'g', 'd']
	bx.clear()
	assert bx == {}
	assert list(bx.keys()) == []
	assert bx._diot_orderedkeys == []

def test_bad_recursive():
	b = Diot()
	bl = b.setdefault("l", [])
	bl.append(["foo"])
	assert bl == [['foo']], bl


def test_inheritance_copy():

	class Box2(Diot):
		pass

	b = Box2(a=1)
	c = b.copy()
	assert c == b
	assert isinstance(c, Diot)
	c = b.__copy__()
	assert c == b
	assert isinstance(c, Diot)

	d = OrderedDiot()
	d.b = 1
	d.a = 0
	d.x = 9
	assert list(d.copy().keys()) == ['b', 'a', 'x']

def test_readme():
	movie_data = {
	"movies": {
		"Spaceballs": {
		"imdb stars": 7.1,
		"rating": "PG",
		"length": 96,
		"director": "Mel Brooks",
		"stars": [{"name": "Mel Brooks", "imdb": "nm0000316", "role": "President Skroob"},
					{"name": "John Candy","imdb": "nm0001006", "role": "Barf"},
					{"name": "Rick Moranis", "imdb": "nm0001548", "role": "Dark Helmet"}
		]
		},
		"Robin Hood: Men in Tights": {
		"imdb stars": 6.7,
		"rating": "PG-13",
		"length": 104,
		"director": "Mel Brooks",
		"stars": [
					{"name": "Cary Elwes", "imdb": "nm0000144", "role": "Robin Hood"},
					{"name": "Richard Lewis", "imdb": "nm0507659", "role": "Prince John"},
					{"name": "Roger Rees", "imdb": "nm0715953", "role": "Sheriff of Rottingham"},
					{"name": "Amy Yasbeck", "imdb": "nm0001865", "role": "Marian"}
		]
		}
	}
	}

	# Box is a conversion_box by default, pass in `conversion_box=False` to disable that behavior
	movie_box = Diot(movie_data, diot_nest = [dict, list])

	assert movie_box.movies.Robin_Hood_Men_in_Tights.imdb_stars == 6.7
	# 6.7

	assert movie_box.movies.Spaceballs.stars[0].name == 'Mel Brooks'
	# 'Mel Brooks'
