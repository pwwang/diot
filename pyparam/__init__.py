"""
parameters module for PyPPL
"""

__version__ = "0.2.4"

import sys
import re
import ast
import builtins
import textwrap
from os import path
from collections import OrderedDict
import colorama
from simpleconf import Config
from .help import HelpItems, HelpOptions, HelpOptionDescriptions, Helps

# the max width of the help page, not including the leading space
MAX_PAGE_WIDTH      = 100
# the max width of the option name (include the type and placeholder, but not the leading space)
MAX_OPT_WIDTH       = 36
# the min gap between optname/opttype and option description
MIN_OPTDESC_LEADING = 5
# maximum warnings to print
MAX_WARNINGS        = 10

THEMES = dict(
	default = dict(
		error   = colorama.Fore.RED,
		warning = colorama.Fore.YELLOW,
		title   = colorama.Style.BRIGHT + colorama.Fore.CYAN,  # section title
		prog    = colorama.Style.BRIGHT + colorama.Fore.GREEN, # program name
		default = colorama.Fore.MAGENTA,              # default values
		optname = colorama.Style.BRIGHT + colorama.Fore.GREEN,
		opttype = colorama.Fore.BLUE,
		optdesc = ''),

	blue = dict(
		title   = colorama.Style.BRIGHT + colorama.Fore.GREEN,
		prog    = colorama.Style.BRIGHT + colorama.Fore.BLUE,
		optname = colorama.Style.BRIGHT + colorama.Fore.BLUE,
		opttype = colorama.Style.BRIGHT),

	plain = dict(
		error   = '', warning = '', title   = '', prog    = '',
		default = '', optname = '', opttype = '')
)

OPT_ALLOWED_TYPES = ('str', 'int', 'float', 'bool', 'list', 'py', 'NoneType', 'dict')

OPT_TYPE_MAPPINGS = dict(
	a = 'auto',  auto  = 'auto',  i = 'int',   int   = 'int',  n = 'NoneType',
	f = 'float', float = 'float', b = 'bool',  bool  = 'bool', none = 'NoneType',
	s = 'str',   str   = 'str',   d = 'dict',  dict = 'dict',  box = 'dict',
	p = 'py',    py    = 'py',    python = 'py', r = 'reset',  reset = 'reset',
	l = 'list',  list  = 'list',  array  = 'list', v = 'verbose', verb = 'verbose',
	verbose = 'verbose'
)

OPT_BOOL_TRUES  = [True , 1, 'True' , 'TRUE' , 'true' , '1']

OPT_BOOL_FALSES = [False, 0, 'False', 'FALSE', 'false', '0', 'None', 'none', None]

OPT_NONES = [None, 'none', 'None']

OPT_PATTERN       = r"^([a-zA-Z@][\w,\._-]*)?(?::([\w:]+))?(?:=(.*))?$"
OPT_INT_PATTERN   = r'^[+-]?\d+$'
OPT_FLOAT_PATTERN = r'^[+-]?(?:\d*\.)?\d+(?:[Ee][+-]\d+)?$'
OPT_NONE_PATTERN  = r'^none|None$'
OPT_BOOL_PATTERN  = r'^(%s)$' % ('|'.join(set(str(x) for x in OPT_BOOL_TRUES + OPT_BOOL_FALSES)))
OPT_PY_PATTERN    = r'^(?:py|repr):(.+)$'

OPT_POSITIONAL_NAME = '_'
OPT_UNSET_VALUE     = '__Param_Value_Not_Set__'
CMD_GLOBAL_OPTPROXY = '_'

REQUIRED_OPT_TITLE = 'REQUIRED OPTIONS'
OPTIONAL_OPT_TITLE = 'OPTIONAL OPTIONS'

class ParamNameError(Exception):
	"""Exception to raise while name of a param is invalid"""

class ParamTypeError(Exception):
	"""Exception to raise while type of a param is invalid"""

class ParamsParseError(Exception):
	"""Exception to raise while failed to parse arguments from command line"""

class ParamsLoadError(Exception):
	"""Exception to raise while failed to load params from dict/file"""

class CommandsParseError(Exception):
	"""Exception to raise while failed to parse command arguments from command line"""

class _Hashable:
	"""
	A class for object that can be hashable
	"""
	def __hash__(self):
		"""
		Use id as identifier for hash
		"""
		return id(self)

	def __eq__(self, other):
		"""
		How to compare the hash keys
		"""
		return id(self) == id(other)

	def __ne__(self, other):
		"""
		Compare hash keys
		"""
		return not self.__eq__(other)

class _Valuable:

	STR_METHODS = ('capitalize', 'center', 'count', 'decode', 'encode', 'endswith', \
		'expandtabs', 'find', 'format', 'index', 'isalnum', 'isalpha', 'isdigit', \
		'islower', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', \
		'partition', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', \
		'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', \
		'translate', 'upper', 'zfill')

	def __str__(self):
		return str(self.value)

	def str(self):
		"""Return the value in str type"""
		return str(self.value)

	def int(self, raise_exc = True):
		"""Return the value in int type"""
		try:
			return int(self.value)
		except (ValueError, TypeError):
			if raise_exc:
				raise
			return None

	def float(self, raise_exc = True):
		"""Return the value in float type"""
		try:
			return float(self.value)
		except (ValueError, TypeError):
			if raise_exc:
				raise
			return None

	def bool(self):
		"""Return the value in bool type"""
		return bool(self.value)

	def __getattr__(self, item):
		# attach str methods
		if item in _Valuable.STR_METHODS:
			return getattr(str(self.value), item)
		raise AttributeError('Class %r: No such attribute: %r' % (self.__class__.__name__, item))

	def __add__(self, other):
		return self.value + other

	def __contains__(self, other):
		return other in self.value

	def __hash__(self): # pragma: no cover
		"""
		Use id as identifier for hash
		"""
		return id(self)

	def __eq__(self, other): # pragma: no cover
		return self.value == other

	def __ne__(self, other):
		return not self.__eq__(other)

def _textwrap(text, width = 70, **kwargs):
	width -= 2 # for ending ' \'
	# keep the indentation
	# '  - hello world' =>
	# '  - hello \'
	# '    world'
	# '  1. hello world' =>
	# '  1. hello \'
	# '     world'
	match = re.match(r'\s*(?:[-*#]|\w{1,2}\.)?\s+', text)
	prefix = ' ' * len(match.group(0)) if match else ''

	kwargs['subsequent_indent'] = prefix + kwargs.get('subsequent_indent', '')
	wraps = textwrap.wrap(text, width, **kwargs)
	return [line + ' \\' if i < len(wraps) - 1 else line
			for i, line in enumerate(wraps)]

