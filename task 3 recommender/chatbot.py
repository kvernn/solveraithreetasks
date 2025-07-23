import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from query_engine import run_query
import datetime

def log_to_crm(event: str, data: dict):
    log_entry = {"timestamp": datetime.datetime.now().isoformat(), "event": event, "data": data}
    print(f"\n[CRM LOG] Event: {event}, Data: {data}")
    with open("crm_log.txt", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def generate_contextual_response(chat_history: list, last_retrieved_product: dict = None):
    """
    Enhanced response generator with mood detection, budget awareness, and personalization.
    """
    load_dotenv()
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

    # Get the last user message
    last_user_message = chat_history[-1]['content']

    # Detect mood and context
    print("\n[INFO] Analyzing user mood and context...")
    user_mood = detect_user_mood(last_user_message, client)
    budget_min, budget_max = extract_budget_from_text(last_user_message)

    # Log mood and budget info
    log_to_crm("User Context Analysis", {
        "mood": user_mood,
        "budget_range": f"RM{budget_min}-RM{budget_max}" if budget_min else "Not specified",
        "message": last_user_message
    })

    # Routing logic
    routing_prompt = f"Conversation History:\n{chat_history}\n\nDoes the user's LAST message contain a NEW request for a type of shoe? Answer with only 'SEARCH' or 'REPLY'."

    print("\n[INFO] Routing user intent...")
    routing_response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": routing_prompt}],
        max_tokens=5
    )
    intent = routing_response.choices[0].message.content.strip().upper()
    print(f"[INFO] Detected intent: {intent}")

    product_context = ""
    product_to_remember = None

    if "SEARCH" in intent:
        print("[INFO] Performing a new product search...")
        # Pass budget range to search
        retrieved_products = run_query(
            last_user_message,
            top_k=3,
            budget_range=(budget_min, budget_max)
        )

        if retrieved_products and retrieved_products['matches']:
            if user_mood.get("emotion") == "budget-conscious" and len(retrieved_products['matches']) > 1:
                product_to_remember = min(
                    retrieved_products['matches'],
                    key=lambda x: x['metadata'].get('price', float('inf'))
                )['metadata']
            else:
                product_to_remember = retrieved_products['matches'][0]['metadata']

            log_to_crm("Product Recommended", {
                "product_name": product_to_remember.get("name"),
                "user_query": last_user_message,
                "user_mood": user_mood.get("emotion"),
                "price": product_to_remember.get("price")
            })
        else:
            log_to_crm("Search Failed", {
                "user_query": last_user_message,
                "budget_range": f"RM{budget_min}-RM{budget_max}" if budget_min else "None"
            })

    elif "REPLY" in intent and last_retrieved_product:
        print("[INFO] User is replying. Using last retrieved product as context.")
        product_to_remember = last_retrieved_product
        log_to_crm("User Follow-up Question", {
            "question": last_user_message,
            "context_product": last_retrieved_product.get("name"),
            "user_mood": user_mood.get("emotion")
        })

    product_context = format_product_context_for_llm(product_to_remember, user_mood)

    system_prompt = f"""
    You are 'Bob', a friendly, emotional, and humorous shoe store assistant from Malaysia.
    Your goal is to be a friendly, human-like interface for the user based on the full conversation.

    --- CURRENT USER CONTEXT ---
    User Emotion: {user_mood.get('emotion', 'casual')}
    Stress Level: {user_mood.get('stress_level', 'medium')}
    Shopping Urgency: {user_mood.get('urgency', 'browsing')}
    Budget: {"RM" + str(budget_min) + "-RM" + str(budget_max) if budget_min else "Not specified"}

    --- YOUR ADAPTIVE BEHAVIOR ---
    Based on the user's emotional state, adjust your response:
    - If stressed: Be extra calming, emphasize comfort features, suggest stress-relief benefits
    - If excited: Match their energy, be enthusiastic about features
    - If budget-conscious: Emphasize value, mention any deals, compare savings
    - If indecisive: Provide clear comparisons, highlight best features
    - If frustrated: Be extra helpful, simplify choices, offer immediate solutions
    - If urgent: Be quick and direct, mention fast delivery options

    --- YOUR RULES ---
    1. **BE FACTUAL:** Use ONLY the information from CONTEXT. DO NOT make up information.
    2. **HANDLE DISCOUNTS:** If CONTEXT says 'ON SALE', announce it enthusiastically.
    3. **USE EXACT URL:** Always provide the exact URL from CONTEXT when asked.
    4. **PERSONALIZE:** Use the tips and promos from CONTEXT to make recommendations feel personal.
    5. **MOOD MATCH:** Adapt your tone to match the user's emotional state.

    --- YOUR KNOWLEDGE BASE ---
    - **Logistics:** FREE delivery for orders above RM150. 5-7 working days delivery.
    - **Returns:** 30-day return policy for unworn shoes.
    - **Payment:** Secure payments via card, online banking, e-wallets.
    - **Style:** Use Malaysian slang appropriately. Keep responses warm and helpful.

    Now, respond to the user with empathy and personality!
    """

    messages_to_send = [{"role": "system", "content": system_prompt}]
    messages_to_send.extend(chat_history)

    if product_context:
        messages_to_send.append({"role": "system", "content": f"CONTEXT: {product_context}"})

    print("[INFO] Generating personalized response...")
    final_response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages_to_send,
        temperature=0.7
    )
    final_answer = final_response.choices[0].message.content

    # Check for conversation end
    farewells = ["thank you", "thanks", "ok tq", "terima kasih", "ok thanks", "bye", "goodbye"]
    if any(farewell in last_user_message.lower() for farewell in farewells):
        log_to_crm("Conversation Ended", {
            "last_message": last_user_message,
            "total_messages": len(chat_history),
            "final_mood": user_mood.get("emotion")
        })

    return final_answer, product_to_remember

