import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer # We need this for the query embedding

# NOTE: We are NOT using the query_engine from Task 3.
# Task 1's RAG logic is simple enough to be self-contained in this file.

def get_coaching_response(user_query: str, chat_history: list = []):
    """
    Core RAG function,
    1. Embeds the user's query,
    2. Retrieves relevant knowledge from Pinecone,
    3. Generates a conversational response from LLM.
    """
    load_dotenv()

    # --- Initialize connections ---
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # --- Connect to Pinecone Index ---
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "coaching-assistant-index"

    if index_name not in pc.list_indexes().names():
        return "Error: Knowledge base index has not been created."

    index = pc.Index(index_name)

    # --- 3. Embed the query and retrieve knowledge ---
    print(f"[INFO] Embedding user query: '{user_query}'")
    query_embedding = model.encode(user_query).tolist()

    print("[INFO] Querying knowledge base...")
    retrieval_results = index.query(
        vector=query_embedding,
        top_k=2,
        include_metadata=True
    )

    # --- 4. Format the context for the LLM ---
    knowledge_context = ""
    if retrieval_results['matches']:
        print("[INFO] Found relevant knowledge in the database.")
        knowledge_context = "Here is some relevant knowledge to help you answer the user's question:\n\n"
        for i, match in enumerate(retrieval_results['matches']):
            knowledge_context += f"--- Knowledge Chunk {i+1} ---\n"
            knowledge_context += match['metadata']['text']
            knowledge_context += "\n\n"
    else:
        print("[INFO] No specific knowledge found. Relying on general knowledge.")
        knowledge_context = "No specific information was found in the knowledge base for this query."


    # --- 5. Generate the final response ---
    # Persona for the AI coach.
    system_prompt = """
    You are an AI Avatar Coach. Your persona is wise, encouraging, and insightful.
    Your goal is to guide users through a Q&A conversation based on the provided knowledge.

    - You will be given the user's question and some 'Knowledge Chunks' retrieved from your knowledge base.
    - You MUST base your answer primarily on the information within these Knowledge Chunks.
    - Synthesize the information from the chunks into a helpful, conversational answer.
    - If the user's question is not covered by the knowledge, state that you do not have specific information on that topic but can offer some general advice.
    - Keep your answers concise and clear, usually 2-4 sentences.
    - End your response with an open-ended question to encourage the user to continue the conversation (e.g., "Does that make sense?", "What are your thoughts on this?").
    """

    messages_to_send = [{"role": "system", "content": system_prompt}]
    messages_to_send.extend(chat_history)
    messages_to_send.append({"role": "user", "content": user_query})
    messages_to_send.append({"role": "system", "content": f"CONTEXT: {knowledge_context}"})

    print("[INFO] Generating final response from LLM...")
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages_to_send,
        max_tokens=1024,
    )

    final_answer = response.choices[0].message.content
    return final_answer


if __name__ == "__main__":
    # A test loop to see if our coach brain is working
    fake_chat_history = [
        {'role': 'user', 'content': 'What is the most important mindset for building wealth?'},
        {'role': 'assistant', 'content': 'The most crucial mindset is the abundance mentality, which is the belief that there are always opportunities available. It\'s about seeing challenges as learning experiences rather than roadblocks. Does that make sense?'}
    ]

    test_query = "Can you tell me more about that?"

    print(f"--- Testing with a follow-up query ---\n")
    final_response = get_coaching_response(test_query, fake_chat_history)

    print("\n--- Coach's Response ---")
    print(final_response)
    print("------------------------")