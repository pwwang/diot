import pytest
from copy import deepcopy
from argparse import Namespace
from collections import OrderedDict
from diot import Diot, CamelDiot, SnakeDiot, OrderedDiot, DiotFrozenError
from diot.diot import FrozenDiot, nest


@pytest.mark.parametrize(
    "value, types, dest_type, expected, expectedtype",
    [
        ({"a": 1}, [], dict, {"a": 1}, 'dict'),
        ({"a": 1}, [list], dict, {"a": 1}, 'dict'),
        ([{"a": 1}], [list], dict, [{"a": 1}], 'list'),
        ({"a": 1}, [dict], OrderedDict, {"a": 1}, 'OrderedDict'),
    ],
)
def test_nest(value, types, dest_type, expected, expectedtype):
    out = nest(value, types, dest_type, True)
    assert out == expected
    assert type(out).__name__ == expectedtype


def test_safe():

    diot = Diot(a__b=1)
    assert diot.a__b == 1
    assert diot["a__b"] == 1

    diot.a_b = 2
    assert diot.a_b == 2
    diot["a_@_c"] = 3
    assert diot.a__c == 3
    diot2 = eval(repr(diot))
    assert diot2.a_b == 2
    assert diot2.a__c == 3
    assert diot2["a_@_c"] == 3

    with pytest.raises(KeyError):
        Diot({"a__b": 1, "a_@_b": 2})

    with pytest.raises(KeyError):
        diot["a_@b"] = 1

    assert diot.__diot__["keymaps"] == {
        "a__b": "a__b",
        "a_b": "a_b",
        "a__c": "a_@_c",
    }

    diot = Diot(
        a={"b": {"c": 1}, "d": ({"e": 2}, {"f": 3}), "g": lambda: True},
        diot_nest=True,
        diot_transform="safe",
    )
    assert diot.a.b.c == 1
    assert diot.a.d[0].e == 2
    assert diot.a.d[1].f == 3
    assert diot.a.g()

    diot = Diot(
        a=Diot(
            {
                "b": {"c": 1},
                "d": ({"e": 2}, {"f": 3}),
                "g": lambda: True,
                "h": Diot(a=1, b=2),
            }
        ),
        diot_nest=Diot,
    )
    assert diot.a.h.a == 1
    assert diot.a.h.b == 2
    assert diot.a.g()

    with pytest.raises(AttributeError):
        diot.a.b.c.x
    with pytest.raises(AttributeError):
        diot.a.d[0].e.x
    with pytest.raises(AttributeError):
        diot.a.d[1].f.x

    diot = Diot({"": 1})
    assert diot[""] == 1

    assert diot.pop("") == 1
    assert diot == {}

    diot.update({"": 1})
    assert diot[""] == 1

    diot = Diot({"__": 1})
    assert diot.__ == 1


def test_camel():

    diot = CamelDiot(a_b=1)
    assert diot.aB == 1


def test_snake():
    diot = SnakeDiot(oneTwo=1)
    assert diot.one_two == 1


def test_ordered():

    diot = OrderedDiot([("c", 1), ("b", 2), ("a", 3)])
    assert list(diot.keys()) == ["c", "b", "a"]

    diot.insert(0, "x", 9)
    assert list(diot.items()) == [("x", 9), ("c", 1), ("b", 2), ("a", 3)]

    diot._ = 8
    assert list(diot.keys()) == ["x", "c", "b", "a", "_"]
    assert list(diot.values()) == [9, 1, 2, 3, 8]

    dt = OrderedDiot(OrderedDict([("b", 1), ("a", 2), ("c", 3)]))
    assert list(dt.keys()) == ["b", "a", "c"]

    x = dt.pop("b")
    assert x == 1
    assert list(dt.keys()) == ["a", "c"]

    x = dt.pop("x", 10)
    assert x == 10
    assert list(dt.keys()) == ["a", "c"]


def test_upper_lower():
    dt = Diot(a=1, diot_transform="upper")
    assert dt.A == dt["a"] == dt["A"] == 1

    dt = Diot(A=1, diot_transform="lower")
    assert dt.a == dt["a"] == dt["A"] == 1


def test_nest_diot():
    dt = Diot(a={"b": {"c": [{"d": 1}]}})
    assert isinstance(dt.a, Diot)
    assert isinstance(dt.a.b, Diot)
    assert isinstance(dt.a.b.c[0], Diot)
    assert dt.a.b.c[0].d == 1


def test_unicode_key():
    dt = Diot({"a键值b": 1})
    assert dt.a_b == 1


