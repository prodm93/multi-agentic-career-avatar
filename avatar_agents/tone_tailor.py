from pathlib import Path
from avatar_agents.system_prompts import tone_tailor_prompt
from agents import Agent, RunConfig, Runner, SessionSettings, SQLiteSession

#TODO
class ToneTailor:
    def __init__(self):
        self.system_prompt = tone_tailor_prompt
        self.agent =  Agent(
                name="ToneTailorAgent",
                instructions=self.system_prompt,
                model='gemini-3-flash-preview',
                tools=[],
                #handoffs=[the_actual_chat_response_agent]
            )
    
    def tailor_tone(self, **args):
        # method should take in:
        # - my template letters (whole or chunks? decide based on chunk size and most accessible source of docs in codebase)
        # - info about role, company and user chatting with the avatar
        # to determine the most suitable 'me'-tone for the chat
        # runs ONCE after opportunity researcher
        pass
        
        


        
