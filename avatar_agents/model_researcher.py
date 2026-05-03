from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
    RetryError
)
import asyncio
from requests.exceptions import ConnectionError, Timeout, HTTPError
from pydantic import BaseModel, Field
from infra.schemas import ( 
                    ModelData,
                    WebSearchQueryItem, 
                    WebSearchPlan, 
                    ModelDataStoreWithRepoContents,     
    )
from agents import Agent, WebSearchTool, trace, Runner, gen_trace_id, function_tool
from agents.model_settings import ModelSettings
from tools.functions import linkup_search, read_repo
from avatar_agents.system_prompts import model_researcher_prompt, model_query_string_prompt
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
 ## use the liteLLM load balancing/fallback/router setup instead


model_query_string_agent = Agent(
            name="ModelQueryStringAgent",
            instructions=model_query_string_prompt,
            tools=[function_tool(read_repo)],
            model_settings=ModelSettings(tool_choice="required"),
            output_type=WebSearchPlan,
            model='gemini-3-flash-preview'
        )


class ModelResearcher:
    def __init__(self):
        self.instructions = model_researcher_prompt
        self.model_data_store = []
        self.store_with_repo_contents = ModelDataStoreWithRepoContents(
                                                    repo_content=[],
                                                    model_data_store=self.model_data_store
                                                )
        self.agent =  Agent(
                        name="ModelResearcherAgent",
                        instructions=self.instructions,
                        model='gemini-3-flash-preview',
                        tools=[function_tool(linkup_search),
                                model_query_string_agent.as_tool(tool_name='model_query_string_agent',
                                description='Create a set of web search query strings to gather use-case-specific information on a given LLM.')],
                        model_settings=ModelSettings(tool_choice="required"),
                        output_type=ModelData,
                    )
        
    async def create_model_data_store(
                    self,
                    model_options: tuple[str, ...] = ('gemini-3-flash-preview',
                                            'llama-3.3-70b-versatile',
                                            'openai/gpt-oss-120b',
                                            'qwen/qwen3-32b'
                                            )
                                        ):
        for model in model_options:
            search_results = await Runner.run(self.agent, model)
            self.model_data_store.append(search_results.final_output)
        self.store_with_repo_contents.model_data_store = self.model_data_store
        self.store_with_repo_contents.repo_content = read_repo()
        return self.store_with_repo_contents

