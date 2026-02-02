import enum
import copy
import random

class Card:
	def __init__(self, c):
		if c == "xx":
			self.suit = 0
			self.card = 0
		else:
			self.suit = suits[c[0]]
			self.card = cards[c[1]]

	def to_string(self):
		if self == null_card:
			return "xx"

		return list(suits.keys())[list(suits.values()).index(self.suit)] + list(cards.keys())[list(cards.values()).index(self.card)]

	def to_int(self):
		return standard_deck.index(self) - 1

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

null_card = Card("c3")
null_card.card = 0
null_card.suit = 0

def gen_deck_of_cards():
	deck = [null_card]

	for c in cards.values():
		for s in suits.values():
			card = Card("c3")
			card.suit = s
			card.card = c
			deck.append(card)

	return deck

standard_deck = gen_deck_of_cards()

class MoveType(enum.Enum):
	COMPLETION = 1
	SINGLE     = 2
	DOUBLE     = 3
	NULL       = 4

class Move:
	def __init__(self, who, t, cards):
		self.move_type = t
		self.cards = cards
		self.who = who

class CapsGame:
	def __init__(self):
		self.pile = []
		self.history = []
		self.hands = [[], [], [], [], []]
		self.current = 0
		self.type = MoveType.NULL

		deck = gen_deck_of_cards()
		deck = deck[1:]

		random.shuffle(deck)

		for i in range(len(deck)):
			self.hands[i % 5].append(deck[i])
		
		shuffle(self.hands)

		for h in self.hands:
			while len(h) < 11:
				h.append(null_card)
			
			if Card("c3") in h:
				self.current = self.hands.index(h)

	# Returns: legality, cnt_cards_played
	def is_legal_move(self, move):
		success = True
		hand = self.hands[move.who]
		who = move.who

		if move.move_type == MoveType.NULL:
			return success, 0
		
		for i in move.cards:
			if self.hands[who][i] == null_card:
				return False, 0
		
		if move.move_type != MoveType.COMPLETION and who != self.current:
			return False, 0
		
		if self.type != MoveType.NULL and move.cards[0] < self.pile[-1].card:
			if len(move.cards) != 4 or move.cards[0] != 2:
				return False, 0
		
		if move.move_type == MoveType.DOUBLE:
			if len(move.cards) != 2 or self.type == MoveType.SINGLE:
				return False, 0
			
			if hand[move.cards[0]].card != hand[move.cards[1]].card:
				return False, 0
			
			if hand[move.cards[0]] == 2:
				return False, 0
			
			return success, 2
		elif move.move_type == MoveType.SINGLE:
			if len(move.cards) != 1 or self.type == MoveType.DOUBLE:
				return False, 0

			return success, 1
		else:
			c = hand[move.cards[0]].card
			n = 0

			for i in move.cards:
				if hand[i].card != c:
					return False, 0
				
				n += 1

			if n == 4:
				return True, 4

			for i in self.pile[-(4 - n):]:
				if i.card != c:
					return False, 0

			return True, n

		return False, 0

	# Returns: did_something, cnt_cards_played
	def do_move(self, move):
		legal, n = self.is_legal_move(move)
		hand = self.hands[move.who]

		if not legal:
			return False, 0
		
		# There is a move to be made here.

		if move.move_type == MoveType.DOUBLE:
			move.cards = move.cards[:2]
			move.who = who
			self.history.append(copy.copy(move))

			for i in range(2):
				c = move.cards[i]
				card = copy.copy(hand[c])
				self.history[-1].cards[i] = card
				self.pile.append(card)
				hand[c] = copy.copy(null_card)

			self.type = MoveType.DOUBLE
	
		elif move.move_type == MoveType.SINGLE:
			move.cards = move.cards[:1]
			self.history.append(copy.copy(move))
			card = copy.copy(hand[move.cards[0]])
			self.history[-1].cards[0] = card
			self.pile.append(card)
			hand[move.cards[0]] = copy.copy(null_card)
			self.type = MoveType.SINGLE

			if card.card == 2:
				self.pile.clear()
				self.type = MoveType.NULL

		elif move.move_type == MoveType.COMPLETION:
			move.cards = move.cards[:n]
			self.history.append(copy.copy(move))

			for i in range(n):
				c = move.cards[i]
				card = copy.copy(hand[c])
				self.history[-1].cards[i] = card
				hand[c] = copy.copy(null_card)
			
			self.pile.clear()
			self.type = MoveType.NULL
		
		elif move.move_type == MoveType.NULL:
			if move.who != self.current:
				return True, 0
		
		# Now that we have actually done stuff, it is time to perform a series of checks,
		# and determine who is up next

		# Either they won, or the deck is clear.
		# It stays their turn.
		if self.type == MoveType.NULL or len(filter(lambda c: c != null_card, hand)) == 0:
			return True, n
		
		# Check if anyone can go
		for p in self.hands:
			for c in p:
				if c.card == 2:
					self.current = (self.current + 1) % 5
					return True, n

		if self.type == MoveType.SINGLE:
			# Really easy
			for p in self.hands:
				for c in p:
					if c.card >= self.pile[-1].card:
						self.current = (self.current + 1) % 5
						return True, n
		elif self.type == MoveType.DOUBLE:
			for p in hands:
				twos = {}
				for c in p:
					if p.card in twos:
						twos[c.card] += 1
					else:
						twos[c.card] = 1
				
				for c in twos.keys():
					if twos[c] >= 2 and c > self.pile[-1].card:
						self.current = (self.current + 1) % 5
						return True, n
			
		# Nobody can go. Clear it
		self.pile.clear()
		self.type = MoveType.NULL
		return True, n

