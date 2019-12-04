from pyparam import params
params._load({
	'v'       : 0,
	'verbose' : 0,
	'V'       : False,
	'quiet'   : False,
	'packages': ['numpy', 'pandas', 'pyparam'],
	'depends' : {'pyparam': '0.0.1'}
})

print(params._dict())