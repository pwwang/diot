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
commands.self        = 'Generate completions for myself.'
# we don't have any required options for command 'self'
commands.self._hbald = False
commands.generate    = 'Generate completions from configuration files'
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
commands.generate.config.required = True       # pylint: disable=no-member
commands.generate.c = commands.generate.config # pylint: disable=no-member
command, options, goptions = commands._parse()
print(command, options, goptions)
