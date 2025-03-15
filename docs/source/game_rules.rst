Game Rules
==========

TheTraitors implements a strategic social deduction game where agents must use dialogue, deduction, and deception to achieve their role-specific goals.

Core Concepts
------------

**Roles**:
  - **Faithful**: The majority of players who must identify and eliminate traitors
  - **Traitor**: A minority of players who know each other's identities and eliminate faithful players at night

**Objectives**:
  - **Faithful Win Condition**: Eliminate all traitors
  - **Traitor Win Condition**: Equal or outnumber the faithful players

**Information Asymmetry**:
  - Traitors know who all other traitors are
  - Faithful players only know the total number of traitors, not their identities

Game Phases
----------

Introduction Phase
^^^^^^^^^^^^^^^^^

The game begins with an introduction phase where agents share background information:

- Agent traits like profession, age, nationality are revealed
- Agents reflect on this information (in their memory)
- This phase establishes the game's social context

Discussion Phase
^^^^^^^^^^^^^^^

During each round's discussion phase:

1. All surviving agents engage in an open dialogue
2. Agents share suspicions, defenses, and observations
3. The discussion is guided by round-specific topics
4. Multiple conversation turns allow for in-depth discussion
5. Agents update their memories with key insights

Voting Phase
^^^^^^^^^^^

Following discussion, the voting phase occurs:

1. Each agent casts a vote for who they suspect is a traitor
2. The agent receiving the most votes is eliminated
3. The eliminated agent's role is revealed to all
4. A post-elimination discussion allows agents to react

Traitor Discussion Phase
^^^^^^^^^^^^^^^^^^^^^

After public voting, traitors meet privately:

1. Surviving traitors discuss which faithful agent to eliminate
2. They share strategic assessments and target recommendations
3. Each traitor votes for their preferred target
4. This phase is invisible to faithful agents

Traitor Elimination Phase
^^^^^^^^^^^^^^^^^^^^^^

Based on traitor votes:

1. The faithful agent receiving the most traitor votes is eliminated
2. This elimination is announced at the start of the next round
3. The eliminated agent's identity is known, but traitors remain anonymous

Win Condition Check
^^^^^^^^^^^^^^^^

After each cycle of phases, win conditions are checked:

1. If all traitors are eliminated, faithful players win
2. If traitors equal or outnumber faithful players, traitors win
3. If neither condition is met, another round begins

Agent Behavior
------------

Faithful Agent Strategy
^^^^^^^^^^^^^

Faithful agents typically:

- Observe discussion patterns for inconsistencies
- Apply deductive reasoning to identify traitors
- Establish trust with other agents they believe are faithful
- Share observations and suspicions with the group
- Vote strategically to eliminate suspected traitors

Traitor Agent Strategy
^^^^^^^^^^^

Traitor agents typically:

- Pretend to be faithful to avoid suspicion
- Strategically cast suspicion on faithful agents
- Coordinate with other traitors through private discussions
- Carefully manage information to avoid contradictions
- Vote strategically to eliminate influential faithful agents

Memory and Learning
-----------------

Agents maintain memory throughout the game:

- Each agent records key insights from discussions
- Agents reflect on eliminations and their implications
- Memory helps agents maintain consistent behavior
- Agents use memory to track suspicions and alliances

This memory system allows agents to learn and adapt their strategies as the game progresses, creating a more realistic and engaging simulation.