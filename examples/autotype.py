from pyparam import params
params.a.desc = 'This is an option with `auto` type.'
print(params._parse())