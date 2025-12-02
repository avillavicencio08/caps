import numpy as np
import gymnasium as gym
import copy
from random import shuffle
from toolz import pipe

suits = {"s":0, "h":1, "d":2, "c":3}
cards = {
	"2":2,
	"3":3,
	"4":4,
	"5":5,
	"6":6,
	"7":7,
	"8":8,
	"9":9,
	# Can only be 1 character, so we use the roman numeral for 10
	"X":10,
	"J":11,
	"Q":12,
	"K":13,
	"A":14
}

null_card: Card
null_card.card = 0
null_card.suit = 0

def gen_deck_of_cards():
	deck = [null_card]

	for s in suits.values():
		for c in cards.values():
			card: Card
			card.suit = s
			card.card = c
			deck.append(card)

	return deck

standard_deck = gen_deck_of_cards()

class Card:
	def __init__(self, c):
		self.suit = suits[c[0]]
		self.card = cards[c[1]]


	def to_string(self):
		return suits.keys()[suits.values().index(self.suit)] + cards.keys()[cards.values().index(self.card)]

	def to_int(self):
		return standard_deck.index(self) - 1

class CapsEnv(gym.Env):
	def __init__(self):
		self._reset()

		# extra 1 to represent a skip/do nothing
		n = len(self.hands[0]) + 1

		self.action_space = gym.spaces.MultiDiscrete([n] * 11, start=-1, dtype=np.int8)
		self.observation_space = gym.spaces.Dict(
			{
				"agent"  : gym.spaces.MultiDiscrete([53] * 11, start=-1, dtype=np.int8),
				"history": gym.spaces.MultiDiscrete([53] * 52, start=-1, dtype=np.int8),
				"doubles": gym.spaces.Discrete(2,dtype=np.int8),
				"whose_turn": gym.spaces.Discrete(5,dtype=np.int8)
			}
		)

	def _reset(self):
		deck = standard_deck.copy()
		shuffle(deck)

		self.hands = [[], [], [], [], []]
		self.history = []
		self._first = 0
		self._num_turns = 0
		self._num_agent_turns = 0
		self.doubles = False
		self.whose_turn = 0

		# Deal hands. self.hands[0] is the agent
		for i in range(50):
			for j in range(5):
				c = deck.pop()
				self.hands[j].append(c)
				if c == Card("c3"):
					self._first = j

		self.whose_turn = self._first

		# pick 2 random players, they get the extra cards
		for i in shuffle(range(5))[:2]:
			self.hands[i].append(deck.pop())


	def _get_obs(self):
		hand = np.asarray(map(lambda c: np.int8(c.to_int()), self.hands[0].copy()))
		pile = np.asarray(map(lambda c: np.int8(c.to_int()),  self.history.copy()))

		pile[len(pile):52] = [np.int8(-1)] * (52 - len(pile))
		hand[len(hand):11] = [np.int8(-1)] * (11 - len(hand))

		return {
			"agent"  : hand,
			"history": pile,
			"doubles": 1 if self.doubles else 0,
			"whose_turn": self.whose_turn
		}

	def _naive_agent_turn(self, h):
		hand = self.hands[h]

	def _handle_naive_agents(self):
		for h in range(1,5):
			hand = self.hands[h]

	def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
		super.reset(seed=seed)

		self._reset()

		return self._get_obs(), {}

	def step(self, action):
		self._num_turns += 1

		reward, terminated, truncated = self._handle_actions()

	def _win_check(self, h):
		return not any(map(lambda c: c != null_card, self.hands[h]))

	def _bomb_out_check(self, h, i):
		for j in range(len(self.hands[h])):
			if i == j:
				continue
			elif self.hands[h][j] != null_card:
				return False

		return True

	def _handle_actions(self, action, reward=0.0, nc=0, first=True, whom=0):
		hand = self.hands[whom]
		terminated = False
		truncated = False

		# There was an illegal move played at some point.
		if len(action) == 0:
			reward = -1.0
			return reward, terminated, truncated

		# Either skip, or we can't play, or this function recursed with an empty hand
		# Check the history to see which it is, and reward/act appropriately
		if action[0] == np.int8(-1):
			if self.whose_turn != whom:
				# Bot made the right choice. Reward it a tensy bit but not much
				reward = 0.1
				return reward, terminated, truncated

			if self.doubles:
				uniqs = {}
				
				for c in hand:
					if c in uniqs:
						uniqs[c] += 1
					else:
						uniqs[c]  = 1
				
				if any(n > self.history[len(self.history - 1)].card and uniqs[n] >= 2 for n in uniqs.keys()):
					# No cards shed, no rewards
					reward -= 0.05
			else:
				if any(c > self.history[len(self.history - 1)].card for c in hand):
					# No cards shed, no rewards
					reward -= 0.05

			return reward, terminated, truncated

		actions = action[:action.index(-1)]
		self._num_agent_turns += 1 if first else 0
		
		# Completion check
		ns = 0
		num = hand[actions[0]].card

		for i in actions:
			if hand[i].card == num:
				ns += 1
			else:
				break
		nhs = ns
		
		for i in range(4 - ns):
			if self.history[-i - 1].card == num:
				ns += 1
			else:
				break
		
		if ns == 4:
			self.history.clear()
			for i in range(len(hand)):
				if hand[i].card == num:
					hand[i] = copy.copy(null_card)

			actions = actions[nhs:]
			nc += nhs

			return self._handle_actions(actions, reward=reward, nc=nc, first=False, whom=whom)

		if len(self.history) == 0:
			# Great! We get to go first.

			# We are first player, and did not make the correct first move
			# Ignore what the bot wants, make the right move, and punish it
			if Card("c3") in hand and hand[actions[0]] != Card("c3"):
				reward = -1.0
				i = hand.index(Card("c3"))

				hand[i] = copy.copy(null_card)
				self.history.append(Card("c3"))

				return reward, terminated, truncated

			# Again, illegal. Just less so.
			if Card("c3") in hand and len(actions[0]) > 1:
				reward = -1.0

			if hand[actions[0]].card == 2:
				# ILLEGAL. BAD.
				reward = -1.0

				# Bomb out, aka snatching defeat from the jaws of victory
				if hand[actions[0]].card == 2 and self._bomb_out_check(whom, actions[0]):
					hand[actions[0]] = copy.copy(null_card)
					terminated = True

				return reward, terminated, truncated

			ns = 0
			num = hand[actions[0]].card

			for i in actions:
				if hand[i].card == num:
					ns += 1
				else:
					break

			error = False

			match ns:
				case 1:
					self.doubles = False
				case _:
					self.doubles = True

			if self.doubles:
				# Illegal Move
				if hand[actions[0]].card != hand[actions[1]].card:
					reward = -1.0
					return reward, terminated, truncated

				# Just make the move.
				nc += 2

				self.history.append(hand[actions[0]])
				self.history.append(hand[actions[1]])

				hand[actions[0]] = copy.copy(null_card)
				hand[actions[1]] = copy.copy(null_card)

				# ILLEGAL MOVE DAMN
				if len(actions) > 2:
					reward = -1.0
				else:
					reward = float(nc) / 5.0

					# We won!
					if self._win_check(whom):
						terminated = True
						reward += float(len(hand)) / 2.0

				return reward, terminated, truncated
			else:
				nc += 1

				self.history.append(hand[actions[0]])
				hand[actions[0]] = copy.copy(null_card)

				reward = float(nc) / 5.0

				if self._win_check(whom):
					terminated = True
					reward += float(len(hand)) / 2.0

				# Illegal Move
				if len(actions) > 1:
					reward = -1.0

				return reward, terminated, truncated

		if hand[actions[0]].card == 2:
			# Illegal. Bad
			if len(actions) < 2:
				reward = -1.0

				if self._bomb_out_check(whom, actions[0]):
					hand[actions[0]] = copy.copy(null_card)
					terminated = True
					self.history.clear()

				return reward, terminated, truncated

			self.history.clear()

			nc += 1
			actions = actions[1:]

			return self._handle_actions(actions, reward=reward, nc=nc, first=False, whom=whom)

		if self.history[-1] < hand[actions[0]].card != 2:
			# Invalid move. Penalize
			reward = -1.0
			return reward, terminated, truncated

		if self.doubles:
			if len(actions) < 2:
				reward = -1.0
				return reward, terminated, truncated

			if (hand[actions[0]].card != hand[actions[1]].card and hand[actions[0]].card != 2):
				# Invalid move. Penalize
				reward = -1.0
				return reward, terminated, truncated

			self.history.append(hand[actions[0]].card)
			self.history.append(hand[actions[1]].card)

			hand[actions[0]] = copy.copy(null_card)
			hand[actions[1]] = copy.copy(null_card)

			nc += 2

			reward = float(nc) / 5.0

			if self._win_check(whom):
				terminated = True
				reward += float(len(hand)) / 2.0
			
			if len(actions) > 2:
				reward = -1.0
		else:
			self.history.append(hand[actions[0]].card)

			hand[actions[0]] = copy.copy(null_card)

			nc += 1

			reward = float(nc) / 5.0

			if self._win_check(whom):
				terminated = True
				reward += float(len(hand)) / 2.0

			if len(actions) > 1:
				reward = -1.0

		return reward, terminated, truncated
