import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


def load_and_chunk_knowledge_base(file_path: str = "knowledge_base.txt"):
    """
    Loads the knowledge base and splits it into chunks (by chapter).
    """
    with open(file_path, "r") as f:
        text = f.read()

    chunks = text.split("Chapter")[1:]
    chunks = [f"Chapter{chunk.strip()}" for chunk in chunks]
    print(f"Loaded and chunked knowledge base into {len(chunks)} chunks.")
    return chunks


def embed_and_store_knowledge(pc: Pinecone, index_name: str, chunks: list):
    """
    Embeds the knowledge chunks and upserts them into the Pinecone index.
    """
    print("Loading sentence transformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    index = pc.Index(index_name)

    batch_size = 32
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        print(f"Embedding batch {i//batch_size + 1}...")
        embeddings = model.encode(batch).tolist()

        ids = [f"chunk_{i+j}" for j in range(len(batch))]

        metadata = [{"text": text_chunk} for text_chunk in batch]

        vectors_to_upsert = list(zip(ids, embeddings, metadata))

        print(f"Upserting batch {i//batch_size + 1} to Pinecone...")
        index.upsert(vectors=vectors_to_upsert)

    print("\n✓ Knowledge base successfully embedded and stored in Pinecone!")
    time.sleep(5)
    stats = index.describe_index_stats()
    print(f"Total vectors in index: {stats['total_vector_count']}")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in .env file")

    pinecone_client = Pinecone(api_key=api_key)

    INDEX_NAME = "coaching-assistant-index"

    if INDEX_NAME not in pinecone_client.list_indexes().names():
        pinecone_client.create_index(
            name=INDEX_NAME, dimension=384, metric="cosine",
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        print(f"Index '{INDEX_NAME}' created. Waiting for it to be ready...")
        time.sleep(10)

    knowledge_chunks = load_and_chunk_knowledge_base("task 1 avatar coach/knowledge_base.txt")
    embed_and_store_knowledge(pinecone_client, INDEX_NAME, knowledge_chunks)