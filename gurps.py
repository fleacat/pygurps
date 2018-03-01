#gurps.py



import random
import unittest
from collections import deque

#arbitrary collection of attributes
#javascript style object
#cribbed from Ben Cherry http://www.adequatelygood.com/JavaScript-Style-Objects-in-Python.html
class Thing(object):
	DEFAULTS = {}
	
	def __init__(self, **kwargs):
		self.parent = None
		self.__dict__.update(self.DEFAULTS)
		self.__dict__.update(kwargs)
		for thing in kwargs.values():
			if isinstance(thing, Thing):
				thing.parent = self
				
	def __getitem__(self, name):
		item = self.__dict__.get(name, None)
		return item if item is not None else (self.parent.__getitem__(name) if self.parent else None)

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

SUCCESS = "success"
CRITICAL_SUCCESS = "critical success"
FAILURE = "failure"
CRITICAL_FAILURE = "critical failure"

class Result:
	pass

	def succeeded(self):
		return self.outcome == SUCCESS or self.outcome == CRITICAL_SUCCESS
	
	def failed(self):
		return not self.succeeded()

def skill_roll(skill_level):
	result = Result()
	roll = roll3d()
	result.roll = roll
	if roll == 18:
		result.outcome = CRITICAL_FAILURE
	elif roll == 17:
		result.outcome = FAILURE if skill_level >= 16 else CRITICAL_FAILURE
	elif roll >= (skill_level+10):
		result.outcome = CRITICAL_FAILURE
	elif roll <= 4:
		result.outcome = CRITICAL_SUCCESS
	elif roll == 5 and skill_level >= 15:
		result.outcome = CRITICAL_SUCCESS
	elif roll == 6 and skill_level >= 16:
		result.outcome = CRITICAL_SUCCESS
	else:
		result.outcome = SUCCESS if roll <= skill_level else FAILURE
	result.skill = skill_level
	result.margin = skill_level - roll
	return result
	
def skill_contest(skill_level, opposing_level):
	margin = skill_level - roll3d()
	opposing_margin = opposing_level - roll3d()
	return margin - opposing_margin


EYE = "eye"
SKULL = "skull"
FACE = "face"
RIGHT_LEG = "right leg"
RIGHT_ARM = "right arm"
LEFT_LEG = "left leg"
LEFT_ARM = "left arm"
TORSO = "torso"
GROIN = "groin"
HAND = "hand" #unspecified hand
LEFT_HAND = "left hand"
RIGHT_HAND = "right hand"
FOOT = "foot" #unspecified foot
LEFT_FOOT = "left foot"
RIGHT_FOOT = "right foot"
NECK = "neck"
VITALS = "vitals"

CUTTING = 'cutting'
IMPALING = 'impaling'
CRUSHING = 'crushing'
SMALL_PIERCING = 'small piercing'
PIERCING = 'piercing'
LARGE_PIERCING = 'large piercing'
	

FRONT = 'front'
BACK = 'back'
LEFT_SIDE = 'left_side'
RIGHT_SIDE = 'right_side'

class Attack(Thing):
	DEFAULTS = {
		'location':None,
		'direction':FRONT }
	
	
				
	

DAMAGE = 'damage'
SHOCK = 'shock'
KNOCKDOWN_ROLL = 'knockdown_roll'
CRIPPLED = 'crippled'
KNOCKBACK = "knockback"




def set_penetration(attack):
	dr = attack.target.DR(attack.location)
	attack.penetration = attack.base_damage - dr;
	return attack
	