class HelpAssembler:
	"""A helper class to help assembling the help information page."""
	def __init__(self, prog = None, theme = 'default'):
		"""
		Constructor
		@params:
			`prog`: The program name
			`theme`: The theme. Could be a name of `THEMES`, or a dict of a custom theme.
		"""
		self.progname = prog or path.basename(sys.argv[0])
		self.theme    = THEMES['default'].copy()
		if theme != 'default':
			self.theme.update(theme if isinstance(theme, dict) else THEMES[theme])

	def error(self, msg, with_prefix = True):
		"""
		Render an error message
		@params:
			`msg`: The error message
		"""
		msg = msg.replace('{prog}', self.prog(self.progname))
		return '{colorstart}{prefix}{msg}{colorend}'.format(
			colorstart = self.theme['error'],
			prefix     = 'Error: ' if with_prefix else '',
			msg        = msg,
			colorend   = colorama.Style.RESET_ALL
		)

	def warning(self, msg, with_prefix = True):
		"""
		Render an warning message
		@params:
			`msg`: The warning message
		"""
		msg = msg.replace('{prog}', self.prog(self.progname))
		return '{colorstart}{prefix}{msg}{colorend}'.format(
			colorstart = self.theme['warning'],
			prefix     = 'Warning: ' if with_prefix else '',
			msg        = msg,
			colorend   = colorama.Style.RESET_ALL
		)

	warn = warning

	def title(self, msg, with_colon = True):
		"""
		Render an section title
		@params:
			`msg`: The section title
		"""
		return '{colorstart}{msg}{colorend}{colon}'.format(
			colorstart = self.theme['title'],
			msg        = msg.capitalize(),
			colorend   = colorama.Style.RESET_ALL,
			colon      = ':' if with_colon else ''
		)

	def prog(self, prog = None):
		"""
		Render the program name
		@params:
			`msg`: The program name
		"""
		if prog is None:
			prog = self.progname
		return '{colorstart}{prog}{colorend}'.format(
			colorstart = self.theme['prog'],
			prog       = prog,
			colorend   = colorama.Style.RESET_ALL
		)

	def plain(self, msg):
		"""
		Render a plain message
		@params:
			`msg`: the message
		"""
		return msg.replace('{prog}', self.prog(self.progname))

	def optname(self, msg, prefix = '  '):
		"""
		Render the option name
		@params:
			`msg`: The option name
		"""
		return '{colorstart}{prefix}{msg}{colorend}'.format(
			colorstart = self.theme['optname'],
			prefix     = prefix,
			msg        = msg,
			colorend   = colorama.Style.RESET_ALL
		)

	def opttype(self, msg):
		"""
		Render the option type or placeholder
		@params:
			`msg`: the option type or placeholder
		"""
		trimmedmsg = msg.rstrip().upper()
		if not trimmedmsg:
			return msg
		return '{colorstart}{msg}{colorend}'.format(
			colorstart = self.theme['opttype'],
			msg        = trimmedmsg,
			colorend   = colorama.Style.RESET_ALL
		) + ' ' * (len(msg) - len(trimmedmsg))

	@staticmethod
	def defaultIndex(msg, defaults = 'DEFAULT: ,Default: ,default: '):
		"""Try to find the index of the default indicator"""
		if not isinstance(defaults, list):
			defaults = defaults.split(',')
		for deft in defaults:
			dindex = msg.rfind(deft)
			if dindex != -1:
				return dindex
		return -1

	def optdesc(self, msg, first = False, alldefault = False):
		"""
		Render the option descriptions
		@params:
			`msg`: the option descriptions
			`alldefault`: If the whole msg is part of default
		"""
		msg = msg.replace('{prog}', self.prog(self.progname))
		if alldefault:
			return '{prefix}{colorstart}{msg}{colorend}'.format(
				prefix     = '- ' if first else '  ',
				colorstart = self.theme['default'],
				msg        = msg,
				colorend   = colorama.Style.RESET_ALL
			)

		default_index = HelpAssembler.defaultIndex(msg)

		if default_index != -1:
			defaults = '{colorstart}{defaults}{colorend}'.format(
				colorstart = self.theme['default'],
				defaults   = msg[default_index:],
				colorend   = colorama.Style.RESET_ALL
			)
			msg = msg[:default_index] + defaults

		return '{prefix}{colorstart}{msg}{colorend}'.format(
			prefix     = '- ' if first else '  ',
			colorstart = self.theme['optdesc'],
			msg        = msg,
			colorend   = colorama.Style.RESET_ALL
		)

	def assemble(self, helps):
		"""
		Assemble the whole help page.
		@params:
			`helps`: The help items. A list with plain strings or tuples of 3 elements, which
				will be treated as option name, option type/placeholder and option descriptions.
			`progname`: The program name used to replace '{prog}' with.
		@returns:
			lines (`list`) of the help information.
		"""
		ret = []
		maxoptwidth = helps.maxOptNameWidth

		for title, helpitems in helps.items():
			if not helpitems:
				continue
			ret.append(self.title(title))

			if isinstance(helpitems, HelpOptions):
				for optname, opttype, optdescs in helpitems:
					descs = sum((_textwrap(desc, MAX_PAGE_WIDTH - maxoptwidth)
								if not desc.endswith(' \\') else [desc]
								for desc in optdescs), [])
					if descs:
						descs[-1] = descs[-1].rstrip(' \\')
					optlen = len(optname + opttype) + MIN_OPTDESC_LEADING + 3
					if optlen > MAX_OPT_WIDTH:
						ret.append(
							self.optname(optname, prefix = '  ') + ' ' + self.opttype(opttype))
						if descs:
							ret.append(' ' * maxoptwidth + self.optdesc(descs[0], True))
					else:
						to_append = self.optname(optname, prefix = '  ') + ' ' + \
									self.opttype(opttype.ljust(maxoptwidth - len(optname) - 3))
						if descs:
							to_append += self.optdesc(descs[0], True)
						ret.append(to_append)
					if descs:
						desc0 = descs.pop(0)
						default_index = HelpAssembler.defaultIndex(desc0)
						ends = desc0.endswith(' \\')
					for desc in descs:
						if default_index != -1 and ends:
							ret.append(' ' * maxoptwidth + self.optdesc(desc, alldefault = True))
						else:
							ret.append(' ' * maxoptwidth + self.optdesc(desc))
							default_index = HelpAssembler.defaultIndex(desc)
							ends = desc.endswith(' \\')
				ret.append('')
			else: # HelpItems
				for item in helpitems:
					if item.endswith(' \\'):
						ret.append('  ' + self.plain(item))
					else:
						ret.extend(self.plain(it) for it in _textwrap('  ' + item, MAX_PAGE_WIDTH))
				ret.append('')

		ret.append('')
		return ret