class RandomAgent:
	def __init__(self, hand, game):
		self.hand = hand
		self.game = game
	
	def make_move():
		hand = self.game.hands[self.hand]
		card_cnts = {}
		top = self.game.pile[-1]
		move_cards = []
		
		# Try to do a completion.
		# We don't need to check the legality of it ourselves.
		# The game will do it anyway
		for c in hand:
			if c.card in card_cnts:
				card_cnts[c.card] += 1
			else:
				card_cnts[c.card] = 1
		
		if top in card_cnts:
			for c in hand:
				if c.card == top:
					move_cards.append(hand.index(c.card))

			move = Move(self.hand, MoveType.COMPLETION, move_cads)
			worked, _ = self.game.do_move(move)

			# That worked! Somehow.
			if worked:
				return
		
		if self.game.current != self.hand:
			# Ain't us chief, move on.
			return
		
		move_cards = []

		worked = False
		n = 0

		while not worked:
			if self.game.type == MoveType.DOUBLE:
				legal_options = []

				for c, n in card_cnts.items():
					if n < 2 or c < top:
						continue
						
					for card in filter(lambda k: k.card >= top, hand):
						move_cards.append(hand.index(card))
					
					move = Move(self.hand, MoveType.DOUBLE, copy.copy(move_cards))
					move_cards = []
					legal_options.append(move)

				# Can't move
				if len(legal_options) == 0:
					move = Move(self.hand, MoveType.NULL, [])
					self.game.do_move(move)
					return
				
				worked, _ = self.game.do_move(random.choice(legal_options))
			
			if 2 in card_cnts and random.random() >= .33:
				move = Move(self.hand, MoveType.SINGLE, [[c.card == 2 for c in hand].index(True)])
				worked, _ = self.game.do_move(move)
				continue

			if self.game.type == MoveType.NULL:
				card = random.choice(hand)

				while card == null_card:
					card = random.choice(hand)
				
				if card_cnts[card.card] >= 2 and random.random() >= .66:
					move_cards = []

					for i, c in enumerate(hand):
						if c.card == card.card:
							move_cards.append(i)

						if len(move_cards) == 2:
							break
					
					move = Move(self.hand, MoveType.DOUBLE, move_cards)
					
				else:
					move = Move(self.hand, MoveType.SINGLE, [hand.index(card)])

				worked, _ = self.game.do_move(move)
				continue
			
			if self.game.type == MoveType.SINGLE:
				card = null_card

				for c in random.shuffle(hand[:]):
					if c.card >= self.game.pile[-1].card:
						card = c
						break

				if card == null_card:
					move = Move(self.hand, MoveType.NULL, [])
				else:
					move = Move(self.hand, MoveType.SINGLE, [hand.index(card)])
				worked, _ = self.game.do_move(move)
				continue
