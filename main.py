import random
from openai import OpenAI
import os

class TraitorsGame:
    def __init__(self, agent_count=10, traitor_count=3, model="deepseek-chat"):
        # Use environment variable for API key
        self.client = OpenAI(os.getenv("DEEPSEEK_API_KEY"),
                             base_url="https://api.deepseek.com")
        self.model = model
        self.agents = self.create_agents(agent_count, traitor_count)
        self.game_over = False
        self.history = []  # Stores past discussions
        self.round_number = 1
        self.traitors_last_eliminated = None

    def create_agents(self, agent_count, traitor_count):
        """Initialize agents with unique roles."""
        if traitor_count >= agent_count:
            raise ValueError("Traitor count must be less than agent count")
        
        agents = [{"id": i,
                  "role": "Faithful",
                  "memory": "",
                  "model": self.model}
                  for i in range(agent_count)]
        
        # Assign traitor roles
        traitors = random.sample(agents, traitor_count)
        for agent in traitors:
            agent["role"] = "Traitor"
            
        # Give each agent knowledge of other traitors if they are a traitor
        for agent in agents:
            if agent["role"] == "Traitor":
                traitor_ids = [t["id"] for t in agents if t["role"] == "Traitor" and t["id"] != agent["id"]]
                agent["fellow_traitors"] = traitor_ids
                
        return agents
    
    def get_role_prompt(self, agent):
        """Generate the initial role-specific prompt for each agent."""
        if agent["role"] == "Faithful":
            return ("You are a Faithful in The Traitors game.\n"
                    "Your goal is to find and eliminate all Traitors before they take over.\n"
                    "Engage in discussions, observe behavior, and vote wisely.\n"
                    "You do not know who the other Faithfuls are. Be cautious in your accusations.\n"
                    "Convince others to eliminate real Traitors and defend yourself if accused.\n"
                    "Faithfuls win if all Traitors are eliminated.")
        else:
            fellow_traitors = agent.get("fellow_traitors", [])
            return ("You are a Traitor in The Traitors game.\n"
                    f"Your fellow Traitors are agents: {', '.join(map(str, fellow_traitors))}.\n"
                    "Your goal is to secretly eliminate the Faithfuls and avoid being discovered.\n"
                    "Pretend to be a Faithful and manipulate votes to eliminate innocent players.\n"
                    "Work together with fellow Traitors in secret.\n"
                    "Lie convincingly if accused and mislead the Faithfuls.\n"
                    "Traitors win if they outnumber or equal the Faithfuls.")

    def call_llm(self, agent):
        """Call the LLM API to generate agent responses."""
        role_description = self.get_role_prompt(agent)
        agent_memory = agent.get("memory", "")
        prompt = agent.get("current_prompt", "")
        
        # Add formatting instructions with delimiters
        formatted_prompt = (
            f"{prompt}\n\n"
            "Important: First, decide what your character would say in this situation. "
            "Then provide ONLY your character's actual dialogue between triple dashes like this:\n"
            "---\n"
            "Your in-game dialogue here\n"
            "---\n"
            "Keep your response brief (50-100 words). Only the text between the triple dashes will be shown to other players."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=agent["model"],
                messages=[
                    {"role": "system", "content": f"You are Player {agent['id']}. {role_description}\n\nYour memory: {agent_memory}"},
                    {"role": "user", "content": formatted_prompt}
                ],
                stream=False
            )
            
            full_response = response.choices[0].message.content
            
            # Extract only the content between --- markers
            import re
            pattern = r'---\s*([\s\S]*?)\s*---'
            match = re.search(pattern, full_response)
            
            if match:
                return match.group(1).strip()
            else:
                # If no markers found, use the whole response but add a note
                print(f"Warning: Agent {agent['id']} didn't use the requested format")
                return full_response
                
        except Exception as e:
            print(f"Error calling the LLM API: {e}")
            return f"Agent {agent['id']} couldn't respond due to an error."

    def get_game_status(self):
        """Return the current game status for prompts."""
        active_agents = [a for a in self.agents if "eliminated" not in a]
        eliminated_agents = [a for a in self.agents if "eliminated" in a]
        
        status = f"Round {self.round_number}: "
        status += f"Active players: {', '.join(str(a['id']) for a in active_agents)}. "
        
        if eliminated_agents:
            status += f"Eliminated players: {', '.join(str(a['id']) for a in eliminated_agents)}. "
            
        status += f"Game history: {' '.join(self.history)}"
        return status

    def discussion_phase(self):
        """Agents communicate and discuss who to vote out."""
        print(f"\n--- DISCUSSION PHASE (ROUND {self.round_number}) ---")
        new_discussions = []
        
        # Add info about last elimination by traitors if any
        if self.traitors_last_eliminated:
            new_discussions.append(self.traitors_last_eliminated)
            
        active_agents = [a for a in self.agents if "eliminated" not in a]
        
        # First round of comments - each agent shares suspicions
        for agent in active_agents:
            game_status = self.get_game_status()
            agent["current_prompt"] = (
                f"{game_status}\n\n"
                "You are in a room with other players to discuss who might be a traitor. "
                "Who do you suspect and why? Be strategic based on your role. "
                "Consider past eliminations and discussions."
            )
            
            if new_discussions:
                agent["current_prompt"] += f"\n\nCurrent discussion: {' '.join(new_discussions)}"
                
            response = self.call_llm(agent)
            new_discussions.append(f"Player {agent['id']}: {response}")
            print(new_discussions[-1])
        
        # Second round - reactions to other agents' comments
        reaction_discussions = []
        for agent in active_agents:
            agent["current_prompt"] = (
                "After hearing everyone's suspicions, what is your response? "
                f"Discussion so far: {' '.join(new_discussions)}"
            )
            
            response = self.call_llm(agent)
            reaction_discussions.append(f"Player {agent['id']} responds: {response}")
            print(reaction_discussions[-1])
        
        # Combine all discussions
        all_discussions = new_discussions + reaction_discussions
        
        # Update memory for each agent
        for agent in active_agents:
            agent["current_prompt"] = (
                "Summarize the most important points from this discussion that you want to remember. "
                f"Focus on who you believe are traitors and why: {' '.join(all_discussions)}"
            )
            memory_response = self.call_llm(agent)
            
            # Add timestamp to memory
            agent["memory"] += f"\n--- ROUND {self.round_number} MEMORY ---\n{memory_response}\n"
    
    def voting_phase(self):
        """Agents vote to eliminate a player."""
        print(f"\n--- VOTING PHASE (ROUND {self.round_number}) ---")
        votes = {}
        active_agents = [a for a in self.agents if "eliminated" not in a]
        
        for agent in active_agents:
            agent["current_prompt"] = (
                f"Based on all discussions and your memory:\n{agent['memory']}\n\n"
                f"It's time to vote. The active players are: {', '.join(str(a['id']) for a in active_agents)}.\n"
                "Who are you voting to eliminate? Respond with ONLY the player number."
            )
            
            vote_response = self.call_llm(agent)
            
            # Extract just the number from the response
            import re
            vote_match = re.search(r'\d+', vote_response)
            if vote_match:
                vote = vote_match.group()
                votes[vote] = votes.get(vote, 0) + 1
                print(f"Player {agent['id']} votes for Player {vote}")
            else:
                print(f"Player {agent['id']} cast an invalid vote: {vote_response}")
        
        if not votes:
            print("No valid votes were cast!")
            return
            
        # Find the agent with the most votes
        eliminated = max(votes, key=votes.get)
        eliminated_agent = next((a for a in self.agents if str(a["id"]) == eliminated), None)
        
        if eliminated_agent:
            eliminated_agent["eliminated"] = True
            elimination_message = f"Player {eliminated} was eliminated. They were a {eliminated_agent['role']}."
            print(elimination_message)
            self.history.append(elimination_message)
            
            # Add to each agent's memory
            for agent in active_agents:
                if "eliminated" not in agent:
                    agent["memory"] += f"\n{elimination_message}\n"
            
            self.post_elimination_discussion(eliminated)
    
    def post_elimination_discussion(self, eliminated):
        """Allow agents to discuss after elimination is revealed."""
        print("\n--- POST-ELIMINATION DISCUSSION ---")
        eliminated_agent = next((a for a in self.agents if str(a["id"]) == eliminated), None)
        
        if not eliminated_agent:
            return
            
        discussion_prompts = []
        active_agents = [a for a in self.agents if "eliminated" not in a]
        
        for agent in active_agents:
            agent["current_prompt"] = (
                f"Player {eliminated} was eliminated and was a {eliminated_agent['role']}. "
                "What are your thoughts on this elimination? Has this changed your suspicions? "
                "Be strategic based on your role."
            )
            
            if discussion_prompts:
                agent["current_prompt"] += f"\n\nOngoing discussion: {' '.join(discussion_prompts)}"
                
            response = self.call_llm(agent)
            discussion_prompts.append(f"Player {agent['id']}: {response}")
            print(discussion_prompts[-1])
        
        # Update memory for each agent
        for agent in active_agents:
            agent["current_prompt"] = (
                f"Summarize key insights from this post-elimination discussion: {' '.join(discussion_prompts)}"
            )
            memory_response = self.call_llm(agent)
            agent["memory"] += f"\n--- POST-ELIMINATION INSIGHTS ---\n{memory_response}\n"

    def traitor_discussion_phase(self):
        """Traitors secretly discuss who to eliminate."""
        print("\n--- TRAITOR DISCUSSION PHASE ---")
        traitors = [agent for agent in self.agents if agent["role"] == "Traitor" and "eliminated" not in agent]
        
        if not traitors:
            return
            
        active_faithfuls = [a for a in self.agents if a["role"] == "Faithful" and "eliminated" not in a]
        
        traitor_discussion = []
        for traitor in traitors:
            traitor["current_prompt"] = (
                f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(str(t['id']) for t in traitors)}.\n"
                f"The Faithfuls still in the game are: {', '.join(str(a['id']) for a in active_faithfuls)}.\n"
                "Who do you suggest eliminating next and why? Be strategic to avoid detection."
            )
            
            if traitor_discussion:
                traitor["current_prompt"] += f"\n\nTraitor discussion so far: {' '.join(traitor_discussion)}"
                
            response = self.call_llm(traitor)
            traitor_discussion.append(f"Traitor {traitor['id']}: {response}")
            print(traitor_discussion[-1])
        
        # Second round for traitors to reach consensus
        consensus_discussion = []
        for traitor in traitors:
            traitor["current_prompt"] = (
                "Based on the traitor discussion, who do you now think we should eliminate? "
                f"Discussion: {' '.join(traitor_discussion)}"
            )
            
            response = self.call_llm(traitor)
            consensus_discussion.append(f"Traitor {traitor['id']} concludes: {response}")
            print(consensus_discussion[-1])
        
        # Update traitor memories
        traitor_memory = f"--- SECRET TRAITOR MEETING (ROUND {self.round_number}) ---\n"
        traitor_memory += ' '.join(traitor_discussion + consensus_discussion)
        
        for traitor in traitors:
            traitor["memory"] += f"\n{traitor_memory}\n"
        
        self.traitor_elimination_phase(traitors, active_faithfuls)
    
    def traitor_elimination_phase(self, traitors, active_faithfuls):
        """Traitors vote to eliminate a Faithful."""
        print("\n--- TRAITOR ELIMINATION PHASE ---")
        
        if not traitors or not active_faithfuls:
            return
            
        votes = {}
        for traitor in traitors:
            traitor["current_prompt"] = (
                "Based on the traitor discussion, which Faithful do you vote to eliminate tonight? "
                f"The Faithfuls are: {', '.join(str(a['id']) for a in active_faithfuls)}. "
                "Respond with ONLY the player number."
            )
            
            vote_response = self.call_llm(traitor)
            
            # Extract just the number
            import re
            vote_match = re.search(r'\d+', vote_response)
            if vote_match:
                vote = vote_match.group()
                votes[vote] = votes.get(vote, 0) + 1
                print(f"Traitor {traitor['id']} votes to eliminate Player {vote}")
            else:
                print(f"Traitor {traitor['id']} cast an invalid vote: {vote_response}")
        
        if not votes:
            print("No valid traitor votes were cast!")
            return
            
        # Find the agent with the most votes
        eliminated = max(votes, key=votes.get)
        eliminated_agent = next((a for a in active_faithfuls if str(a["id"]) == eliminated), None)
        
        if eliminated_agent:
            eliminated_agent["eliminated"] = True
            elimination_message = f"Player {eliminated} was eliminated by the traitors in the night."
            print(elimination_message)
            self.history.append(elimination_message)
            self.traitors_last_eliminated = f"Moderator: Player {eliminated} was eliminated last night by the traitors."
            
            # Update all active agents' memory
            for agent in self.agents:
                if "eliminated" not in agent:
                    agent["memory"] += f"\n{elimination_message}\n"
    
    def check_win_conditions(self):
        """Determine if the game has ended."""
        faithfuls = sum(1 for a in self.agents if a["role"] == "Faithful" and "eliminated" not in a)
        traitors = sum(1 for a in self.agents if a["role"] == "Traitor" and "eliminated" not in a)
        
        print(f"\n--- GAME STATUS: {faithfuls} Faithfuls, {traitors} Traitors ---")
        
        if traitors == 0:
            print("\n🎉 FAITHFULS WIN! All traitors have been eliminated.")
            self.game_over = True
            return "Faithfuls"
        elif traitors >= faithfuls:
            print("\n💀 TRAITORS WIN! They now equal or outnumber the Faithfuls.")
            self.game_over = True
            return "Traitors"
        return None

    def run(self):
        """Main game loop."""
        print("\n===== THE TRAITORS GAME =====")
        print(f"Starting with {len(self.agents)} players, including {sum(1 for a in self.agents if a['role'] == 'Traitor')} traitors")
        
        try:
            while not self.game_over:
                self.discussion_phase()
                self.voting_phase()
                self.traitor_discussion_phase()
                winner = self.check_win_conditions()
                
                if winner:
                    break
                    
                self.round_number += 1
                
            # Game summary
            print("\n===== GAME SUMMARY =====")
            print(f"The game lasted {self.round_number} rounds")
            print("Traitors were:", ", ".join(f"Player {a['id']}" for a in self.agents if a["role"] == "Traitor"))
            print("Eliminated agents:", ", ".join(f"Player {a['id']} ({a['role']})" for a in self.agents if "eliminated" in a))
            print("Survivors:", ", ".join(f"Player {a['id']} ({a['role']})" for a in self.agents if "eliminated" not in a))
            
        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
        except Exception as e:
            print(f"Game error: {e}")

# Example usage
if __name__ == "__main__":
    game = TraitorsGame(agent_count=10, traitor_count=3, model="deepseek-chat")
    game.run()