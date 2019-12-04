import colorama
from pyparam import params
params._theme = dict(title = colorama.Style.BRIGHT + colorama.Fore.YELLOW)
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
print(params._parse())
