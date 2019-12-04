## Basic usage

`examples/basic.py`
```python
from pyparam import params
# define arguments
params.version      = False
params.version.desc = 'Show the version and exit.'
params.quiet        = False
params.quiet.desc   = 'Silence warnings'
params.v            = 0
# verbose option
params.v.type = 'verbose'
# alias
params.verbose = params.v
# list/array options
params.packages      = []
params.packages.desc = 'The packages to install.'
params.depends       = {}
params.depends.desc  = 'The dependencies'

print(params._parse())
```
```python
> python example/basic.py
```
![help][9]

```python
> python examples/basic.py -vv --quiet \
	--packages numpy pandas pyparam \
	--depends.completions 0.0.1
{'h': False, 'help': False, 'H': False,
 'v': 2, 'verbose': 2, 'version': False,
 'V': False, 'quiet': True, 'packages': ['numpy', 'pandas', 'pyparam'],
 'depends': {'completions': '0.0.1'}}
```

!!! Note
	Default help options are `h`, `help` and `H`, if values are parsed, those values should all be `False`. In later this document, these items will not be shown.

## Fixed prefix
By default, prefix is set to `auto`, which means `-` for short option and `--` for long options.

`examples/fixedPrefix.py`
```python
from pyparam import params
params._prefix = '-'
# same as basic.py
```
```python
> python examples/fixedPrefix.py  -vv \
	-packages numpy pandas pyparam \
	-depends.completions 0.0.1 --quiet
Warning: Unrecognized positional values: '--quiet'
{'v': 2, 'verbose': 2, 'version': False,
 'V': False, 'quiet': False, 'packages': ['numpy', 'pandas', 'pyparam'],
 'depends': {'completions': '0.0.1'}}
```

## Option types
`pyparam` supports following types. We will see how these types are used to define an option or overwrite the type of an option on command line.

|Type|Alias|Meaning|
|----|-----------|-------|
|`auto`|`a`|Used when type is not define. Values will be converted automatically|
|`int`|`i`|Values will be converted into an `int`|
|`float`|`f`|Values will be converted into a `float`|
|`bool`|`b`|Values will be converted into a `bool`|
|`NoneType`|`none`, `n`|Values will be converted into `None`|
|`str`|`s`|Values will be converted into a `str`|
|`dict`|`d`, `box`|Values will be converted into a `dict`|
|`list`|`l`, `array`|Values will be converted into a `list`|
|`verbose`|`v`, `verb`|Values will be parsed in `verbose` mode|
|`python`|`p`, `py`|Values will be converted using `ast.literal_eval`|
|`reset`|`r`|Reset a `list`, a `list:list` or a `dict`|

## Auto options
If a type of an option is not defined, then `auto` will be used. While parsing, the value will be cased into:
1. `None` if value is either `"none"`, `"None"` or `None` itself.
2. an `int` if value matches an integer
3. a `float` if value matches a float
4. `True` if value is in `[True , 1, 'True' , 'TRUE' , 'true' , '1']`
5. `False` if value is in `[False, 0, 'False', 'FALSE', 'false', '0', 'None', 'none', None]`
6. a value casted by `ast.literal_eval` if it starts with `py:` or `repr:`
7. a string of the value.

`examples/autotype.py`
```python
from pyparam import params
params.a.desc = 'This is an option with `auto` type.'
print(params._parse())
```

```python
python examples/autotype.py -a none
{'a': None}

python examples/autotype.py -a 1
{'a': 1}

python examples/autotype.py -a 1.1
{'a': 1.1}

python examples/autotype.py -a true
{'a': True}

python examples/autotype.py -a false
{'a': False}

python examples/autotype.py -a 'py:{"x": 1}'
{'a': {'x': 1}}

# you want to pass everything as str
python examples/autotype.py -a:str 1
{'a': '1'}
```

## List/Array options

```python
> python examples/basic.py --packages pkg1 pkg2 pkg3 # or
> python examples/basic.py --packages pkg1 --packages pkg2 --packages pkg3
# other values not shown
{'packages': ['pkg1', 'pkg2', 'pkg3']}
```

Default values:
```python
params.packages = ['required_package']
```
```python
> python examples/basic.py --packages pkg1 pkg2 pkg3
'packages': ['required_package', 'pkg1', 'pkg2', 'pkg3']
```

Reset list options
```python
# we don't want to install the "required_package"
> python examples/basic.py --packages:list:reset pkg1 pkg2 pkg3
# or simply
> python examples/basic.py --packages:reset pkg1 pkg2 pkg3
'packages': ['pkg1', 'pkg2', 'pkg3']
```

Elements are casted using `auto` type by default:
```python
> python examples/basic.py --packages:reset pkg1 pkg2 true
'packages': ['pkg1', 'pkg2', True]
```

