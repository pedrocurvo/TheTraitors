import random
from openai import OpenAI

class TraitorsGame:
    def __init__(self, agent_count=10, traitor_count=3):
        self.agents = self.create_agents(agent_count, traitor_count)
        self.game_over = False
        self.history = []  # Stores past discussions

        self.traitors_last_eliminated = None

        # Initialize the client
        self.client = OpenAI(api_key='your_api_key_here')

    def create_agents(self, agent_count, traitor_count):
        """Initialize agents with unique roles."""
        agents = [{"id": i,
                   "role": "Faithful",
                   "memory": "",
                   "model": "gpt-4o-mini"}
                   for i in range(agent_count)]
        traitors = random.sample(agents, traitor_count)
        for agent in traitors:
            agent["role"] = "Traitor"
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
            return ("You are a Traitor in The Traitors game.\n"
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

        response = self.client.chat.completions.create(
            model=agent["model"],
            messages=[
                {"role": "system", "content": f"You are Agent {agent['id']}. {role_description}\n\nYour memory: {agent_memory}"},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]

    def discussion_phase(self):
        """Agents communicate and discuss who to vote out."""
        print("\n--- DISCUSSION PHASE ---")
        new_discussions = []
        if self.traitors_last_eliminated:
            new_discussions.append(self.traitors_last_eliminated)
        for agent in self.agents:
            if "eliminated" not in agent:
                agent["current_prompt"] = "You are in a room with other agents to discuss who the traitor is. The current players are: " \
                                            f"{', '.join(str(a['id']) for a in self.agents if 'eliminated' not in a)}. " \
                                            f"The players eliminated so far are: {', '.join(str(a['id']) for a in self.agents if 'eliminated' in a)}. " \
                                            "Who do you suspect is a traitor and why?"
                if new_discussions:
                    agent["current_prompt"] += f" Keep the ongoing discussion: {' '.join(new_discussions)}"
                response = self.call_llm(agent)
                new_discussions.append(f"Agent {agent['id']}: {response}")
                print(new_discussions[-1])
        
        for agent in self.agents:
            if "eliminated" not in agent:
                agent["current_prompt"] = f"Summarize the most important points you want to remember for voting, based on this discussion: {' '.join(new_discussions)}"
                memory_response = self.call_llm(agent)
                agent["memory"] += memory_response
    
    def voting_phase(self):
        """Agents vote to eliminate a player."""
        print("\n--- VOTING PHASE ---")
        votes = {}
        for agent in self.agents:
            if "eliminated" not in agent:
                agent["current_prompt"] = f"Based on your memory: {agent['memory']}\nWho are you voting to eliminate? Just say the agent number."
                vote_response = self.call_llm(agent)  
                votes[vote_response] = votes.get(vote_response, 0) + 1
                print(f"Agent {agent['id']} votes for Agent {vote_response}")
        
        eliminated = max(votes, key=votes.get)
        for agent in self.agents:
            if str(agent["id"]) == eliminated:
                agent["eliminated"] = True
                print(f"Agent {agent['id']} was eliminated. They were a {agent['role']}.")
                self.history.append(f"Agent {agent['id']} was eliminated. They were a {agent['role']}.")
        
        self.post_elimination_discussion(eliminated)
        self.traitor_discussion_phase()
    
    def post_elimination_discussion(self, eliminated):
        """Allow agents to discuss after elimination is revealed."""
        print("\n--- POST-ELIMINATION DISCUSSION ---")
        discussion_prompts = []
        for agent in self.agents:
            if "eliminated" not in agent:
                agent["current_prompt"] = f"You are in a room with other agents to discuss the elimination of Agent {eliminated}. " \
                                            f"Agent {eliminated} was eliminated and was a {agent['role']}. What are your thoughts?"
                if discussion_prompts:
                    agent["current_prompt"] += f" Keep the ongoing discussion: {' '.join(discussion_prompts)}"
                response = self.call_llm(agent)
                discussion_prompts.append(f"Agent {agent['id']}: {response}")
                print(discussion_prompts[-1])
        
        for agent in self.agents:
            if "eliminated" not in agent:
                agent["current_prompt"] = f"Summarize the most important points you want to remember for voting, based on this discussion: {' '.join(discussion_prompts)}"
                memory_response = self.call_llm(agent)
                agent["memory"] += memory_response

    def traitor_discussion_phase(self):
        """Traitors secretly discuss who to eliminate."""
        print("\n--- TRAITOR DISCUSSION PHASE ---")
        traitors = [agent for agent in self.agents if agent["role"] == "Traitor" and "eliminated" not in agent]
        current_discussion = []
        for traitor in traitors:
            traitor["current_prompt"] = f"You are in a room with other traitors to discuss who to eliminate next. " \
                                        f"The current traitors are: {', '.join(str(t['id']) for t in traitors)}. " \
                                        f"The players eliminated so far are: {', '.join(str(a['id']) for a in self.agents if 'eliminated' in a)}. " \
                                        f"The players still in the game are: {', '.join(str(a['id']) for a in self.agents if 'eliminated' not in a)}. " \
                                        f"Who do you suggest to eliminate next as a traitor and why?"
            if current_discussion:
                traitor["current_prompt"] += f" Ongoing discussion: {' '.join(current_discussion)}"
            response = self.call_llm(traitor)
            current_discussion.append(f"Traitor {traitor['id']}: {response}")
            print(current_discussion[-1])
        
        for traitor in traitors:
            traitor["current_prompt"] = f"Summarize the most important points from this discussion: {' '.join(current_discussion)}"
            memory = self.call_llm(traitor)
            traitor["memory"] += memory
        
        self.traitor_voting_phase(memory)
    
    def traitor_voting_phase(self, memory):
        """Traitors vote to eliminate a Faithful."""
        print("\n--- TRAITOR VOTING PHASE ---")
        traitors = [agent for agent in self.agents if agent["role"] == "Traitor" and "eliminated" not in agent]
        votes = {}
        for traitor in traitors:
            traitor["current_prompt"] = f"Based on your memory of the discussion with the traitors: {memory}\n And your whole memory.\nWho are you voting to eliminate? Just say the agent number. The faithfuls are: {', '.join(str(a['id']) for a in self.agents if a['role'] == 'Faithful' and 'eliminated' not in a)}"
            vote = self.call_llm(traitor)
            votes[vote] = votes.get(vote, 0) + 1
            print(f"Traitor {traitor['id']} votes for Agent {vote}")
        
        eliminated = max(votes, key=votes.get)
        for agent in self.agents:
            if str(agent["id"]) == eliminated:
                agent["eliminated"] = True
                print(f"Agent {agent['id']} was eliminated by the traitors.")
                self.history.append(f"Agent {agent['id']} was eliminated by the traitors.")
                self.traitors_last_eliminated = f"Moderator: Agent {agent['id']} was eliminated last night by the traitors."

    
    def check_win_conditions(self):
        """Determine if the game has ended."""
        faithfuls = sum(1 for a in self.agents if a["role"] == "Faithful" and "eliminated" not in a)
        traitors = sum(1 for a in self.agents if a["role"] == "Traitor" and "eliminated" not in a)
        if traitors == 0:
            print("Faithfuls win!")
            self.game_over = True
        elif traitors >= faithfuls:
            print("Traitors win!")
            self.game_over = True

    def run(self):
        """Main game loop."""
        while not self.game_over:
            self.discussion_phase()
            self.voting_phase()
            self.traitor_discussion_phase()
            self.traitor_voting_phase()
            self.check_win_conditions()

game = TraitorsGame()
game.run()