from collections import OrderedDict
import re
import pytest
import colorama
from pyparam.help import Helps, HelpOptions, HelpItems
from pyparam import HelpAssembler, MAX_PAGE_WIDTH, MAX_OPT_WIDTH, \
	Param, Params, params, commands, ParamNameError, ParamTypeError, \
	ParamsParseError, ParamsLoadError, OPT_UNSET_VALUE, OPT_POSITIONAL_NAME, \
	Commands, CommandsParseError

def striphelp(msg):
	msg = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', msg.strip())
	return re.sub(r'\s+', ' ', msg)

class TestHelpAssembler:

	@classmethod
	def setup_class(cls):
		import sys
		sys.argv = ['program']
		cls.assembler = HelpAssembler()

	def test_init(self):
		assert self.assembler.progname == 'program'
		assert self.assembler.theme['error'] == colorama.Fore.RED

	@pytest.mark.parametrize('msg, with_prefix, expt', [
		('', True, '{f.RED}Error: {s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('', False, '{f.RED}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('{prog}', False, '{f.RED}{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('1{prog}2', True, '{f.RED}Error: 1{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}2{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
	])
	def test_error(self, msg, with_prefix, expt):
		assert self.assembler.error(msg, with_prefix) == expt

	@pytest.mark.parametrize('msg, with_prefix, expt', [
		('', True, '{f.YELLOW}Warning: {s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('', False, '{f.YELLOW}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('{prog}', False, '{f.YELLOW}{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('1{prog}2', True, '{f.YELLOW}Warning: 1{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}2{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
	])
	def test_warning(self, msg, with_prefix, expt):
		assert self.assembler.warning(msg, with_prefix) == expt

	@pytest.mark.parametrize('title, with_colon, expt', [
		('', True, '{s.BRIGHT}{f.CYAN}{s.RESET_ALL}:'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('title', False, '{s.BRIGHT}{f.CYAN}Title{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('title', True, '{s.BRIGHT}{f.CYAN}Title{s.RESET_ALL}:'.format(
			f = colorama.Fore,
			s = colorama.Style)),
	])
	def test_title(self, title, with_colon, expt):
		assert self.assembler.title(title, with_colon) == expt

	@pytest.mark.parametrize('prog, expt', [
		(None, '{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('another', '{s.BRIGHT}{f.GREEN}another{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
	])
	def test_prog(self, prog, expt):
		assert self.assembler.prog(prog) == expt

	@pytest.mark.parametrize('msg, expt', [
		('', ''),
		('a', 'a'),
		('a{prog}', 'a{s.BRIGHT}{f.GREEN}program{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
	])
	def test_plain(self, msg, expt):
		assert self.assembler.plain(msg) == expt

	@pytest.mark.parametrize('msg, prefix, expt', [
		('optname', '', '{s.BRIGHT}{f.GREEN}optname{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('optname', '  ', '{s.BRIGHT}{f.GREEN}  optname{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
	])
	def test_optname(self, msg, prefix, expt):
		assert self.assembler.optname(msg, prefix) == expt

	@pytest.mark.parametrize('msg, expt', [
		('<opttype>', '{f.BLUE}<OPTTYPE>{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('<opttype>   ', '{f.BLUE}<OPTTYPE>{s.RESET_ALL}   '.format(
			f = colorama.Fore,
			s = colorama.Style)),
		('  ', '  ')
	])
	def test_opttype(self, msg, expt):
		assert self.assembler.opttype(msg) == expt

	@pytest.mark.parametrize('msg, first, alldefault, expt', [
		('', False, False, '  {s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
		('DEfault: 1', True, False, '- DEfault: 1{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
		('Default: 1', False, False, '  {f.MAGENTA}Default: 1{s.RESET_ALL}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
		('XDEFAULT: 1', True, False, '- X{f.MAGENTA}DEFAULT: 1{s.RESET_ALL}{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
		('a DEFAULT: 1', False, True, '  {f.MAGENTA}a DEFAULT: 1{s.RESET_ALL}'.format(
			f = colorama.Fore,
			s = colorama.Style
		)),
	])
	def test_optdesc(self, msg, first, alldefault, expt):
		assert self.assembler.optdesc(msg, first, alldefault) == expt

	@pytest.mark.parametrize('helps, expt', [
		({}, ['']),
		# hello is not asembled
		({'description': ['some description about the program'], 'hello': []}, [
			'{s.BRIGHT}{f.CYAN}Description{s.RESET_ALL}:'.format(
				f = colorama.Fore, s = colorama.Style),
			'  some description about the program',
			'', '']),
		({'optional options': [('-h, --help, -H', '', ['Show help message and exit.'])]}, [
			'{s.BRIGHT}{f.CYAN}Optional options{s.RESET_ALL}:'.format(
				f = colorama.Fore, s = colorama.Style),
			'{s.BRIGHT}{f.GREEN}  -h, --help, -H{s.RESET_ALL} '
			'     - Show help message and exit.{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),
			'', '']),
		({'description': ['some very very very very very very very very very very very very '
			'very very very very description about the program']}, [
			'{s.BRIGHT}{f.CYAN}Description{s.RESET_ALL}:'.format(
				f = colorama.Fore, s = colorama.Style),
			'  some very very very very very very very very very very very very very very '
			'very very description \\',
			'  about the program',
			'', '']),
		({'options': [('-nthreads', '<int>', ['Number of threads to use. Default: 1'])]}, [
			'{s.BRIGHT}{f.CYAN}Options{s.RESET_ALL}:'.format(
				f = colorama.Fore, s = colorama.Style),
			'{s.BRIGHT}{f.GREEN}  -nthreads{s.RESET_ALL} '
			'{f.BLUE}<INT>{s.RESET_ALL}     - Number of threads to use. '
			'{f.MAGENTA}Default: 1{s.RESET_ALL}{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),
			'', '']),
		({'options': [
			('-nthreads', '<int>', ['Number of threads to use. Default: 1']),
			('-opt1', '<str>', ['String options.', 'DEFAULT: "Hello world! \\', 'Not end"']),
			('-option, --very-very-long-option-name', '<int>', [
				'Option descript without default value. And this is a long long long '
				'long description'])]}, [ # expt

			'{s.BRIGHT}{f.CYAN}Options{s.RESET_ALL}:'.format(
				f = colorama.Fore, s = colorama.Style),

			'{s.BRIGHT}{f.GREEN}  -nthreads{s.RESET_ALL} '
			'{f.BLUE}<INT>{s.RESET_ALL}     - Number of threads to use. '
			'{f.MAGENTA}Default: 1{s.RESET_ALL}{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),

			'{s.BRIGHT}{f.GREEN}  -opt1{s.RESET_ALL} {f.BLUE}<STR>{s.RESET_ALL}'
			'         - String options.{s.RESET_ALL}'.format(f = colorama.Fore, s = colorama.Style),

			'                        {f.MAGENTA}DEFAULT: "Hello world! \\{s.RESET_ALL}{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),
			'                        {f.MAGENTA}Not end"{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),

			'{s.BRIGHT}{f.GREEN}  -option, --very-very-long-option-name{s.RESET_ALL} '
			'{f.BLUE}<INT>{s.RESET_ALL}'.format(f = colorama.Fore, s = colorama.Style),

			'                      - Option descript without default value. '
			'And this is a long long long long \\{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),

			'                        description{s.RESET_ALL}'.format(
				f = colorama.Fore, s = colorama.Style),
			'', '']),
	])
	def test_assemble(self, helps, expt):
		hs = Helps()
		for key, val in helps.items():
			hs.add(key, HelpOptions() if val and isinstance(val[0], tuple) else HelpItems())
			for v in val:
				hs.select(key).add(v)
		assert self.assembler.assemble(hs) == expt

# region: test Param
def test_param_init():
	with pytest.raises(ParamNameError):
		Param(None, 'value')
	with pytest.raises(ParamNameError):
		Param('*1234', 'value')

	param = Param('name')
	param.type = 'int'
	param.value = '1'
	assert param.type == 'int:'
	assert param.value == '1'

	param = Param('name')
	param.value = '1'
	param.type = 'int'
	assert param.type == 'int:'
	assert param.value == 1

	param = Param('name')
	assert param.type == 'auto:'
	assert param.value is None

	param = Param('name', None)
	assert param.type == 'NoneType:'
	assert param.value is None

	param = Param('name', 'value')
	assert param.type == 'str:'
	assert param.value == 'value'

	param = Param('name', {'value'})
	assert param.type == 'list:'
	assert param.value == ['value']

	param = Param('name', {'a': 1})
	assert param.type == 'dict:'
	assert param.value == {'a': 1}
	assert param.name == 'name'

	with pytest.raises(ParamTypeError):
		Param('name', object())

def test_param_value():
	param = Param('name', None)
	assert param.value is None
	assert param.type == 'NoneType:'
	param.value = 1
	assert param.value == 1
	assert param.type == 'NoneType:'
	assert param.setValue(2) is param
	assert param.value == 2
	param.setValue(3, update_type = True)
	assert param.value == 3
	assert param.type == 'int:'

def test_param_desc():
	param = Param('name', None)
	assert param.desc == ['Default: None']

	param.value = 1
	param.setDesc('option description.')
	assert param.desc == ['option description. Default: 1']
	param.setDesc('long long option description.')
	assert param.desc == ['long long option description.', 'Default: 1']

	param = Param('name')
	param.desc = []
	assert param.desc == ['Default: None']
	param.required = True
	assert param.desc == ['[No description]']

	param = Param('name', 'default')
	assert param.desc == ["Default: 'default'"]
	assert param.desc == ["Default: 'default'"]



def test_param_required():
	param = Param('name', 'value')
	assert param.required is False
	param.required = True
	assert param.required is True
	param.setRequired(False)
	assert param.required is False
	param.setRequired()
	assert param.required is True

	param.setValue(True, True)
	with pytest.raises(ParamTypeError):
		param.setRequired()

def test_param_show():
	param = Param('name', 'value')
	assert param.show is True
	param.show = False
	assert param.show is False
	param.setShow()
	assert param.show is True
	assert param.setShow(False) is param
	assert param.show is False

def test_param_callback():
	param = Param('name', 'value')
	assert param.callback is None
	param.callback = lambda: None
	assert callable(param.callback)
	assert param.setCallback(lambda: None) is param
	with pytest.raises(TypeError):
		param.setCallback(1)

def test_param_type():
	param = Param('name', '1')
	assert param.type == 'str:'
	param.type = int
	assert param.type == 'int:'
	assert param.value == 1
	assert param.setType(int, update_value = True) is param
	assert param.value == 1
	with pytest.raises(ParamTypeError):
		param.type = 'int:list'
	with pytest.raises(ParamTypeError):
		param.type = 'verbose'

@pytest.mark.parametrize('value, typename, expt, name', [
	('whatever', None, 'whatever', None),
	('1', 'int:', 1, None),
	('1.1', 'float:', 1.1, None),
	('1.0', 'str:', '1.0', None),
	('1', 'bool:', True, None),
	('0', 'bool:', False, None),
	('none', 'NoneType:', None, None),
	(None, 'py:', None, None),
	('py:None', 'py:', None, None),
	('repr:None', 'py:', None, None),
	('None', 'py:', None, None),
	('{"a":1}', 'py:', {"a":1}, None),
	('none', 'auto:', None, None),
	('1', 'auto:', 1, None),
	('1.1', 'auto:', 1.1, None),
	('true', 'auto:', True, None),
	('py:1.23', 'auto:', 1.23, None),
	('xyz', 'auto:', 'xyz', None),
	(1, 'auto:', 1, None),
	('xyz', 'list:', ['xyz'], None),
	({'xyz'}, 'list:', ['xyz'], None),
	(1, 'list:', [1], None),
	([1], 'list:', [1], None),
	(['x', 'y'], 'list:', ['x', 'y'], None),
	('1', 'list:str', ['1'], None),
	('1', 'list:reset', ['1'], None),
	('1', 'list:list', [['1']], None),
	([1,2,3], 'list:list', [[1,2,3]], None),
	('', 'dict:', {}, None),
	(None, 'dict:', None, None),
	(None, 'verbose:', 0, None),
	(1, 'verbose:', 1, None),
	('2', 'verbose:', 2, None),
	('', 'verbose:', 1, None),
	('v', 'verbose:', 2, 'v'),
	('vv', 'verbose:', 3, 'v'),
])
def test_param_forcetype(value, typename, expt, name):
	assert Param._forceType(value, typename, name) == expt

@pytest.mark.parametrize('value, typename, exception', [
	('x', 'bool:', ParamTypeError),
	('x', 'NoneType:', ParamTypeError),
	('x', 'x:', ParamTypeError),
	(1, 'dict:', ParamTypeError),
	([], 'verbose:', ParamTypeError),
])
def test_param_forcetype_exc(value, typename, exception):
	with pytest.raises(exception):
		Param._forceType(value, typename)

def test_param_repr():
	param = Param('name', 'value')
	assert repr(param).startswith(
		"<Param(name='name',value='value',type='str',required=False,show=True) @ ")

def test_param_baseclass():
	param1 = Param('name', '1')
	param2 = Param('name', '1')
	assert hash(param1) == id(param1)
	assert hash(param2) == id(param2)
	assert hash(param1) != hash(param2)
	assert param1 == param2
	param_dict = {param1: 1, param2: 2}
	assert len(param_dict) == 2
	assert param1 in list(param_dict.keys())
	assert param2 in list(param_dict.keys())

	assert param1.value == '1'
	assert param1.int() == 1
	assert param1.str() == '1'
	assert str(param1) == '1'
	assert param1.float() == 1.0
	assert param1.bool() is True
	assert bool(param1) is True
	assert param1.isdigit() is True
	assert param1 + '2' == '12'
	assert '1' in param1
	assert param1 == '1'

	param2.value = 1
	assert param1 != param2
	with pytest.raises(TypeError):
		assert param2 + '2' == '12'
	with pytest.raises(TypeError):
		assert '1' in param2
	assert param2 != '1'

	param2.value = 'a'
	with pytest.raises(ValueError):
		param2.int()
	with pytest.raises(ValueError):
		param2.float()
	with pytest.raises(AttributeError):
		param2.x
	assert param2.int(raise_exc = False) is None
	assert param2.float(raise_exc = False) is None
	assert param2 == 'a'

@pytest.mark.parametrize('value, exptval, exptype', [
	((1,), [1], 'list:'),
	({1}, [1], 'list:'),
	({'a':1}, {'a':1}, 'dict:'),
	(OrderedDict([('b', 2), ('a', 1)]), OrderedDict([('b', 2), ('a', 1)]), 'dict:'),
	(OPT_UNSET_VALUE, None, 'auto:'),
])
def test_param_typefromvalue(value, exptval, exptype):
	assert Param._typeFromValue(value) == (exptval, exptype)

@pytest.mark.parametrize('typename, exptype', [
	(None, None),
	(list, 'list:'),
	('l:l', 'list:list'),
	('a', 'auto:'),
	('auto', 'auto:'),
	('i', 'int:'),
	('int', 'int:'),
	('n', 'NoneType:'),
	('none', 'NoneType:'),
	('f', 'float:'),
	('float', 'float:'),
	('b', 'bool:'),
	('bool', 'bool:'),
	('s', 'str:'),
	('str', 'str:'),
	('d', 'dict:'),
	('dict', 'dict:'),
	('box', 'dict:'),
	('p', 'py:'),
	('py', 'py:'),
	('python', 'py:'),
	('r', 'reset:'),
	('reset', 'reset:'),
	('l', 'list:'),
	('list', 'list:'),
	('array', 'list:'),
])
def test_param_normalizetype(typename, exptype):
	assert Param._normalizeType(typename) == exptype

@pytest.mark.parametrize('typename', [
	'reset:a',
	'dict:x',
	'int:list',
	'int:auto',
])
def test_param_normalizetype_exc(typename):
	with pytest.raises(ParamTypeError):
		Param._normalizeType(typename)

def test_param_push():
	param = Param('name')
	param.push(1)
	assert param.type == 'auto:'
	assert param.value is None
	assert param.stacks == [('auto:', [1])]
	param.push(2)
	assert param.stacks == [('auto:', [1, 2])]
	param.push(1, 'list:list')
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1]])]
	param.push(2)
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1, 2]])]
	param.push(3, 'list:list')
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1, 2], [3]])]
	param.push(4)
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1, 2], [3, 4]])]
	param.push('a')
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1, 2], [3, 4, 'a']])]
	param.push('a', str)
	assert param.stacks == [('auto:', [1, 2]), ('list:list', [[1, 2], [3, 4, 'a']]), ('str:', ['a'])]

	param = Param('a', 1)
	param.push(2)
	assert param.type == 'int:'
	assert param.value == 1
	assert param.stacks == [('int:', [2])]

	param.push(1, 'list:list')
	assert param.stacks == [('int:', [2]), ('list:list', [[1]])]

	# reset
	param = Param('a', [])
	assert param.type == 'list:'
	assert param.value == []
	param.push(1)
	param.push(2)
	assert param.stacks == [('list:', [1,2])]
	param.push(3, 'list:reset')
	assert param.stacks == [('list:', [3])]
	param.push(4)
	assert param.stacks == [('list:', [3, 4])]
	param.push(5, 'list:reset')
	assert param.stacks == [('list:', [5])]
	param.push(6)
	assert param.stacks == [('list:', [5, 6])]

	# OPT_UNSET_VALUE
	param = Param('a')
	param.push(1, typename = 'list:list')
	param.push(typename = 'list:list')
	assert param.stacks == [('list:list', [[1], []])]
	param.push(typename = 'int:')
	assert param.stacks == [('list:list', [[1], []]), ('int:', [])]

	# OPT_UNSET_VALUE, None
	param = Param('a')
	param.push()
	assert param.stacks == []
	param.push('1')
	assert param.stacks == [('auto:', ['1'])]
	param.push()
	param.push('2')
	param.push('3')
	assert param.stacks == [('auto:', ['1', '2', '3'])]
	param = Param('a', 1)
	param.push()
	assert param.stacks == [('int:', [])]

	# push forcely
	param.push(typename = True)
	assert param.stacks == [('int:', []), ('int:', [])]

	# push dict
	param = Param('a')
	param2 = Param('a.b', 1)
	param3 = Param('a.c.x', 2)
	param.push(param2, 'dict:')
	assert param.stacks == [('dict:', [param2])]
	param.push(param3, 'dict:')
	assert param.stacks == [('dict:', [param2, param3])]
	param.push({'a': {'c': {'y': 3}}})
	assert param.stacks == [('dict:', [param2, param3, {'a': {'c': {'y': 3}}}])]

	# push reset
	param = Param('a', [1,2])
	param.push(3)
	assert param.stacks == [('list:', [1,2,3])]
	param.push(typename = 'reset:')
	assert param.stacks == [('list:', [])]

	param = Param('a', [1,2])
	param.push(3, 'reset:')
	assert param.stacks == [('list:', [3])]

	param = Param('a')
	param.type = 'list:list'
	param.value = [[1,2]]
	param.push(3)
	assert param.stacks == [('list:list', [[1,2],[3]])]
	param.push(4, 'reset:')
	assert param.stacks == [('list:list', [[4]])]

	param = Param('a')
	param.type = 'list:list'
	param.value = [[1,2]]
	param.push(4, 'reset:')
	assert param.stacks == [('list:list', [[4]])]

	param = Param('a', [1,2])
	param.push(3, 'list:reset')
	assert param.stacks == [('list:', [3])]
	param.push(4)
	assert param.stacks == [('list:', [3,4])]
	param.push(5)
	assert param.stacks == [('list:', [3,4,5])]

