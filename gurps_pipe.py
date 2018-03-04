#gurps.py with pipes

from funcpipe import pipe, branch, switch
from functools import partial
from copy import copy

from gurps_constants import *

import random
import unittest
from collections import deque

#arbitrary collection of attributes
#javascript style object
#cribbed from Ben Cherry http://www.adequatelygood.com/JavaScript-Style-Objects-in-Python.html
class Thing(object):
	
	def __init__(self, **kwargs):
		self.__dict__.update(self.get_defaults())
		self.__dict__.update(kwargs)
				
	
	def get_defaults(self):
		return {} #override			
	
	def __getitem__(self, name):
		return self.__dict__.get(name, None)
		

	def __setitem__(self, name, val):
		return self.__dict__.__setitem__(name, val)

	def __delitem__(self, name):
		if self.__dict__.has_key(name):
			del self.__dict__[name]

	def __getattr__(self, name):
		return self.__getitem__(name)

	def __setattr__(self, name, val):
		return self.__setitem__(name, val)

	def __delattr__(self, name):
		return self.__delitem__(name)

	def __iter__(self):
		return self.__dict__.__iter__()

	def __repr__(self):
		return self.__dict__.__repr__()

	def __str__(self):
		return self.__dict__.__str__()
	



test_rolls_q = deque()
def set_test_roll(roll):
	test_rolls_q.appendleft(roll)

def roll_dice(num_dice, modifier=0):
	if len(test_rolls_q):
		return test_rolls_q.pop()
	else:
		sum = 0
		for i in range(num_dice):
			sum += random.randint(1, 6)
		return sum + modifier

def roll3d():
	return roll_dice(3)

def coin_flip():
	return roll_dice(1) > 3



def skill_roll(skill_level, roll):
	if roll == 18:
		return CRITICAL_FAILURE
	elif roll == 17:
		return FAILURE if skill_level >= 16 else CRITICAL_FAILURE
	elif roll >= (skill_level+10):
		return CRITICAL_FAILURE
	elif roll <= 4:
		return CRITICAL_SUCCESS
	elif roll == 5 and skill_level >= 15:
		return CRITICAL_SUCCESS
	elif roll == 6 and skill_level >= 16:
		return CRITICAL_SUCCESS
	else:
		return SUCCESS if roll <= skill_level else FAILURE
	

class Action(Thing):
	pass

class Damage(Thing):
	def get_defaults(self):
		return {'dice':0, 'mod':0}

class Attack(Thing):
	def get_defaults(self):
		return {'skill_level':0, 
				'num_attacks':1,
				'damage':Damage(),
				'location':None }
	
				
class Humanoid:
	DAMAGE_MULTIPLIERS = {
	CUTTING: 1.5,
	IMPALING: 2.0,
	SMALL_PIERCING: 0.5,
	LARGE_PIERCING: 1.5 }	
	
	EXTREMITIES = set((LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG, LEFT_HAND,
				  RIGHT_HAND, LEFT_FOOT, RIGHT_FOOT))

	TARGET_MODIFIERS = {
		None: 0,
		EYE: -9,
		SKULL: -7,
		FACE: -5,
		RIGHT_LEG: -2,
		LEFT_LEG: -2,
		RIGHT_ARM: -2,
		LEFT_ARM: -2,
		TORSO: 0,
		GROIN: -3,
		LEFT_HAND: -4,
		RIGHT_HAND: -4,
		LEFT_FOOT: -4,
		RIGHT_FOOT: -4,
		NECK: -5,
		VITALS: -3 }

	RANDOM_HIT_LOCATION = {
		3: SKULL,
		4: SKULL,
		5: FACE,
		6: RIGHT_LEG,
		7: RIGHT_LEG,
		8: RIGHT_ARM,
		9: TORSO,
		10: TORSO,
		11: GROIN,
		12: LEFT_ARM,
		13: LEFT_LEG,
		14: LEFT_LEG,
		15: HAND,
		16: FOOT,
		17: NECK,
		18: NECK  }

	def hit_modifier(location):
		return Humanoid.TARGET_MODIFIERS[location]

	def random_location():
		location = Humanoid.RANDOM_HIT_LOCATION[roll3d()]
		if location == HAND:
			location = LEFT_HAND if coin_flip() else RIGHT_HAND
		elif location == FOOT:
			location = LEFT_FOOT if coin_flip() else RIGHT_FOOT
		return location


	def get_damage_multiplier(location, damage_type):
		if location == SKULL:
			return 4.0
		elif location == VITALS and damage_type == IMPALING:
			return 3.0
		elif location in Humanoid.EXTREMITIES and damage_type == IMPALING:
			return 1.0
		elif damage_type in Humanoid.DAMAGE_MULTIPLIERS:
			return Humanoid.DAMAGE_MULTIPLIERS[damage_type]
		else:
			return 1.0 


