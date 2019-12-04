from pyparam import params
params._load({
	'v'                : 0,
	'v.type'           : 'verbose',
	'verbose.alias'    : 'v',
	'version'          : False,
	'version.desc'     : 'Show the version and exit.',
	'V.alias'          : 'version',
	'quiet'            : False,
	'quiet.desc'       : 'Silence warnings.',
	'packages.type'    : 'list',
	'packages.required': True,
	'packages.desc'    : 'The packages to install.',
	'depends'          : {},
	'depends.desc'     : 'The dependencies.'
})
print(params._parse())