def set_hit_effects(attack):
	attack.effects = {}
	if attack.damage_type == CRUSHING or (attack.damage_type == CUTTING and attack.penetration < 1):
		knockback = int(attack.base_damage / (attack.target.ST-2))
		if knockback > 0:
			attack.effects[KNOCKBACK] = knockback
	if attack.penetration < 1:
		return attack #no other effects
	d_mod = attack.target.damage_modifier(attack)
	damage = int(attack.penetration * d_mod)
	if attack.location in (LEFT_LEG, RIGHT_LEG, LEFT_ARM, RIGHT_ARM):
		threshold = int(attack.target.HP/2)
		damage = min(threshold, damage)
		if damage >= threshold:
			attack.effects[CRIPPLED] = attack.location
	elif attack.location in (LEFT_FOOT, RIGHT_FOOT, LEFT_HAND, RIGHT_HAND):
		threshold = int(attack.target.HP/3)
		damage = min(threshold, damage)
		if damage >= threshold:
			attack.effects[CRIPPLED] = attack.location
	attack.effects[DAMAGE] = damage
	shock_div = int(attack.target.HP/10) if attack.target.HP >= 20 else 1
	attack.effects[SHOCK] = -1 * min( (int(damage/shock_div), 4) )	
	if damage >= int(attack.target.HP/2):
		#major wound
		if attack.location == SKULL:
			knockdown = -10
		elif attack.location == FACE or attack.location == VITALS:
			knockdown = -5
		else:
			knockdown = 0
		attack.effects[KNOCKDOWN_ROLL] = knockdown
	elif damage >= 1 and attack.location in (SKULL, FACE, VITALS):
		#minor wound to head, vitals
		attack.effects[KNOCKDOWN_ROLL] = 0
	return attack
		
	

STUNNED = 'stunned'
UNCONSCIOUS = 'unconscious'
DEAD = 'dead'
DYING = 'dying'
OBLITERATED = 'obliterated'
REELING = 'reeling'

STANDING = 'standing'
PRONE = 'prone'
KNEELING = 'kneeling'
SITTING = 'sitting'

def apply_effects(attack):
	target = attack.target
	effects = attack.effects
	if DAMAGE in effects:
		apply_damage(target, effects[DAMAGE])
	if SHOCK in effects:
		target.modifiers[SHOCK] = min(target.modifiers.get(SHOCK, 0), effects[SHOCK])
	if target.active and KNOCKDOWN_ROLL in effects:
		effective_ht = target.HT + effects[KNOCKDOWN_ROLL] + target.modifiers.get(KNOCKDOWN_ROLL, 0)
		roll = skill_roll(effective_ht)
		if roll.outcome == FAILURE or roll.outcome == CRITICAL_FAILURE:
			if roll.margin <= -4 or roll.outcome == CRITICAL_FAILURE:
				target.conditions.add(UNCONSCIOUS)
			else:
				target.conditions.add(STUNNED)
	if not target.active:
		target.position = PRONE
	if CRIPPLED in effects:	
		target.crippled.add(effects[CRIPPLED])
	return attack

#helper for apply_effects
def apply_damage(target, damage):
	before_hp = target.currentHP
	target.damage += damage
	after_hp = target.currentHP
	if target.currentHP <= int(target.HP):
		target.conditions.add(REELING)
	if target.currentHP <= (-5 * target.HP):
		target.conditions.add(DEAD)
		if target.currentHP <= (-10 * target.HP):
			target.conditions.add(OBLITERATED)
	else:
		#calculate death checks
		while before_hp <= (-1 * target.HP):
			before_hp += target.HP
			after_hp += target.HP
		while after_hp <= (-1 * target.HP):
			#check
			roll = skill_roll(target.HT)
			if roll.failed():
				if roll.margin < -2:
					target.conditions.add(DEAD)
				else:
					target.conditions(DYING)
				return
			after_hp += target.HP


NOT_ACTIVE = set((DEAD, DYING, UNCONSCIOUS, STUNNED))
EXTREMITIES = set((LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG, LEFT_HAND,
				  RIGHT_HAND, LEFT_FOOT, RIGHT_FOOT))


class Humanoid:
	DAMAGE_MODIFIERS = {
	CUTTING: 1.5,
	IMPALING: 2.0,
	SMALL_PIERCING: 0.5,
	LARGE_PIERCING: 1.5 }	

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

	def hit_location(self):
		location = self.RANDOM_HIT_LOCATIONS[roll3d()]
		if location == HAND:
			location = LEFT_HAND if roll_dice(1) <= 3 else RIGHT_HAND
		elif location == FOOT:
			location = LEFT_FOOT if roll_dice(1) <= 3 else RIGHT_FOOT
		return location

	def attack_modifier(self, attack):
		return self.TARGET_MODIFIERS[attack.location]

	def damage_modifier(self, attack):
		if attack.location == SKULL:
			return 4.0
		if attack.location == VITALS and attack.damage_type == IMPALING:
			return 3.0
		elif attack.location in EXTREMITIES and attack.damage_type in (IMPALING, LARGE_PIERCING):
			return 1.0
		elif attack.damage_type in self.DAMAGE_MODIFIERS:
			return self.DAMAGE_MODIFIERS[attack.damage_type]
		else:
			return 1.0
			
			
