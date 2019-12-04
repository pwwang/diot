from os import path
from pyparam import params
__here__ = path.dirname(path.realpath(__file__))
params._loadFile(
	path.join(__here__, 'options.ini'),
	profile = 'default',
	show = True)
# options loaded from config file are not showing by default
# unless `option.show` is set to True in the file
print(params._parse())