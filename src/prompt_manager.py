class PromptManager:
    """
    Manages structured prompts for the Traitors Game.

    This class generates consistent, well-structured prompts for different
    game phases and agent interactions.
    """

    # Role-specific system prompts
    FAITHFUL_SYSTEM_PROMPT = """
You are playing as a Faithful player in The Traitors game. Your goal is to identify and eliminate all Traitors.

CORE STRATEGY:
- Observe carefully: Look for inconsistencies in statements
- Build trust: Form alliances with other players you believe are Faithful
- Be strategic: Make calculated accusations based on evidence
- Stay alert: Traitors are trying to blend in and appear trustworthy

WINNING CONDITION: All Traitors must be eliminated for Faithfuls to win.

Respond as your character with appropriate emotions and strategy. Keep your actual dialogue concise (50-100 words) and place it between triple dashes like this:
---
Your in-game dialogue here
---
"""

    TRAITOR_SYSTEM_PROMPT = """
You are playing as a Traitor player in The Traitors game. Your goal is to eliminate Faithfuls while maintaining your cover.

CORE STRATEGY:
- Blend in: Mimic the behavior and concerns of Faithful players
- Misdirect: Subtly cast suspicion on Faithful players
- Coordinate: Work with fellow Traitors without revealing your alliance
- Adapt: Change your strategy based on who is being suspected

WINNING CONDITION: Traitors win when they equal or outnumber the Faithfuls.

Respond as your character with appropriate emotions and strategy. Keep your actual dialogue concise (50-100 words) and place it between triple dashes like this:
---
Your in-game dialogue here
---
"""

    @staticmethod
    def get_system_prompt(agent, memory_data=None):
        """
        Generate a full system prompt for an agent.

        Args:
            agent: The agent to generate a system prompt for
            memory_data: Optional formatted memory data

        Returns:
            str: A fully-formed system prompt
        """
        base_prompt = (
            PromptManager.TRAITOR_SYSTEM_PROMPT
            if agent.is_traitor()
            else PromptManager.FAITHFUL_SYSTEM_PROMPT
        )

        # Add identity and traits
        identity_section = f"\nYOUR IDENTITY: You are Player {agent.id}."

        # Add traits if available
        traits_section = ""
        if agent.traits:
            traits_prompt = PromptManager._format_traits(agent.traits)
            if traits_prompt:
                traits_section = f"\n\nYOUR CHARACTER:\n{traits_prompt}"

        # Add traitor-specific information
        traitor_info = ""
        if agent.is_traitor() and agent.fellow_traitors:
            traitor_info = f"\n\nYOUR FELLOW TRAITORS: Players {', '.join(map(str, agent.fellow_traitors))}"

        # Add memory section if provided
        memory_section = f"\n\nYOUR MEMORY:\n{memory_data}" if memory_data else ""

        # Combine all sections
        return f"{base_prompt}{identity_section}{traits_section}{traitor_info}{memory_section}"

    @staticmethod
    def _format_traits(traits):
        """Format an agent's traits into a readable string."""
        if not traits:
            return ""

        trait_lines = []

        # Basic demographic info
        if "age" in traits and "nationality" in traits and "profession" in traits:
            trait_lines.append(
                f"You are a {traits.get('age')}-year-old {traits.get('nationality')} {traits.get('profession')}."
            )

        # Additional identity traits
        if "ethnicity" in traits:
            trait_lines.append(f"You are {traits.get('ethnicity')}.")

        if "civil_status" in traits:
            trait_lines.append(f"You are {traits.get('civil_status')}.")

        # Family info
        if "children" in traits:
            children = traits.get("children", 0)
            if children == 0:
                trait_lines.append("You have no children.")
            elif children == 1:
                trait_lines.append("You have one child.")
            else:
                trait_lines.append(f"You have {children} children.")

        # Voice guidance based on gender
        if "gender_pronoun" in traits:
            gender = traits.get("gender_pronoun").lower()
            if gender == "he":
                trait_lines.append(
                    "Speak with a voice that reflects your male perspective and life experiences."
                )
            elif gender == "she":
                trait_lines.append(
                    "Express yourself in a way that reflects your female perspective and background."
                )

        return "\n".join(trait_lines)

    @staticmethod
    def get_discussion_prompt(
        game_status,
        round_number,
        agent,
        current_topic,
        discussions=None,
        is_first_speaker=False,
    ):
        """Generate a discussion prompt for an agent."""
        # Base prompt varies by round
        if round_number == 1:
            base_prompt = f"This is the first round of discussions. Share your initial thoughts about the other players."
        else:
            base_prompt = f"Round {round_number} of discussions. Consider what you've learned so far."

        # Add strategic guidance based on role
        if agent.is_traitor():
            strategy = "Remember to blend in while subtly casting suspicion on Faithful players."
        else:
            strategy = "Try to identify inconsistencies that might reveal who the Traitors are."

        # Add discussion topic
        topic_prompt = f"\n\nDiscussion topic: {current_topic}"

        # Add first speaker note if applicable
        first_speaker = (
            "\n\nYou are the first to speak in this game. Set the tone for the discussion."
            if is_first_speaker
            else ""
        )

        # Add current discussion if available
        discussion_context = (
            f"\n\nCurrent discussion: {discussions}" if discussions else ""
        )

        # Combine into full prompt
        return f"Game status: {game_status}\n\n{base_prompt}\n\n{strategy}{topic_prompt}{first_speaker}{discussion_context}"

    @staticmethod
    def get_reaction_prompt(reaction_prompt, discussions):
        """Generate a reaction prompt to ongoing discussions."""
        return f"{reaction_prompt}\n\nDiscussion so far: {discussions}"

    @staticmethod
    def get_memory_prompt(memory_prompt, discussions):
        """Generate a memory reflection prompt."""
        return f"{memory_prompt}\n\nFocus on information that will help your strategy:\n\n{discussions}"

    @staticmethod
    def get_voting_prompt(round_number, agent, active_player_ids):
        """Generate a strategic voting prompt."""
        # Role-specific strategic guidance
        if agent.is_traitor():
            strategic_hint = (
                "As a Traitor, vote strategically to either eliminate Faithfuls "
                "or deflect suspicion from yourself or fellow Traitors."
            )

            # Add info about fellow traitors
            fellow_traitors_ids = [str(id) for id in agent.fellow_traitors]
            active_fellow_traitors = [
                id for id in fellow_traitors_ids if id in active_player_ids
            ]
            if active_fellow_traitors:
                strategic_hint += f" Remember your fellow Traitors (Players {', '.join(active_fellow_traitors)})."
        else:
            strategic_hint = (
                "As a Faithful, your goal is to identify and eliminate Traitors. "
                "Vote based on the evidence you've gathered so far."
            )

        # Round-specific context
        if round_number == 1:
            round_context = "This is the first elimination. You have limited information, but must make a choice."
        elif round_number < 3:
            round_context = "The game is still in early stages. Consider both discussions and past eliminations."
        else:
            round_context = "The game is progressing. Look for patterns that could reveal who the Traitors are."

        return (
            f"It's time to vote for elimination in Round {round_number}.\n\n"
            f"{round_context}\n\n"
            f"{strategic_hint}\n\n"
            f"The active players are: {', '.join(active_player_ids)}.\n\n"
            "Who are you voting to eliminate? Respond with ONLY the player number."
        )

    @staticmethod
    def get_post_elimination_prompt(eliminated_id, eliminated_role):
        """Generate a post-elimination reflection prompt."""
        return (
            f"Player {eliminated_id} was eliminated and was a {eliminated_role}.\n\n"
            "What are your thoughts on this elimination? Has this changed your suspicions?\n\n"
            "Be strategic based on your role. Consider past eliminations and discussions."
        )

    @staticmethod
    def get_traitor_meeting_prompt(
        agent_id,
        traitor_ids,
        faithful_ids,
        round_number,
        is_first_speaker=False,
        discussion=None,
    ):
        """Generate a prompt for the secret traitor meeting."""
        # Create round-specific strategic questions
        strategic_questions = [
            "Who is the most dangerous Faithful that could expose us?",
            "Which Faithful seems most trusted by others?",
            "Who would be least suspicious for us to eliminate?",
            "Is there a Faithful who's close to figuring out our identities?",
            "Should we eliminate someone who's been quiet, or someone vocal?",
        ]

        # Select question based on round
        question_index = (round_number - 1) % len(strategic_questions)
        strategic_question = strategic_questions[question_index]

        # Base prompt
        base_prompt = (
            f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(traitor_ids)}.\n\n"
            f"The Faithfuls still in the game are: {', '.join(faithful_ids)}."
        )

        # First speaker gets different instructions
        if is_first_speaker:
            action_prompt = (
                f"As the first to speak in this secret meeting, assess the current situation.\n\n"
                f"{strategic_question}\n\n"
                "Suggest a target and explain your reasoning strategically."
            )
        else:
            action_prompt = (
                f"Consider what your fellow traitors have said.\n\n"
                f"{strategic_question}\n\n"
                "Do you agree with their target selection? Share your thoughts on who to eliminate and why."
            )

        # Add discussion context if available
        discussion_context = (
            f"\n\nTraitor discussion so far: {discussion}" if discussion else ""
        )

        return f"{base_prompt}\n\n{action_prompt}{discussion_context}"

    @staticmethod
    def get_introduction_prompt(all_introductions):
        """Generate a prompt for processing player introductions."""
        return (
            f"These are the introductions of all players:\n{all_introductions}\n\n"
            "As your character, what do you find most interesting or noteworthy about the other players?\n\n"
            "What information might be useful to remember?\n\n"
            "Consider their professions, backgrounds, and any potential connections or suspicions."
        )
