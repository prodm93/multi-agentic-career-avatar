from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
    RetryError
)
# might not need tenacity with litellm load balancing
from agents import Agent, WebSearchTool, trace, Runner, gen_trace_id, SQLiteSession
from agents.model_settings import ModelSettings
from avatar_agents.system_prompts import opportunity_researcher_prompt
from tools.sdk_wrapped_tools import handrolled_toolkit
from infra.schemas import OpportunityResearchOutput
import logging
logger = logging.getLogger(__name__)

# might be good for chat agent to do handoff to this agent as soon as it has all the info
class OpportunityResearcher: #input here will be company and roles from conv history
    def __init__(self): # gets passed in within main app.py module
        self.system_prompt= opportunity_researcher_prompt
        self.agent = Agent(
                name="OpportunityResearcherAgent",
                instructions=self.system_prompt,
                model='gemini-3-flash-preview',
                tools=[
                    handrolled_toolkit.get('search_company'), 
                    handrolled_toolkit.get('search_role_requirements')
                ],
                model_settings=ModelSettings(tool_choice="required"),
                output_type = OpportunityResearchOutput
            )
        self.opportunity_research = None
    
    #TODO
    async def research_role_context(self, user_state_id):
        session = SQLiteSession(f'career_avatar_conv_{user_state_id}') # might make sense to initialise the session outside class once in the main app.py module--mod this later when it comes to that
        # or maybe not bc we want the session to load new message each time--check later how that logic works in gradio chatbot)
        result = await Runner.run(
            self.agent,
            # insert initial user prompt here
            session = session,
        )

        self.opportunity_research = result.final_output
        return self.opportunity_research