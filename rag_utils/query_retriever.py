import os
from redisvl.query import HybridQuery
from redisvl.index import AsyncSearchIndex
from redisvl.utils.rerank import HFCrossEncoderReranker
from redisvl.extensions.llmcache import SemanticCache
from flashrank import Ranker, RerankRequest
from rag_utils.embedder import get_embedder
import numpy as np

# load and initialise index here--should be done after repo sync. should I save updated/checked index to yaml?

# idea: the generator agent returns both the initial response and a quick summary of the conv history so far
# since it will already be getting conv history as session anyways. then, for queries, pass both the
# latest message and summary of conv up until that point
# trying to see if there is a way to weight the latest message higher than conv

# there doesn't seem to be an analogous AsyncSemanticCache, otherwise should've been run async
llmcache = SemanticCache(
    redis_url=os.getenv('REDIS_URL'),
    distance_threshold=0.2, # Lower = stricter matching
    vectorizer=get_embedder() # E.g. HuggingFace
)

def _weight_input_vectors(latest_message: str, conversation_summary: str):
    vectoriser = get_embedder()
    latest_message_embed = vectoriser.encode(latest_message)
    conv_summary_embed = vectoriser.encode(conversation_summary)
    weighted = (latest_message_embed * 0.75) + (conv_summary_embed * 0.25)
    return weighted /  np.linalg.norm(weighted)

async def get_rag_matches(index: AsyncSearchIndex, latest_message: str, conversation_summary: str, rerank_method: str='flash_rerank'):
    weighted_cache_query = f'{latest_message} ({conversation_summary})=>{{$weight: 1.5;}}'
    cached_rag_match = llmcache.check(prompt=weighted_cache_query)
    if cached_rag_match:
        return cached_rag_match
    else:
        weighted_vector_query = _weight_input_vectors(latest_message, conversation_summary)
        weighted_text_query = f'({latest_message})=>{{$weight: 3.0;}} {conversation_summary}'
        # blended search rather than separate queries for latest msg & conv history to facilitate
        # better anaphora resolution, esp w/ singular chatbot messages often being vague w/o context
        hybrid_query = HybridQuery(
                text=weighted_text_query,
                text_field_name="text_contents",
                vector=weighted_vector_query,
                vector_field_name="embedding",
                text_scorer="BM25STD",
                yield_text_score_as="text_score",
                yield_vsim_score_as="vector_similarity",
                combination_method="LINEAR",
                linear_alpha=0.4,
                yield_combined_score_as="hybrid_score",
                num_results=20,
                return_fields=["text_contents", "s3_key"],
                stopwords="english",
            )
        hybrid_rag_results = await index.query(hybrid_query)

        # reranking only by latest message bc hybrid RAG already surfaced a larger pool of relevant results
        # based on history/broader context
        if rerank_method == 'cross_encoder':
            reranker = HFCrossEncoderReranker(
                model_name='mixedbread-ai/mxbai-rerank-xsmall-v1',
                rank_by="text_contents",
                limit=5  
            )
            reranker_docs = [{'content': r['text_contents'], **r} for r in hybrid_rag_results]
            raw_reranked_results = reranker.rank(query=latest_message, docs=reranker_docs)
            reranked_results = [{'text': result['text_contents'], 'score': result['score']} for result in raw_reranked_results]

        elif rerank_method == 'flash_rerank':
            reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")
            passages = [{"id": i,"text": result["text_contents"], "meta": result}
                            for i, result in enumerate(hybrid_rag_results)]
            rerank_request = RerankRequest(query=latest_message, passages=passages)
            #raw_reranked_results is a list of dicts with "id", "text", "score", "meta"
            raw_reranked_results = reranker.rerank(rerank_request)[:5]
            reranked_results = [{'text': result['text'], 'score': result['score']} for result in raw_reranked_results]

        # initial hybrid search using both msg & history, then reranking w/ msg only to sharpen--wide net, tight filter

        llmcache.store(prompt=weighted_cache_query, response=reranked_results)
        return reranked_results 
