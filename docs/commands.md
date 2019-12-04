## An example
`examples/subcommands.py`
```python
from pyparam import commands
# default global options proxy name '_'
commands._.shell      = 'auto'
commands._.shell.desc = [
	'The shell, one of bash, fish, zsh and auto.',
	'Shell will be detected from `os.environ["SHELL"]` if auto.',
]
commands._.auto      = False
commands._.auto.desc = [
	'Automatically write completions to destination file.',
	'Bash: `~/bash_completion.d/<name>.bash-completion`',
	'  Also try to source it in ~/.bash_completion',
	'Fish: `~/.config/fish/completions/<name>.fish`',
	'Zsh:  `~/.zfunc/_<name>`',
	'  `fpath+=~/.zfunc` is ensured to add before `compinit`'
]
commands._.a         = commands._.auto
commands._.s         = commands._.shell
# description for the command
commands.self        = 'Generate completions for myself.'
# we don't have any required options for command 'self'
commands.self._hbald = False
commands.generate    = 'Generate completions from configuration files'
# define an option for command 'generate'
commands.generate.config.desc = [
	'The configuration file. Scheme should be aligned following json data:',
	'{',
	'	"program": {',
	'		"name": "program",',
	'		"desc": "A program",',
	'		"options": {',
	'			"-o": "Output file",',
	'			"--output": "Long version of -o"',
	'		}',
	'	},',
	'	"commands": {',
	'		"list": {',
	'			"desc": "List commands",',
	'			"options": {',
	'				"-a": "List all commands",',
	'				"--all": "List all commands"',
	'			}',
	'		}',
	'	}',
	'}',
	'',
	'Configuration file that is supported by `python-simpleconf` is supported.'
]
commands.generate.config.required = True
# alias
commands.generate.c = commands.generate.config
command, options, goptions = commands._parse()
print(command, options, goptions)
```

![subcommand][12]
```python
> python examples/subcommands.py generate -sfish -a -c some.json
('generate',  # command
 {'config': 'some.json', 'c': 'some.json',
  'shell': 'fish', 'auto': True, 'a': True, 's': 'fish'}, # command options
 {'h': False, 'help': False, 'H': False, 'shell': 'fish',
  'auto': True, 'a': True, 's': 'fish'} # global options
```

## Inheritage of global options
As you may see from the results, the parameters from global options are inherited in the command options. This allows the users to pass the global options after the command:
```shell
python examples/subcommands.py self --shell fish --auto
```
However, you may turn this off `commands._inherit = False`, then the only way to pass the global options is to put them before the command:
```shell
python examples/subcommands.py --shell fish --auto self
```

[12]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/subcommand.png
