import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

# System Prompt
SYSTEM_PROMPT = """
CRITICAL: Return ONLY valid JSON without any markdown formatting or code blocks. Do not wrap your response in ```json or any other markers.

IMPORTANT: Do NOT use n8n expression syntax like {{$node[...].json}}. Instead, use placeholder values like "[FORM_DATA]", "[PHONE_FROM_FORM]", etc.

You are an expert automation workflow builder. Your task is to convert a user's plain-text request into a single, structured JSON object.

Your response MUST be a single JSON object containing TWO keys: "summary" and "workflow".

--- PART 1: The "summary" Key ---
Create a clear, step-by-step summary of the workflow:
- Start with the trigger event
- List each action in order
- Include key parameters (phone numbers, emails, etc.)

--- PART 2: The "workflow" Key ---
Create the n8n-compatible JSON following these rules:

1. **Multiple Triggers**: If the user mentions multiple trigger conditions, create separate trigger nodes
2. **Parallel Actions**: Actions that should happen simultaneously connect to the same source
3. **Sequential Actions**: Use intermediate nodes if actions must happen in order
4. **Smart Defaults**: If parameters are missing, use reasonable placeholders like "[PHONE_NUMBER]"
5. **Time Formats**: For scheduleTrigger, use cron format (e.g., "0 9 * * *" for 9 AM daily)

--- Supported Node Types (Extended) ---
You can ONLY use the following node types:

**Trigger Nodes:**
- `n8n-nodes-base.jotformTrigger` - When a Jotform is submitted
- `n8n-nodes-base.scheduleTrigger` - Time-based triggers (daily, hourly, etc.)
- `n8n-nodes-base.webhookTrigger` - When webhook/API receives data
- `n8n-nodes-base.crmTrigger` - When CRM record is created/updated
- `n8n-nodes-base.emailTrigger` - When email is received

**Action Nodes:**
- `n8n-nodes-base.whatsApp` - Send WhatsApp message
- `n8n-nodes-base.sendEmail` - Send email
- `n8n-nodes-base.googleSheets` - Add/update Google Sheets
- `n8n-nodes-base.httpRequest` - Make API calls
- `n8n-nodes-base.slack` - Send Slack message
- `n8n-nodes-base.crm` - Update CRM records
- `n8n-nodes-base.telegram` - Send Telegram message
- `n8n-nodes-base.function` - Execute custom code/conditions
- `n8n-nodes-base.wait` - Wait/delay before next action

--- Parameter Extraction Guidelines ---
- Phone numbers: Look for patterns like +1234567890, (123) 456-7890
- Emails: Extract anything with @ symbol
- Times: Convert "9 AM" to "0 9 * * *", "every hour" to "0 * * * *"
- Messages: Use exact quotes if provided, otherwise create descriptive placeholders
- Channels: For Slack/Telegram, look for #channel-name patterns

--- Node Parameters ---
Each node type requires specific parameters:

**scheduleTrigger**: 
- cronExpression: Use standard cron format
- timezone: Default to "UTC" if not specified

**whatsApp/telegram**:
- phoneNumber/chatId: Required
- message: The message content

**sendEmail**:
- recipient: Email address
- subject: Email subject
- body: Email content

**slack**:
- channel: Channel name (with or without #)
- message: Message content

**googleSheets**:
- sheetId: Use placeholder "[SHEET_ID]" if not provided
- operation: "append" or "update"
- data: The data to add/update

**function**:
- jsCode: JavaScript code to execute
- Use for: Conditional logic, data transformation, complex decisions

**wait**:
- amount: Number of time units to wait
- unit: "seconds", "minutes", "hours", "days"

--- Timing and Delays ---
- For "after X hours" conditions: Use function node with time checks
- For "wait X hours then do Y": Use wait node between actions
- For recurring checks: Use separate workflow with scheduleTrigger

--- Example Output ---
{
  "summary": [
    "Trigger: Every day at 9:00 AM",
    "Action 1: Send WhatsApp to +1234567890 with daily reminder",
    "Action 2: Update Google Sheets with timestamp",
    "Action 3: Send Slack notification to #general channel"
  ],
  "workflow": {
    "nodes": [
      {
        "name": "Daily Schedule",
        "type": "n8n-nodes-base.scheduleTrigger",
        "parameters": {
          "cronExpression": "0 9 * * *",
          "timezone": "UTC"
        },
        "position": [0, 100]
      },
      {
        "name": "WhatsApp Reminder",
        "type": "n8n-nodes-base.whatsApp",
        "parameters": {
          "phoneNumber": "+1234567890",
          "message": "Good morning! Time for your daily standup."
        },
        "position": [250, 0]
      }
    ],
    "connections": [
      {"source": "Daily Schedule", "target": "WhatsApp Reminder"}
    ]
  }
}

Now, process the user's request and create a comprehensive workflow.
"""

