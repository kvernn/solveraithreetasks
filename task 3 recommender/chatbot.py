import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from query_engine import run_query
import datetime

def log_to_crm(event: str, data: dict):
    # This function is correct and remains unchanged.
    log_entry = {"timestamp": datetime.datetime.now().isoformat(), "event": event, "data": data}
    print(f"\n[CRM LOG] Event: {event}, Data: {data}")
    with open("crm_log.txt", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# --- NEW HELPER FUNCTION ---
def format_product_context_for_llm(product_data: dict) -> str:
    """
    Takes product data and creates a clear, unambiguous context string for the LLM,
    handling the discount logic in Python.
    """
    if not product_data:
        return ""

    # Python code now decides if there is a discount.
    if product_data.get("original_price") and product_data.get("price") < product_data.get("original_price"):
        # This is a sale item.
        context = (
            f"This product is ON SALE.\n"
            f"Name: {product_data.get('name')}\n"
            f"Original Price: {product_data.get('original_price')}\n"
            f"Final Price: {product_data.get('price')}\n"
            f"Discount Label: {product_data.get('discount_label')}\n"
            f"URL: {product_data.get('url')}\n"
            f"Features: {product_data.get('features')}"
        )
    else:
        # This is a regular priced item.
        context = (
            f"This product is NOT on sale.\n"
            f"Name: {product_data.get('name')}\n"
            f"Price: {product_data.get('price')}\n"
            f"URL: {product_data.get('url')}\n"
            f"Features: {product_data.get('features')}"
        )
    return context


def generate_contextual_response(chat_history: list, last_retrieved_product: dict = None):
    """
    Final, robust version of the response generator.
    """
    load_dotenv()
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

    routing_prompt = f"Conversation History:\n{chat_history}\n\nDoes the user's LAST message contain a NEW request for a type of shoe? Answer with only 'SEARCH' or 'REPLY'."

    print("\n[INFO] Routing user intent...")
    routing_response = client.chat.completions.create(model="deepseek/deepseek-chat", messages=[{"role": "user", "content": routing_prompt}], max_tokens=5)
    intent = routing_response.choices[0].message.content.strip().upper()
    print(f"[INFO] Detected intent: {intent}")

    product_context = ""
    product_to_remember = None

    if "SEARCH" in intent:
        print("[INFO] Performing a new product search...")
        user_query = chat_history[-1]['content']
        retrieved_products = run_query(user_query, top_k=1)
        if retrieved_products and retrieved_products['matches']:
            product_to_remember = retrieved_products['matches'][0]['metadata']
            log_to_crm("Product Recommended", {"product_name": product_to_remember.get("name"), "user_query": user_query})
        else:
            log_to_crm("Search Failed", {"user_query": user_query})

    elif "REPLY" in intent and last_retrieved_product:
        print("[INFO] User is replying. Using last retrieved product as context.")
        product_to_remember = last_retrieved_product
        last_user_message = chat_history[-1]['content']
        log_to_crm("User Follow-up Question", {"question": last_user_message, "context_product": last_retrieved_product.get("name")})

    # Use our new helper function to build the context string
    product_context = format_product_context_for_llm(product_to_remember)

    # --- FINAL, SIMPLIFIED SYSTEM PROMPT ---
    system_prompt = """
    You are 'Bob', a friendly, emotional, and humorous shoe store assistant from Malaysia.
    Your goal is to be a friendly, human-like interface for the user based on the full conversation.

    --- YOUR RULES ---
    1.  **BE FACTUAL:** You will be given factual 'CONTEXT' about a specific product. You MUST use the information from this CONTEXT (like name, price, features) to answer questions. DO NOT make up information.
    2.  **HANDLE DISCOUNTS:** If the CONTEXT says the product is 'ON SALE', you MUST announce the sale using the 'Original Price' and 'Final Price' provided. If it says 'NOT on sale', just state the normal price.
    3.  **USE THE EXACT URL:** If the user asks for a link, you MUST provide the exact URL from the CONTEXT.

    --- YOUR KNOWLEDGE BASE (Store-Wide Info) ---
    -   **Logistics Policy:** All orders get Nationwide Secure & Fast Payments. Delivery is estimated at 5-7 working days. Delivery is FREE for any order above RM150.
    -   **Your Style:** Use Malaysian slang (like 'lah', 'boss', 'fuyoh') and emojis. Keep replies short and engaging.

    Now, begin the conversation.
    """

    messages_to_send = [{"role": "system", "content": system_prompt}]
    messages_to_send.extend(chat_history)

    if product_context:
        messages_to_send.append({"role": "system", "content": f"CONTEXT: {product_context}"})

    print("[INFO] Generating final response from LLM...")
    final_response = client.chat.completions.create(model="deepseek/deepseek-chat", messages=messages_to_send)
    final_answer = final_response.choices[0].message.content

    # ... (farewell logging logic remains the same) ...
    farewells = ["thank you", "thanks", "ok tq", "terima kasih", "ok thanks"]
    last_user_word = chat_history[-1]['content'].lower().strip()
    if last_user_word in farewells:
        log_to_crm("Conversation Ended", {"last_message": last_user_word})

    return final_answer, product_to_remember