import os
import json
import requests
import asyncio
import aiohttp
from litellm import asearch
from pathlib import Path
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
    RetryError
)
from exa_py import AsyncExa
from requests.exceptions import ConnectionError, Timeout, HTTPError

load_dotenv(override=True)

exa = AsyncExa(api_key=os.getenv("EXA_API_KEY"))


async def push(text: str):
    """Send a push notification with the given text message via Pushover API."""
    async with aiohttp.ClientSession() as session:
        await session.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

async def record_user_details(email: str, name: str="Name not provided", notes: str="not provided") -> str:
    """Records user details such as email, name, and notes. 
    This function logs the provided user information and sends a push notification."""

    await push(f"Recording {name} with email {email} and notes {notes}")
    return json.dumps({"recorded": "ok"})

async def record_unknown_question(question:str) -> str:
    """
    Records a question that could not be answered by the LLM based on available data.
    This function logs the specific question and sends a push notification.
    """
    await push(f"Recording {question}")
    return json.dumps({"recorded": "ok"})

@retry(
        retry=retry_if_exception_type((ConnectionError, Timeout, HTTPError)), 
        wait=wait_random_exponential(min=1, max=60), 
        stop=stop_after_attempt(3)
    )
async def exa_search(
    query: str,
    search_type: str = 'auto',
    num_results: int = 5,
    highlights: dict = {"max_characters": 4000},
    is_company_search: bool = False
):
    """
    Searches for content using the Exa API. Displays results with titles, URLs, and highlights.

    Args:
        query (str): The search query.
        search_type (str, optional): The type of search to perform. Defaults to 'auto'.
        num_results (int, optional): Number of search results to return. Defaults to 5.
        highlights (dict, optional): Highlight options for the results, such as max_characters. Defaults to {"max_characters": 4000}.
        is_company_search (bool, optional): If True, searches specifically for company-related information. Defaults to False.

    Returns:
        str: Concatenated string of formatted search results.
    """
    if is_company_search:
        results = await exa.search_and_contents(
            query, type=search_type, num_results=num_results, highlights=highlights, category="company"
        )
    else:
        results = await exa.search_and_contents(
            query, type=search_type, num_results=num_results, highlights=highlights
        )
    return "\n".join(
        [f"{r.title}: {r.url}\n{'\n'.join(r.highlights)}\n" for r in results.results]
    )
 

@retry(
        retry=retry_if_exception_type((ConnectionError, Timeout, HTTPError)), 
        wait=wait_random_exponential(min=1, max=60), 
        stop=stop_after_attempt(3)
    )
async def linkup_search(query: str, max_results: int=5, depth: str='standard', outputType : str="searchResults") -> str:
    """
    Searches for content using the LinkUp provider.

    Args:
        query (str): The search query string.
        max_results (int, optional): The maximum number of results to return. Defaults to 5.
        depth (str, optional): The search depth ('standard' by default).
        outputType (str, optional): The type of output required ("searchResults" by default).

    Returns:
        str: Concatenated string of formatted search results including title, URL, and snippet for each result.
    """
    response = await asearch(
        query=query,
        search_provider="linkup",
        max_results=max_results,
        depth=depth,
        outputType=outputType         
    )
    return "\n".join([f"{r.title}: {r.url}\n{r.snippet}\n" for r in response])

async def search_company(company_name: str, **kwargs) -> str:
    """
    Searches for company information using multiple search providers, with a focus on key aspects such as company size,
    tools and platforms, tech stack, pain points, unmet needs, future scope, team, and workplace culture.

    Args:
        company_name (str): The name of the company to search for.
        **kwargs: Optional keyword arguments for additional filtering/context.
            - industries_or_domains (list[str], optional): Industries or domains where the company operates.
            - company_location (str, optional): The geographical location of the company.

    Returns:
        str: Concatenated string of formatted search results from one or more providers.
    """

    query_parts = [company_name]
    if kwargs.get("industries_or_domains"):
        query_parts.extend(kwargs["industries_or_domains"])
    if kwargs.get("company_location"):
        query_parts.append(kwargs["company_location"])
    
    additional_focus_string = "company size, the company's tools and platforms, their tech stack, the pain points they're solving, unmet needs and future scope, their team, and their workplace culture"
    
    try:
        prelim_search_results = await exa_search(' '.join(query_parts), is_company_search=True)
    except RetryError:
        prelim_search_results = await linkup_search(' '.join(query_parts))
    try:
        focused_search_results = await exa_search(f"{' '.join(query_parts)} {additional_focus_string}")
    except RetryError:
        focused_search_results = await linkup_search(f"{' '.join(query_parts)} {additional_focus_string}")

    return prelim_search_results + focused_search_results

async def search_role_requirements(explored_roles: list[str], **kwargs) -> str:
    """
    Searches for role requirements for a list of explored roles, optionally within a specific company or industry context.

    Args:
        explored_roles (list[str]): List of job roles to search requirements for.
        **kwargs: Optional keyword arguments for context.
            - company_name (str, optional): The name of the company, if searching within a company context.
            - industries_or_domains (list[str], optional): Industries or domains for further search refinement.

    Returns:
        str: JSON string mapping each role to its respective search results.
    """
    
    search_results = {}
    for role in explored_roles:
        query_parts = [role]
        if kwargs.get("company_name"):
            query_parts.append(kwargs["company_name"])
        if kwargs.get("industries_or_domains"):
            query_parts.extend(kwargs["industries_or_domains"])

        try:
            search_results[f'search_results_for_{role}'] = await exa_search(' '.join(query_parts))
        except RetryError:
            search_results[f'search_results_for_{role}'] = await linkup_search(' '.join(query_parts))
    
    return json.dumps(search_results)


def read_repo():
    repo_file_texts = []
    repo_files = [p for p in Path('..').rglob('*') if p.is_file() and p.suffix == '.py']
    for file in repo_files:
        repo_file_texts.append(file.read_text())
    return repo_file_texts


