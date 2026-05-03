# onstart: run a function/agent to compare repo files--move this somewhere else related to onstart stuff:
import json
import litellm
import asyncio
from tools.functions import read_repo
from infra.schemas import (
                            RepoSimilarityOutput, 
                            ModelDataStoreWithRepoContents,
                            UserRoleInfoReceiptOutput
                            )
from datetime import datetime
from pathlib import Path
from avatar_agents import ModelResearcher
from agents import SQLiteSession
from persona_docs.vectordb_builder import (
                            idx_schema,
                            get_object_summaries,
                            initialise_redis_index,
                            needs_vectordb_update,
                            store_embeddings
                        )
import logging
logger = logging.getLogger(__name__)

def is_repo_same(model_data_store_json):
    
    user_prompt = f"""You are comparing two snapshots of a Python repository's source code to determine whether the codebase has changed meaningfully since the last model research run.
                    Return {{"is_same": true}} if the differences are trivial, and {{"is_same": false}} if there are meaningful changes.
                    Trivial differences to IGNORE: whitespace, formatting, and line break changes; comment additions, removals, or edits; import additions, removals, or reordering; file renames without content changes; minor refactors like renaming a local variable; adding or removing a few lines within an existing function that don't change its core purpose; docstring changes.
                    Meaningful changes that should trigger a rerun: new modules, classes, or agents added; new tools or tool definitions added; changes to the overall architecture or pipeline flow; new Pydantic models or significant schema changes; new system prompts or significant prompt rewrites; removal of major components.
                    Return ONLY a JSON object: {{"is_same": true}} or {{"is_same": false}}. Do not return any other commentary, prefixes, or explanatory text.
                    
                    Repo snapshot #1 (current): {read_repo()}
                    Repo snapshot #2 (previous): {model_data_store_json.repo_content}
                    """
    
    response = litellm.completion(
                    model="groq/openai/gpt-oss-20b",
                    messages=[ {"role": "user", "content": user_prompt}],
                    response_format=RepoSimilarityOutput   
                )
    return response.choices[0].message.content

def kickstart_model_research(): #run upon receipt of first user message
    data_store_path_string = './model_data_store.json'
    ds_path = Path(data_store_path_string)
    if ds_path.exists():
        with open('./model_data_store.json', 'r', encoding='utf-8') as f: #change to .. if moving to someplace below root
            data = ModelDataStoreWithRepoContents.model_validate(json.load(f))
        repo_similarity_response = is_repo_same(data) # read this in, obviously
        try:
            parsed = RepoSimilarityOutput.model_validate_json(repo_similarity_response)
            repo_same = parsed.is_same
        except Exception:
            logger.error('Response does not conform to model schema!')

    if not repo_same or not ds_path.exists():
        model_researcher = ModelResearcher()
        model_and_repo_data_store = asyncio.run(model_researcher.create_model_data_store())
        filename = 'model_data_store.json'
        try:
            with open(data_store_path_string, 'w') as f:
                json.dump(model_and_repo_data_store.model_dump(), f, indent=4)
                logger.info(f"Successfully wrote data to {data_store_path_string}")
        except IOError as e:
            logger.error(f"Error writing to file: {e}")

async def check_and_build_vectordb(): #run upon receipt of first user message
    object_summaries = get_object_summaries()
    index = await initialise_redis_index(idx_schema)
    sync_data = await needs_vectordb_update(object_summaries, index)
    if any(v for v in sync_data.values()):
        index = await store_embeddings(object_summaries, index, sync_data)
    return index

async def received_user_role_info(user_state_id):
    session = SQLiteSession(f'career_avatar_conv_{user_state_id}') 
    # write out prompt properly--this is a placeholder
    # this output should have Pydantic schema--both for True/False and feedback/what's missing if False
    # if this returns False, should also pass on to response generator to re-prompt for the info
    user_prompt = f"""You are analysing an ongoing conversation on a career avatar chatbpt. Your task is to assess whether 
                    the user has provided information about who they are, the name of their company and the role(s) they are exploring
                    at the company (if any), such that a downstream agent can perform web searches to tailor responses and extract
                    pertinent information from resumes and career history documentation.

                    Conversation history: {session}
                    """ # must include bit that if no roles are being explored, ths should be explicitly confirmed by user
    
    response = litellm.completion(
                    model="groq/openai/gpt-oss-120b",
                    messages=[ {"role": "user", "content": user_prompt}],
                    response_format=UserRoleInfoReceiptOutput  
                )
    return response.choices[0].message.content