def test_param_push_listreset():
	param = Param('a', ['0'])
	param.type == 'list:str'
	param.push(typename = 'list:reset')
	assert param.stacks == [('list:', [])]
	param.push('1', 'list:str')
	assert param.stacks == [('list:str', ['1'])]
	param.push('2', 'list:str')
	assert param.stacks == [('list:str', ['1', '2'])]


@pytest.mark.parametrize('stacks, exptwarns, exptype, exptval', [
	([], [], 'auto:', None),
	([('int:', [1])], [], 'int:', 1),
	([('int:', [1, 2])],
	 ["Later value 2 was ignored for option 'a' (type='int:')"],
	 'int:', 1),
	([('int:', [1, 2]), ('list:list', [[1]])],
	 ["Previous settings (type='int:', value=[1, 2]) were ignored for option 'a'"],
	 'list:list', [[1]]),
	([('int:', [1, 2]), ('list:list', [[1, 2]])],
	 ["Previous settings (type='int:', value=[1, 2]) were ignored for option 'a'"],
	 'list:list', [[1,2]]),
	([('int:', [1, 2]), ('list:list', [[1, 2], [3, 4, 'a']])],
	 ["Previous settings (type='int:', value=[1, 2]) were ignored for option 'a'"],
	 'list:list', [[1, 2], [3, 4, 'a']]),
	([('int:', [1, 2]), ('list:list', [[1, 2], [3, 4, 'a']]), ('str:', ['a', 'b'])],
	 ["Previous settings (type='int:', value=[1, 2]) were ignored for option 'a'",
	  "Previous settings (type='list:list', value=[[1, 2], [3, 4, 'a']]) were ignored for option 'a'",
	  "Later value 'b' was ignored for option 'a' (type='str:')"],
	 'str:', 'a'),
	([('list:', [1,2]), ('list:', [3, 4])],
	 ["Previous settings (type='list:', value=[1, 2]) were ignored for option 'a'"],
	 'list:', [3,4]),
	([('list:', [1,2]), ('list:', [3, 4]), ('list:', [5, 6])],
	 ["Previous settings (type='list:', value=[1, 2]) were ignored for option 'a'",
	  "Previous settings (type='list:', value=[3, 4]) were ignored for option 'a'"],
	 'list:', [5,6]),
	([('list:', [1,2,'py:3','None'])], [], 'list:', [1,2,3,None]),
	# bool
	([('bool:', [])], [], 'bool:', True),
	# list:auto
	([('list:', ['1'])], [], 'list:', [1]),
	# param
	([('dict:', [Param('a.b', 1)])], [], 'dict:', {'b': 1}),
	([('verbose:', [])], [], 'verbose:', 1),
])
def test_param_checkout(stacks, exptwarns, exptype, exptval):
	param = Param('a')
	param.stacks = stacks
	assert param.checkout() == exptwarns
	assert param.type == exptype
	assert param.value == exptval

