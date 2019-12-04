import re
import pytest
from pyparam.help import _match, HelpItems, HelpOptions, HelpOptionDescriptions, Helps, NotAnOptionException
from pyparam import Param, Params

@pytest.mark.parametrize('selector, item, regex, expt', [
	(r'what\d+ever', '1what123ever', True, True),
	(re.compile(r'what\d+ever'), '1what123ever', True, True),
	(r'/what\d+ever/', '1what123ever', False, True),
	(r'what\d+ever', '1whxat123ever', True, False),
	(re.compile(r'what\d+ever'), '1whxat123ever', True, False),
	('what', 'what123ever', False, True),
	('what', 'whxat123ever', False, False),
	(r'-o, --o', ('-o, --output',), True, True),
	(re.compile(r'-o, --o'), ('-o, --output',), True, True),
	(r'-o,\d--o', ('-o, --output',), True, False),
	(re.compile(r'-o,\d--o'), ('-o, --output',), True, False),
	('-o', ('-o, --output',), False, True),
	('output', ('-o, --output',), False, True),
	('-ou', ('-o, --output',), False, False),
])
def test_match(selector, item, regex, expt):
	assert _match(selector, item, regex) is expt

def test_helpitems():

	hi = HelpItems()
	assert hi == []

	hi = HelpItems(["a", "b"])
	assert hi == ["a", "b"]

	hi = HelpItems("a", "b")
	assert hi == ["a", "b"]

	hi = HelpItems("a\nb")
	assert hi == ["a", "b"]

	hi = HelpItems()
	hi.add(["a", "b"])
	assert hi == ["a", "b"]

	hi = HelpItems()
	hi.add("a")
	hi.add("b")
	assert hi == ["a", "b"]

	hi = HelpItems()
	hi.add("a\nb")
	assert hi == ["a", "b"]

@pytest.mark.parametrize("items,selector,regex,expt", [
	(["abc", "a1bc"], "bc", False, 0),
	(["abc", "a1bc"], "1bc", False, 1),
	(["abc", "a1bc"], "1bc", False, 1),
	(["abc", "a1bc"], r"\dbc", True, 1),
])
def test_helpitems_query(items, selector, regex, expt):
	assert HelpItems(items).query(selector, regex) == expt

def test_helpitems_query_exc():
	with pytest.raises(ValueError):
		HelpItems([]).query('')

def test_helpitems_operations():
	hi = HelpItems("abc\ndef\nhij")
	hi.before("def", "ccc")
	assert hi == ["abc", "ccc", "def", "hij"]
	hi.after("cc", "999")
	assert hi == ["abc", "ccc", "999", "def", "hij"]
	hi.replace("cc", "xxxx")
	assert hi == ["abc", "xxxx", "999", "def", "hij"]
	assert hi.select('9') == '999'
	hi.delete('9')
	assert hi == ["abc", "xxxx", "def", "hij"]

def test_helpoptions():
	ho = HelpOptions()
	assert ho == []
	assert ho.prefix == 'auto'

	ho = HelpOptions(('', '', 'a'), ('', '', 'b'), prefix = '-')
	assert ho == [('', '', ['a']), ('', '', ['b'])]
	assert ho.prefix == '-'

@pytest.mark.parametrize("name, prefix,expt", [
	('-a', '', '-a'),
	('a', '', 'a'),
	('a', '-', '-a'),
	('a', 'auto', '-a'),
	('a.b', 'auto', '-a.b'),
	('ab', 'auto', '--ab'),
])
def test_helpoptions_prefixname(name, prefix, expt):
	assert HelpOptions(prefix = prefix)._prefixName(name) == expt

@pytest.mark.parametrize("param, aliases, ishelp, prefix, expt", [
	(Param('v', 0).setType('verbose'),
	 ['verbose'], False, 'auto',
	 [('-v|vv|vvv, --verbose', '<VERBOSITY>', ['Default: 0'])]),
	(Param('v', 0).setType('verbose'),
	 [], False, 'auto',
	 [('-v|vv|vvv', '', ['Default: 0'])]),
	(Param('a', False),
	 ['auto'], False, 'auto',
	 [('-a, --auto', '[BOOL]', ['Default: False'])]),
	(Param('d', 1).setDesc('Whehter to show the description or not.'),
	 ['desc'], False, 'auto',
	 [('-d, --desc', '<INT>', ['Whehter to show the description or not.', 'Default: 1'])]),
	(Param('help', False).setDesc('Show the help message for command.'),
	 [], True, 'auto',
	 [('--help', '', ['Show the help message for command.'])]), # don't show default
])
def test_helpoptions_addparam(param, aliases, ishelp, prefix, expt):
	ho = HelpOptions(prefix = prefix)
	ho.addParam(param, aliases, ishelp)
	assert ho == expt

@pytest.mark.parametrize("params, aliases, ishelp, expt", [
	(Params()._setDesc('Command 1'),
	 ['cmd1'], False,
	 [('cmd1', '', ['Command 1'])]),
	(Params()._setDesc('Print help page and exit'),
	 ['help'], True,
	 [('help', '[COMMAND]', ['Print help page and exit'])]),
])
def test_helpoptions_addcommand(params, aliases, ishelp, expt):
	ho = HelpOptions()
	ho.addCommand(params, aliases, ishelp)
	assert ho == expt

