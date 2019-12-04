from os import path
from pyparam import params

params.o.required = True
params.o.callback = lambda param: 'Directory of output file does not exist.' \
	if not path.exists(path.dirname(param.value)) else None
print(params._parse())