def test_param_checkout_list():
	param = Param('a', [])
	assert param.type == 'list:'
	assert param.value == []
	param.stacks = [('list:', ['x', 'y'])]
	param.checkout()
	assert param.type == 'list:'
	assert param.value == ['x', 'y']

@pytest.mark.parametrize('dorig, dup, expt', [
	({}, {'a':1}, {'a':1}),
	({'a': {'b': 2, 'c': 3}}, {'a': {'b': 1}}, {'a': {'b': 1, 'c': 3}}),
])
def test_param_dictupdate(dorig, dup, expt):
	assert Param._dictUpdate(dorig, dup) == expt

@pytest.mark.parametrize('param, expt', [
	(Param('a.b.c', 1), {'b': {'c': 1}}),
])
def test_param_dict(param, expt):
	assert param.dict() == expt

def test_param_dict_exc():
	with pytest.raises(ParamTypeError):
		Param('a').dict()

# endregion

# region: Params
def test_params_lock():
	params = Params()
	params.a = 1
	params.b = 2
	params.b.show = False
	params._locked = True
	with pytest.raises(ParamNameError):
		params.a = 2
	with pytest.raises(ParamNameError):
		params.b.value = 3
	with pytest.raises(ParamNameError):
		params.b.desc = 'Description of b'
	with pytest.raises(ParamNameError):
		params.b.required = True
	with pytest.raises(ParamNameError):
		params.b.type = int
	with pytest.raises(ParamNameError):
		params.b.setCallback(lambda opt: None)