ST = "ST"
DX = 'DX'
IQ = 'IQ'
HT = 'HT'

class Character:
	
	DAMAGE_MODIFIERS = {
	CUTTING: 1.5,
	IMPALING: 2.0,
	CRUSHING: 1.0,
	SMALL_PIERCING: 0.5,
	PIERCING: 1.0,
	LARGE_PIERCING: 1.5 }
	
	def __init__(self, **args):
		self.ST = args.get('ST', 10)
		self.DX = args.get('DX', 10)
		self.IQ = args.get('IQ', 10)
		self.HT = args.get('HT', 10)
		self.body = args.get('body', Humanoid())
		self.armor = args.get('armor', {})
		self.skills = {}
		init_skills = args.get('skills', {})
		for s in init_skills:
			self.add_skill(s, init_skills[s])
		self.conditions = set()
		self.crippled = set()
		self.modifiers = {}
		self.damage = 0
		self.position = STANDING
		self.holding = {}

	def pp(self):
		print("ST: {0}".format(self.ST))
		print("DX: {0}".format(self.DX))
		print("IQ: {0}".format(self.IQ))
		print("HT: {0}".format(self.HT))
		
	@property
	def HP(self):
		return self.ST + self.modifiers.get('HP', 0)
	
	@property
	def currentHP(self):
		return self.HP - self.damage
        
	def DR(self, location = TORSO):
		if location == VITALS:
			location = TORSO
		dr = self.armor.get(location, 0)
		if location == SKULL:
			dr += 2
		return dr
	
	def damage_modifier(self, attack):
		return self.body.damage_modifier(attack)	
	
	@property
	def active(self):
		return len( NOT_ACTIVE & self.conditions) == 0
	
	@property
	def alive(self):
		return DEAD not in self.conditions
	
	@property
	def BasicSpeed(self):
		return (self.DX + self.HT) / 4.0
	
	@property
	def encumbrance(self):
		return 0 #fix
	
	@property
	def BasicMove(self):
		return int(self.BasicSpeed) - self.encumbrance
	
	@property
	def Dodge(self):
		return self.BasicSpeed + 3
		
	def add_skill(self, skill_name, modifier):
		assert(skill_name in Skill.TABLE)
		self.skills[skill_name] = modifier 
		
	def skill_level(self, skill_name):
		return Skill.getLevel(skill_name, self)		
					
	def hold(self, item, appendage):
		self.holding[appendage] = item
		
	def drop(self, appendage):
		item = self.holding.get(appendage, None)
		self.holding[appendage] = None
		return item
	
	@property
	def swingDice(self):
		return 1 if self.ST < 9 else int((self.ST-5)/4) 
	
	@property
	def swingMod(self):
		if self.ST < 9:
			return -5 + int((self.ST-1)/2)
		else:
			return ((self.ST-1) % 4) - 1
		
	@property
	def thrustDice(self):
		return 1 if self.ST < 19 else 2
	
	@property
	def thrustMod(self):
		return -1 if self.ST > 18 else int((self.ST-1)/2) - 6
		
SWING = 'swing'
THRUST = 'thrust'
THROW = 'throw'
SHOOT = 'shoot'
C = 'close'
		

	
def roll_damage(attack):
	damage = roll_dice(attack.damage_dice, attack.damage_mod)
	if damage < 1: #minimum 
		damage = 0 if attack.damage_type == CRUSHING else 1
	attack.base_damage = damage
	return attack

		
class Weapon:
	def swing(dice_mod, damage_type):
		def set_damage(attack):
			attack.damage_dice = attack.attacker.swingDice
			attack.damage_mod = attack.attacker.swingMod + dice_mod
			attack.damage_type = damage_type
			return attack
		return set_damage

	def thrust(dice_mod, damage_type):
		def set_damage(attack):
			attack.damage_dice = attack.attacker.thrustDice
			attack.damage_mod = attack.attacker.thrustMod + dice_mod
			attack.damage_type = damage_type
			return attack
		return set_damage

	def fixed(dice, mod, damage_type):
		def set_damage(attack):
			attack.damage_dice = dice
			attack.damage_mod = mod
			attack.damage_type = damage_type
			return attack
		return set_damage
	
	def st_range(half, max):
		def set_range(attack):
			attack.half_range = int(attack.attacker.ST * half)
			attack.max_range = int(attack.attacker.ST * max)
			return attack
		return set_range
	
	def fixed_range(half, max):
		def set_range(attack):
			attack.half_range = half
			attack.max_range = max
			return attack
		return set_range
	


	
	
