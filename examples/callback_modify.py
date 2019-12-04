from pyparam import params
params.amplifier = 10
params.number.type = int
params.number.callback = lambda param, ps: param.setValue(
	param.value * ps.amplifier.value)
print(params._parse())