def extract_contact_info(text):
    """
    Extract phone numbers, emails, and other identifiers from text
    """
    phone_patterns = [
        # US format
        r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        # International format
        r'\+([0-9]{1,3})\s?([0-9]{4,14})',
        # General format
        r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}'
    ]

    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                phone = ''.join(match)
            else:
                phone = match
            if len(phone) >= 10:
                phones.append(phone)

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)

    # Slack/Telegram channels
    channel_pattern = r'#([a-zA-Z0-9-_]+)'
    channels = re.findall(channel_pattern, text)

    # Time patterns
    time_pattern = r'(\d{1,2})\s*(AM|PM|am|pm)'
    times = re.findall(time_pattern, text.upper())

    return {
        'phones': list(set(phones)),
        'emails': list(set(emails)),
        'channels': channels,
        'times': times
    }

def convert_time_to_cron(time_str):
    """
    Convert natural language time to cron expression
    """
    time_str_lower = time_str.lower()

    # Common patterns
    if 'every hour' in time_str_lower:
        return "0 * * * *"
    elif 'every day' in time_str_lower or 'daily' in time_str_lower:
        time_match = re.search(r'(\d{1,2})\s*(am|pm)', time_str_lower)
        if time_match:
            hour = int(time_match.group(1))
            if time_match.group(2) == 'pm' and hour != 12:
                hour += 12
            elif time_match.group(2) == 'am' and hour == 12:
                hour = 0
            return f"0 {hour} * * *"
        return "0 9 * * *"
    elif 'every week' in time_str_lower or 'weekly' in time_str_lower:
        return "0 9 * * 1"
    elif 'every month' in time_str_lower or 'monthly' in time_str_lower:
        return "0 9 1 * *"
    else:
        return "0 9 * * *"

def enhance_workflow_with_extracted_data(user_query, workflow_json):
    """
    Post-process to ensure all parameters are captured
    """
    extracted = extract_contact_info(user_query)

    phone_index = 0
    email_index = 0
    channel_index = 0

    # Update nodes with extracted data
    for node in workflow_json.get('nodes', []):
        # WhatsApp nodes
        if node['type'] == 'n8n-nodes-base.whatsApp':
            if not node['parameters'].get('phoneNumber') or '[PHONE' in node['parameters'].get('phoneNumber', ''):
                if phone_index < len(extracted['phones']):
                    node['parameters']['phoneNumber'] = '+' + extracted['phones'][phone_index].replace('-', '').replace(' ', '')
                    phone_index += 1

        # Email nodes
        elif node['type'] == 'n8n-nodes-base.sendEmail':
            if not node['parameters'].get('recipient') or '[EMAIL' in node['parameters'].get('recipient', ''):
                if email_index < len(extracted['emails']):
                    node['parameters']['recipient'] = extracted['emails'][email_index]
                    email_index += 1

        # Slack nodes
        elif node['type'] == 'n8n-nodes-base.slack':
            if not node['parameters'].get('channel') or '[CHANNEL' in node['parameters'].get('channel', ''):
                if channel_index < len(extracted['channels']):
                    node['parameters']['channel'] = '#' + extracted['channels'][channel_index]
                    channel_index += 1

        # Schedule nodes - enhance cron expression
        elif node['type'] == 'n8n-nodes-base.scheduleTrigger':
            if 'cronExpression' in node['parameters']:
                # If it's a placeholder, try to extract from user query
                if node['parameters']['cronExpression'] == "0 9 * * *":  # Default
                    cron = convert_time_to_cron(user_query)
                    node['parameters']['cronExpression'] = cron

    return workflow_json

