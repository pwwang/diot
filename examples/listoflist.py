from pyparam import params
params.pkgset = [['required-pkg']]
params.pkgset.desc = 'Sets of packages.'
params.pkgset.type = 'list:list'
print(params._parse())