# Caps Evaluator

Tool for a personal project to calculate the ideal starting hand for a game of caps with 5 players

## What is Caps?

Caps is a card game, incredibly popular in Northern Virginia public schools, and not many other places, in my exeperience.
The rules are similar to Uno.

It is played with a standard deck of cards.
The entire deck is dealt.

The first card played is always the three of clubs.
Each card played has to be greater than or equal to the last, where the ace is the highest card.
Twos are counted as bombs, where playing one will always clear the discard, and the player who played the two can place any card they want.
If two of the same card are played in a row, the next player is skipped.
If a player does not have a card they can play, they are skipped.
Players can choose not to play a card in a round.
If no one can play, the deck is cleared, and the player whose turn it is gets to place any card they want.
If one player has enough of the same number card that is currently at the top of the discard pile, they can play all of them at once, and thus clear the discard as thought it were a bomb.
The first player to discard all of their cards wins.

If the player who cleared the discard puts down two of the same card, the game is played as doubles until the next time the deck is cleared.
When played as doubles, the rules are the same, but you have to play two cards at once instead of one. This does not apply for bombs, however.

## Important Definitions

### Rational Actor

Someone or something that acts rationally in all scenarios.
The goal of a rational actor is to make the optimal decision, in all scenarios, given the information available to them.
In Economics, a rational actor optimizes utility. In Game Theory, a rational actor seeks a Nash equilibrium.
In this simulation, a rational actor seeks to make the move that brings them closest to victory in the fewest moves.
