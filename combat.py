#gurps.py with pipes

from funcpipe import pipe, ifelse, switch, identity
from functools import partial, reduce
from copy import copy

from gurps_constants import *

import random
import unittest
from collections import deque

from thing import Thing, Branch
import skill
import weapon
	

test_rolls_q = deque()
def set_test_roll(roll):
	test_rolls_q.appendleft(roll)

def clear_test_rolls():
	test_rolls_q.clear()
	
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
	

	
def init_attack():
	return Thing()
	
	
				
class Humanoid:
	DAMAGE_MULTIPLIERS = {
	CUTTING: 1.5,
	IMPALING: 2.0,
	SMALL_PIERCING: 0.5,
	LARGE_PIERCING: 1.5 }	
	
	LIMBS = set((LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG))
	EXTREMITIES = set((LEFT_HAND, RIGHT_HAND, LEFT_FOOT, RIGHT_FOOT))

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
		elif location in (Humanoid.EXTREMITIES | Humanoid.LIMBS) and damage_type == IMPALING:
			return 1.0
		elif damage_type in Humanoid.DAMAGE_MULTIPLIERS:
			return Humanoid.DAMAGE_MULTIPLIERS[damage_type]
		else:
			return 1.0 
		
	def is_limb(location):
		return location in Humanoid.LIMBS
	
	def is_extremity(location):
		return location in Humanoid.EXTREMITIES	
		


def init_character(**kwargs):
	params = {'ST':10, 
	            'DX':10, 
	            'IQ':10, 
	            'HT':10, 
	            'skills':{},
	            'body':Humanoid,
			 	'can_defend':True,}
	params['HP'] = params['HT']
	params.update(kwargs)
	return Thing(**params)
	
	
def set_precise_attack(a):
	a.skill_level += 4
	a.attacker.can_defend = False
	return a
	
def set_extra_attack(a):
	a.num_attacks += 1
	a.attacker.can_defend = False
	return a
	
def set_hard_attack(a):
	a.damage.mod += 2
	a.attacker.can_defend = False
	return a
	
def roll_random_hit_location(action):
	loc = action.attack.target.body.random_location(roll3d())
	action.attack.location = loc
	return action

def set_target_location(location):
	def hitloc(a):
		
		a.location = location
		a.skill_level += a.target.body.hit_modifier(location)
		return a
	return hitloc

def set_attacker(attacker_ch):
	def f(a):
		a.attacker = attacker_ch
		a.attacker.can_defend = True  #basic attack
		return a
	return f

def set_target(target_ch):
	def f(a):
		a.target = target_ch
		return a
	return f
	
def swing(a):
	return a.attacker.weapon.swing(a)

def thrust(a):
	return a.attacker.weapon.thrust(a)
	
def roll_attack(a):
	a.attack_roll = roll3d()
	a.attack_outcome = skill_roll(a.skill_level, a.attack_roll)
	return a
	
def basic_speed(character):
	return (character.DX + character.HT) / 4.0
	
def basic_move(character):
	return int(basic_speed(character))

def dodge(a):
	a.defense = DODGE
	a.defense_skill = basic_move(a.target) + 3
	return a
	
def parry(a):
	return a.target.weapon.parry(a) if a.target.weapon else a

def block(a):
	return a.target.shield.block(a) if a.target.shield else a
	
def roll_defense(a):
	a.defense_roll = roll3d()
	a.defense_outcome = skill_roll(a.defense_skill, a.defense_roll)
	return a
	
def end_turn(a):
	#end any effects from current turn
	a.attacker.shock_penalty = 0
	a.attacker.parries = 0
	return a

def roll_damage(a):
	a.damage.base_damage = roll_dice(a.damage.dice, a.damage.mod)
	return a


def damage_resistance(character, location):
	dr = character.armor[location] if character.armor else 0
	if location == SKULL:
		dr += 2
	return dr

def penetration(a):
	dr = damage_resistance(a.target, a.location)
	pen = a.damage.base_damage - dr
	a.damage.penetration = pen if pen > 0 else 0
	return a
	
def injury(a):
	injury = int(a.damage.penetration * a.damage.multiplier)
	#limbs and extremities can only take so much damage in one hit
	if a.target.body.is_limb(a.location):
		injury = min(injury, int(a.target.HP/2))
	elif a.target.body.is_extremity(a.location):
		injury = min(injury, int(a.target.HP/3))
	a.damage.injury = injury
	a.target.injury += injury
	return a

def shock(a):
	a.target.shock_penalty = min(a.damage.injury, 4)
	return a
	
