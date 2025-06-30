/zen:refactor
I am considering using PyDantic Graph for the Command execution system. While the current project needs are focused on sequential step execution, the Graph library already has several features that map well to our needs IMO. 

https://ai.pydantic.dev/graph/

- A Command can manage a GraphRunContext
- Steps can be Node / inherit from BaseNode and the Command would hold the graph of Nodes/Steps
- Iterating over a Graph should give the control flow we need
- We can use BaseStatePersistence to integrate with our prunejuice.db sqlite database: https://ai.pydantic.dev/api/pydantic_graph/persistence/#pydantic_graph.persistence.BaseStatePersistence
- The Human-in-the-Loop example is very relevant to the PruneJuice philosophy where running a command might invoke several steps that require input, each after some underdetermined period of time. https://ai.pydantic.dev/graph/#example-human-in-the-loop
- Determine if session.Session is still needed or if it can be rolled into Command and handled by GraphRunContext; the name Session is confusing when we also have Tmux sessions as a first-class concept so at the very least we should rename it to CommandSession or CommandState for example
