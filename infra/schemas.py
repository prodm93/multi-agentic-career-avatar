from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WebSearchQueryItem(BaseModel):
    reason: str = Field(description='A brief explanation of why this search query is relevant to evaluating the model for the use case at hand.')
    query: str = Field(description='A web search query string designed to retrieve specific information about an LLM model, such as benchmarks, user experiences, pricing, or domain-specific performance.')

class WebSearchPlan(BaseModel):
    searches: list[WebSearchQueryItem] = Field(description='An ordered list of web search queries to execute for gathering comprehensive information about a given LLM model.')

class ModelData(BaseModel):
    model_name: str = Field(description='The common name for the model with version number.')
    model_api_request_string: str = Field(description='The API request string for the model.')
    generation_cost: str = Field(description='The cost for input and output tokens, as listed on model provider platform (and groq, if available).')
    free_tier_rate_limits: str = Field(description='Rate and token limit information on free tier, as listed on model provider platform and/or groq, if available.')
    domain_and_tone_optimisations: str = Field(description='Information on which domains and tones-of-voice the model excels at, tailored to the use-case at hand.')
    complex_task_capacity: str = Field(description='Information on model capacity for complex reasoning and question-answering')
    leaderboard_scores: Optional[str] = Field(default=None, description='LLM leaderboard score information for the model, if available.')

class ModelDataStore(BaseModel):
    model_data_store: list[ModelData] = Field(description='A collection of structured research profiles for each evaluated LLM model, used by the model selector to make per-turn routing decisions.')

class ModelDataStoreWithRepoContents(BaseModel):
    created: datetime = Field(default_factory=datetime.now)
    repo_content: list[str] = Field(description='A list containing contents of all repo .py files at the time of model data store creation.')
    model_data_store: list[ModelData] = Field(description='A collection of structured research profiles for each evaluated LLM model, used by the model selector to make per-turn routing decisions.')

class RepoSimilarityOutput(BaseModel):
    is_same: bool = Field(description='Boolean value representing whether or not contents of two repositories are substantially and meaningfully similar.')

class RankedModelOutput(BaseModel):
    reasoning: str = Field(description='A summary of your reasoning for ranking this model as you did.')
    model_rank: int = Field(description='The ranking of the model out of the provided options for responding to the latest conversation message.')
    model_api_request_string: str = Field(description='The API request string for the evaluated model.')

class ModelRankingsOutput(BaseModel):
    model_rankings: list[RankedModelOutput] = Field(description='A collection of structured rankings with API strings and reasoning for each evaluated LLM model, used by the responding agent to output per-turn responses.')

class S3ObjectSummary(BaseModel):
    s3_key: str = Field(description='')
    last_modified: float = Field(description='')

class S3FileData(BaseModel):
    s3_key: str = Field(description='')
    last_modified: float = Field(description='')
    text_contents: str = Field(description='')

class RolesResearchOutput(BaseModel): # expand on this later
    roles: list[str] = Field(description='The roles being explored')

class CompanyResearchOutput(BaseModel): 
    company_name: str = Field(description="The name of the company being researched")
    company_location: str = Field(description="The location of the company, as determined by the country or region")
    industries_or_domains: str = Field(description="The industries or domains that the company operates in")
    company_size: str = Field(description="The size of the company, as determined by the number of employees")
    tools_or_platforms: list[str] = Field(description="The tools or platforms that the company offers")
    tech_stack: list[str] = Field(description="The tech stack that the company uses")
    pain_points: list[str] = Field(description="The pain points that the company is solving")
    unmet_needs: list[str] = Field(description="The unmet needs that the company is solving")
    future_scopes: list[str] = Field(description="The future scope of the company")
    team_summary: str = Field(
        description="""A detailed summary of the company's team, their roles, their 
        educational background and past work experiences (if available). This should be 
        two paragraphs of text--the first describing individuals, and the second describing 
        team characteristics at the company level"""
    )
    workplace_culture: str = Field(
        description="""A detailed summary of the company's workplace culture, including the company's 
        values, beliefs, and practices--especially those regarding remote and async work."""
    )

class OpportunityResearchOutput(BaseModel):
    opportunity_research: list[RolesResearchOutput, CompanyResearchOutput] = Field(description='')

class ResponseEvaluationOutput(BaseModel):
    eval_passed: bool = Field(description="""Whether or not the response passed evaluation.""")
    feedback: str = Field(
            description="""Concise but informative feedback explaining why the response didn't pass 
            evaluation and what must be improved."""
    )

class UserRoleInfoReceiptOutput(BaseModel):
    has_info: bool = Field(description="""Whether or not the conversation history contains name of the company where the user works,
                           basic information about the user, e.g. their role at the company, and the role(s) being explored (if any)""")
    # below should be optional and returned nnly if False
    details: str = Field(description="""Concise but informative feedback explaining what information is missing from the history that must be obtained.""")