class Param(_Valuable):
	"""
	The class for a single parameter
	"""
	def __init__(self, name, value = OPT_UNSET_VALUE):
		"""
		Constructor
		@params:
			`name`:  The name of the parameter
			`value`: The initial value of the parameter
		"""
		self._value, self._type = Param._typeFromValue(value)

		self._desc     = []
		self._required = False
		self.show      = True
		self.name      = name
		self.default   = self._value
		self.stacks    = []
		self.callback  = None
		# should I raise an error if the parameters are locked?
		self._shouldRaise = False

		# We cannot change name later on
		if not isinstance(name, str):
			raise ParamNameError(name, 'Not a string')
		if not re.search(r'^[A-Za-z0-9_,\-.]{1,255}$', name):
			raise ParamNameError(name,
				'Expect a string with comma, alphabetics ' +
				'and/or underlines in length 1~255, but we got')

	@staticmethod
	def _typeFromValue(value):
		typename = type(value).__name__
		if isinstance(value, (tuple, set)):
			typename = 'list'
			value = list(value)
		# dict could have a lot of subclasses
		elif isinstance(value, (Param, dict)):
			typename = 'dict'
		elif value != OPT_UNSET_VALUE:
			if typename not in OPT_ALLOWED_TYPES:
				raise ParamTypeError('Type not allowed: %r' % typename)
		else:
			typename = 'auto'
			value    = None
		return value, Param._normalizeType(typename)

	@staticmethod
	def _normalizeType(typename):
		if typename is None:
			return None
		if not isinstance(typename, str):
			typename = typename.__name__
		type1, type2 = (typename.rstrip(':') + ':').split(':')[:2]
		type1 = OPT_TYPE_MAPPINGS.get(type1, type1)
		type2 = OPT_TYPE_MAPPINGS.get(type2, type2)
		if type1 == 'reset' and type2:
			raise ParamTypeError("Subtype not allowed for 'reset'")
		if type1 == 'dict' and type2 and type2 != 'reset':
			raise ParamTypeError("Only allowed subtype 'reset' for 'dict'")
		if type2 == 'list' and type1 != 'list':
			raise ParamTypeError("Subtype 'list' of only allow for 'list'")
		if type2 and type1 not in ('list', 'dict'):
			raise ParamTypeError('Subtype %r is only allowed for list and dict' % type2)
		# make sure split returns 2 elements, even if type2 == ''
		return '%s:%s' % (type1, type2)

	@staticmethod
	def _dictUpdate(dorig, dup):
		for key, val in dup.items():
			if isinstance(val, dict):
				dorig[key] = Param._dictUpdate(dorig.get(key, {}), val)
			else:
				dorig[key] = val
		return dorig

	# this will set to None if __eq__ is overwritten
	def __hash__(self):
		"""
		Use id as identifier for hash
		"""
		return id(self)

	def __eq__(self, other):
		if isinstance(other, Param):
			return self.value == other.value and (
				not self.type or not other.type or self.type == other.type)
		return self.value == other

	def push(self, value = OPT_UNSET_VALUE, typename = None):
		"""
		Push the value to the stack.
		"""
		# nothing to do, no self.type, no typename and no value
		if typename is None and value == OPT_UNSET_VALUE and self.type == 'auto:':
			return

		# push an item forcely using previous type
		# in case the option is give by '-a 1' without any type specification
		# if no type specified, deduct from the value
		# otherwise auto
		origtype = self.stacks[-1][0] if self.stacks else self.type

		if typename is True:
			typename = origtype
		# if typename is give, push a tuple anyway unless
		# type1 == 'list:' and type2 != 'reset'
		# type1 == 'dict:' and type2 != 'reset'
		if typename:
			# normalize type and get primary and secondary type
			typename = Param._normalizeType(typename)
			type1, type2 = typename.split(':')

			# no values pushed yet, push one anyway
			if not self.stacks:
				# try to push [[]] if typename is 'list:list' or
				# typename is 'reset' and self.type is list:list
				if typename == 'list:list':
					if origtype == typename and self.value and self.value[0]:
						# we don't need to forceType because list:list can't be deducted from value
						self.stacks.append((typename, self.value[:] + [[]]))
					else:
						self.stacks.append((typename, [[]]))
				elif type1 == 'reset':
					if origtype == 'list:list':
						self.stacks.append((origtype, [[]]))
					else:
						self.stacks.append((origtype, []))
				elif type2 == 'reset':
					self.stacks.append((type1 + ':', []))
				elif type1 == 'list':
					if origtype == typename:
						self.stacks.append((typename, (self.value or [])[:]))
					else:
						self.stacks.append((typename, []))
				elif type1 == 'dict':
					if origtype == typename:
						self.stacks.append((typename, [(self.value or {}).copy()]))
					else:
						self.stacks.append((typename, []))
				else:
					self.stacks.append((typename, []))
			elif type2 == 'reset':
				# no warnings, reset is intended
				self.stacks[-1] = (origtype, [])
			elif type1 == 'reset':
				if origtype == 'list:list':
					# no warnings, reset is intended
					self.stacks = [(origtype, [[]])]
				else:
					self.stacks = [(origtype, [])]
			elif type2 == 'list':
				if origtype == 'list:list':
					self.stacks[-1][-1].append([])
				else:
					self.stacks.append((typename, [[]]))
			elif type1 not in ('list', 'dict'):
				self.stacks.append((typename, []))
			elif type1 == 'list' and origtype != typename and not self.stacks[-1][-1]:
				# previous is reset
				self.stacks[-1] = (typename, [])

			# since container has been created
			self.push(value)
		else:
			if not self.stacks:
				self.push(value, typename = True)
			elif value != OPT_UNSET_VALUE:
				type2 = origtype.split(':')[1]
				prevalue = self.stacks[-1][-1][-1] if type2 == 'list' else self.stacks[-1][-1]
				prevalue.append(value)

	def checkout(self):
		"""Checkout the types and values in stack"""
		# use self._value = value instead of self.value = value
		# don't update default
		if not self.stacks:
			return []

		typename, value = self.stacks.pop(-1)
		warns = ['Previous settings (type=%r, value=%r) were ignored for option %r' % (
				 wtype, wval, self.name) for wtype, wval in self.stacks]
		self.stacks = []

		type1, type2 = typename.split(':')
		self._type = typename
		if type2 == 'list':
			self._value = value
		elif type1 == 'list':
			self._value = Param._forceType(value, typename)
		elif type1 in ('bool', 'auto') and not value:
			self._value = True
		elif type1 == 'dict':
			if not value:
				self._value = {}
			else:
				val0 = value.pop(0)
				if isinstance(val0, Param):
					val0 = val0.dict()
				for val in value:
					if isinstance(val, Param):
						val = val.dict()
					val0 = Param._dictUpdate(val0, val)
				self._value = val0
		else:
			if type1 == 'verbose' and not value:
				value.append(1)
			self._value = Param._forceType(value.pop(0), typename, self.name)
			for val in value:
				warns.append('Later value %r was ignored for option %r (type=%r)' % (
					val, self.name, typename))

		return warns

	@property
	def value(self):
		"""Get the value of the parameter"""
		return self._value

	@value.setter
	def value(self, value):
		if self._shouldRaise:
			raise ParamNameError("Try to change a hiden parameter in locked parameters.")
		self._value = value
		self.default = value

	@property
	def desc(self):
		"""Return the description of a param"""
		# try to add default value information in desc
		self._desc = self._desc or []
		if not self._desc:
			self._desc.append('')
		self._desc[-1] = self._desc[-1].rstrip()
		#  add default only if
		# 1. not self.required
		# 2. self.required and self.value is not None
		# 3. default not in self._desc[-1]
		if not ('DEFAULT: ' in self._desc[-1] or 'Default: ' in self._desc[-1] or (
			self.required and self.default is None)):
			if len(self._desc[-1]) > 20:
				self._desc.append('Default: %r' % self.default)
			else:
				self._desc[-1] = self._desc[-1] and self._desc[-1] + ' '
				self._desc[-1] = self._desc[-1] + 'Default: %r' % self.default

		if len(self._desc) == 1 and not self._desc[-1]:
			self._desc[-1] = '[No description]'
		return self._desc

	@desc.setter
	def desc(self, desc):
		if self._shouldRaise:
			raise ParamNameError("Try to change a hiden parameter in locked parameters.")
		assert isinstance(desc, (list, str))
		self._desc = desc if isinstance(desc, list) else desc.splitlines()

	@property
	def required(self):
		"""Return if the param is required"""
		return self._required

	@required.setter
	def required(self, req):
		if self._shouldRaise:
			raise ParamNameError("Try to change a hiden parameter in locked parameters.")
		if self.type == 'bool:':
			raise ParamTypeError(
				self.value, 'Bool option %r cannot be set as required' % self.name)
		# try remove default: in desc if self.value is None
		if self._desc and self._desc[-1].endswith('Default: None'):
			self._desc[-1] = self._desc[-1][:-13].rstrip()
		self._required = req

	@property
	def type(self):
		"""Return the type of the param"""
		return self._type

	@type.setter
	def type(self, typename):
		if self._shouldRaise:
			raise ParamNameError("Try to change a hiden parameter in locked parameters.")
		self.setType(typename, True)

	@staticmethod
	def _forceType(value, typename, name = None):
		if not typename:
			return value
		type1, type2 = typename.split(':')
		try:
			if type1 in ('int', 'float', 'str'):
				if value is None:
					return None
				return getattr(builtins, type1)(value)

			if type1 == 'verbose':
				if value is None:
					return 0
				if value == '':
					return 1
				if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
					return int(value)
				if isinstance(value, str) and value.count(name) == len(value):
					return len(value) + 1
				raise ParamTypeError('Unable to coerce value %r to verbose (int)' % value)

			if type1 == 'bool':
				if value in OPT_BOOL_TRUES:
					return True
				if value in OPT_BOOL_FALSES:
					return False
				raise ParamTypeError('Unable to coerce value %r to bool' % value)

			if type1 == 'NoneType':
				if not value in OPT_NONES:
					raise ParamTypeError('Unexpected value %r for NoneType' % value)
				return None

			if type1 == 'py':
				if value is None:
					return None
				value = value[3:] if value.startswith('py:') else \
						value[5:] if value.startswith('repr:') else value
				return ast.literal_eval(value)

			if type1 == 'dict':
				if value is None:
					return None
				if not isinstance(value, dict):
					if not value:
						value = {}
					try:
						value = dict(value)
					except TypeError:
						raise ParamTypeError('Cannot coerce %r to dict.' % value)
				return OrderedDict(value.items())

			if type1 == 'auto':
				try:
					if re.match(OPT_NONE_PATTERN, value):
						typename = 'NoneType'
					elif re.match(OPT_INT_PATTERN, value):
						typename = 'int'
					elif re.match(OPT_FLOAT_PATTERN, value):
						typename = 'float'
					elif re.match(OPT_BOOL_PATTERN, value):
						typename = 'bool'
					elif re.match(OPT_PY_PATTERN, value):
						typename = 'py'
					else:
						typename = 'str'
					return Param._forceType(value, Param._normalizeType(typename))
				except TypeError: # value is not a string, cannot do re.match
					return value

			if type1 == 'list':
				if value is None:
					return None
				type2 = type2 or 'auto'
				if isinstance(value, str):
					value = [value]
				try:
					value = list(value)
				except TypeError:
					value = [value]
				if type2 == 'reset':
					return value
				if type2 == 'list':
					return value if value and isinstance(value[0], list) else [value]
				type2 = Param._normalizeType(type2)
				return [Param._forceType(x, type2) for x in value]

			raise TypeError
		except (ValueError, TypeError):
			raise ParamTypeError('Unable to coerce value %r to type %r' % (value, typename))

	def dict(self):
		"""
		Return the value in dict format
		There must be dot('.') in the name
		The first part will be ignored
		params a.b.c with value 1 will be converted into
		{"b": {"c": 1}}
		"""
		if '.' not in self.name:
			raise ParamTypeError(
				'Unable to convert param into dict without dot in name: %r' % self.name)
		ret0 = ret = {}
		parts = self.name.split('.')
		for part in parts[1:-1]:
			ret[part] = {}
			ret = ret[part]
		ret[parts[-1]] = self.value
		return ret0

	def __repr__(self):
		typename = self.type or ''
		return '<Param(name={!r},value={!r},type={!r},required={!r},show={!r}) @ {}>'.format(
			self.name, self.value, typename.rstrip(':'), self.required, self.show, hex(id(self)))

	def setDesc (self, desc):
		"""
		Set the description of the parameter
		@params:
			`desc`: The description
		"""
		self.desc = desc
		return self

	def setRequired (self, req = True):
		"""
		Set whether this parameter is required
		@params:
			`req`: True if required else False. Default: True
		"""
		self.required = req
		return self

	def setType (self, typename, update_value = True):
		"""
		Set the type of the parameter
		@params:
			`typename`: The type of the value. Default: str
			- Note: str rather then 'str'
		"""
		if not isinstance(typename, str):
			typename = typename.__name__
		self._type = Param._normalizeType(typename)
		# verbose type can only have name with length 1
		if self._type == 'verbose:' and len(self.name) != 1:
			raise ParamTypeError("Option with type 'verbose' can only have name with length 1.")
		if update_value:
			self._value = Param._forceType(self.value, self._type)
		return self

	def setCallback(self, callback):
		"""
		Set callback
		@params:
			`callback`: The callback
		"""
		if self._shouldRaise:
			raise ParamNameError("Try to change a hiden parameter in locked parameters.")
		if callback and not callable(callback):
			raise TypeError('Callback is not callable.')
		self.callback = callback
		return self

	def setShow (self, show = True):
		"""
		Set whether this parameter should be shown in help information
		@params:
			`show`: True if it shows else False. Default: True
		"""
		self.show = show
		return self

	def setValue(self, value, update_type = False):
		"""
		Set the value of the parameter.
		Note default value will be not updated
		@params:
			`val`: The value
		"""
		if update_type:
			self._value, self._type = Param._typeFromValue(value)
		else:
			self._value = value
		return self