EASY = 'easy'
AVERAGE = 'average'
HARD = 'hard'
VERY_HARD = 'very_hard'
	
class Skill:
	TABLE = {}
		
	def getLevel(skill_name, character):
		skill = Skill.TABLE[skill_name]
		base = getattr(character, skill.attribute)
		if skill.name in character.skills:
			level = base + character.skills[skill.name]
		elif skill.default is not None:
			level = base + skill.default
		else:
			level = 0 #no attribute based default
		#check other skill defaults
		for name in skill.default_skills:
			default_skill = Skill.TABLE[name]
			if default_skill.name in character.skills:
				base = getattr(character, default_skill.attribute)
				modifier = character.skills[default_skill.name]
				penalty = skill.default_skills[name]
				default_level = base + modifier + penalty
				level = max(level, default_level)
		return level 
		
	def __init__(self, name, attribute, difficulty, default=None, default_skills={}):
		self.name = name
		self.attribute = attribute
		self.difficulty = difficulty
		self.default = default
		self.default_skills = default_skills
		self.TABLE[self.name] = self
		
		

Skill('Brawling', DX, EASY, default=0) #use DX if unskilled
Skill('Knife', DX, EASY, default=-3)
Skill('Shortsword', DX, AVERAGE, default=-4, default_skills={'Broadsword':-2})
Skill('Broadsword', DX, AVERAGE, default=-4, default_skills={'Shortsword':-2})

		
class RollTests(unittest.TestCase):	
	def test_rolls(self):
		cases = [
			(3, 4, CRITICAL_SUCCESS), #3-4 always crit success
			(5, 4, CRITICAL_SUCCESS), #3-4 always crit success
			(5, 9, FAILURE), #roll is higher
			(5, 15, CRITICAL_FAILURE), #roll is 10 or more higher
			(12, 12, SUCCESS), #roll is equal
			(15, 5, CRITICAL_SUCCESS), #5 on 15+ skill
			(15, 6, SUCCESS), 
			(16, 6, CRITICAL_SUCCESS), #6 on 16+ skill
			(15, 17, CRITICAL_FAILURE), #lower than 16, 17 is crit fail
			(16, 17, FAILURE), #higher than 15 skill,17 is normal fail
			(19, 17, FAILURE), #17 is always failure,
			(19, 18, CRITICAL_FAILURE) ] #18 is always crit fail
		for (skill, roll, result) in cases:
			with self.subTest(skill=skill, roll=roll, result=result):
				set_test_roll(roll)
				self.assertEqual(skill_roll(skill).outcome, result)
		
		
class SkillTests(unittest.TestCase):
	def test_skill(self):
		bob = Character(DX=11)
		bob.add_skill('Broadsword', +1)
		self.assertEqual(bob.skill_level('Broadsword'), 12)
		self.assertEqual(bob.skill_level('Shortsword'), 10) #Broadsword-2		
		self.assertEqual(bob.skill_level('Knife'), 8) #DX-3	
		
		
	
		
