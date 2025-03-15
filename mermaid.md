# TheTraitors Codebase Architecture Diagrams

This document contains Mermaid diagrams visualizing the architecture and flow of the TheTraitors framework.

## Component Relationships

```mermaid
graph TD
    Main["main.py\n(Entry Point)"] --> Config["utils/config.py\n(Configuration)"]
    Main --> TraitorsGame["traitors_game.py\n(Game Engine)"]
    
    TraitorsGame --> Agent["agent.py\n(Agent Class)"]
    TraitorsGame --> Metrics["utils/metrics.py\n(Game Analytics)"]
    
    Agent --> LLMClient["llm_client.py\n(Client Interface)"]
    LLMClient --> OpenAIClient["OpenAIClient\n(OpenAI, DeepSeek, Together)"]
    LLMClient --> HFClient["HuggingFaceClient\n(Hugging Face)"]
    LLMClient --> MLXClient["MLXChatClient.py\n(Local Apple Silicon)"]
    
    subgraph "Configuration System"
        Config
        YAML["YAML Config Files"]
        CLI["Command Line Arguments"]
        YAML --> Config
        CLI --> Config
    end
    
    subgraph "Game Engine"
        TraitorsGame
        GameState["Game State & History"]
        ResultsDir["Results Directory"]
        TraitorsGame --> GameState
        TraitorsGame --> ResultsDir
    end
    
    subgraph "Agent System"
        Agent
        Memory["Agent Memory"]
        Traits["Agent Traits"]
        Agent --> Memory
        Agent --> Traits
    end
```

## Game Flow Sequence

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Game as TraitorsGame
    participant Agents as Agents
    participant Traitors as Traitor Agents
    participant LLM as LLM Clients
    
    Main->>Game: Initialize with config
    Game->>Agents: Create agents
    Agents->>LLM: Initialize LLM clients
    
    Game->>Agents: Run introduction phase
    Agents->>LLM: Generate introductions
    LLM-->>Agents: Introduction responses
    
    loop Game Rounds
        Game->>Agents: Run discussion phase
        Agents->>LLM: Generate discussion messages
        LLM-->>Agents: Discussion responses
        
        Game->>Agents: Run voting phase
        Agents->>LLM: Generate vote decisions
        LLM-->>Agents: Voting responses
        Game->>Game: Process elimination
        
        Game->>Agents: Post-elimination discussion
        Agents->>LLM: Generate reactions
        LLM-->>Agents: Reaction responses
        
        Game->>Traitors: Run traitor discussion
        Traitors->>LLM: Generate elimination strategy
        LLM-->>Traitors: Strategic responses
        
        Game->>Traitors: Run traitor elimination
        Traitors->>LLM: Generate elimination vote
        LLM-->>Traitors: Vote responses
        Game->>Game: Process traitor elimination
        
        Game->>Game: Check win conditions
    end
    
    Game->>Game: Post-game analysis
    Game->>Main: Return results
```

## Agent Decision Making

```mermaid
flowchart TD
    Start([Agent Turn]) --> GetState[Get Game State]
    GetState --> GetMemory[Retrieve Agent Memory]
    GetMemory --> FormPrompt[Formulate Prompt]
    
    FormPrompt --> Role{Check Role}
    Role -->|Faithful| FaithfulPrompt[Add Faithful-specific Guidance]
    Role -->|Traitor| TraitorPrompt[Add Traitor-specific Guidance]
    
    FaithfulPrompt --> CallLLM[Call LLM Client]
    TraitorPrompt --> CallLLM
    
    CallLLM --> ParseResponse[Parse Response]
    ParseResponse --> ExtractContent[Extract Relevant Content]
    
    ExtractContent --> PhaseCheck{Which Phase?}
    PhaseCheck -->|Discussion| StoreMessage[Store Message in Transcript]
    PhaseCheck -->|Voting| ProcessVote[Process Vote]
    PhaseCheck -->|Reflection| UpdateMemory[Update Agent Memory]
    
    StoreMessage --> End([End Turn])
    ProcessVote --> End
    UpdateMemory --> End
```

## Configuration System

```mermaid
graph LR
    YAML[YAML Config File] --> Parser[Config Parser]
    CLI[Command Line Args] --> ArgsParser[Args Parser]
    
    Parser --> Merger[Config Merger]
    ArgsParser --> Merger
    
    Merger --> GameConfig[Game Configuration]
    Merger --> LLMConfig[LLM Configuration]
    Merger --> AgentConfig[Agent Configuration]
    
    GameConfig --> TraitorsGame
    LLMConfig --> ClientFactory[LLM Client Factory]
    AgentConfig --> AgentCreation[Agent Creation]
    
    ClientFactory --> OpenAI[OpenAI Client]
    ClientFactory --> HF[HuggingFace Client]
    ClientFactory --> MLX[MLX Client]
    
    style YAML fill:#f9f,stroke:#333,stroke-width:2px
    style CLI fill:#f9f,stroke:#333,stroke-width:2px
    style TraitorsGame fill:#bbf,stroke:#333,stroke-width:2px
```

## Results and Analytics Flow

```mermaid
graph TD
    Game[TraitorsGame] --> History[Game History]
    Game --> Votes[Vote Records]
    Game --> Config[Game Configuration]
    
    History --> ResultsDir[Results Directory]
    Votes --> ResultsDir
    Config --> ResultsDir
    
    Votes --> Metrics[Metrics Computation]
    Metrics --> MetricsFile[Metrics File]
    MetricsFile --> ResultsDir
    
    ResultsDir --> ExperimentDir["experiment_name/model/run-X/"]
    
    subgraph "Analysis Outputs"
        ExperimentDir --> HistoryFile["history.txt"]
        ExperimentDir --> VotesFile["votes.csv"]
        ExperimentDir --> ConfigFile["config.yaml"]
        ExperimentDir --> MetricsOutput["metrics.txt"]
        ExperimentDir --> AgentLogs["agent_logs/"]
    end
```