class Params(_Hashable):
	"""
	A set of parameters
	"""

	def __init__(self, command = None, theme = 'default'):
		"""
		Constructor
		@params:
			`command`: The sub-command
			`theme`: The theme
		"""
		prog = path.basename(sys.argv[0])
		prog = prog + ' ' + command if command else prog
		self.__dict__['_props'] = dict(
			prog      = prog,
			usage     = [],
			desc      = [],
			hopts     = ['h', 'help', 'H'],
			prefix    = 'auto',
			hbald     = True,
			assembler = HelpAssembler(prog, theme),
			helpx     = None,
			locked    = False
		)
		self.__dict__['_params']    = OrderedDict()
		self._setHopts(self._hopts)

	def __setattr__(self, name, value):
		"""
		Change the value of an existing `Param` or create a `Param`
		using the `name` and `value`. If `name` is an attribute, return its value.
		@params:
			`name` : The name of the Param
			`value`: The value of the Param
		"""
		if name.startswith('__') or name.startswith('_' + self.__class__.__name__):
			super(Params, self).__setattr__(name, value)
		elif isinstance(value, Param): # set alias
			if value.type == 'verbose:' and len(name) == 1:
				raise ParamNameError('Cannot alias verbose option to a short option')
			self._params[name] = value
		elif name in self._params:
			if self._locked:
				raise ParamNameError(
					'Parameters are locked and parameter {0!r} exists. '
					'To change the value of an existing parameter, '
					'use \'params.{0}.value = xxx\''.format(name))
			self._params[name].value = value
		elif name in ('_assembler', '_helpx', '_prog', '_locked'):
			self._props[name[1:]] = value
		elif name in ['_' + key for key in self._props.keys()] + ['_theme']:
			getattr(self, '_set' + name[1:].capitalize())(value)
		else:
			self._params[name] = Param(name, value)

	def __getattr__(self, name):
		"""
		Get a `Param` instance if possible, otherwise return an attribute value
		@params:
			`name`: The name of the `Param` or the attribute
		@returns:
			A `Param` instance if `name` exists in `self._params`, otherwise,
			the value of the attribute `name`
		"""
		if name.startswith('__') or name.startswith('_' + self.__class__.__name__):
			return getattr(super(Params, self), name)
		if name in ('_' + key for key in self._props.keys()):
			return self._props[name[1:]]
		if name not in self._params:
			self._params[name] = Param(name)
		elif self._locked and not self._params[name].show:
			self._params[name]._shouldRaise = True
		return self._params[name]

	__getitem__ = __getattr__
	__setitem__ = __setattr__

	def _setTheme(self, theme):
		"""
		Set the theme
		@params:
			`theme`: The theme
		"""
		self._props['assembler'] = HelpAssembler(self._prog, theme)
		return self

	def _setUsage(self, usage):
		"""
		Set the usage
		@params:
			`usage`: The usage
		"""
		assert isinstance(usage, (list, str))
		self._props['usage'] = usage if isinstance(usage, list) else usage.splitlines()
		return self

	def _setDesc(self, desc):
		"""
		Set the description
		@params:
			`desc`: The description
		"""
		assert isinstance(desc, (list, str))
		self._props['desc'] = desc if isinstance(desc, list) else desc.splitlines()
		return self

	def _setHopts(self, hopts):
		"""
		Set the help options
		@params:
			`hopts`: The help options
		"""
		if hopts is None:
			raise ValueError('No option specified for help.')
		assert isinstance(hopts, (list, str))
		# remove all previous help options
		for hopt in self._hopts:
			if hopt in self._params:
				del self._params[hopt]

		self._props['hopts'] = hopts if isinstance(hopts, list) else \
			[ho.strip() for ho in hopts.split(',')]
		if any('.' in hopt for hopt in self._hopts):
			raise ValueError('No dot allowed in help option name.')

		if self._hopts:
			self[self._hopts[0]] = False
			self[self._hopts[0]].desc = 'Show help message and exit.'
			for hopt in self._hopts[1:]:
				self[hopt] = self[self._hopts[0]]
		return self

	def _setPrefix(self, prefix):
		"""
		Set the option prefix
		@params:
			`prefix`: The prefix
		"""
		if prefix not in ('-', '--', 'auto'):
			raise ParamsParseError('Prefix should be one of -, -- and auto.')
		self._props['prefix'] = prefix
		return self

	def _prefixit(self, name):
		if self._prefix == 'auto':
			return '-' + name if len(name.split('.')[0]) <= 1 else '--' + name
		return self._prefix + name

	def __contains__(self, name):
		return name in self._params

	def _setHbald(self, hbald = True):
		"""
		Set if we should show help information if no arguments passed.
		@params:
			`hbald`: The flag. show if True else hide. Default: `True`
		"""
		self._props['hbald'] = hbald
		return self

	def __repr__(self):
		return '<Params({}) @ {}>'.format(','.join(
			'{name}:{p.value!r}'.format(name = key, p = param)
			for key, param in self._params.items()
		), hex(id(self)))

	def _allFlags(self, optname):
		"""See if it all flag option in the option name"""
		optnames = list(optname)
		# flags should not be repeated
		if len(optnames) != len(set(optnames)):
			return False
		for opt in optnames:
			if opt not in self._params or self._params[opt].type != 'bool:':
				return False
		return True

	def _preParseOptionCandidate(self, arg, parsed, pendings, lastopt):
		# --abc.x:list
		# abc.x:list
		argnoprefix = arg.lstrip('-')
		# abc
		argoptname  = re.split(r'[.:=]', argnoprefix)[0]
		# False
		argshort    = len(argoptname) <= 1
		# --
		argprefix   = arg[:-len(argnoprefix)] if argnoprefix else arg

		# impossible an option
		# ---a
		# self.prefix == '-'    : --abc
		# self.prefix == '--'   : -abc
		# self.prefix == 'auto' : --a
		if len(argprefix) > 2 or \
			(self._prefix == '-' and argprefix == '--') or \
			(self._prefix == '--' and argprefix == '-') or \
			(self._prefix == 'auto' and argprefix == '--' and argshort):
			return self._preParseValueCandidate(arg, parsed, pendings, lastopt)

		# if a, b and c are defined as bool types, then it should be parsed as
		#  {'a': True, 'b': True, 'c': True} like '-a -b -c'
		#	# in the case '-abc' with self._prefix == '-'
		#	# 'abc' is not defined
		if (self._prefix in ('auto', '-') and argprefix == '-' and len(argoptname) > 1) \
			and (self._prefix != '-' or argoptname not in self._params) \
			and '=' not in argnoprefix:
			# -abc:bool
			if (':' not in argnoprefix or argnoprefix.endswith(':bool')) \
				and self._allFlags(argoptname):
				for opt in list(argoptname):
					parsed[opt] = self._params[opt]
					parsed[opt].push(True, 'bool:')
				return None
			# see if -abc can be parsed as '-a bc'
			# -a. will also be parsed as '-a .' if a is not defined as dict
			#   otherwise it will be parsed as {'a': {'': ...}}
			# -a1:int is also allowed
			if argoptname[0] in self._params \
				and (argoptname[1] != '.' or self._params[argoptname[0]].type != 'dict:'):
				argname = argoptname[0]
				argval  = argoptname[1:]
				argtype = argnoprefix.split(':', 1)[1] if ':' in argnoprefix else True
				parsed[argname] = self._params[argname]
				parsed[argname].push(argval, argtype)
				return None

			if self._prefix == 'auto' and argprefix == '-' and len(argoptname) > 1:
				return self._preParseValueCandidate(arg, parsed, pendings, lastopt)

		matches = re.match(OPT_PATTERN, argnoprefix)
		if not matches:
			return self._preParseValueCandidate(arg, parsed, pendings, lastopt)
		argname = matches.group(1) or OPT_POSITIONAL_NAME
		argtype = matches.group(2)
		argval  = matches.group(3) or OPT_UNSET_VALUE

		if argname not in parsed:
			lastopt = parsed[argname] = self._params[argname] \
				if argname in self._params else Param(argname, []) \
				if argname == OPT_POSITIONAL_NAME and not argtype else Param(argname)

		lastopt = parsed[argname]
		lastopt.push(argval, argtype or True)

		if '.' in argname:
			doptname = argname.split('.')[0]
			if doptname in parsed:
				dictopt = parsed[doptname]
			else:
				dictopt = self._params[doptname] \
					if doptname in self._params else Param(doptname, {})
				parsed[doptname] = dictopt
			dictopt.push(lastopt, 'dict:')
		return lastopt

	def _preParseValueCandidate(self, arg, parsed, pendings, lastopt):
		if lastopt:
			lastopt.push(arg)
		else:
			pendings.append(arg)
		return lastopt

	def _preParse(self, args):
		"""
		Parse the arguments from command line
		Don't coerce the types and values yet.
		"""
		parsed   = OrderedDict()
		pendings = []
		lastopt  = None

		for arg in args:
			lastopt = self._preParseOptionCandidate(arg, parsed, pendings, lastopt) \
				if arg.startswith('-') \
				else self._preParseValueCandidate(arg, parsed, pendings, lastopt)
		# no options detected at all
		# all pendings will be used as positional
		if lastopt is None and pendings:
			if OPT_POSITIONAL_NAME not in parsed:
				parsed[OPT_POSITIONAL_NAME] = self._params[OPT_POSITIONAL_NAME] \
					if OPT_POSITIONAL_NAME in self._params else Param(OPT_POSITIONAL_NAME, [])
			for pend in pendings:
				parsed[OPT_POSITIONAL_NAME].push(pend)
			pendings = []
		elif lastopt is not None:
			# lastopt is not list, so use the values pushed as positional
			posvalues = []
			if not lastopt.stacks or lastopt.stacks[-1][0].startswith('list:') or \
				len(lastopt.stacks[-1][1]) < 2:
				posvalues = []
			elif lastopt.stacks[-1][0] == 'bool:' and lastopt.stacks[-1][1] \
				and not re.match(OPT_BOOL_PATTERN, lastopt.stacks[-1][1][0]):
				posvalues = lastopt.stacks[-1][1]
				lastopt.stacks[-1] = (lastopt.stacks[-1][0], [])
			else:
				posvalues = lastopt.stacks[-1][1][1:]
				lastopt.stacks[-1] = (lastopt.stacks[-1][0], lastopt.stacks[-1][1][:1])

			# is it necessary to create positional? or it exists
			# or it is already there
			# if it is already there, that means tailing values should not be added to positional

			if OPT_POSITIONAL_NAME in parsed or not posvalues:
				pendings.extend(posvalues)
				return parsed, pendings

			parsed[OPT_POSITIONAL_NAME] = self._params[OPT_POSITIONAL_NAME] \
				if OPT_POSITIONAL_NAME in self._params else Param(OPT_POSITIONAL_NAME, [])
			for posval in posvalues:
				parsed[OPT_POSITIONAL_NAME].push(posval)
		return parsed, pendings

	def _parse(self, args = None, arbi = False, dict_wrapper = builtins.dict, raise_exc = False):
		# verbose option is not allowed for prefix '--'
		if self._prefix == '--':
			for param in self._params.values():
				if param.type == 'verbose:':
					raise ParamTypeError(
						"Verbose option %r is not allow with prefix '--'" % param.name)

		args = sys.argv[1:] if args is None else args
		try:
			if not args and self._hbald and not arbi:
				raise ParamsParseError('__help__')
			parsed, pendings = self._preParse(args)

			warns  = ['Unrecognized value: %r' % pend for pend in pendings]
			# check out dict options first
			for name, param in parsed.items():
				if '.' in name:
					warns.extend(param.checkout())
			for name, param in parsed.items():
				if '.' in name:
					continue
				if name in self._hopts:
					raise ParamsParseError('__help__')
				elif name in self._params:
					pass
				elif arbi:
					self._params[name] = param
				elif name != OPT_POSITIONAL_NAME:
					warns.append('Unrecognized option: %r' % self._prefixit(name))
					continue
				else:
					warns.append('Unrecognized positional values: %s' % ', '.join(
						repr(val) for val in param.stacks[-1][-1]))
					continue

				warns.extend(param.checkout())

			# apply callbacks
			for name, param in self._params.items():
				if not callable(param.callback):
					continue
				try:
					ret = param.callback(param)
				except TypeError as ex: # wrong # arguments
					if 'missing' not in str(ex) and 'argument' not in str(ex):
						raise
					ret = param.callback(param, self)
				if ret is True or ret is None or isinstance(ret, Param):
					continue

				error = 'Callback error.' if ret is False else ret
				raise ParamsParseError('Option %r: %s' % (self._prefixit(name), error))
			# check required
			for name, param in self._params.items():
				if param.required and param.value is None and param.type != 'NoneType:':
					if name == OPT_POSITIONAL_NAME:
						raise ParamsParseError('POSITIONAL option is required.')
					raise ParamsParseError('Option %r is required.' % (self._prefixit(name)))

			for warn in warns[:(MAX_WARNINGS+1)]:
				sys.stderr.write(self._assembler.warning(warn) + '\n')

			return self._asDict(dict_wrapper)
		except ParamsParseError as exc:
			if raise_exc:
				raise
			exc = str(exc)
			if exc == '__help__':
				exc = ''
			self._help(exc, print_and_exit = True)

	@property
	def _helpitems(self):
		# collect aliases
		required_params = {}
		optional_params = {}
		for name, param in self._params.items():
			if not param.show or name in self._hopts + [OPT_POSITIONAL_NAME]:
				continue
			if param.required:
				required_params.setdefault(param, []).append(name)
			else:
				optional_params.setdefault(param, []).append(name)

		# positional option
		pos_option = None
		if OPT_POSITIONAL_NAME in self._params:
			pos_option = self._params[OPT_POSITIONAL_NAME]

		helps = Helps()
		# DESCRIPTION
		if self._desc:
			helps.add('DESCRIPTION', self._desc)

		# USAGE
		helps.add('USAGE', HelpItems())
		# auto wrap long lines in usage
		# allow 2 {prog}s
		maxusagelen = MAX_PAGE_WIDTH - (len(self._prog.split()[0]) - 6)*2 - 10
		if self._usage:
			helps['USAGE'].add(sum((_textwrap(
				# allow 2 program names with more than 6 chars each in one usage
				# 10 chars for backup.
				usage, maxusagelen, subsequent_indent = '  ')
				for usage in self._props['usage']), []))
		else: # default usage
			defusage = '{prog}'
			for param, names in required_params.items():
				defusage += ' <{} {}>'.format(
					self._prefixit(names[0]),
					(param.type.rstrip(':') or names[0]).upper())
			defusage += ' [OPTIONS]'

			if pos_option:
				defusage += ' POSITIONAL' if pos_option.required else ' [POSITIONAL]'

			defusage = _textwrap(defusage, maxusagelen, subsequent_indent = '  ')
			helps['USAGE'].add(defusage)

		helps.add(REQUIRED_OPT_TITLE, HelpOptions(prefix = self._prefix))
		helps.add(OPTIONAL_OPT_TITLE, HelpOptions(prefix = self._prefix))

		for param, names in required_params.items():
			helps[REQUIRED_OPT_TITLE].addParam(param, names)

		for param, names in optional_params.items():
			helps[OPTIONAL_OPT_TITLE].addParam(param, names)

		helps[OPTIONAL_OPT_TITLE].add(self._params[self._hopts[0]], self._hopts, ishelp = True)

		if pos_option:
			helpsection = helps[REQUIRED_OPT_TITLE] if pos_option.required \
				  else helps[OPTIONAL_OPT_TITLE]
			if helpsection:
				# leave an empty line for positional
				helpsection.add(('', '', ['']))
			helpsection.addParam(pos_option)

		if callable(self._helpx):
			self._helpx(helps)

		return helps

	def _help (self, error = '', print_and_exit = False):
		"""
		Calculate the help page
		@params:
			`error`: The error message to show before the help information. Default: `''`
			`print_and_exit`: Print the help page and exit the program?
				Default: `False` (return the help information)
		@return:
			The help information
		"""
		assert error or isinstance(error, (list, str))

		ret = []
		if error:
			if isinstance(error, str):
				error = error.splitlines()
			ret = [self._assembler.error(err.strip()) for err in error]

		ret.extend(self._assembler.assemble(self._helpitems))

		if print_and_exit:
			sys.stderr.write('\n'.join(ret))
			sys.exit(1)
		else:
			return '\n'.join(ret)

	def _loadDict (self, dict_var, show = False):
		"""
		Load parameters from a dict
		@params:
			`dict_var`: The dict variable.
			- Properties are set by "<param>.required", "<param>.show", ...
			`show`:    Whether these parameters should be shown in help information
				- Default: False (don'typename show parameter from config object in help page)
				- It'll be overwritten by the `show` property inside dict variable.
				- If it is None, will inherit the param's show value
		"""
		# load the params first
		for key, val in dict_var.items():
			if '.' in key:
				continue
			if not key in self._params:
				self._params[key] = Param(key, val)
			self._params[key].value = val
			if show is not None:
				self._params[key].show = show
		# load the params that is not given a value
		# start with setting an attribute
		for key, val in dict_var.items():
			if '.' not in key or key.endswith('.alias'):
				continue
			key = key.split('.')[0]
			if key in self._params:
				continue
			self[key] = Param(key)
			if show is not None:
				self[key].show = show
		# load aliases
		for key, val in dict_var.items():
			if not key.endswith('.alias'):
				continue
			key = key[:-6]
			if val not in self._params:
				raise ParamsLoadError('Cannot set alias %r to an undefined option %r' % (key, val))
			self[key] = self[val]
		# then load property
		for key, val in dict_var.items():
			if '.' not in key or key.endswith('.alias'):
				continue
			opt, prop = key.split('.', 1)
			if not prop in ('desc', 'required', 'show', 'type', 'value'):
				raise ParamsLoadError('Unknown attribute %r for option %r' % (prop, opt))
			setattr(self[opt], prop, val)
		return self

	def _loadFile (self, cfgfile, profile = False, show = False):
		"""
		Load parameters from a json/config file
		If the file name ends with '.json', `json.load` will be used,
		otherwise, `ConfigParser` will be used.
		For config file other than json, a section name is needed, whatever it is.
		@params:
			`cfgfile`: The config file
			`show`:    Whether these parameters should be shown in help information
				- Default: False (don'typename show parameter from config file in help page)
				- It'll be overwritten by the `show` property inside the config file.
		"""
		config = Config(with_profile = bool(profile))
		config._load(cfgfile)
		if profile:
			config._use(profile)
		return self._loadDict(config, show = show)

	def _asDict (self, wrapper = builtins.dict):
		"""
		Convert the parameters to dict object
		@returns:
			The dict object
		"""
		ret = wrapper()
		for name in self._params:
			ret[name] = self._params[name].value
		return ret

	def _addToCompletions(self, completions, withtype = False, alias = False, showonly = True):
		revparams = OrderedDict()
		for name, param in self._params.items():
			if name in self._hopts or (showonly and not param.show):
				continue
			revparams.setdefault(param, []).append(name)
		for param, names in revparams.items():
			if not alias: # keep the longest one
				names = [list(sorted(names, key = len))[-1]]
			names = ['' if name == OPT_POSITIONAL_NAME else name for name in names]
			if withtype:
				names.extend([name + ':' + param.type.rstrip(':')
					for name in names if param.type and param.type != 'auto'])
			completions.addOption([self._prefixit(name) for name in names],
								  param.desc and param.desc[0] or '')
			if param.type == 'verbose:':
				completions.addOption(['-' + param.name * 2, '-' + param.name * 3],
									  param.desc and param.desc[0] or '')

	def _complete(self, shell, auto = False, withtype = False, alias = False, showonly = True):
		from completions import Completions
		completions = Completions(desc = self._desc and self._desc[0] or '')
		self._addToCompletions(completions, withtype, alias, showonly)

		return completions.generate(shell, auto)

	_dict = _asDict
	_load = _loadDict