def test_bytes_key():
    dt = Diot({b"a_@_b": 1})
    assert dt.a__b == 1


def test_to_dict():
    dt = Diot(a={"b": {"c": [{"d": 1}], "e": ({"f": 2},)}})
    assert isinstance(dt.a, Diot)
    assert isinstance(dt.a.b, Diot)
    assert isinstance(dt.a.b.c[0], Diot)
    assert isinstance(dt.a.b.e[0], Diot)
    assert dt.a.b.c[0].d == 1
    assert dt.a.b.e[0].f == 2

    d = dt.dict()
    assert not isinstance(d["a"], Diot)
    assert not isinstance(d["a"]["b"], Diot)
    assert not isinstance(d["a"]["b"]["c"][0], Diot)
    assert not isinstance(d["a"]["b"]["e"][0], Diot)

    assert d == {"a": {"b": {"c": [{"d": 1}], "e": ({"f": 2},)}}}


def test_deepcopy():
    dt = Diot(a={"b": {"c": [{"d": 1}], "e": ({"f": 2},)}})
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
    def tryDeepCopy(obj, _recurvise=True):
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

    dt = Diot(a=Diot(b=Diot(c=1)))
    dt3 = tryDeepCopy(dt)
    assert dt3 == dt


def test_ordereddiot_insert():

    od = OrderedDiot()
    od.insert(0, "c", "d")
    assert od == {"c": "d"}
    od.insert(0, ("a", "b"))
    assert od == {"a": "b", "c": "d"}
    assert list(od.keys()) == ["a", "c"]

    od.insert(None, "x", "y")
    assert list(od.keys()) == ["a", "c", "x"]
    assert od.x == "y"
    del od.x

    od.insert_before("a", "e", "f")
    assert list(od.keys()) == ["e", "a", "c"]
    assert od.e == "f"

    od.insert_after("a", ("g", "h"))
    assert list(od.keys()) == ["e", "a", "g", "c"]
    assert od.g == "h"

    od2 = OrderedDiot()
    od2.a1 = "b1"
    od2.c1 = "d1"
    od.insert(-1, od2)
    assert list(od.keys()) == ["e", "a", "g", "a1", "c1", "c"]
    assert od.a1 == "b1"
    assert od.c1 == "d1"

    od3 = OrderedDiot()
    od3.a2 = "b2"
    od3.c2 = "d2"
    od.insert_before("c", od3)
    assert list(od.keys()) == ["e", "a", "g", "a1", "c1", "a2", "c2", "c"]
    assert od.a2 == "b2"
    assert od.c2 == "d2"

    od4 = OrderedDiot()
    od4.a3 = "b3"
    od4.c3 = "d3"
    od.insert_after("a2", od4)
    assert list(od.keys()) == [
        "e",
        "a",
        "g",
        "a1",
        "c1",
        "a2",
        "a3",
        "c3",
        "c2",
        "c",
    ]
    assert od.a3 == "b3"
    assert od.c3 == "d3"

    with pytest.raises(KeyError):
        od.insert_before("Nosuchkey", "x", "y")

    with pytest.raises(KeyError):
        od.insert_after("Nosuchkey", "x", "y")

    with pytest.raises(KeyError):
        od.insert_before("c", "c", "y")  # key exists

    with pytest.raises(KeyError):
        od.insert_after("c", "c", "y")  # key exists

    with pytest.raises(ValueError):
        od.insert(0, od4, 1)

    with pytest.raises(ValueError):
        od.insert(0, ("m", 2), 1)

    with pytest.raises(ValueError):
        od.insert(0, ("m", 1, 2))

    with pytest.raises(ValueError):
        od.insert_before("a", od4, 1)

    with pytest.raises(ValueError):
        od.insert_before("a", ("m", 2), 1)

    with pytest.raises(ValueError):
        od.insert_after("a", od4, 1)

    with pytest.raises(ValueError):
        od.insert_after("a", ("m", 2), 1)


def test_od_iter():
    od = OrderedDiot([("b", 1), ("a", 2)])
    assert list(od) == ["b", "a"]

    it = iter(od)
    assert next(it) == "b"
    assert next(it) == "a"

    od.__diot__["orderedkeys"] = ["a", "b"]
    assert list(od) == ["a", "b"]

    it = iter(od)
    assert next(it) == "a"
    assert next(it) == "b"


