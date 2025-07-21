import os
import time
import json
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from data_parser import get_product_data, create_embedding_text

def setup_pinecone():
    """
    Loads Pinecone API key from .env file
    """
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in .env file")

    pc = Pinecone(api_key=api_key)
    return pc

def create_pinecone_index(pc: Pinecone, index_name: str):
    """
    Creates a new Pinecone index
    """
    if index_name not in pc.list_indexes().names():
        print(f"Index '{index_name}' not found. Creating a new one...")
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        while not pc.describe_index(index_name).status['ready']:
            print("Waiting for index to be ready...")
            time.sleep(5)
        print(f"Index '{index_name}' created successfully.")
    else:
        print(f"Index '{index_name}' already exists. Skipping creation.")

def embed_and_upsert_data(pc: Pinecone, index_name: str):
    """
    Embeds product data and upserts it into the Pinecone index
    """
    print("Loading sentence transformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Loading product data...")
    products = get_product_data()

    print(f"Preparing {len(products)} products for embedding...")
    index = pc.Index(index_name)

    batch_size = 32
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]

        texts_to_embed = [create_embedding_text(p) for p in batch]

        print(f"Embedding batch {i//batch_size + 1}...")
        embeddings = model.encode(texts_to_embed).tolist()

        vectors_to_upsert = []
        for product, embedding in zip(batch, embeddings):
            metadata = {
                "name": product.get("name"),
                "price": product.get("price"),
                "original_price": product.get("original_price") or 0,
                "discount_label": product.get("discount_label") or "",
                "category": product.get("category"),
                "url": product.get("url"),
                "description": product.get("description"),
                "features": json.dumps(product.get("features", {}))
            }
            vectors_to_upsert.append({
                "id": product["id"],
                "values": embedding,
                "metadata": metadata
            })

        print(f"Upserting batch {i//batch_size + 1} to Pinecone...")
        index.upsert(vectors=vectors_to_upsert)

    print("\n✓ All products have been successfully embedded and stored in Pinecone!")
    stats = index.describe_index_stats()
    print(f"Total vectors in index: {stats['total_vector_count']}")


if __name__ == "__main__":
    INDEX_NAME = "shoe-recommender-index"

    try:
        pinecone_client = setup_pinecone()
        create_pinecone_index(pinecone_client, INDEX_NAME)
        embed_and_upsert_data(pinecone_client, INDEX_NAME)
    except Exception as e:
        print(f"An error occurred: {e}")