def stun(a):
	major_wound = a.damage.injury >= int(a.target.HT/2)
	vulnerable_spot = a.damage.injury >=1 and a.location in (SKULL, FACE, VITALS)
	if major_wound or vulnerable_spot:
		a.stun_skill = a.target.HT + a.target.stun_modifier  #number to roll against
		if major_wound and a.location == FACE:
			a.stun_skill -= 5
		elif major_wound and a.location == SKULL:
			a.stun_skill -= 10
		a.stun_roll = roll3d()
		outcome = skill_roll(a.stun_skill, a.stun_roll)
		margin = a.stun_skill - a.stun_roll
		if outcome == CRITICAL_FAILURE or margin <= -4:
			a.target.unconscious = True
		elif outcome == FAILURE:
			a.target.stunned = True
	return a
		
def cripple(a):
	if ( (a.target.body.is_limb(a.location) and a.damage.injury >= int(a.target.HP/2)) or
		 (a.target.body.is_extremity(a.location) and a.damage.injury >= int(a.target.HP/3)) ):
		if not a.target.crippled:
			a.target.crippled = Thing()
		a.target.crippled[a.location] = True
		a.damage.cripple = a.location
	return a
		
	
	


#applies functions in a list, defers any function that failes with AttributeError and
#retries again after calling others
def apply_all(*functions):
	def f(x=None):
		if x is None:
			x = Thing()
		flist = functions
		while len(flist) > 0:
			deferred = []
			stuck = True
			for function in flist:
				try:
					x = function(Branch(x)).commit()
					stuck = False
				except (AttributeError,KeyError):
					deferred.append(function) #not ready yet
			if stuck:
				x = deferred[0](x) #should raise AttributeError
			flist = deferred #try again with what is left
		return x
	return f
		

apply_damage = pipe(injury, shock, stun, cripple)
	
target_hit = pipe(
	roll_damage, 
	penetration, 
	ifelse(lambda a:a.damage.penetration > 0, apply_damage) )


DEFENSES = [dodge, parry, block]

def best_defense(a):
	#try them all, use branches to undo side effects of any unused ones
	# keep the ones that actually work
	valid_results = [r for r in [d(Branch(a)) for d in DEFENSES] if r.defense_skill]
	
	if len(valid_results):
		#find best one, commit it, and return
		return reduce(lambda a,b:a if a.defense_skill >= b.defense_skill else b,
					  [ r for r in valid_results ] ).commit()
	else:
		return a

def defense_bonus(a):
	#things like shields give a universal bonus to defense,if there is one
	if a.target.shield:
		a = a.target.shield.defense_bonus(a)
	return a
	
resolve_defense = pipe(defense_bonus,
			           roll_defense,
				       switch(lambda a:a.defense_outcome, {CRITICAL_SUCCESS: identity, #TODO attacker critical miss
													       SUCCESS: identity,
													       FAILURE: target_hit,
													       CRITICAL_FAILURE: target_hit}) )
do_defense = pipe(
	ifelse(lambda a:a.target.can_defend, best_defense, identity), 
	ifelse(lambda a:a.defense_skill, resolve_defense, identity) )
	
	
resolve_attack = pipe(
	roll_attack,
	switch(lambda a:a.attack_outcome, {CRITICAL_SUCCESS: target_hit, #no defense, TODO critical hit effects
									   SUCCESS: do_defense,
									   FAILURE: identity,
									   CRITICAL_FAILURE: identity}), #TODO add critical miss
	end_turn )