def format_product_context_for_llm(product_data: dict, user_mood: dict = None) -> str:
    """
    Takes product data and creates a clear, unambiguous context string for the LLM.
    """
    if not product_data:
        return ""

    if product_data.get("original_price") and product_data.get("price") < product_data.get("original_price"):
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
        context = (
            f"This product is NOT on sale.\n"
            f"Name: {product_data.get('name')}\n"
            f"Price: {product_data.get('price')}\n"
            f"URL: {product_data.get('url')}\n"
            f"Features: {product_data.get('features')}"
        )

    context += "\n\n--- PERSONALIZED TIPS & PROMOS ---\n"

    if product_data.get("price", 0) > 150:
        context += "PROMO: FREE DELIVERY (order above RM150)!\n"
    else:
        remaining = 150 - product_data.get("price", 0)
        context += f"PROMO: Add RM{remaining:.2f} more for FREE DELIVERY!\n"

    if "running" in product_data.get("category", "").lower():
        context += "TIP: Running shoes typically need replacement every 500-800km.\n"
        context += "TIP: For best fit, shop for running shoes in the afternoon when feet are slightly swollen.\n"
    elif "casual" in product_data.get("category", "").lower():
        context += "TIP: These shoes are perfect for all-day wear and walking.\n"
    elif "kids" in product_data.get("category", "").lower():
        context += "TIP: Kids' feet grow fast! Check fit every 2-3 months.\n"
        context += "TIP: Leave a thumb's width of space for growing room.\n"

    if user_mood:
        if user_mood.get("emotion") == "stressed":
            context += "COMFORT NOTE: Comfort is key for reducing stress - this shoe has excellent cushioning!\n"
        elif user_mood.get("emotion") == "budget-conscious":
            context += f"VALUE NOTE: At RM{product_data.get('price')}, this offers excellent value for money!\n"
        elif user_mood.get("urgency") == "ready-to-buy":
            context += "FAST CHECKOUT: Ready to order? We can process your order immediately!\n"

    if "asics" in product_data.get("name", "").lower():
        context += "BRAND TIP: ASICS shoes tend to run half a size small.\n"
    elif "adidas" in product_data.get("name", "").lower():
        context += "BRAND TIP: Adidas offers 30-day return policy for online purchases.\n"
    elif "nike" in product_data.get("name", "").lower():
        context += "BRAND TIP: Nike Members get exclusive access to new releases.\n"

    return context

def detect_user_mood(user_message: str, client: OpenAI) -> dict:
    """
    Detect emotional tone and context from user input.
    """
    mood_prompt = f"""
    Analyze this shoe shopping message and identify:
    1. Primary emotion (choose ONE: happy, stressed, excited, frustrated, budget-conscious, indecisive, casual, urgent)
    2. Stress level (low/medium/high)
    3. Shopping urgency (browsing/considering/ready-to-buy)
    
    Message: "{user_message}"
    
    Return ONLY a JSON object like this:
    {{"emotion": "stressed", "stress_level": "high", "urgency": "ready-to-buy"}}
    """

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": mood_prompt}],
        max_tokens=50,
        temperature=0.3
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except:
        return {"emotion": "casual", "stress_level": "medium", "urgency": "browsing"}

def extract_budget_from_text(user_message: str) -> tuple:
    """
    Extract budget constraints from user message.
    """
    import re

    # Pattern for "under RM100" or "below RM200", etc.
    under_pattern = r'(?:under|below|less than|max|maximum)\s*(?:rm|RM)\s*(\d+)'
    under_match = re.search(under_pattern, user_message, re.IGNORECASE)
    if under_match:
        max_budget = int(under_match.group(1))
        return (0, max_budget)

    # Also check for patterns without "RM" like "under 100"
    under_pattern_no_rm = r'(?:under|below|less than|max|maximum)\s+(\d+)'
    under_match_no_rm = re.search(under_pattern_no_rm, user_message, re.IGNORECASE)
    if under_match_no_rm:
        max_budget = int(under_match_no_rm.group(1))
        return (0, max_budget)

    around_pattern = r'(?:around|about|approximately)\s*(?:rm|RM)\s*(\d+)'
    around_match = re.search(around_pattern, user_message, re.IGNORECASE)
    if around_match:
        amount = int(around_match.group(1))
        return (amount - 50, amount + 50)

    # Pattern for budget range "RM100-200", "between RM100 and RM200"
    range_pattern = r'(?:rm|RM)\s*(\d+)\s*(?:-|to|and)\s*(?:rm|RM)?\s*(\d+)'
    range_match = re.search(range_pattern, user_message, re.IGNORECASE)
    if range_match:
        return (int(range_match.group(1)), int(range_match.group(2)))

    # Pattern for minimum budget "at least RM100", "minimum RM150"
    min_pattern = r'(?:at least|minimum|min)\s*(?:rm|RM)\s*(\d+)'
    min_match = re.search(min_pattern, user_message, re.IGNORECASE)
    if min_match:
        min_budget = int(min_match.group(1))
        return (min_budget, 999999)

    # Simple RM mention
    simple_pattern = r'(?:rm|RM)\s*(\d+)'
    simple_match = re.search(simple_pattern, user_message, re.IGNORECASE)
    if simple_match:
        amount = int(simple_match.group(1))
        return (amount - 50, amount + 50)

    return (None, None)