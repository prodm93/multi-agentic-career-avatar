from functools import lru_cache
from redisvl.utils.vectorize import HFTextVectorizer

@lru_cache(maxsize=1)
def get_embedder(model_name: str='Qwen/Qwen3-Embedding-0.6B'):  
    return HFTextVectorizer(model=model_name, dims=512)