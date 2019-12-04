# pyparam
[![pypi][1]][2] [![pypi][10]][11] [![travis][3]][4] [![docs][18]][19] [![codacy quality][5]][6] [![codacy quality][7]][6] ![pyver][8]

Powerful parameter processing

## Features
- Command line argument parser (with subcommand support)
- `list/array`, `dict`, `positional` and `verbose` options support
- Type overwriting for parameters
- Rich API for Help page redefinition
- Parameter loading from configuration files
- Shell completions

## Installation
```shell
pip install pyparam
# install latest version via poetry
git clone https://github.com/pwwang/pyparam.git
cd pyparam
poetry install
```

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
```shell
> python example/basic.py
```
![help][9]

```shell
> python examples/basic.py -vv --quiet \
	--packages numpy pandas pyparam \
	--depends.completions 0.0.1
{'h': False, 'help': False, 'H': False,
 'v': 2, 'verbose': 2, 'version': False,
 'V': False, 'quiet': True, 'packages': ['numpy', 'pandas', 'pyparam'],
 'depends': {'completions': '0.0.1'}}
```

## Documentation
[ReadTheDocs][19]


[1]: https://img.shields.io/pypi/v/pyparam.svg?style=flat-square
[2]: https://pypi.org/project/pyparam/
[3]: https://img.shields.io/travis/pwwang/pyparam.svg?style=flat-square
[4]: https://travis-ci.org/pwwang/pyparam
[5]: https://img.shields.io/codacy/grade/a34b1afaccf84019a6b138d40932d566.svg?style=flat-square
[6]: https://app.codacy.com/project/pwwang/pyparam/dashboard
[7]: https://img.shields.io/codacy/coverage/a34b1afaccf84019a6b138d40932d566.svg?style=flat-square
[8]: https://img.shields.io/pypi/pyversions/pyparam.svg?style=flat-square
[9]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/help.png
[10]: https://img.shields.io/github/tag/pwwang/pyparam.svg?style=flat-square
[11]: https://github.com/pwwang/pyparam
[18]: https://img.shields.io/readthedocs/pyparam.svg?style=flat-square
[19]: https://pyparam.readthedocs.io/en/latest/
