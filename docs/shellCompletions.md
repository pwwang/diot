## Generate completion scripts for shell

We currently support `bash`, `fish` and `zsh`, which are actually currently supported by [`completions`][1]

### For fish
`examples/pyparam-completions.py`
```python
from pyparam import params
# define arguments
params.v            = 0
# verbose option
params.v.type = 'verbose'
# alias
params.verbose   = params.v
params.version      = False
params.version.desc = 'Show the version and exit.'
# alias
params.V            = params.version
params.quiet        = False
params.quiet.desc   = 'Silence warnings.'
# list/array options
params.packages.type     = 'list'
# required
params.packages.required = True
params.packages.desc     = 'The packages to install.'
params.depends           = {}
params.depends.desc      = 'The dependencies.'
print(params._complete(shell = 'fish'))
```

Install the script:
```shell
# make it executable
chmod +x examples/pyparam-completions.py
examples/pyparam-completions.py > ~/.config/fish/completions/pyparam-completions.py.fish
```
(You may need to restart your shell for the changes to take effect)
![completions][2]

### For `bash`
```python
print(params._complete(shell = 'bash'))
```
```shell
# make it executable
chmod +x examples/pyparam-completions.py
examples/pyparam-completions.py > ~/.bash_completion.d/pyparam-completions.py.bash-completion
```

Append following to your `.bashrc` file:
```bash
for bcfile in ~/.bash_completion.d/*.bash-completion; do
	[ -f "$bcfile" ] && . $bcfile
done
```

### For `zsh`
```python
print(params._complete(shell = 'zsh'))
```
```shell
# make it executable
chmod +x examples/pyparam-completions.py
examples/pyparam-completions.py > ~/.zsh-completions/_pyparam-completions
```

You may need to add following before `compinit` in your `.zshrc`
```zsh
fpath+=~/.zsh-completions/
```

### Automation
If you are bothered with the rcfile stuff, [`completions`][1] offers automation for the process. You just need to pass `True` to argument `auto` for `_complete` method:
```python
params._complete(shell = "bash", auto = True)
```

### Alias and type completion
By default the defined types and alias for an option are not included for completion. For option names, the longest one is used. To enable them for completion:
```python
params._complete(shell = "bash", auto = True, withtype = True, alias = True)
```
![completions-withtypealias][3]


[1]: https://github.com/pwwang/completions
[2]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/pyparam-completions.png
[3]: https://raw.githubusercontent.com/pwwang/pyparam/master/docs/static/pyparam-completions-withtypealias.png
