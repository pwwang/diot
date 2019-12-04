from pyparam import params
params.packages = []
# default key for positional option is '_'
params._.desc = 'Positional option'
print(params._parse())