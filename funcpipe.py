#pipetests

import functools
from functools import partial, reduce


def pipe(*functions):
	def pipe_f(x):
		return functools.reduce(lambda a,f: f(a), functions, x)    
	return pipe_f
	
def branch(test, on_true, on_false):
	def branch_f(x):
		return on_true(x) if test(x) else on_false(x)
	return branch_f
	
def switch(selector, casemap):
	return lambda x: casemap[selector(x)](x)


if __name__ == '__main__':
	#demo/test
	def add(x, y):
		return x + y

	def negate(x):
		return -1 * x
	
	def mul(x, y):
		return x * y
	
	
	double = partial(mul, 2)
	inc = partial(add, 1)

	machine = pipe(double, inc, inc)

	print("pipe")
	print(machine(4))

	
	test = lambda x: x < 10
	
	branch_machine = branch(test, machine, negate)

	print("branch")
	print(branch_machine(5))
	print(branch_machine(15))

	def is_positive(x):
		try:
			return x > 0
		except TypeError:
			return None
		
	switch_machine = switch(is_positive, 
							{True:branch_machine,
							 False:negate,
							 None:lambda x:"ERROR:{0}".format(x)} )
							 
	print("select")
	print(switch_machine(12))
	print(switch_machine(3))
	print(switch_machine(-2))
	print(switch_machine("blah"))




