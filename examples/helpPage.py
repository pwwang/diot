from pyparam import params
from pyparam.help import HelpOptions, HelpItems

def helpx(helps):
	# # initiate it with an option
	# # or initiate with empty
	# helps.add('Java options', HelpOptions())
	# # or
	# helps.add('Java options', sectype = 'option')
	helps.add('Java options', ('-Xmx', '<SIZE>', 'set maximum Java heap size'))

	# add another option
	helps.select('Java options').add(('-Xms', '<SIZE>', 'set initial Java heap size'))

	# add a section before USAGE
	# # or initiate with empty
	# helps.before('USAGE', 'Description', sectype = 'item')
	# # or
	# helps.before('USAGE', 'Description', HelpItems())
	helps.before('USAGE', 'Description', 'This is an example of help manipulation.')

	# add another line to description
	helps.select('Description').add('Another description')

	# add a line before 'Another description'
	helps.select('Description').before('Another description', 'One description')

	# add required option section before optional
	# because no required options defined
	helps.before('Optional options', 'Required Options', sectype = 'option')

	# add an option
	helps.select('Required options').add(
		('-v',  # option name
			'',    # type
			# description in multiple lines
			'The verbosity\nSome very very long description\nabout this option.'
		))

	# add a line to the description after 'The verbosity'
	helps.select('Required options') \
			.select('-v')[2] \
			.after('The verbosity', 'Default: 0')

	# add another
	helps.select('Required options').add(
		('-d, --depend', '<DICT>', 'The dependencies.'))

	# add an option after -v
	helps.select('Required options').after('-v',
		('--version', '[BOOL]', 'Show the version.'))

params._helpx = helpx
print(params._parse())
