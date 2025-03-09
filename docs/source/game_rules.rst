Game Rules
==========

TheTraitors is a social deduction game where agents must identify and eliminate the traitors among them.

Roles
-----

There are two roles in the game:

**Faithfuls**
  The majority of agents are Faithfuls. They don't know who the other Faithfuls are and must work together to identify and eliminate the Traitors.

**Traitors**
  A small number of agents are secretly Traitors. They know who the other Traitors are and must eliminate the Faithfuls while avoiding detection.

Game Flow
--------

The game proceeds in rounds, with each round consisting of several phases:

1. **Discussion Phase**
   - All active agents discuss and share suspicions
   - Agents can strategically reveal information or mislead others
   - Each agent gets a chance to speak and respond to others

2. **Voting Phase**
   - All active agents vote to eliminate one player
   - The player with the most votes is eliminated
   - The eliminated player's role is revealed to all

3. **Post-Elimination Discussion**
   - Agents discuss the recent elimination
   - This provides an opportunity to update strategies based on new information

4. **Traitor Discussion Phase** (Secret)
   - Traitors meet secretly to discuss their strategy
   - They decide which Faithful to eliminate

5. **Traitor Elimination Phase** (Secret)
   - Traitors vote to eliminate one Faithful
   - The eliminated player is announced but their role is not revealed

Win Conditions
-------------

The game continues until one of the following conditions is met:

**Faithfuls Win**
  All Traitors have been eliminated.

**Traitors Win**
  The number of Traitors equals or exceeds the number of Faithfuls.

Agent Memory
-----------

Each agent maintains a memory of game events, including:

- Discussions and accusations
- Eliminations and revealed roles
- Their own observations and conclusions

This memory influences their future decisions and strategies.

Game Parameters
--------------

The game can be customized with various parameters:

- **Number of agents**: Total number of players (default: 10)
- **Number of traitors**: Number of traitors among the agents (default: 3)
- **LLM model**: The language model used for agent responses
- **Random seed**: For reproducible game simulations

Example Game Round
-----------------

Here's an example of how a round might proceed:

1. **Discussion Phase**:
   - Player 1 (Faithful): "I'm suspicious of Player 5 because they've been quiet."
   - Player 5 (Traitor): "I've been observing. Actually, Player 3 seems suspicious to me."
   - ... (all players contribute)

2. **Voting Phase**:
   - Players cast votes
   - Player 3 receives the most votes and is eliminated
   - Player 3 is revealed to be a Faithful

3. **Post-Elimination Discussion**:
   - Players discuss the elimination of Player 3
   - Player 5 (Traitor) strategically deflects suspicion

4. **Traitor Discussion** (secret):
   - Traitors discuss who to eliminate next
   - They decide on Player 8, who they believe is influential

5. **Traitor Elimination**:
   - Player 8 is eliminated overnight
   - The game announces: "Player 8 was eliminated by the traitors in the night."

The next round begins with fewer players, and the cycle continues until a win condition is met. 