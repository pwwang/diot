"""Help stuff for help message"""
import re
from .utils import OrderedDict

class NotAnOptionException(Exception):
	"""Raises while item is not an option"""

def _match(selector, item, regex = False):
	if isinstance(selector, str):
		if regex:
			selector = re.compile(selector, re.IGNORECASE)
		elif len(selector) > 2 and selector[0] == '/' and selector[-1] == '/':
			selector = re.compile(selector[1:-1], re.IGNORECASE)

	if hasattr(selector, 'search'):
		return bool(selector.search(item[0] if isinstance(item, tuple) else item))

	if isinstance(item, tuple):
		items = item[0].split(' | ') if ' | ' in item[0] else item[0].split(', ')
		items = [it.lower() for it in items] + [it.lstrip('-').lower() for it in items]
		return selector.lower() in items
	return selector.lower() in item.lower()

class HelpItems(list):
	"""
	An item of a help message without divisions.
	For example, a line of description, usage or example.
	"""
	def __init__(self, *args):
		super(HelpItems, self).__init__()
		for arg in args:
			self.add(arg)

	def add(self, item):
		"""Add an item. Expected a list, if not will be .splitlines() for str.
		"""
		if not isinstance(item, list):
			item = item.splitlines()
		self.extend(item)
		return self

	def query(self, selector, regex = False):
		"""Get the index of the matched item"""
		for i, item in enumerate(self):
			if _match(selector, item, regex):
				return i
		raise ValueError('No element found by selector: %r' % selector)

	def after(self, selector, item, **kwargs):
		"""Add an item after the item matched selector"""
		index = self.query(selector, kwargs.pop('regex', False)) + 1
		if not isinstance(item, list):
			item = item.splitlines()
		self[index:index] = item
		return self

	def before(self, selector, item, **kwargs):
		"""Add an item before the item matched selector"""
		index = self.query(selector, kwargs.pop('regex', False))
		if not isinstance(item, list):
			item = item.splitlines()
		self[index:index] = item
		return self

	def replace(self, selector, content, **kwargs):
		"""Replace the content of the item matching the selector"""
		index = self.query(selector, kwargs.pop('regex', False))
		self[index] = content
		return self

	def select(self, selector, **kwargs):
		"""Select the content of the item matching the selector"""
		return self[self.query(selector, kwargs.pop('regex', False))]

	def delete(self, selector, **kwargs):
		"""Delete the item matching the selector"""
		del self[self.query(selector, kwargs.pop('regex', False))]
		return self
	remove = delete

class HelpOptionDescriptions(HelpItems):
	"""Option description in help page"""

