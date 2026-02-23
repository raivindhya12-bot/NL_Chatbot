import chromadb
from chromadb.config import Settings
import json
import yaml
import os

# Load config
with open("config/embedding_config.yaml", 'r') as f:
    config = yaml.safe_load(f)

persist_directory = config['vector_db']['persist_directory']
collection_name = config['vector_db']['collection_name']

client = chromadb.PersistentClient(
    path=persist_directory,
    settings=Settings(anonymized_telemetry=False)
)

# Delete collection if exists
try:
    client.delete_collection(name=collection_name)
    print(f"Deleted collection: {collection_name}")
except Exception as e:
    print(f"Note: {e}")

# Re-create and populate
collection = client.create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}
)

# Load chunks with embeddings
with open("data/processed/chunks_with_embeddings.json", 'r') as f:
    chunks = json.load(f)

ids = []
embeddings = []
documents = []
metadatas = []

for chunk in chunks:
    ids.append(chunk['chunk_id'])
    embeddings.append(chunk['embedding'])
    documents.append(chunk['content'])
    # Clean up metadata - convert all values to basic types for ChromaDB
    meta = chunk.get('metadata', {}).copy()
    for k, v in meta.items():
        if isinstance(v, (dict, list)):
            meta[k] = str(v)
    metadatas.append(meta)

collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=documents,
    metadatas=metadatas
)

print(f"Successfully repopulated collection '{collection_name}' with {len(ids)} chunks.")
