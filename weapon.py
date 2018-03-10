from gurps_constants import *
from skill import Skill
from thing import Thing
from funcpipe import pipe

def uses_skill(skill_name):
	sk = Skill.TABLE[skill_name]
	def f(a):
		a.skill_level += sk(a.attacker)
		return a
	return f

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
	a.damage = Thing()
	a.damage.dice += 1 if st < 9 else int((st-5)/4)
	if st < 9:
		a.damage.mod += (-5 + int((st-1)/2))
	else:
		a.damage.mod += ((st-1) % 4) - 1 
	return a

def thrust_damage(a):
	a.attack_type = THRUST
	st = a.attacker.ST
	a.damage = Thing()
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

def crushing(a):
	a.damage.type = CRUSHING
	a.damage.multiplier = a.target.body.get_damage_multiplier(a.location, CRUSHING)
	return a

def damage_mod(mod):
	def f(a):
		a.damage.mod += mod
		return a
	return f
	
def parry(skill_name):
	def f(a):
		sk = Skill.TABLE[skill_name]
		a.defense_skill += int(sk(a.target)/2)
		a.defense = PARRY
		a.target.parries += 1
		return a
	return f

def defense_bonus(mod):
	def f(a):
		a.defense_skill += mod
		return a
	return f
	
broadsword = Thing()
broadsword.attack = pipe(uses_skill('Broadsword'), reach([1]), min_strength(9))
broadsword.thrust = pipe(broadsword.attack, thrust_damage, damage_mod(+1), impaling)
broadsword.swing = pipe(broadsword.attack, swing_damage, damage_mod(+1), cutting) 	
broadsword.parry = parry('Broadsword')
		
staff = Thing()
staff.attack = pipe(uses_skill('Staff'), reach([1,2]), min_strength(6))
staff.thrust = pipe(staff.attack, thrust_damage, damage_mod(+2), crushing)
staff.swing = pipe(staff.attack, swing_damage, damage_mod(+2), crushing) 	
staff.parry = pipe(parry('Staff'), defense_bonus(+2))





	