class HelpOptions(HelpItems):
	"""All options of an option section"""

	def __init__(self, *args, **kwargs):
		self.prefix = kwargs.pop('prefix', 'auto')
		super(HelpOptions, self).__init__()
		options = self._tupleToOption(list(args))
		self.add(options)

	def _prefixName(self, name):
		if name.startswith('-') or not self.prefix:
			return name
		if self.prefix != 'auto':
			return self.prefix + name
		return '-' + name if len(name) <= 1 or name[1] == '.' else '--' + name

	def _tupleToOption(self, item):
		if isinstance(item, list):
			return [self._tupleToOption(it) for it in item]
		if not isinstance(item, tuple) or len(item) != 3:
			raise NotAnOptionException('Expect a 3-element tuple as an option item in help page.')
		if not isinstance(item[2], HelpOptionDescriptions):
			return (item[0], item[1], HelpOptionDescriptions(item[2]))
		return item

	def addParam(self, param, aliases = None, ishelp = False):
		"""Add a param"""
		from . import OPT_POSITIONAL_NAME
		aliases = aliases or []
		aliases.append(param.name)
		aliases = list(set(aliases))
		if param.type == 'verbose:':
			aliases[aliases.index(param.name)] = '-' + '|'.join(
				param.name * (i+1) for i in range(3))
		paramtype = '<VERBOSITY>' if param.type == 'verbose:' and len(aliases) > 1 \
			else '' if ishelp or (param.type == 'verbose:' and len(aliases) == 1) \
			else '[BOOL]' if param.type == 'bool:' \
			else '' if not param.type \
			else '<AUTO>' if param.type == 'NoneType' \
			else '<%s>' % param.type.rstrip(':').upper()
		paramdesc = param.desc[:]
		if ishelp and paramdesc and paramdesc[-1].endswith('Default: False'):
			paramdesc[-1] = paramdesc[-1][:-14].rstrip(' ')
			if not paramdesc[-1]:
				del paramdesc[-1]
		return self.add((
			', '.join(self._prefixName(alias) if alias != OPT_POSITIONAL_NAME else 'POSITIONAL'
				for alias in sorted(aliases, key = lambda alia: (
					0 if '|' in alia else len(alia) , [
					# try to lower case first
					a.lower() + '1' if a.isupper() else a for a in list(alia)]
				) )),
			paramtype, paramdesc))

	def addCommand(self, params, aliases, ishelp = False):
		"""Add a set of params"""
		cmdtype = '[COMMAND]' if ishelp else ''
		return self.add((
			' | '.join(sorted(set(aliases), key = lambda alias: (len(alias), alias))),
			cmdtype,
			params['_desc'] if ishelp else params._desc
		))

	def add(self, item, aliases = None, ishelp = False): # pylint: disable=arguments-differ
		from . import Param, Params
		if isinstance(item, Param):
			self.addParam(item, aliases, ishelp)
		elif isinstance(item, (dict, Params)):
			self.addCommand(item, aliases, ishelp)
		elif isinstance(item, list):
			for it in item:
				self.add(it)
		else:
			self.append(self._tupleToOption(item))
		self.fixMixed()
		return self

	def insert(self, index, item):
		"""Insert an item at index"""
		if isinstance(item, HelpOptions):
			self[index:index] = item
		elif isinstance(item, list):
			self[index:index] = self._tupleToOption(item)
		else:
			self[index:index] = [self._tupleToOption(item)]
		return self

	def after(self, selector, item, **kwargs):
		"""Add an item after the item matched selector"""
		index = self.query(selector, kwargs.pop('regex', False)) + 1
		return self.insert(index, item)

	def before(self, selector, item, **kwargs):
		"""Add an item before the item matched selector"""
		index = self.query(selector, kwargs.pop('regex', False))
		return self.insert(index, item)

	@property
	def isMixed(self):
		"""Tell whether options are mixed with short and long ones
		check only if first option has a short name.
		"""
		firstopts = [item[0] for item in self
			if item[0].startswith('-') and '|' not in item[0]]
		if not firstopts or firstopts[0].startswith('--'):
			return False
		_, mixed = divmod(sum([opt[:2].count('-') for opt in firstopts]), len(firstopts))
		return bool(mixed)

	def fixMixed(self):
		"""
		Fix indention of mixed option names
		For example, fix this:
		  -o, --output <STR>     - The output file.
		  --all [BOOL]           - Run all steps.
		into:
		  -o, --output <STR>     - The output file.
		      --all [BOOL]       - Run all steps.
		"""
		if not self.isMixed:
			return
		for i, item in enumerate(self):
			if not item[0].startswith('--'):
				continue
			#           -a, --
			self[i] = ('    ' + item[0], item[1], item[2])

class Helps(OrderedDict):
	"""All sections of help"""

	def query(self, selector, regex = False):
		"""Get the  key matching the selector"""
		for key in self:
			if _match(selector, key, regex):
				return key
		raise ValueError('No section found by selector: %r\n- Available sections:\n  %s' % (
			selector, '\n  '.join(self.keys())))

	def select(self, selector, regex = False):
		"""Select the selection of the  key matching the selector"""
		return self[self.query(selector, regex = regex)]

	@staticmethod
	def _section(*args, **kwargs):
		if len(args) == 1 and isinstance(args[0], HelpOptions):
			return args[0]
		if len(args) == 1 and isinstance(args[0], HelpItems):
			return args[0]
		sectype = kwargs.pop('sectype', '').lower()
		if sectype == 'option':
			return HelpOptions(*args, **kwargs)
		if sectype in ('item', 'plain'):
			return HelpItems(*args, **kwargs)
		try:
			return HelpOptions(*args, **kwargs)
		except NotAnOptionException:
			return HelpItems(*args, **kwargs)

	def add(self, section, *args, **kwargs):
		"""Add a selection"""
		sectionobj = Helps._section(*args, **kwargs)
		self[section] = sectionobj
		return self

	def before(self, selector, section, *args, **kwargs):
		"""Add a section before one with titile matching selector"""
		key = self.query(selector, kwargs.pop('regex', False))
		sectionobj = Helps._section(*args, **kwargs)
		self.insert_before(key, (section, sectionobj))
		return self

	def after(self, selector, section, *args, **kwargs):
		"""Add a section after one with titile matching selector"""
		key = self.query(selector, kwargs.pop('regex', False))
		sectionobj = Helps._section(*args, **kwargs)
		self.insert_after(key, (section, sectionobj))
		return self

	def delete(self, selector, regex = False):
		"""Delete the section titile matching selector"""
		key = self.query(selector, regex = regex)
		del self[key]
		return self

	remove = delete

	@property
	def maxOptNameWidth(self, min_optdesc_leading = 5, max_opt_width = 36):
		"""Calculate the width of option name and type"""
		ret = 0

		for item in self.values():
			if not item or not isinstance(item, HelpOptions):
				continue

			# 3 = <first 2 spaces: 2> +
			#     <gap between name and type: 1> +
			itemlens = [len(it[0] + it[1]) + min_optdesc_leading + 3
					for it in item
					if len(it[0] + it[1]) + min_optdesc_leading + 3 <= max_opt_width]
			ret = ret if not itemlens else max(ret, max(itemlens))
		return ret or max_opt_width
