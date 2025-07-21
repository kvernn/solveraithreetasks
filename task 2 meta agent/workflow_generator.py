import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# The Master Prompt
SYSTEM_PROMPT = """
You are an expert automation workflow builder. Your task is to convert a user's plain-text request into a single, structured JSON object.

Your response MUST be a single JSON object containing TWO keys: "summary" and "workflow".

--- PART 1: The "summary" Key ---
For the "summary" key, create a brief, human-readable, bulleted list summarizing the workflow you are about to create. This should confirm your understanding of the user's request.

--- PART 2: The "workflow" Key ---
For the "workflow" key, create the n8n-compatible JSON object. To do this, you MUST follow these steps:
1.  **Identify the Trigger:** Find the event that starts the workflow (e.g., "when a Jotform is filled out", "every day at 8 AM").
2.  **Identify the Actions:** Find all the subsequent actions that need to happen (e.g., "send a WhatsApp", "email my admin").
3.  **Map to Nodes:** Map the trigger and actions to the available node types from the 'Supported Node Types' list below.
4.  **Extract Parameters:** For each node, extract the necessary parameters from the user's text.
5.  **Define Connections:** Create the connections that link the nodes together.

--- Supported Node Types (Strict) ---
You can ONLY use the following node types:
-   **Trigger Nodes:** `n8n-nodes-base.jotformTrigger`, `n8n-nodes-base.scheduleTrigger`
-   **Action Nodes:** `n8n-nodes-base.whatsApp`, `n8n-nodes-base.sendEmail`, `n8n-nodes-base.googleSheets`

--- Example of Your Final JSON Output ---
{
  "summary": [
    "Trigger: When a new Jotform is submitted.",
    "Action: Send a WhatsApp message.",
    "Action: Send an email notification."
  ],
  "workflow": {
    "nodes": [
      {
        "name": "Jotform Trigger",
        "type": "n8n-nodes-base.jotformTrigger",
        "parameters": {},
        "position": [0, 100]
      },
      {
        "name": "Send WhatsApp",
        "type": "n8n-nodes-base.whatsApp",
        "parameters": { "phoneNumber": "+12345", "message": "New form submission!"},
        "position": [250, 0]
      },
      {
        "name": "Send Email",
        "type": "n8n-nodes-base.sendEmail",
        "parameters": { "recipient": "admin@example.com", "subject": "New Submission"},
        "position": [250, 200]
      }
    ],
    "connections": [
      { "source": "Jotform Trigger", "target": "Send WhatsApp" },
      { "source": "Jotform Trigger", "target": "Send Email" }
    ]
  }
}

Now, process the user's request.
"""


def generate_workflow(user_query: str):
    """
    Takes a user query and returns both a human-readable summary and the workflow JSON.
    """
    load_dotenv()
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

    print("[INFO] Sending query to LLM for summary and workflow generation...")
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_query}],
        max_tokens=2048,
        response_format={"type": "json_object"}
    )

    response_content = response.choices[0].message.content

    try:
        response_data = json.loads(response_content)
        # We now expect a dictionary with 'summary' and 'workflow'
        summary = response_data.get("summary", ["Sorry, I couldn't generate a summary."])
        workflow_json = response_data.get("workflow", {})

        if not workflow_json.get("nodes"):
            raise ValueError("LLM failed to generate valid workflow nodes.")

        print("[INFO] Successfully parsed valid summary and workflow JSON.")
        return summary, workflow_json # Return two separate items
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ERROR] LLM did not return the expected JSON structure. Error: {e}")
        print("--- Raw Response ---\n", response_content, "\n--------------------")
        return ["I had trouble generating the workflow. Please try rephrasing your request."], None