class HitTests(unittest.TestCase):
	def test_impaling(self):
		joe = Character(armor={TORSO:2})
		attack = Attack(target=joe,
						location=TORSO,
						base_damage=5,
						damage_type=IMPALING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:6, SHOCK:-4, KNOCKDOWN_ROLL:0})
		
	def test_crippling(self):
		joe = Character()
		attack = Attack(target=joe,
						location=RIGHT_ARM,
						base_damage=5,
						damage_type=IMPALING)
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:5, SHOCK:-4, KNOCKDOWN_ROLL:0, CRIPPLED:RIGHT_ARM})
		
	def test_scratch(self):
		joe = Character()
		attack = Attack(target=joe,
						location=TORSO,
						base_damage=1,
						damage_type=CUTTING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:1, SHOCK:-1})

		
	def test_head(self):
		joe = Character()
		attack = Attack(target=joe,
						location=SKULL,
						base_damage=4,
						damage_type=CRUSHING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:8, SHOCK:-4, KNOCKDOWN_ROLL:-10})
	
	def test_face(self):
		joe = Character()
		attack = Attack(target=joe,
						location=FACE,
						base_damage=2,
						damage_type=CRUSHING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:2, SHOCK:-2, KNOCKDOWN_ROLL:0})

	def test_vitals(self):
		joe = Character(armor={TORSO:2})
		attack = Attack(target=joe,
						location=VITALS,
						base_damage=3,
						damage_type=IMPALING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:3, SHOCK:-3, KNOCKDOWN_ROLL:0})
		
	def test_giant(self):
		giant = Character(ST=25)
		attack = Attack(target=giant,
						location=TORSO,
						base_damage=3,
						damage_type=CUTTING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:4, SHOCK:-2}) #reduced shock, HP > 20
		
	def test_knockback(self):
		joe = Character(ST=12, armor={TORSO:7})
		attack = Attack(target=joe,
						location=TORSO,
						base_damage=11,
						damage_type=CRUSHING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		self.assertEqual(attack.effects, {DAMAGE:4, SHOCK:-4, KNOCKBACK:1})
	
class WeaponTests(unittest.TestCase):
	def test_sword(self):
		broadsword = Thing(skill='Broadsword',
				           thrust=Thing(damage=Weapon.thrust(+1, IMPALING)),
				           swing=Thing(damage=Weapon.swing(+1, CUTTING)),
				           reach=[1,])
		bob = Character(ST=11, DX=11)
		bob.add_skill('Broadsword', +1)
		attack = Attack(attacker=bob)
		attack = broadsword.swing.damage(attack)
		self.assertEqual(bob.swingDice, 1)
		self.assertEqual(bob.swingMod, +1)
		self.assertEqual(attack.damage_type, CUTTING)
		self.assertEqual(attack.damage_dice, 1)
		self.assertEqual(attack.damage_mod, +2)
		
	def test_knife(self):
		knife = Thing(skill="Knife",
					   thrust=Thing(damage=Weapon.thrust(0, IMPALING),
									reach=[C,]),
					   swing=Thing(damage=Weapon.swing(-2, CUTTING),
								   reach=[C,1]),
					   throw=Thing(skill='Knife Throwing',
								   damage=Weapon.thrust(0, IMPALING),
								   range=Weapon.st_range(0.8, 1.5))
					  )
		
	
class DamageTests(unittest.TestCase):
	
	def test_damage(self):
		joe = Character(armor={TORSO:2})
		attack = Attack(target=joe,
						location=TORSO,
						base_damage=5,
						damage_type=IMPALING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		set_test_roll(5)  #success on knockdown roll
		attack = apply_effects(attack)
		self.assertEqual(joe.damage, 6)
		self.assertEqual(joe.modifiers[SHOCK], -4)
		self.assertEqual(joe.position, STANDING)
		
		
	def test_knockdown(self):
		joe = Character(armor={TORSO:2})
		attack = Attack(target=joe,
						location=TORSO,
						base_damage=5,
						damage_type=IMPALING )
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		set_test_roll(13) #failed knockdown roll
		attack = apply_effects(attack)
		self.assertEqual(joe.damage, 6)
		self.assertEqual(joe.modifiers[SHOCK], -4)
		self.assertTrue(STUNNED in joe.conditions)
		self.assertEqual(joe.position, PRONE)
		
	def test_knockout(self):
		joe = Character()
		attack = Attack(target=joe,
						location=SKULL,
						base_damage=4,
						damage_type=CRUSHING)
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		set_test_roll(9) #failed knockdown roll -10
		attack = apply_effects(attack)
		self.assertEqual(joe.damage, 8)
		self.assertEqual(joe.modifiers[SHOCK], -4)
		self.assertTrue(UNCONSCIOUS in joe.conditions)
		self.assertFalse(joe.active)
		self.assertEqual(joe.position, PRONE)
		
	def test_kill(self):
		joe = Character()
		attack = Attack(target=joe,
						location=VITALS,
						base_damage=9,
						damage_type=IMPALING)
		attack = set_penetration(attack)
		attack = set_hit_effects(attack)
		set_test_roll(13) #failed stay alive roll
		attack = apply_effects(attack)
		self.assertEqual(joe.damage, 27)
		self.assertFalse(joe.alive)
		self.assertEqual(joe.position, PRONE)

		
if __name__ == '__main__':
	unittest.main()
		
		
		
		
	
		
		
		
		
