import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

def run_query(query_text: str, top_k: int = 3):
    """
    Takes a user query, embeds it, and retrieves the top_k most relevant products
    """
    load_dotenv()

    print("Initializing connections...")

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in .env file")
    pc = Pinecone(api_key=api_key)

    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    index_name = "shoe-recommender-index"
    if index_name not in pc.list_indexes().names():
        raise ValueError(f"Index '{index_name}' does not exist. Please run embed_and_store.py first.")

    index = pc.Index(index_name)
    print("Successfully connected to Pinecone index.")

    print(f"\nEmbedding your query: '{query_text}'")
    query_embedding = model.encode(query_text).tolist()

    print("Querying Pinecone to find the best matches...")
    query_results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    print("\n--- Top Recommendations ---")
    if not query_results['matches']:
        print("No matches found.")
        return

    for i, result in enumerate(query_results['matches']):
        metadata = result['metadata']
        print(f"\n{i+1}. {metadata.get('name', 'N/A')} (Score: {result['score']:.4f})")
        print(f"   Price: RM {metadata.get('price', 'N/A'):.2f}")
        print(f"   Category: {metadata.get('category', 'N/A')}")
        print(f"   Description: {metadata.get('description', 'N/A')}")

        try:
            features = json.loads(metadata.get('features', '{}'))
            print("   Features:")
            for category, feature_list in features.items():
                print(f"     - {category.replace('_', ' ').title()}:")
                for item in feature_list:
                    print(f"       - {item}")
        except (json.JSONDecodeError, TypeError):
            print("   (Could not parse features)")

    print("\n---------------------------\n")

    return query_results

if __name__ == "__main__":
    # --- Example Queries to Test ---
    # query1 = "a bouncy shoe that is good for running"
    # query2 = "cheap shoes for casual walking"
    # query3 = "what do you have for kids that is easy to put on?"
    # query4 = "i need a shoe that is comfortable for someone with wide feet" # Not in data, good test

    try:
        user_query = "a bouncy shoe that is good for running"
        run_query(user_query)
    except Exception as e:
        print(f"An error occurred: {e}")