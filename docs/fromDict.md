## Loading data from a dict

`examples/fromDict.py`

```python
from pyparam import params
params._load({
	'v'       : 0,
	'verbose' : 0,
	'V'       : False,
	'quiet'   : False,
	'packages': ['numpy', 'pandas', 'pyparam'],
	'depends' : {'pyparam': '0.0.1'}
})

print(params._dict())
```
```python
{'V': False, 'quiet': False, 'packages': ['numpy', 'pandas', 'pyparam'],
 'depends': {'pyparam': '0.0.1'}}
```

## Load option definitions from dict
`examples/optionsFromDict.py`

```python
from pyparam import params
params._load({
	'v'                : 0,
	'v.type'           : 'verbose',
	'verbose.alias'    : 'v',
	'version'          : False,
	'version.desc'     : 'Show the version and exit.',
	'V.alias'          : 'version',
	'quiet'            : False,
	'quiet.desc'       : 'Silence warnings.',
	'packages.type'    : 'list',
	'packages.required': True,
	'packages.desc'    : 'The packages to install.',
	'depends'          : {},
	'depends.desc'     : 'The dependencies.',
}, show = True)
# options loaded from dict are not showing in the help page
print(params._parse())
```
![fromdict][1]

```python
> python examples/optionsFromDict.py -vv --quiet \
	--packages numpy pandas pyparam \
	--depends.completions 0.0.1
{'h': False, 'help': False, 'H': False,
 'v': 2, 'verbose': 2, 'version': False,
 'V': False, 'quiet': True, 'packages': ['numpy', 'pandas', 'pyparam'],
 'depends': {'completions': '0.0.1'}}
```

## Loading from a configuration file

Parameters can also be loaded from a configuration file that is supported by [`python-simpleconf`][17]

`examples/options.ini`
```ini
[default]
v                 = 0
v.type            = verbose
verbose.alias     = v
version           = py:False
version.desc      = Show the version and exit.
V.alias           = version
quiet             = py:False
quiet.desc        = Silence warnings.
packages.type     = list
packages.required = py:True
packages.desc     = The packages to install.
depends           = py:{}
depends.desc      = The dependencies.
token             = some-secrete-token
; Don't show it in help page
; Even it's loaded by show = True
token.show        = py:False
[dev]
dev-depends      = py:{}
dev-depends.desc = The dependencies for dev.
```

`examples/fromFile.py`
```python
from os import path
from pyparam import params
__here__ = path.dirname(path.realpath(__file__))
params._loadFile(
	path.join(__here__, 'options.ini'),
	profile = 'default',
	show = True)
# options loaded from config file are not showing by default
# unless `option.show` is set to True in the file
print(params._parse())
```

```python
> python examples/fromFile.py --packages numpy --dev-depends.pytest=3.4
Warning: Unrecognized option: '--dev-depends'
{'v': 0, 'version': False, 'quiet': False,
 'depends': {}, 'token': 'some-secrete-token',
 'packages': ['numpy'], 'verbose': 0, 'V': False}
```

Load from different profile:
```python
params._loadFile(..., profile = 'dev')
```
```python
> python examples/fromFile.py --packages numpy --dev-depends.pytest=3.4
{'v': 0, 'version': False, 'quiet': False, 'dev-depends': {'pytest': '3.4'}
 'depends': {}, 'token': 'some-secrete-token',
 'packages': ['numpy'], 'verbose': 0, 'V': False}
```

[1]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/optionsFromDict.png
[17]: https://github.com/pwwang/simpleconf