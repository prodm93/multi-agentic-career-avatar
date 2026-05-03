from avatar_agents.system_prompts import response_evaluator_prompt
from infra.schemas import ResponseEvaluationOutput
from agents import Agent, Runner, SQLiteSession


class ResponseEvaluator: # while loop goimg through generator and evaluator in main app.py
    def __init__(self):
        self.system_prompt = response_evaluator_prompt
        self.agent = Agent(
                name="ResponseEvaluationAgent",
                instructions=self.system_prompt,
                model='gemini-3-flash-preview', # maybe consider a different model not in use elsewhere entirely
                tools=[],
                output_type = ResponseEvaluationOutput
            )
        
    async def evaluate_response(self, response, user_state_id): # mention in instructions that both session and converted vector embeddings should be referred to
        session = SQLiteSession(f'career_avatar_conv_{user_state_id}') # might make sense to initialise the session outside class once in the main app.py module--mod this later when it comes to it
        # or maybe not bc we want the session to load new message each time--check later how that logic works in gradio chatbot)
        result = await Runner.run(
            self.agent,
            f'Evaluate the response below as per instructions: \n{response}',
            session = session
        )
        eval_output = result.final_output
        return eval_output
    
    # ^ this is not complete. need to store queried embeddings hits converted to bytes (?) and
    # pass it into both the response generator and eval agent. 

# re: instructions for this agent--the evaluation system prompt should be added with += to the actual generator prompt