def validate_workflow(workflow_json):
    """
    Validate the workflow structure
    """
    errors = []
    warnings = []

    # Check for required keys
    if not workflow_json.get('nodes'):
        errors.append("No nodes found in workflow")
        return errors, warnings

    if not workflow_json.get('connections'):
        warnings.append("No connections defined - workflow has isolated nodes")

    # Check for at least one trigger
    trigger_nodes = [n for n in workflow_json.get('nodes', [])
                     if 'Trigger' in n.get('type', '')]
    if not trigger_nodes:
        errors.append("Workflow must have at least one trigger node")

    # Check all connections reference existing nodes
    node_names = {n['name'] for n in workflow_json.get('nodes', [])}
    for conn in workflow_json.get('connections', []):
        if conn['source'] not in node_names:
            errors.append(f"Connection source '{conn['source']}' not found")
        if conn['target'] not in node_names:
            errors.append(f"Connection target '{conn['target']}' not found")

    # Check for required parameters
    for node in workflow_json.get('nodes', []):
        if node['type'] == 'n8n-nodes-base.whatsApp':
            if not node.get('parameters', {}).get('phoneNumber'):
                warnings.append(f"WhatsApp node '{node['name']}' missing phone number")
        elif node['type'] == 'n8n-nodes-base.sendEmail':
            if not node.get('parameters', {}).get('recipient'):
                warnings.append(f"Email node '{node['name']}' missing recipient")

    return errors, warnings

def generate_workflow(user_query: str):
    """
    Takes a user query and returns both a human-readable summary and the workflow JSON
    """
    load_dotenv()
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

    print("[INFO] Sending query to LLM for summary and workflow generation...")
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_query}],
        max_tokens=2048,
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    response_content = response.choices[0].message.content

    try:
        # Clean up the response
        cleaned_content = response_content.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.startswith('```'):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]

        # Parse the cleaned JSON
        response_data = json.loads(cleaned_content.strip())
        summary = response_data.get("summary", ["Sorry, I couldn't generate a summary."])
        workflow_json = response_data.get("workflow", {})

        if not workflow_json.get("nodes"):
            raise ValueError("LLM failed to generate valid workflow nodes.")

        workflow_json = enhance_workflow_with_extracted_data(user_query, workflow_json)

        errors, warnings = validate_workflow(workflow_json)

        print("[INFO] Successfully parsed and enhanced workflow JSON.")
        return summary, workflow_json, errors, warnings

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ERROR] LLM did not return the expected JSON structure. Error: {e}")
        print("--- Raw Response ---\n", response_content, "\n--------------------")
        return ["I had trouble generating the workflow. Please try rephrasing your request."], None, ["Failed to generate workflow"], []

# Test functions for debugging
if __name__ == "__main__":
    # Test parameter extraction
    test_text = "Send WhatsApp to +1234567890 and email admin@company.com at 3 PM daily #general"
    extracted = extract_contact_info(test_text)
    print("Extracted:", extracted)

    # Test cron conversion
    print("Cron for '9 AM daily':", convert_time_to_cron("9 AM daily"))
    print("Cron for 'every hour':", convert_time_to_cron("every hour"))