def test_or_ior():
    a = Diot({"data": 2, "count": 5})
    b = Diot(data=2, count=5)  # noqa: F841

    c = a | {"data": 3}
    assert c == {"data": 3, "count": 5}

    c = a | [("data", 3)]
    assert c == {"data": 3, "count": 5}

    a |= {"data": 3}
    assert a == {"data": 3, "count": 5}

    with pytest.raises(TypeError):
        a | 1

    od = OrderedDiot([("b", 1), ("a", 2)])
    od |= {"a": 1, "b": 2}

    assert od.__diot__["orderedkeys"] == ["b", "a"]
    assert od.a == 1
    assert od.b == 2


def tform(key):
    return key * 2


def test_pickle():
    from pickle import loads, dumps

    a = Diot(a=1, diot_transform=tform)
    assert a.a == 1
    assert a.aa == 1
    pickled = dumps(a)
    b = loads(pickled)  # noqa: F841
    assert a.a == 1
    assert a.aa == 1


def test_from_namespace():
    ns = Namespace(a=1, b=2)
    d = Diot.from_namespace(ns)
    assert len(d) == 2
    assert d.a == 1
    assert d.b == 2
    # recursive
    ns.c = Namespace()
    d2 = Diot.from_namespace(ns, recursive=True)
    assert len(d2) == 3
    assert isinstance(d2.c, Diot)

    d3 = Diot.from_namespace(ns, recursive=False)
    assert isinstance(d3.c, Namespace)


def test_keywords():

    d = Diot(a=1, get=2)
    assert d.a == 1
    assert d["get"] == 2
    assert callable(d.get)


def test_od_copy():

    od = OrderedDiot()
    od.i = 0
    od2 = od.copy()
    assert od2.i == 0
    od2.j = 1

    od3 = od.copy()
    assert "j" not in od3


def test_frozen_modify():
    d = Diot(a=1, b=2, diot_frozen=True)
    with pytest.raises(DiotFrozenError):
        d.a = 2

    with pytest.raises(DiotFrozenError):
        d["a"] = 2

    with pytest.raises(DiotFrozenError):
        d.pop("a")

    with pytest.raises(DiotFrozenError):
        d.popitem()

    with pytest.raises(DiotFrozenError):
        d.update({})

    with pytest.raises(DiotFrozenError):
        d.update_recursively({})

    with pytest.raises(DiotFrozenError):
        d |= {}

    with pytest.raises(DiotFrozenError):
        del d["item"]

    with pytest.raises(DiotFrozenError):
        d.setdefault("c", 3)

    with pytest.raises(DiotFrozenError):
        d.clear()

    d2 = d.copy()
    with pytest.raises(DiotFrozenError):
        d2.clear()

    d2.unfreeze()
    d2.c = 3
    assert d2.c == 3

    d2.freeze()
    with pytest.raises(DiotFrozenError):
        d2.d = 4


def test_cameldiot_repr():
    d = CamelDiot(a_b=1)
    assert d.aB == 1
    assert repr(d) == "CamelDiot({'a_b': 1})"


def test_snakediot_repr():
    d = SnakeDiot(aB=1)
    assert d.a_b == 1
    assert repr(d) == "SnakeDiot({'aB': 1})"


def test_ordereddiot_repr():
    d = OrderedDiot(a_b=1)
    assert d.a_b == 1
    assert repr(d) == "OrderedDiot([('a_b', 1)])"


def test_unfreeze_recursive():
    d = Diot({"a": {"b": 1}})
    d.freeze(True)
    d.unfreeze()
    d.c = 2
    assert d.a == {"b": 1}
    assert d.c == 2

    with pytest.raises(DiotFrozenError):
        d.a.x = 1

    d.unfreeze(True)
    d.a.x = 1


def test_frozen_diot():
    d = FrozenDiot(a=1, b=2)
    with pytest.raises(DiotFrozenError):
        d.c = 3
    assert repr(d) == "FrozenDiot({'a': 1, 'b': 2})"

    with d.thaw():
        d.c = 3

    assert d.c == 3
    with pytest.raises(DiotFrozenError):
        d.c = 4


def test_missing_handler():
    d = Diot(a=1, b=2, diot_missing=None)
    assert d.c is None

    d = Diot(a=1, b=2, diot_missing=RuntimeError)
    with pytest.raises(RuntimeError):
        d["c"]

    d = Diot(a=1, b=2, diot_missing=RuntimeError("abc"))
    with pytest.raises(RuntimeError, match="abc"):
        d["c"]

    with pytest.raises(RuntimeError, match="abc"):
        d.c

    d = Diot(a=1, b=2, diot_missing=lambda key, diot: diot.a + diot.b)
    assert d.c == 3

    assert "c" not in d


def test_diot_construct_ignores_none():

    d = Diot(None)
    assert d == {}

    d = Diot(None, a=1)
    assert d == {"a": 1}