def test_params_init():
	import sys
	sys.argv = ['program']
	params = Params()
	assert params._prog == 'program'
	assert params._usage == []
	assert params._desc == []
	assert params._hopts == ['h', 'help', 'H']
	assert params._prefix == 'auto'
	assert params._hbald == True
	assert list(params._params.keys()) == params._hopts
	assert params._assembler.theme['error'] == colorama.Fore.RED
	assert params._helpx == None

	params = Params(command = 'list')
	assert params._prog == 'program list'
	assert 'h' in params

def test_params_props():
	params = Params()
	# theme
	params._setTheme('plain')
	assert params._assembler.theme['error'] == ''
	params._theme = 'default'
	assert params._assembler.theme['error'] == colorama.Fore.RED

	# usage
	params._setUsage('a\nb')
	assert params._usage == ['a', 'b']
	params._usage = ['1', '2']
	assert params._usage == ['1', '2']

	# desc
	params._setDesc('a\nb')
	assert params._desc == ['a', 'b']
	params._desc = ['1', '2']
	assert params._desc == ['1', '2']

	# hopts
	params._setHopts('-h, --help')
	assert params._hopts == ['-h', '--help']
	params._hopts = ['-H']
	assert params._hopts == ['-H']
	with pytest.raises(ValueError):
		params._setHopts(None)
	with pytest.raises(ValueError):
		params._setHopts('h.e.l.p')

	# prefix
	params._setPrefix('--')
	assert params._prefix == '--'
	assert params._prefixit('a') == '--a'
	params._prefix = '-'
	assert params._prefix == '-'
	assert params._prefixit('a') == '-a'
	with pytest.raises(ParamsParseError):
		params._prefix = ''



	# hbald
	params._setHbald()
	assert params._hbald is True
	params._hbald = False
	assert params._hbald is False