class Character(Thing):
	def get_defaults(self):
		return {'ST':10, 
	            'DX':10, 
	            'IQ':10, 
	            'HT':10, 
	            'skills':{},
	            'body':Humanoid,
	            'can_defend':True }
	            
	def attack(self, target):
		self.can_defend = True
		self.move = 1
		return Attack(attacker=self, target=target)


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



def precise_attack(a):
	a.skill_level += 4
	a.attacker.can_defend = False
	return a
	
def extra_attack(a):
	a.num_attacks += 1
	a.attacker.can_defend = False
	return a
	
def hard_attack(a):
	a.damage.mod += 2
	a.attacker.can_defend = False
	return a
	
def skill(skill_name):
	sk = Skill.TABLE[skill_name]
	def f(a):
		a.skill_level = sk(a.attacker)
		return a
	return f
	
def random_hit_location(action):
	loc = action.attack.target.body.random_location(roll3d())
	action.attack.location = loc
	return action

def target_location(location):
	def hitloc(a):
		a.location = location
		a.skill_level += a.target.body.hit_modifier(location)
		return a
	return hitloc
	
def reach(reachlist):
	def f(a):
		a.reach = reachlist
		return a
	return f
	
def min_strength(min_st):	
	def f(a):
		a.min_strength = min_st
		if a.attacker.ST < min_st:
			a.skill_level -= (min_st - a.attacker.ST)
		return a
	return f

def swing_damage(a):
	a.attack_type = SWING
	st = a.attacker.ST
	a.damage.dice += 1 if st < 9 else int((st-5)/4)
	if st < 9:
		a.damage.mod += (-5 + int((st-1)/2))
	else:
		a.damage.mod += ((st-1) % 4) - 1 
	return a
	
def thrust_damage(a):
	a.attack_type = THRUST
	st = a.attacker.ST
	a.damage.dice += 1 if st < 19 else 2
	a.damage.mod = (-1 if st > 18 else int((st-1)/2) - 6)
	return a	

def impaling(a):
	a.damage.type = IMPALING
	a.damage.multiplier = a.target.body.get_damage_multiplier(a.location, IMPALING)
	return a
	
def cutting(a):
	a.damage.type = CUTTING
	a.damage.multiplier = a.target.body.get_damage_multiplier(a.location, CUTTING)
	return a

def damage_mod(mod):
	def f(a):
		a.damage.mod += mod
		return a
	return f
	

al = Character(ST=11, DX=11)
al.skills['Broadsword'] = +1

bob = Character()

broadsword = Thing()
broadsword.base = pipe(skill('Broadsword'), reach([1]), min_strength(9))
broadsword.thrust = pipe(broadsword.base, thrust_damage, damage_mod(+1), impaling)
broadsword.swing = pipe(broadsword.base, swing_damage, damage_mod(+1), cutting) 	
	
al_swing = pipe(al.attack,
    		    broadsword.swing,
			    target_location(TORSO))
			  
print(al_swing(bob))			  






	
	
	