class AttackTests(unittest.TestCase):
	def setUp(self):
		clear_test_rolls()
		self.al = init_character(ST=11, DX=11, name="Al")
		self.al.skills['Broadsword'] = +1
		self.al.weapon = weapon.broadsword
		self.al.shield = weapon.medium_shield
		self.al.skills['Shield']= +3

		self.bob = init_character(name="Bob")
		self.bob.skills['Staff'] = +2
		self.bob.weapon = weapon.staff
		
		self.al_setup = apply_all(set_attacker(self.al),
								  swing,
								  set_precise_attack,
								  set_target(self.bob),
								  set_target_location(SKULL) )
		
		self.bob_setup = apply_all(set_attacker(self.bob),
								   swing,
								   set_target(self.al),
								   set_target_location(TORSO) )
		
	def test_attack(self):
		set_test_roll(8) #attack success
		set_test_roll(15) #defense fail
		set_test_roll(6) #damage_roll (with mod)
		a = resolve_attack( self.al_setup() )	
		#print(a)
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.defense_outcome, FAILURE)
		self.assertEqual(a.damage.base_damage, 6) 
		self.assertEqual(a.damage.penetration, 4)  #DR2 skull
		self.assertEqual(a.damage.injury, 16)  #x4 for cutting attack to skull
		self.assertEqual(a.target.shock_penalty, 4)  #max of 4 from injury
		
	def test_defense(self):
		set_test_roll(8) #attack success
		set_test_roll(7) #defense success
		a = resolve_attack( self.al_setup() )	
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.defense_outcome, SUCCESS)
		self.assertEqual(a.damage.base_damage, None) 
		
	def test_miss(self):
		set_test_roll(14) #attack failed
		a = resolve_attack( self.al_setup() )	
		self.assertEqual(a.attack_outcome, FAILURE)
		self.assertEqual(a.defense_outcome, None)
		self.assertEqual(a.damage.base_damage, None) 
		
	def test_critical_hit(self):
		set_test_roll(4) #attack crit success
		set_test_roll(5) #defense skipped,damage roll
		a = resolve_attack( self.al_setup() )	
		self.assertEqual(a.attack_outcome, CRITICAL_SUCCESS)
		self.assertEqual(a.defense_outcome, None)
		self.assertEqual(a.damage.base_damage, 5) 
		
		
	def test_dodge(self):
		del self.bob.skills['Staff']  #go to default DX-5
		#parry skill should be 2 + 3 + 2 for staff, lower than dodge=8
		set_test_roll(8) #attack success
		a = resolve_attack( self.al_setup() )	
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.defense, DODGE)
		self.assertEqual(a.defense_skill, 8) 
		self.assertEqual(a.target.parries, None) #parry action should have been rolled back
		
	def test_parry(self):
		#parry skill should be 6 + 3 + 2 for staff, higher than dodge=8
		set_test_roll(8) #attack success
		a = resolve_attack( self.al_setup() )	
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.defense, PARRY)
		self.assertEqual(a.defense_skill, 11) 
		self.assertEqual(a.target.parries, 1)
	
	def test_block(self):
		#block should be 7 + 3  +2(for shield defense bonus)
		set_test_roll(10) #attack success
		a = resolve_attack( self.bob_setup() )	
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.defense, BLOCK)
		self.assertEqual(a.defense_skill, 12) 
		self.assertEqual(a.target.has_blocked, True)
		
class InjuryTests(unittest.TestCase):
	def setUp(self):
		clear_test_rolls()
		self.al = init_character(ST=11, DX=11)
		self.al.skills['Broadsword'] = +1
		self.al.weapon = weapon.broadsword

		self.bob = init_character()		
		
	def do_al_attack(self, target, location):
		return pipe(set_attacker(self.al), 
					set_target(target),
					set_target_location(location),
					thrust,
					resolve_attack)(init_attack())			
	
	def test_hp_loss(self):
		set_test_roll(10) #attack success
		set_test_roll(13) #defense fail
		set_test_roll(1) #damage_roll (with mod)
		a = self.do_al_attack(self.bob, TORSO)
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.damage.injury, 2)  #x2 for impaling
		self.assertEqual(a.target.shock_penalty, 2) #equal to injury
		self.assertEqual(a.target.injury, 2)
		
	def test_stunning(self):
		set_test_roll(10) #attack success
		set_test_roll(13) #defense fail
		set_test_roll(4) #damage_roll (with mod)
		set_test_roll(12) #failed stun roll
		a = self.do_al_attack(self.bob, TORSO)
		self.assertEqual(a.damage.injury, 8)  #x2 for impaling
		self.assertEqual(a.target.stunned, True)
		
	def test_knockout(self):
		set_test_roll(5) #attack success
		set_test_roll(13) #defense fail
		set_test_roll(4) #damage_roll (with mod)
		set_test_roll(7) #failed roll of HT-10,by more than 4
		a = self.do_al_attack(self.bob, SKULL)
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.damage.injury, 8)  #x4 for skull,  DR2
		self.assertEqual(a.target.unconscious, True)
		
class CripplingTests(unittest.TestCase):
	def setUp(self):
		clear_test_rolls()
		self.al = init_character(ST=11, DX=11)
		self.al.skills['Broadsword'] = +3
		self.al.weapon = weapon.broadsword
		self.bob = init_character()		
		
	def do_al_attack(self, target, location):
		return pipe(set_attacker(self.al), 
					set_target(target),
					set_target_location(location),
					swing,
					resolve_attack)(init_attack())	
	
	def test_leg_cripple(self):
		set_test_roll(9) #hit
		set_test_roll(15) #defense fail
		set_test_roll(5) #damage
		a = self.do_al_attack(self.bob, LEFT_LEG)
		self.assertEqual(a.attack_outcome, SUCCESS)
		self.assertEqual(a.damage.injury, 5)  #x1.5 for cutting, max HP/2 to leg
		self.assertEqual(a.damage.cripple, LEFT_LEG)
		self.assertEqual(a.target.crippled[LEFT_LEG], True)
		
if __name__ == '__main__':
	unittest.main()


	
	
	