class Commands:
	"""
	Support sub-command for command line argument parse.
	"""

	def __init__(self, theme = 'default', prefix = 'auto'):
		"""
		Constructor
		@params:
			`theme`: The theme
		"""
		self.__dict__['_props'] = dict(
			_desc     = [],
			_hcmd     = ['help'],
			cmds      = OrderedDict(),
			inherit   = True,
			assembler = HelpAssembler(None, theme),
			helpx     = None,
			prefix    = prefix
		)
		self._cmds[CMD_GLOBAL_OPTPROXY] = Params(None, theme)
		self._cmds[CMD_GLOBAL_OPTPROXY]._prefix = prefix
		self._cmds[CMD_GLOBAL_OPTPROXY]._hbald  = False

		self._installHelpCommand()

	def _installHelpCommand(self):
		helpcmd = Params(None, self._assembler.theme)
		helpcmd._desc = 'Print help message for the command and exit.'
		helpcmd._hbald = False
		helpcmd[OPT_POSITIONAL_NAME] = ''
		helpcmd[OPT_POSITIONAL_NAME].desc = 'The command.'

		def helpPositionalCommandCallback(param):
			if not param.value or param.value in self._hcmd:
				raise CommandsParseError('__help__')
			if param.value not in self._cmds:
				raise CommandsParseError('No such command: %s' % param.value)
			self._cmds[param.value]._help(print_and_exit = True)
		helpcmd[OPT_POSITIONAL_NAME].callback = helpPositionalCommandCallback
		for hcmd in self._hcmd:
			self._cmds[hcmd] = helpcmd

	def _setInherit(self, inherit):
		self._inherit = inherit

	def _setDesc(self, desc):
		"""
		Set the description
		@params:
			`desc`: The description
		"""
		self._desc = desc
		return self

	def _setHcmd(self, hcmd):
		"""
		Set the help command
		@params:
			`hcmd`: The help command
		"""
		for cmd in self._hcmd:
			if cmd in self._cmds:
				del self._cmds[cmd]

		self._props['_hcmd'] = [cmd.strip() for cmd in hcmd.split(',')] \
			if isinstance(hcmd, str) else hcmd

		self._installHelpCommand()
		return self

	def _setTheme(self, theme):
		"""
		Set the theme
		@params:
			`theme`: The theme
		"""
		self._theme = theme
		return self

	def _setPrefix(self, prefix):
		self._prefix = prefix
		return self

	def __getattr__(self, name):
		"""
		Get the value of the attribute
		@params:
			`name` : The name of the attribute
		@returns:
			The value of the attribute
		"""
		if name.startswith('__') or name.startswith('_' + self.__class__.__name__):
			return getattr(super(Commands, self), name)
		if name in ('_desc', '_hcmd'):
			return self._props[name]
		if name in ('_cmds', '_assembler', '_helpx', '_prefix', '_inherit'):
			return self._props[name[1:]]
		if name not in self._cmds:
			self._cmds[name] = Params(name, self._assembler.theme)
			self._cmds[name]._prefix = self._prefix
		return self._cmds[name]

	def __setattr__(self, name, value):
		"""
		Set the value of the attribute
		@params:
			`name` : The name of the attribute
			`value`: The value of the attribute
		"""
		if name.startswith('__') or name.startswith('_' + self.__class__.__name__):
			super(Commands, self).__setattr__(name, value)
		elif name == '_theme':
			self._assembler = HelpAssembler(None, value)
		elif name == '_hcmd':
			self._setHcmd(value)
		elif name == '_desc':
			self._props['_desc'] = value.splitlines() if isinstance(value, str) else value
		elif name == '_prefix':
			self._props['prefix'] = value
			for cmd in self._cmds.values():
				cmd._prefix = value
		elif name in ('_cmds', '_assembler', '_helpx', '_inherit'):
			self._props[name[1:]] = value
		elif isinstance(value, Params): # alias
			self._cmds[name] = value
			if name != value._prog.split()[-1]:
				value._prog += '|' + name
				value._assembler = HelpAssembler(value._prog, value._assembler.theme)
		else:
			if name not in self._cmds:
				self._cmds[name] = Params(name, self._assembler.theme)
				self._cmds[name]._prefix = self._prefix
			self._cmds[name]._desc = value

	__getitem__ = __getattr__
	__setitem__ = __setattr__

	def _inheritGlobalOptions(self):
		if not self._inherit:
			return

		globalopts = self._cmds[CMD_GLOBAL_OPTPROXY]
		for name, param in globalopts._params.items():
			if name in globalopts._hopts:
				continue
			for cmd, cmdparams in self._cmds.items():
				if cmd == CMD_GLOBAL_OPTPROXY or cmd in self._hcmd:
					continue
				if self._cmds[CMD_GLOBAL_OPTPROXY]._prefix != cmdparams._prefix:
					raise ValueError(
						'Cannot inheirt global options (%s) with inconsistent prefix (%s).' % (
							self._cmds[CMD_GLOBAL_OPTPROXY]._prefix, cmdparams._prefix))

				if name in cmdparams._params and cmdparams[name] is not param:
					raise ParamNameError(
						('Cannot have option %r defined for both global and command %r\n' +
						 'if you let command inherit global options (_inherit = True).') % (
							name, cmd))
				cmdparams[name] = param

	def _parse(self, args = None, arbi = False, dict_wrapper = dict):
		"""
		Parse the arguments.
		@params:
			`args`: The arguments (list). `sys.argv[1:]` will be used if it is `None`.
			`arbi`: Whether do an arbitrary parse.
				If True, options do not need to be defined. Default: `False`
		@returns:
			A `tuple` with first element the subcommand and second the parameters being parsed.
		"""
		# check if inherit is True, then we should also attach global options to commands
		self._inheritGlobalOptions()
		if arbi:
			for hcmd in self._hcmd:
				self._cmds[hcmd][OPT_POSITIONAL_NAME].callback = None

		args = sys.argv[1:] if args is None else args
		# the commands have to be defined even for arbitrary mode
		try:
			if not args:
				raise CommandsParseError('__help__')
			# get which command is hit
			cmdidx  = None
			if arbi:
				# arbitrary mode does not have global options
				cmdidx = 0
				if args[cmdidx] not in self._cmds:
					self._cmds[args[cmdidx]] = Params(args[cmdidx], self._assembler.theme)
					self._cmds[args[cmdidx]]._prefix = self._prefix
			else:
				for i, arg in enumerate(args):
					if arg != CMD_GLOBAL_OPTPROXY and arg in self._cmds:
						cmdidx = i
						break
				else:
					raise CommandsParseError('No command given.')

			command      = args[cmdidx]
			global_args  = args[:cmdidx]
			command_args = args[(cmdidx+1):]

			if (self._inherit and command not in self._hcmd):
				command_opts = self._cmds[command]._parse(
					global_args + command_args, arbi, dict_wrapper)
				global_opts = self._cmds[CMD_GLOBAL_OPTPROXY]._dict(wrapper = dict_wrapper)
			else:
				try:
					global_opts = self._cmds[CMD_GLOBAL_OPTPROXY]._parse(
						global_args, arbi, dict_wrapper, raise_exc = True)
				except ParamsParseError as exc:
					raise CommandsParseError(str(exc))
				command_opts = self._cmds[command]._parse(
					command_args, arbi, dict_wrapper)

			return command, command_opts, global_opts

		except CommandsParseError as exc:
			exc = str(exc)
			if exc == '__help__':
				exc = ''
			self._help(error = exc, print_and_exit = True)

	def _help(self, error = '', print_and_exit = False):
		"""
		Construct the help page
		@params:
			`error`: the error message
			`print_and_exit`: print the help page and exit instead of return the help information
		@returns:
			The help information if `print_and_exit` is `False`
		"""
		helps = Helps()

		if self._desc:
			helps.add('DESCRIPTION', self._desc)

		helps.add('USAGE', '{prog} <command> [OPTIONS]' if self._inherit \
			else '{prog} [GLOBAL OPTIONS] <command> [COMMAND OPTIONS]')

		global_opt_items = self._cmds[CMD_GLOBAL_OPTPROXY]._helpitems
		helps.add('GLOBAL ' + REQUIRED_OPT_TITLE, global_opt_items[REQUIRED_OPT_TITLE])
		helps.add('GLOBAL ' + OPTIONAL_OPT_TITLE, global_opt_items[OPTIONAL_OPT_TITLE])

		helps.add('AVAILABLE COMMANDS', HelpOptions(prefix = ''))

		revcmds = OrderedDict()
		for name, command in self._cmds.items():
			if name == CMD_GLOBAL_OPTPROXY:
				continue
			revcmds.setdefault(command, []).append(name)

		for command, names in revcmds.items():
			if self._hcmd[0] in names:
				continue
			helps['AVAILABLE COMMANDS'].add(command, names)

		command_section = helps['AVAILABLE COMMANDS']
		command_section.addCommand(self._cmds[self._hcmd[0]], self._hcmd)
		command_help_index = command_section.query(self._hcmd[0])
		command_help = command_section[command_help_index]
		command_section[command_help_index] = (
			command_help[0],
			'[COMMAND]',
			command_help[2])

		if callable(self._helpx):
			self._helpx(helps)

		ret = []
		if error:
			if isinstance(error, str):
				error = error.splitlines()
			ret = [self._assembler.error(err.strip()) for err in error]

		ret.extend(self._assembler.assemble(helps))

		if print_and_exit:
			sys.stderr.write('\n'.join(ret))
			sys.exit(1)
		else:
			return '\n'.join(ret)

	def _complete(self, shell, auto = False, inherit = True,
		withtype = False, alias = True, showonly = True):
		from completions import Completions
		completions = Completions(inherit = inherit,
								  desc = self._desc and self._desc[0] or '')
		revcmds = OrderedDict()
		for key, val in self._cmds.items():
			if key == CMD_GLOBAL_OPTPROXY:
				continue
			revcmds.setdefault(val, []).append(key)

		if CMD_GLOBAL_OPTPROXY in self._cmds:
			self._cmds[CMD_GLOBAL_OPTPROXY]._addToCompletions(
				completions, withtype, alias, showonly)

		helpoptions = {
			cmdname: (command._desc and command._desc[0] or '')
			for cmdname, command in self._cmds.items()
			if cmdname not in self._hcmd and cmdname != CMD_GLOBAL_OPTPROXY
		}
		for command, names in revcmds.items():
			if not alias:
				names = [list(sorted(names, key = len))[-1]]
			compdesc = command._desc and command._desc[0] or ''
			for name in names:
				if name in self._hcmd:
					completions.addCommand(name, compdesc, helpoptions)
				else:
					completions.addCommand(name, compdesc)
					command._addToCompletions(
						completions.command(name), withtype, alias, showonly)
		return completions.generate(shell, auto)

# pylint: disable=invalid-name
params   = Params()
commands = Commands()
