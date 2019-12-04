## Accessing the values

You actually don't need to use the return values from `params._parse()`. You can access the values via `params` itself.

```python
from pyparam import params
params.a = 1
params._parse()

# -a 2
assert params.a.value == 2
```

## Casting the values
If the value is a `str`, you can try to cast into different types using:
```python
# assume
# params.a.value == '1'

assert params.a.int() == 1
assert params.a.float() == 1.0
assert params.a.bool() == True
assert params.a.str() == '1'
```

## Str methods
You may also use some methods of `str` directly:
```python
# assume
# params.a.value == 'abcdefg'

assert params.a + 'hij' == 'abcdefghij'
assert 'abc' in params.a
assert params.a.capitalize() == 'Abcdefg'
assert params.a.count('a') == 1
assert params.a.islower() == True
assert params.a.find('b') == 1
assert params.a.upper()  == 'ABCDEFG'
... ...
```

## Using a different wrapper for parsed values
```python
# python-box
from box import Box
from pyparam import params
params.a = {}

ret = params._parse(['-a.b.c.d', '1'], dict_wrapper = Box)
assert ret.a.b.c.d == 1
```

## Using multiple params instances
You may want multiple `params` to store parameters from different sources, or for different uses.
```python
from pyparam import Params

params1 = Params()
params1._loadFile('config1')
params2 = Params()
params2._loadFile('config2')
```
