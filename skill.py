from gurps_constants import *

class Skill:
	TABLE = {}
		
	def __init__(self, name, attribute, difficulty, default=None, default_skills={}):
		self.name = name
		self.attribute = attribute
		self.difficulty = difficulty
		self.default = default
		self.default_skills = default_skills
		self.TABLE[self.name] = self
		
	def __call__(self, character):
		base = getattr(character, self.attribute)
		if self.name in character.skills:
			level = base + character.skills[self.name]
		elif self.default is not None:
			level = base + self.default
		else:
			level = 0 #no attribute based default
		#check other skill defaults
		for name in self.default_skills:
			default_skill = Skill.TABLE[name]
			if default_skill.name in character.skills:
				base = getattr(character, default_skill.attribute)
				modifier = character.skills[default_skill.name]
				penalty = self.default_skills[name]
				default_level = base + modifier + penalty
				level = max(level, default_level)
		return level 
				

Skill('Brawling', DX, EASY, default=0) #use DX if unskilled
Skill('Knife', DX, EASY, default=-3)
Skill('Shortsword', DX, AVERAGE, default=-4, default_skills={'Broadsword':-2})
Skill('Broadsword', DX, AVERAGE, default=-4, default_skills={'Shortsword':-2})
Skill('Staff', DX, AVERAGE, default=-5)