def test_params_attr():
	params.__file__ = None
	assert params.__file__ is None
	params.b = Param('b', None)
	assert isinstance(params.b, Param)
	params.b = 1
	assert params.b.value == 1
	params.a = 1
	assert isinstance(params.a, Param)
	params['c'] = 1
	assert isinstance(params['c'], Param)

	params.v.type = 'verbose'
	with pytest.raises(ParamNameError):
		params.s = params.v

def test_params_repr():
	params = Params()
	params.a = 1
	params.b = 2
	assert repr(params).startswith('<Params(h:False,help:False,H:False,a:1,b:2) @ ')

@pytest.mark.parametrize('mark, args, exptstacks, exptpendings', [
	(1, [], {}, []),
	(2, ['a', 'b'], {OPT_POSITIONAL_NAME: [('list:', ['a', 'b'])]}, []),
	(3, ['-1'], {OPT_POSITIONAL_NAME: [('list:', ['-1'])]}, []),
	# predefined
	(4, ['-b'], {'b': [('bool:', [])]}, []),
	(5, ['x', '-a'], {'a': [('auto:', [])]}, ['x']),
	(6, ['-a=1'], {'a': [('auto:', ['1'])]}, []),
	(7, ['-a', '1'], {'a': [('auto:', ['1'])]}, []),
	(8, ['-a=1', '2'], {'a': [('auto:', ['1'])],
		OPT_POSITIONAL_NAME: [('list:', ['2'])]}, []),
	(9, ['-a:list=1', '2'], {'a': [('list:', ['1', '2'])]}, []),
	(10, ['-', '1', '-a', '2'], {'a': [('auto:', ['2'])],
		OPT_POSITIONAL_NAME: [('list:', ['1'])]}, []),
	(11, ['-', '1', '-a', '2', '-a', '3', '4'], {'a': [('auto:', ['2']), ('auto:', ['3'])],
		OPT_POSITIONAL_NAME: [('list:', ['1'])]}, ['4']),
	(12, ['-bb'], {'b': [('bool:', ['b'])]}, []),
	(13, ['--b'], {'_': [('list:', ['--b'])]}, []),
	(14, ['-b', 'b', 'a'], {'b': [('bool:', [])], '_': [('list:', ['b', 'a'])]}, []),
])
def test_params_preparse(mark, args, exptstacks, exptpendings):
	params = Params()
	params._prefix = '-'
	params.b = Param('b', False)
	parsed, pendings = params._preParse(args)
	assert pendings == exptpendings
	assert {name: param.stacks for name, param in parsed.items()} == exptstacks

