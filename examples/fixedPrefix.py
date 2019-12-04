from pyparam import params
params._prefix = '-'
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