import numpy as np
import gymnasium as gym
import copy
import random
from toolz import pipe
import caps
import itertools

class CapsEnv(gym.Env):
	def __init__(self):
		self._reset()

		self.action_space = gym.spaces.Dict(
			{
				"type": gym.spaces.Discrete(4, start=1, dtype=np.int8),
				"cards": gym.spaces.MultiDiscrete([12] * 4, start=-1, dtype=np.int8)
			}
		)

		self.observation_space = gym.spaces.Dict(
			{
				"agent"  : gym.spaces.MultiDiscrete([53] * 11, start=-1, dtype=np.int8),
				"history": gym.spaces.MultiDiscrete([53] * 52, start=-1, dtype=np.int8),
				"pile"   : gym.spaces.MultiDiscrete([53] * 52, start=-1, dtype=np.int8),
				"type": gym.spaces.Discrete(4, start=1, dtype=np.int8),
				"whose_turn": gym.spaces.Discrete(5, dtype=np.int8),
				"hands": gym.spaces.MultiDiscrete([11] * 5, dtype=np.int8)
			}
		)

	def _reset(self):
		self.game = caps.CapsGame()
		self.agents = []
		
		for i in range(1, 5):
			self.agents.append(caps.RandomAgent(i, self.game))

	def _get_obs(self):
		observe = {}

		# First, the easy stuff
		observe["type"] = np.int8(self.game.type)
		observe["whose_turn"] = np.int8(self.game.current)
		observe["hands"] = [np.int8(len(filter(lambda c: c != null_card, h))) for h in self.game.hands]
		observe["agent"] = [np.int8(c.to_int() - 1) for c in self.game.hands[0]]
		
		# Then pile
		pile = [np.int8(c.to_int() - 1) for c in self.game.pile]
		observe["pile"] = pile + [np.int8(-1)] * (52 - len(pile))
		
		# Then history
		history = [m.cards for m in self.game.history[:]]
		history = list(itertools.chain.from_iterable(history))
		history = [np.int8(c.to_int() - 1) - 1 for c in history]
		observe["history"] = history + [np.int8(-1)] * (52 - len(history))

		observe["hands"] = np.array(observe["hands"])
		observe["agent"] = np.array(observe["agent"])
		observe["pile"] = np.array(observe["pile"])
		observe["history"] = np.array(observe["history"])

		return observe
	
	def _handle_actions(action):
		# First, our dear beloved agent
		hand = self.game.hands[0][:]
		who_up = self.game.current
		move = caps.Move(0, caps.MoveType(int(action["type"])), [int(i) for i in action["cards"]])
		reward = -0.05
		terminated = False
		truncated = False

		if move.move_type == caps.MoveType.SINGLE:
			move.cards = move.cards[:1]
		elif move.move_type == caps.MoveType.DOUBLE:
			move.cards = move.cards[:2]
		
		move.cards = filter(lambda c: c == -1, move.cards)

		legal,played = self.game.do_move(move)

		if not legal:
			return -1.0, False, False
		
		if who_up == 0:
			reward = played * .1 if played > 0 else -0.05
		else:
			reward = played * .125 if played > 0 else 0.05

		# Our dear agent won
		if len(filter(lambda c: c != null_card, self.game.hands[0])) == 0:
			# Bomb out
			if hand[move.cards[0]].card == 2:
				reward = -0.5
			else:
				reward = 1.5
			
			terminated = True
		
		# Now, the others
		for a in self.agents:
			a.make_move()

			if len(filter(lambda c: c != null_card, self.game.hands[a.hand])) == 0:
				terminated = True

		return reward, terminated, truncated

	def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
		super.reset(seed=seed)

		self._reset()

		return self._get_obs(), {}

	def step(self, action):
		self._num_turns += 1

		reward, terminated, truncated = self._handle_actions(action)

		return self._get_obs(), reward, terminated, truncated, {}
