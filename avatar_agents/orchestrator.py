import inspect
from typing import Literal
from agents import Agent
from avatar_agents import (
    ModelResearcher,
    ModelRouter,
    OpportunityResearcher,
    ResponseGenerator,
    ResponseEvaluator,
    ToneTailor
)
from avatar_agents.system_prompts import orchestrator_prompt
from agents import Agent, RunConfig, Runner, SessionSettings, SQLiteSession
from infra.lazy_init import is_repo_same

#TODO
class OrchestratorAgent:
    def __init__(
            self,
            process_type: Literal['sequential', 'hierarchical'] = 'sequential',
            ):
        self.process_type = process_type
        self.system_prompt= orchestrator_prompt
        self.managed_agent_classes = {
                            agent_name: agent for agent_name, agent in globals().items()
                                if inspect.isclass(agent) and
                                hasattr(agent, '__module__') and
                                agent.__module__=='avatar_agents'
                         }
        self.agent = Agent(
            name='OrchestratorAgent',
            instructions=self.system_prompt,
            model='gemini-3-flash-preview',
            tools=[]
        )

    def orchestrate(self, user_state_id: str):
        # system prompt MUST include asking to refer to session, and address the latest msg while considering the conv history as broader context
        session = SQLiteSession(f'career_avatar_conv_{user_state_id}')
        agent_objects = {k: v() for k, v in self.managed_agent_classes}
        # Basic flow of orchestration:
        # - Read repo + ModelResearcher, file loading + embeddings sync etc should happen ONCE AT RECEIPT OF FIRST USER MESSAGE --> take out of orchestrator
        # - OpportunityResearcher and ToneTailor should run ONCE UPON RECEIVING KEY INFO ABOUT THE USER/ROLE (although should be former to be use-case specific research)
        # the above are handled by lazy_init and main app.py code at entrypoint
        # - ModelRouter should route and choose models by ranking PER NEW USER MESSAGE
        # - ResponseEvaluator should run PER USER MESSAGE

        # need to set up these triggers
        if self.process_type == 'sequential':
            if session[-1]['role'] == 'user':
                litellm_list = agent_objects['ModelRouter'].construct_litellm_model_list(session)
            """more code here"""
            pass
        
        elif self.process_type == 'hierarchical':
            # offload the orchestration by passing read_repo contents to a manager agent LLM, like CrewAI does
            pass

            