You may force it all strings after reset:
```python
> python examples/basic.py --packages:reset --packages:list:str pkg1 pkg2 true
'packages': ['pkg1', 'pkg2', 'true']
# or define the subtype:
# params.packages.type = 'list:str'
```

## List of list options
Aimed to get values like `[[1, 2], [3, 4], ...]`

`examples/listoflist.py`
```python
from pyparam import params
params.pkgset = [['required-pkg']]
params.pkgset.desc = 'Sets of packages.'
params.pkgset.type = 'list:list'
print(params._parse())
```
```python
> python examples/listoflist.py --pkgset pkg1 pkg2 --pkgset pkg3 pkg4
{'pkgset': [['required-pkg'], ['pkg1', 'pkg2'], ['pkg3', 'pkg4']]}

# if we don't want default values
> python examples/listoflist.py --pkgset:reset pkg1 pkg2 --pkgset pkg3 pkg4
{'pkgset': [['pkg1', 'pkg2'], ['pkg3', 'pkg4']]}
```

## Positional options
`examples/positional.py`
```python
from pyparam import params
params.packages = []
# default key for positional option is '_'
params._.desc = 'Positional option'
print(params._parse())
```
```python
> python examples/positional.py file1
{'packages': [], '_': 'file1'}
```

If it is next a list option:
Say we want `{'packages': ['pkg'], '_': 'file1'}`
```python
> python examples/positional.py --packages pkg file1
# but we get
{'packages': ['pkg', 'file1'], '_': None}

# to get the intentional results
> python examples/positional.py --packages pkg - file1
{'packages': ['pkg', 'file1'], '_': None}
```

Positional option can also be `list`:
```python
params._ = []
params._.desc = 'Positional option'
```
```python
> python examples/positional.py file1
{'packages': [], '_': ['file1']}
```

## Dict options
Like defined in `examples/basic.py`
```python
params.depends = {} # type auto detected
```
```python
> python examples/basic.py --depends.completions 0.0.1 --packages completions
{'packages': ['completions'], 'depends': {'completions': '0.0.1'}}
```

You may chain the dict options:
```python
> python examples/basic.py --depends.completions.version 0.0.1 \
	--depends.completions.optional \
	--packages completions
{'packages': ['completions'], 'depends': {
	'completions': {'version': '0.0.1', 'optional': True}
}}
```

You values are parsed using `auto` type, you can also declare the type:
```python
> python examples/basic.py --depends.dev.pytest:float 3.4 \
	--packages pytest
{'packages': ['pytest'], 'depends': {'dev': {'pytest': 3.4}}}
```

!!! Note
	If you are using prefix `auto`, then whether the option is short or long is determined by the name without the types and the keys of a dict option. For example: `-d.key1` should be a short one.

## Pooled options
Sometimes people like to pool the options and/or values together:
```shell
tar -zxvf some.tar.gz
head -n20 some.txt
```
We also support this feature:
`examples/pooled.py`
```python
from pyparam import params
params.z = params.x = params.v = params.f = False
params.n = 10
print(params._parse())
```
```python
> python examples/pooled.py -zxvf -n20
{'z': True, 'x': True, 'v': True, 'f': True, 'n': 20}
```

## Callbacks
Callbacks are used to modified/check option values.

`examples/callback_check.py`
```python
from os import path
from pyparam import params
params._prefix = '-'
params.o.required = True
params.o.callback = lambda param: 'Directory of output file does not exist.' \
	if not path.exists(path.dirname(param.value)) else None
print(params._parse())
```
```python
python examples/callback_check.py -o /path/not/exists/outfile
```
![callback_error][11]

Modify value with other options:

`examples/callback_modify.py`
```python
from pyparam import params
params.amplifier = 10
params.number.type = int
params.number.callback = lambda param, ps: param.setValue(
	param.value * ps.amplifier.value)
print(params._parse())
```
```python
> python examples/callback_modify.py -amplifier 100 -number 2
{'amplifier': 100, 'number': 200}
```

## Contination on no arguments passed
We can switch it off for print help message and exit when no arguments passed. In case we don't have any required options and we can get enough parameters from default values of optional options:
```python
params._hbald = False
```


## Arbitrary parsing
Parse the arguments without definition
`examples/arbitrary.py`
```python
from pyparam import params
print(params._parse(arbi = True))
```
```python
> python examples/arbitrary.py -a 1 -b:list 2 3 -c:dict \
	-c.a.b 4 -c.a.c 5 -d:list:list 6 7 -d 8 9
{'a': 1, 'b': [2, 3], 'c': {'a': {'b': 4, 'c': 5}},
 'd': [['6', '7'], ['8', '9']]}
```

[9]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/help.png
[11]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/callback_error.png
