import os
import json
import asyncio
from litellm import Router
from infra.registry import LLM_CONFIG
from datetime import datetime
from avatar_agents.system_prompts import model_selector_prompt
from infra.schemas import ModelDataStoreWithRepoContents, ModelRankingsOutput
from agents import Agent, RunConfig, Runner, SessionSettings, SQLiteSession

DEFAULT_TPM = 5000
DEFAULT_RPM = 10

with open('./model_data_store.json', 'r', encoding='utf-8') as f: #change to .. if moving to someplace below root
    model_data = ModelDataStoreWithRepoContents.model_validate(json.load(f))

class ModelRouter:
    def __init__(self):
        self.system_prompt = model_selector_prompt
        self.agent =  Agent(
                name="ModelSelectorAgent",
                instructions=self.system_prompt,
                model='gemini-3-flash-preview',
                output_type = ModelRankingsOutput,
                tools=[],
                #handoffs=[the_actual_chat_response_agent]
            )
        self.user_prompt = f""" Given the data about the model options in the provided context, 
        return the API request string for the best model choice to respond to the most recent user message 
        in the session conversation history.
        
        Model Options Data: {[str(m.model_dump()) for m in model_data.model_data_store]}""" # change to just str(model_data.model_dump()) if I want repo contents to be considered in selection as well
    
    async def rank_models(self, session):
    #async def rank_models(self, user_state_id):
        #session = SQLiteSession(f'career_avatar_conv_{user_state_id}')
        result = await Runner.run(
            self.agent,
            self.user_prompt,
            session = session
        )

        model_rankings = result.final_output
        return model_rankings
    
    async def construct_litellm_model_list(self, session):
    #async def construct_litellm_model_list(self, user_state_id):
        #model_rankings = await self.rank_models(user_state_id)
        model_rankings = await self.rank_models(session)
        model_list = []

        for ranked_model in model_rankings.model_dump()['model_rankings']:
            api_string = ranked_model['model_api_request_string']
            config = LLM_CONFIG.get(api_string, LLM_CONFIG['unavailable_model'])
            model_list.append({
                'model_name': config['get_base_name'](api_string),
                'model': config['handle_api_path'](api_string),
                'api_key': config['api_key'],
                'order': ranked_model.get('model_ranking', 9999),
                'tpm': config.get('fallback_tpm', DEFAULT_TPM),
                'rpm': config.get('fallback_rpm', DEFAULT_RPM)
            })
        
        litellm_model_list = model_list
        return litellm_model_list
