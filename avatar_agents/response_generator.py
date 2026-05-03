import os
import asyncio
from litellm import Router
from avatar_agents.system_prompts import response_generation_prompt
from rag_utils.query_retriever import get_rag_matches
from redisvl.index import AsyncSearchIndex


#TODO
class ResponseGenerator:
    
    # class variable
    _index = None

    @classmethod
    async def get_index(cls):
        if not cls._index:
            cls._index = AsyncSearchIndex.from_existing(
                                        "s3_embeddings",
                                        redis_url=os.getenv('REDIS_URL')
                                    )
        return cls._index # returns coroutine, awaited in get_rag_matches

    def __init__(self):
        pass
    
    #TODO
    def summarise_conversation(self, conv_history): # pass the gradio history here since not doing an agent run
        history_until_latest_msg = conv_history[:-1]
        summary = """LLM call here with a small model like gpt-oss-20b to generate summary from history_until_latest_msg"""
        return summary
    
    async def generate(self, 
                 index: AsyncSearchIndex,
                 litellm_model_list: list[dict], 
                 gradio_history: list[dict],
                 rag_context: str=''):
        
        """first set up RAG with semantic caching for redis.
        then, set up an llm pipeline to construct RAG query that embeds the user query within context of
        conv history -- had thought of applying temporal decay to add most weight to recent message while 
        dumping full sdk session conv history, but this will likely not work well
        so, I need a RAG query constructor agent!
        next, look through my resumes and template letters to tailor both role/industry domain info and tone 
        while sounding as much like me as possible--need a beefed up prompt for this"""
        
        conv_summary = self.summarise_conversation(gradio_history)
        rag_context = get_rag_matches(ResponseGenerator._index, gradio_history[-1], conv_summary)
                
        sorted_model_list = sorted(litellm_model_list, key=lambda x: x['order'])
        
        messages = [
            {'role': 'system', 'content': f'{response_generation_prompt}\nUse this context to answer: {rag_context}'},
            *gradio_history
        ]
        router = Router(model_list=litellm_model_list,
                        allowed_fails=1,
                        cooldown=60)
        response = router.completion(
            model=sorted_model_list[0]['model_name'],
            messages=messages,
        )

        return response.choices[0].message.content

""" 
ResponseGenerator takes in model choice config from ModelRouter via LiteLLM
also takes in RAG hit results

"""