# test branching


import unittest

#a None value with some extra features
class Empty:
	def __bool__(self):
		return False
	
	def __add__(self, number):
		return number
	
	def __sub__(self, number):
		return -number	
	
	def __eq__(self, other):
		return other is None or isinstance(other, Empty)
		
	

class Thing:
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)
		
	def __repr__(self):
		return self.__dict__.__repr__()

	def __str__(self):
		return self.__dict__.__str__()
	
	def __getattr__(self, name):
		return Empty()  #treated as a zero for math, False for boolean


class Branch:
	INTERNAL_ATTR = set(['_trunk'])
	
	def __init__(self, trunk, **kwargs):
		self._trunk = trunk
		self.__dict__.update(kwargs)
		
	def __getattr__(self, name):
		#called if attribute not already in __dict__, check if in trunk
		#make new branch in __dict__ if it is a complex object (Thing) or already a Branch
		val = getattr(self._trunk, name)
		if isinstance(val, (Thing, Branch)): 
			val = Branch(val)
			setattr(self, name, val) #save in __dict__
		return val
	
	def commit(self):
		#anything in dict is modified or branched
		#copy values to trunk, commit sub-branches
		for (k,v) in self.__dict__.items():
			if k not in self.INTERNAL_ATTR:
				if isinstance(v, Branch):
					v.commit()
				else:
					setattr(self._trunk, k, v)
		return self._trunk
	

class ThingTests(unittest.TestCase):
	def test_create(self):
		test = Thing(a=1, b=2, c=3)
		self.assertEqual(test.a, 1)
		self.assertEqual(test.x, Empty())

	def test_add_sub_empty(self):
		test = Thing()
		test.a += 4
		test.b -= 2
		self.assertEqual(test.a, 4)
		self.assertEqual(test.b, -2)
		
	
class BranchTests(unittest.TestCase):	
	def test_create(self):
		test = Thing()
		test.a = 'trunk'
		branch = Branch(test)
		branch.a = 'branch'
		self.assertEqual(test.a, 'trunk')
		self.assertEqual(branch.a, 'branch')
		
	def test_tree(self):
		trunk = Thing()
		trunk.a = Thing()
		trunk.b = Thing()
		trunk.a.a = "a.a trunk"
		trunk.b.b = "b.b trunk"
		branch = Branch(trunk)
		branch.b.b = "b.b branch 1"
		branch.b.a = "b.a branch 1"
		branch.b.b = "b.b branch 2"
		self.assertEqual(trunk.a.a, "a.a trunk")
		self.assertEqual(trunk.b.b, "b.b trunk")
		self.assertEqual(branch.a.a, "a.a trunk") #was not changed by branch
		self.assertEqual(branch.b.b, "b.b branch 2")
		
	def test_commit(self):
		trunk = Thing()
		trunk.a = Thing()
		trunk.a.a = Thing()
		trunk.b = Thing()
		trunk.a.a.a = "a.a.a trunk"
		trunk.b.b = "b.b trunk"
		trunk_keys = len(trunk.__dict__.keys())
		branch = Branch(trunk)
		branch.a.a.a = "a.a.a branch 1"
		branch.a.a.a = "a.a.a branch 2"
		self.assertEqual(trunk.a.a.a, "a.a.a trunk")
		self.assertEqual(trunk.b.b, "b.b trunk")
		self.assertEqual(branch.a.a.a, "a.a.a branch 2") 
		self.assertEqual(branch.b.b, "b.b trunk") #was not changed by branch
		branch.commit()
		self.assertEqual(trunk.a.a.a, "a.a.a branch 2")
		self.assertEqual(trunk_keys, len(trunk.__dict__.keys())) #should not have changed
		
	def test_branch_initargs(self):
		trunk = Thing()
		trunk.a = "a trunk"
		trunk.b ="b trunk"
		branch = Branch(trunk, b="b branch")
		self.assertEqual(trunk.b, "b trunk")
		self.assertEqual(branch.b, "b branch")
		branch.commit()
		self.assertEqual(trunk.b, "b branch")
	
if __name__ == '__main__':
	unittest.main()
	
	"""
	test=Thing()
	test.a = Thing()
	test.a.a = 23
	test.b = 42
	print(test)
	branch = Branch(test)
	branch.a.a = 99
	branch.a.b = 9
	print(branch)
	print(test)
	branch.commit()
	print(test)
	"""
	
	
	
	
	
	
	
	
	
