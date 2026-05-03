import io
import os
import json
import boto3
from redis.asyncio import Redis # add redis-py to requirements
from redisvl.index import AsyncSearchIndex
from redisvl.query import FilterQuery
from redisvl.query.filter import Tag
from redisvl.schema import IndexSchema
from pypdf import PdfReader
from infra.schemas import S3ObjectSummary, S3FileData
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag_utils.embedder import get_embedder

import logging
#from collections import OrderedDict
logger = logging.getLogger(__name__)

redis_client = Redis(
        host=os.getenv('REDIS_URL'),
        port=15270,
        decode_responses=True,
        username="default",
        password="*******",
)


## should probably make all the redis calls in this module async -- update: DONE

 # setting index schema--using HNSW to reduce latency & search complexity--important for this app with so many agents & free models
 # move this elsewhere, could be schemas.yaml but already have schemas.py--something else a bit less confusing by name
idx_schema = {
    "index": {
        "name": "s3_embeddings",
        "prefix": "doc"
    },
    "fields": [
        {"name": "s3_key", "type": "tag"},
        {"name": "text_contents", "type": "text"},
        {"name": "last_modified", "type": "numeric"},
        {"name": "embedding", "type": "vector",
         "attrs": {"dims": 512, "algorithm": "hnsw", "distance_metric": "cosine"}}
    ]
}

BUCKET_NAME = 'career-avatar-docs'
#LOCAL_DOWNLOAD_DIR = './downloaded_career_files'
s3 = boto3.resource('s3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name='eu-north-1')

def get_object_summaries() -> list[S3ObjectSummary]:
    bucket = s3.Bucket(BUCKET_NAME)
    raw_summaries = [obj for obj in bucket.objects.all() if not obj.key.endswith('/')]
    object_summaries = [S3ObjectSummary(
                            s3_key=obj.key,
                            last_modified=obj.last_modified.timestamp(),
                                        ) for obj in raw_summaries]
    return object_summaries


def get_s3_file_data(object_summary: S3ObjectSummary) -> S3FileData:
    s3_key, lastmod = object_summary.s3_key, object_summary.last_modified
    file_obj = s3.Object(BUCKET_NAME, object_summary.s3_key).get()
    if '.txt' in s3_key:
        file_text = file_obj['Body'].read().decode('utf-8')
        return S3FileData(s3_key=s3_key, last_modified=lastmod.timestamp(), text_contents= file_text)
    elif '.pdf' in s3_key:
        pdf_bytes = file_obj['Body'].read()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        file_text = f'# Contents of File "{s3_key}":\n'
        for page in reader.pages:
            text = page.extract_text()
            if text:
                file_text += text
        return S3FileData(s3_key=s3_key, last_modified=lastmod.timestamp(), text_contents= file_text)
    else:
        return None

#embeddings_model_name = 'all-MiniLM-L6-v2'
#vectorizer = HFTextVectorizer(embeddings_model_name)

#TODO
async def initialise_redis_index(idx_schema: dict): # move to yaml, the dict is messy and unsophisticated
    #index = AsyncSearchIndex.from_yaml("schema.yaml") 
    index = AsyncSearchIndex.from_dict(
            schema_dict=idx_schema,
            redis_client=redis_client,
            validate_on_load=True # Optional: validates data before loading
        )
    if not await index.exists():
        await index.create()
    return index


async def needs_vectordb_update(object_summaries: list[S3ObjectSummary], index: AsyncSearchIndex) -> dict:
    #sync_data = OrderedDict() # no need bc dicts in Python 3.7+ are ordered, can just zip on regular dict later
    sync_data = {}
    key_filters_list = [Tag("s3_key") == file_data.s3_key for file_data in object_summaries]

    queries = [FilterQuery(
                filter_expression=key_filter,
                num_results=999999,
                return_fields=["s3_key", "last_modified", "id"]
            ) for key_filter in key_filters_list]
    matches_batches = await index.batch_query(queries, batch_size=25)

    for file_data, matches in zip(object_summaries, matches_batches):
        if not matches:
            sync_data[file_data.s3_key] = True
        elif any(float(match['last_modified']) < file_data.last_modified.timestamp() for match in matches):
            doc_ids_to_drop = [doc.get('id', None) for doc in matches]
            await index.drop_documents([doc_id for doc_id in doc_ids_to_drop if doc_id is not None])
            if None in doc_ids_to_drop:
                logger.error(f'Could not remove some chunks in {file_data.s3_key} from index!')
            sync_data[file_data.s3_key] = True
        else:
            sync_data[file_data.s3_key] = False
        
    return sync_data

def _split_text(text_content, chunk_size=384, chunk_overlap=48):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_text(text_content)
    return chunks

async def store_embeddings(object_summaries: list['S3ObjectSummary'], index: AsyncSearchIndex, sync_data: dict):
    vectoriser = get_embedder()

    for summary, needs_sync in zip(object_summaries, sync_data.values()):
        if needs_sync:
            file_data = get_s3_file_data(summary)
            if file_data is not None and file_data.text_contents.strip():
                text_chunks = _split_text(file_data.text_contents)
                data_to_embed = [chunk for chunk in text_chunks if chunk.strip()]
                embeddings = vectoriser.embed_many(data_to_embed) 
                data = []

                for chunk, embedding in zip(data_to_embed, embeddings):
                    data.append({
                        'text_contents': chunk,
                        'embedding': embedding,
                        's3_key': file_data.s3_key,
                        'last_modified': file_data.last_modified,
                    })

                await index.load(data)
                logging.info(f'Stored {file_data.s3_key} with embeddings in Redis Stack vectorDB')

    return index




# at startup, stuff from this module should run as follows:
# 1. get all object summaries from s3 bucket
# 2. run __needs_vectordb_update