@pytest.mark.parametrize("param, aliases, ishelp, prefix, expt", [
	(Param('v', 0).setType('verbose'),
	 ['verbose'], False, 'auto',
	 [('-v|vv|vvv, --verbose', '<VERBOSITY>', ['Default: 0'])]),
	(Param('a', False),
	 ['auto'], False, 'auto',
	 [('-a, --auto', '[BOOL]', ['Default: False'])]),
	(Param('d', 1).setDesc('Whehter to show the description or not.'),
	 ['desc'], False, 'auto',
	 [('-d, --desc', '<INT>', ['Whehter to show the description or not.', 'Default: 1'])]),
	 (Params()._setDesc('Command 1'),
	 ['cmd1'], False, 'auto',
	 [('cmd1', '', ['Command 1'])]),
	(Params()._setDesc('Print help page and exit'),
	 ['help'], True, 'auto',
	 [('help', '[COMMAND]', ['Print help page and exit'])]),
	(('-option', '<INT>', HelpOptionDescriptions("Description 1", "Description 2")),
	 [], False, 'auto',
	 [('-option', '<INT>', ["Description 1", "Description 2"])])
])
def test_helpoptions_add(param, aliases, ishelp, prefix, expt):
	ho = HelpOptions(prefix = prefix)
	ho.add(param, aliases, ishelp)
	assert ho == expt

def test_helpoptions_ba():
	ho = HelpOptions()
	ho.add(('-option', '<INT>', 'Description'))
	ho.after('-option', ('-option2', '<INT>', 'Description 2'))
	assert ho == [
		('-option', '<INT>', ['Description']),
		('-option2', '<INT>', ['Description 2']),
	]
	ho.before('-option2', ('-option1', '<INT>', 'Description 1'))
	assert ho == [
		('-option', '<INT>', ['Description']),
		('-option1', '<INT>', ['Description 1']),
		('-option2', '<INT>', ['Description 2']),
	]

	ho = HelpOptions()
	options = HelpOptions(
		('-option', '<INT>', ['Description']),
		('-option1', '<INT>', ['Description 1']),
		('-option2', '<INT>', ['Description 2']),
	)
	ho.insert(0, options)
	assert ho == [
		('-option', '<INT>', ['Description']),
		('-option1', '<INT>', ['Description 1']),
		('-option2', '<INT>', ['Description 2']),
	]

	ho = HelpOptions()
	options = [
		('-option', '<INT>', ['Description']),
		('-option1', '<INT>', ['Description 1']),
		('-option2', '<INT>', ['Description 2']),
	]
	ho.insert(0, options)
	assert ho == [
		('-option', '<INT>', ['Description']),
		('-option1', '<INT>', ['Description 1']),
		('-option2', '<INT>', ['Description 2']),
	]

def test_helpoptions_add_exc():
	ho = HelpOptions()
	with pytest.raises(NotAnOptionException):
		ho.add((1,))

@pytest.mark.parametrize("args, kwargs, expt", [
	([HelpOptions()], {}, HelpOptions),
	([HelpItems()], {}, HelpItems),
	(["Hello world"], {}, HelpItems),
	([("-opt", "int", "Hello world")], {}, HelpOptions),
])
def test_helps_section(args, kwargs, expt):
	assert isinstance(Helps._section(*args, **kwargs), expt)

def test_helps_insert():
	helps = Helps()
	helps['A'] = '1'
	helps['B'] = '2'
	helps['C'] = '3'
	helps.after('B', 'B1', '21')
	assert list(helps.items()) == [('A', '1'), ('B', '2'), ('B1', ['21']), ('C', '3')]
	helps.after('C', 'D', '4')
	assert list(helps.items()) == [('A', '1'), ('B', '2'), ('B1', ['21']), ('C', '3'), ('D', ['4'])]
	helps.before('C', 'C0', '30')
	assert list(helps.items()) == [('A', '1'), ('B', '2'), ('B1', ['21']), ('C0', ['30']), ('C', '3'), ('D', ['4'])]
	helps.before('A', '_', '0')
	assert list(helps.items()) == [('_', ['0']), ('A', '1'), ('B', '2'), ('B1', ['21']), ('C0', ['30']), ('C', '3'), ('D', ['4'])]

	helps.remove('_')
	assert list(helps.items()) == [('A', '1'), ('B', '2'), ('B1', ['21']), ('C0', ['30']), ('C', '3'), ('D', ['4'])]

	with pytest.raises(ValueError):
		helps.remove('keynotexists')

	assert helps.select('A') == '1'
	helps.clear()
	assert list(helps.items()) == []

	helps.add('A', '1')
	helps.add('B', '2')
	assert list(helps.items()) == [('A', ['1']), ('B', ['2'])]

	helps.add('X', 'plain', sectype = 'plain')
	assert list(helps.items()) == [('A', ['1']), ('B', ['2']), ('X', ['plain'])]

	helps.add('Y', sectype = 'option')
	assert isinstance(helps.select('Y'), HelpOptions)