@pytest.mark.parametrize('args, exptdict, exptwarns', [
	([], {}, []),
	(['a', 'b'], {'_': ['a', 'b']}, []),
	(['-a'], {'a': True}, []),
	(['-a:bool'], {'a': True}, []),
	(['x', '-a'], {'a': True}, ["Unrecognized value: 'x'"]),
	(['-a=1'], {'a': 1}, []),
	(['-a', '1'], {'a': 1}, []),
	(['-a', '1', '2'], {'a': 1, OPT_POSITIONAL_NAME: [2]}, []),
	(['-a', '1', '2', '-b'], {'a': 1, 'b': True}, ["Later value '2' was ignored for option 'a' (type='auto:')"]),
	(['a', 'b', 'c', 'd', '-a', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-b'],
	 {'a': 1, 'b': True},
	 ["Unrecognized value: 'a'",
	  "Unrecognized value: 'b'",
	  "Unrecognized value: 'c'",
	  "Later value '2' was ignored for option 'a' (type='auto:')",
	  "Later value '3' was ignored for option 'a' (type='auto:')",
	  "Later value '4' was ignored for option 'a' (type='auto:')",
	  "Later value '5' was ignored for option 'a' (type='auto:')",
	  "Later value '6' was ignored for option 'a' (type='auto:')",
	  "Later value '7' was ignored for option 'a' (type='auto:')",
	  "Later value '8' was ignored for option 'a' (type='auto:')"]),
	(['-a.b', '1', '-a.c.x', '2', '-b'], {'a': {'b': 1, 'c': {'x': 2}}, 'b': True}, []),
	(['-a:dict'], {'a': {}}, [])
])
def test_params_parse_arbi(args, exptdict, exptwarns, capsys):
	params = Params()
	params._hbald = False
	exptdict.update(zip(params._hopts, [False] * len(params._hopts)))
	assert params._parse(args, True) == exptdict
	err = capsys.readouterr().err
	for exptwarn in exptwarns:
		assert exptwarn in err

def test_params_parse_verbosecheck():
	params = Params()
	params._prefix = '--'
	params.v.type = 'verbose'
	with pytest.raises(ParamTypeError):
		params._parse()

def test_params_parse(capsys):
	import sys
	sys.argv = ['program']

	params1 = Params()
	params1._hbald = True
	with pytest.raises(SystemExit):
		params1._parse()
	assert 'help' in capsys.readouterr().err

	with pytest.raises(ParamsParseError):
		params1._parse(raise_exc = True)

	params1.a = 1
	params1._parse(['-a', '2', '-b', '3'])
	assert "Unrecognized option: '-b'" in capsys.readouterr().err
	assert params1._dict() == {'H': False, 'h': False, 'help': False, 'a': 2}

	with pytest.raises(SystemExit):
		params1._parse(['-h'])
	assert 'help' in capsys.readouterr().err

	params1.a.callback = lambda param: param.setValue(param.value + 1)
	params1._parse(['-a', '2'])
	assert params1._dict() == {'H': False, 'h': False, 'help': False, 'a': 3}

	params1.b = 10
	params1.b.callback = lambda param, params: param.setValue(param.value * params.a.value)
	params1._parse(['-a', '2'])
	assert params1._dict() == {'H': False, 'h': False, 'help': False, 'a': 3, 'b': 30}

	params1.a.callback = lambda param: list(1)
	params1.b.callback = None
	with pytest.raises(TypeError):
		params1._parse(['-a', '2'])

	params1.a.callback = lambda param: 'Should be negative number' if param.value > 0 else None
	params1._parse(['-a', '-2'])
	assert params1._dict() == {'H': False, 'h': False, 'help': False, 'a': -2, 'b': 30}

	with pytest.raises(SystemExit):
		params1._parse(['-a', '2'])
	assert "Option '-a': Should be negative number" in capsys.readouterr().err

	params1.c.required = True
	params1.d = 3
	with pytest.raises(SystemExit):
		params1._parse(['-a', '-2'])
	assert "Option '-c' is required." in capsys.readouterr().err

	# see if lists get accumulated
	params2 = Params()
	params2.e = [1,2,3]
	params2._parse(['-e', '4', '-e', '5', '6'])
	assert params2._dict() == {'H': False, 'h': False, 'help': False, 'e': [1,2,3,4,5,6]}
	# list:reset
	params2._parse(['-e:l:r', '4', '-e', '5', '6', '-e', '7', '8'])
	assert params2._dict() == {'H': False, 'h': False, 'help': False, 'e': [4, 5, 6, 7, 8]}

	# reset
	params2._parse(['-e:r', '4', '-e', '5', '6', '-e', '7', '8'])
	assert params2._dict() == {'H': False, 'h': False, 'help': False, 'e': [4, 5, 6, 7, 8]}

	# list of list
	params3 = Params()
	params3.f = []
	params3.f.type = 'list:list'
	params3._parse(['-f', '1', '2', '-f', '3', '4'])
	assert params3._dict() == {'H': False, 'h': False, 'help': False, 'f': [['1', '2'], ['3', '4']]}

	# reset dict
	params4 = Params()
	params4.g = {'a': 1}
	params4._parse(['-g.b', '2'])
	assert params4._dict() == {'H': False, 'h': False, 'help': False, 'g': {'a':1, 'b':2}}

	# option names include one another
	params6 = Params()
	params6._prefix = '-'
	params6.sort = 1
	params6.s = False
	assert params6._dict() == {'H': False, 'h': False, 'help': False, 'sort': 1, 's': False}
	assert params6._parse(['-sort', '2', '-s']) == {'H': False, 'h': False, 'help': False, 'sort': 2, 's': True}
	assert params6._parse(['-s1', '-sort', '2']) == {'H': False, 'h': False, 'help': False, 'sort': 2, 's': True}

	params7 = Params()
	params7._.required = True
	with pytest.raises(SystemExit): # optional required
		params7._parse(['-a'])
	assert 'POSITIONAL option is required.' in capsys.readouterr().err

def test_params_parse_pooled():
	# linked name and values
	params = Params()
	params.v = 0
	params.v.type = 'verbose'
	params.verbose = params.v
	params.a = False
	params.abool = params.a
	params.b = False
	params.bbool = params.b
	params.c = False
	params.cbool = params.c
	params.n = 10
	params.nrows = params.n
	params._ = 'x'
	assert params._parse(['-abc', '-n20', '-vv', 'y']) == {'H': False, 'h': False, 'help': False, 'a': True, 'abool': True, 'b': True, 'bbool': True, 'c': True, 'cbool': True, 'n': 20, 'nrows': 20, '_': 'y', 'v': 2, 'verbose': 2}

	assert params._parse(['-ab', '-c', '--nrows=20', '-v2', 'y']) == {'H': False, 'h': False, 'help': False, 'a': True, 'abool': True, 'b': True, 'bbool': True, 'c': True, 'cbool': True, 'n': 20, 'nrows': 20, '_': 'y', 'v': 2, 'verbose': 2}

	with pytest.raises(ParamTypeError):
		params._parse(['-abc:int'])

	params = Params()
	params._prefix = '-'
	params.a = False
	params.abc = 2
	assert params._parse(['-abc', '3', '-a', 'true']) == {'H': False, 'h': False, 'help': False, 'a': True, 'abc': 3}

	params = Params()
	params.abc = True
	params._ = []
	assert params._parse(['-abc', 'true']) == {'H': False, 'h': False, 'help': False, 'abc': True, '_': ['-abc', True]}


def test_params_parse_verbose():
	# verbose
	params5 = Params()
	params5.v = 0
	params5.a = 0
	params5.v.type = 'verbose'
	params5._parse(['-v', '-a1'])
	assert params5._dict() == {'H': False, 'h': False, 'help': False, 'v': 1, 'a': 1}
	params5._parse(['-vv', '-a1'])
	assert params5._dict() == {'H': False, 'h': False, 'help': False, 'v': 2, 'a': 1}
	params5._parse(['-vvv', '-a1'])
	assert params5._dict() == {'H': False, 'h': False, 'help': False, 'v': 3, 'a': 1}
	params5._parse(['-v4', '-a1'])
	assert params5._dict() == {'H': False, 'h': False, 'help': False, 'v': 4, 'a': 1}

def test_params_parse_positional(capsys):
	# positional
	params5 = Params()
	params5[OPT_POSITIONAL_NAME].desc = 'positional'
	assert params5._parse(['x', 'y']) == {'H': False, 'h': False, 'help': False, OPT_POSITIONAL_NAME: 'x'}
	assert "Later value 'y' was ignored for option '_' (type='auto:')" in capsys.readouterr().err

	params5 = Params()
	params5[OPT_POSITIONAL_NAME] = []
	assert params5._parse(['x', 'y']) == {'H': False, 'h': False, 'help': False, OPT_POSITIONAL_NAME: ['x','y']}

	params5 = Params()
	params5[OPT_POSITIONAL_NAME] = []
	params5.a.type = str
	assert params5._parse(['-a', '1', 'x', 'y']) == {'H': False, 'h': False, 'help': False, 'a': '1', '_': ['x', 'y']}

	params5 = Params()
	params5[OPT_POSITIONAL_NAME] = []
	assert params5._parse(['-:str', 'x', 'y']) == {'H': False, 'h': False, 'help': False, '_': 'x'}
	assert "Unrecognized value: 'y'" in capsys.readouterr().err


def test_params_help(capsys):
	import sys
	sys.argv = ['program']
	params = Params()
	#print ('-'*10, params._help(), '-'*10)
	#assert striphelp(params._help()) == 'Usage: program [OPTIONS] Optional options: -h, -H, --help ' + \
	#	'- Show help message and exit.'

	params.optional = 'default'
	assert striphelp(params._help()) == 'Usage: program [OPTIONS] Optional options: --optional <STR> ' + \
		"- Default: 'default' -h, -H, --help " + \
		'- Show help message and exit.'
	params.r.required = True
	params.r.type = 'NoneType'
	params.req2.required = True
	params.req3 = params.r
	params.req4 = params.r
	params.req5 = params.r
	params.req6 = params.r
	params.req7 = params.r
	params.req73333 = params.r
	params.req722222 = params.r
	params.req722222222 = params.r
	params.opt = params.optional
	params.opt2 = 1
	assert striphelp(params._help()) == "Usage: program <-r NONETYPE> <--req2 AUTO> [OPTIONS] Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit."

	params._usage = '{prog} <-this THIS> <-is IS> <-a A> <-very VERY> <-very VERY>' + \
		' <-very VERY> <-very VERY> <-very VERY> <-very VERY> <-very VERY> <-long LONG>' + \
		' <-usage Usage>'
	assert striphelp(params._help()) == "Usage: program <-this THIS> <-is IS> <-a A> <-very VERY> <-very VERY> <-very VERY> <-very \\ VERY> <-very VERY> <-very VERY> <-very VERY> <-long LONG> <-usage Usage> Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit."

	params._ = ['positional']
	params._usage = []
	assert striphelp(params._help()) == "Usage: program <-r NONETYPE> <--req2 AUTO> [OPTIONS] [POSITIONAL] Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit. POSITIONAL <LIST> - Default: ['positional']"

	params._.required = True
	params._desc = 'An example description'
	assert striphelp(params._help()) == "Description: An example description Usage: program <-r NONETYPE> <--req2 AUTO> [OPTIONS] POSITIONAL Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] POSITIONAL <LIST> - Default: ['positional'] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit."

	params._helpx = lambda items: items.add('helpx', HelpItems()).select('helpx').add('helpx demo')
	assert striphelp(params._help(error = 'example error')) == "Error: example error Description: An example description Usage: program <-r NONETYPE> <--req2 AUTO> [OPTIONS] POSITIONAL Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] POSITIONAL <LIST> - Default: ['positional'] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit. Helpx: helpx demo"

	with pytest.raises(SystemExit):
		params._help(print_and_exit = True)

	assert striphelp(capsys.readouterr().err) == "Description: An example description Usage: program <-r NONETYPE> <--req2 AUTO> [OPTIONS] POSITIONAL Required options: -r, --req3, --req4, --req5, --req6, --req7, --req73333, --req722222, --req722222222 <NONETYPE> - [No description] --req2 <AUTO> - [No description] POSITIONAL <LIST> - Default: ['positional'] Optional options: --opt, --optional <STR> - Default: 'default' --opt2 <INT> - Default: 1 -h, -H, --help - Show help message and exit. Helpx: helpx demo"

	params1 = Params()
	params1.v.type = 'verbose'
	params1.verbose = params1.v

	assert striphelp(params1._help()) == "Usage: program [OPTIONS] Optional options: -v|vv|vvv, --verbose <VERBOSITY> - Default: None -h, -H, --help - Show help message and exit."

def test_params_hashable():
	params = Params()
	params2 = Params()
	params_dict = {params: 1}
	assert list(params_dict.keys())[0] == params
	assert list(params_dict.keys())[0] != params2

def test_params_loaddict():
	params = Params()
	params._loadDict({})
	assert params._dict() == {'H': False, 'h': False, 'help': False, }

	params._load({"a": 1})
	assert isinstance(params.a, Param)
	assert not params.a.show
	params._load({"b.show": True})
	assert params.b.show

	with pytest.raises(ParamsLoadError):
		params._load({"x": True, "x.t": 1})

def test_params_loadfile(tmp_path):
	tmpfile1 = tmp_path / 'params1.config'
	tmpfile1.write_text(
		"[DEFAULT]\n"
		"a = 1\n"
		"a.required = py:False\n"
	)
	params = Params()
	params._loadFile(tmpfile1.as_posix())
	assert isinstance(params.a, Param)
	assert not params.a.required

	tmpfile2 = tmp_path / 'params2.config'
	tmpfile2.write_text(
		"[DEFAULT]\n"
		"a = 1\n"
		"a.required = py:False\n"
		"[profile]\n"
		"a.type = int\n"
		"a = 2\n"
		"b.alias = a\n"
	)
	params._loadFile(tmpfile2.as_posix(), profile = 'profile')
	assert params.a.value == 2
	assert params.b is params.a

	tmpfile3 = tmp_path / 'params3.config'
	tmpfile3.write_text(
		"[DEFAULT]\n"
		"a = 1\n"
		"a.required = py:False\n"
		"[profile]\n"
		"a.type = int\n"
		"a = 2\n"
		"b.alias = c\n"
	)
	with pytest.raises(ParamsLoadError):
		params._loadFile(tmpfile3.as_posix(), profile = 'profile')

def test_params_completions():
	params = Params()
	assert re.search(r'# .+_complete', params._complete(shell = 'fish'))
	params.option = ''
	assert re.search(r"-l 'option'", params._complete(shell = 'fish'))
	assert re.search(r"-l 'option:str'", params._complete(shell = 'fish', withtype = True))
	params.v = 0
	params.v.type = 'verbose'
	assert re.search(r"-s 'v'", params._complete(shell = 'fish'))
	assert re.search(r"-o 'vv'", params._complete(shell = 'fish'))
	assert re.search(r"-o 'vvv'", params._complete(shell = 'fish'))
	params.v.show = False
	assert not re.search(r"-o 'vvv'", params._complete(shell = 'fish'))
# endregion

# region: Commands
def test_commands_init():
	commands = Commands()
	assert commands._prefix == 'auto'
	commands._setPrefix('--')
	commands._prefix == '--'
	commands._._prefix == '--'
	assert commands._desc == []
	assert commands._desc is commands._props['_desc']
	assert commands._hcmd == ['help']
	assert commands._hcmd is commands._props['_hcmd']
	commands._desc = 'a\nb'
	assert commands._desc == ['a', 'b']
	commands._setDesc('c\nd')
	assert commands._desc == ['c', 'd']
	commands._setHcmd('help,h')
	assert commands._hcmd == ['help', 'h']
	assert commands._assembler.theme['error'] == colorama.Fore.RED
	commands._setTheme('plain')
	assert commands._assembler.theme['error'] == ''

	commands.list = 'List all commands'
	commands.show = commands.list
	assert commands.show._prog.endswith('list|show')

	commands._setInherit(False)
	assert commands._inherit is False

def test_commands_attr():
	commands.__file__ = None
	assert commands.__file__ is None

def test_commands_help(capsys):
	commands = Commands()
	commands._props['assembler'].progname = 'program'
	assert striphelp(commands._help()) == "Usage: program <command> [OPTIONS] Global optional options: -h, -H, --help - Show help message and exit. Available commands: help [COMMAND] - Print help message for the command and exit."

	commands.cmd1 = 'Comman 1'
	commands.alongcommand = 'A long command'
	commands.cmd2 = commands.cmd1
	assert striphelp(commands._help()) == "Usage: program <command> [OPTIONS] Global optional options: -h, -H, --help - Show help message and exit. Available commands: cmd1 | cmd2 - Comman 1 alongcommand - A long command help [COMMAND] - Print help message for the command and exit."

	commands._helpx = lambda items: items.add('Additional', HelpItems()).select('/Addi/').add('demo')
	assert striphelp(commands._help()) == "Usage: program <command> [OPTIONS] Global optional options: -h, -H, --help - Show help message and exit. Available commands: cmd1 | cmd2 - Comman 1 alongcommand - A long command help [COMMAND] - Print help message for the command and exit. Additional: demo"

	commands._.a.required = True
	assert striphelp(commands._help('some errors')) == "Error: some errors Usage: program <command> [OPTIONS] Global required options: -a <AUTO> - [No description] Global optional options: -h, -H, --help - Show help message and exit. Available commands: cmd1 | cmd2 - Comman 1 alongcommand - A long command help [COMMAND] - Print help message for the command and exit. Additional: demo"

	with pytest.raises(SystemExit):
		commands._help(print_and_exit = True)
	assert 'help' in capsys.readouterr().err

	commands._desc = 'Command description'
	commands.cmd1         = 'First command'
	commands.cmd1._usage  = '{prog} options'
	commands.cmd2         = commands.cmd1
	commands._.a.required = True
	assert striphelp(commands._help()) == "Description: Command description Usage: program <command> [OPTIONS] Global required options: -a <AUTO> - [No description] Global optional options: -h, -H, --help - Show help message and exit. Available commands: cmd1 | cmd2 - First command alongcommand - A long command help [COMMAND] - Print help message for the command and exit. Additional: demo"

def test_commands_parse(capsys):
	commands = Commands()
	commands._inherit = False
	with pytest.raises(SystemExit):
		commands._parse()
	assert 'help' in capsys.readouterr().err

	with pytest.raises(SystemExit):
		commands._parse(['help'])
	assert 'help' in capsys.readouterr().err

	with pytest.raises(SystemExit):
		commands._parse(['1'])
	assert 'No command given.' in capsys.readouterr().err

	commands.cmd1            = 'First command'
	commands.cmd1._usage     = '{prog} options'
	commands.cmd2            = commands.cmd1
	commands.cmd2.a.required = True
	commands._.a.required    = True
	with pytest.raises(SystemExit):
		commands._parse(['cmd2'])
	assert "Option '-a' is required." in capsys.readouterr().err

	with pytest.raises(SystemExit):
		commands._parse(['-a', 'cmd2', '0'])
	err = capsys.readouterr().err
	assert "Option '-a' is required." in err
	assert "program cmd1|cmd2" in err

	command, opts, gopts = commands._parse(['-a', '2', 'cmd1', '-a', '1'])
	assert command == 'cmd1'
	assert opts == {'h': False, 'help': False, 'H': False, 'a': 1}
	assert gopts == {'h': False, 'help': False, 'H': False, 'a': 2}

def test_commands_parse_inherit():
	commands = Commands()
	commands._._prefix = '-'
	commands._.a = 1
	commands.list = 'List commands'
	with pytest.raises(ValueError): # inconsistent prefix
		commands._parse()
	commands._._prefix = 'auto'
	commands.list.a = True
	with pytest.raises(ParamNameError): # can't share option
		commands._parse()
	del commands.list._params['a']

	commands.list.x = 9
	command, opts, gopts = commands._parse(['-a', '2', 'list', '-x', '1'])
	assert command == 'list'
	assert opts == {'h': False, 'help': False, 'H': False, 'a': 2, 'x': 1}
	assert gopts == {'h': False, 'help': False, 'H': False, 'a': 2}

	command, opts, gopts = commands._parse(['list', '-a', '2', '-x', '1'])
	assert command == 'list'
	assert opts == {'h': False, 'help': False, 'H': False, 'a': 2, 'x': 1}
	assert gopts == {'h': False, 'help': False, 'H': False, 'a': 2}

def test_commands_parse_arbi(capsys):
	commands = Commands()
	command, options, goptions = commands._parse(['-x', 'command', '-a', '1'], arbi = True)
	assert "Unrecognized value: 'command'" in capsys.readouterr().err
	assert command == '-x'
	assert goptions == {'H': False, 'h': False, 'help': False}
	assert options == {'H': False, 'h': False, 'help': False, 'a': 1}

def test_commands_help_command(capsys):
	commands = Commands()
	with pytest.raises(SystemExit):
		commands._parse(['help', 'x'])
	assert 'No such command: x' in capsys.readouterr().err
	commands.show = 'Show the list.'
	with pytest.raises(SystemExit):
		commands._parse(['help', 'show'])
	# leading '  ' makes sure it is in Description
	assert '  Show the list.' in capsys.readouterr().err

	commands._hcmd = 'h'
	with pytest.raises(SystemExit):
		commands._parse(['h', 'show'])
	# leading '  ' makes sure it is in Description
	assert '  Show the list.' in capsys.readouterr().err

def test_commands_completions():
	commands = Commands()
	assert re.search(r"-a 'help'", commands._complete(shell = 'fish', alias = False))
	commands.show = 'Show the list'
	assert re.search(r"-a 'show'", commands._complete(shell = 'fish'))
# endregion