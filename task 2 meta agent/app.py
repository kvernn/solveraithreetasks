import streamlit as st
import json
from workflow_generator import generate_workflow, validate_workflow
from streamlit_agraph import agraph, Node, Edge, Config

# Page config
st.set_page_config(page_title="Agentic Flow Builder", page_icon="🤖", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .example-button {
        margin: 5px 0;
    }
    .workflow-node {
        padding: 10px;
        margin: 5px;
        border-radius: 5px;
    }
    .trigger-node {
        background-color: #e3f2fd;
        border: 2px solid #2196f3;
    }
    .action-node {
        background-color: #f3e5f5;
        border: 2px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def create_visual_graph(workflow_json):
    """
    Parses the workflow JSON and creates a visual graph with better styling.
    """
    nodes = []
    edges = []

    if "nodes" in workflow_json:
        for node_data in workflow_json["nodes"]:
            # Different colors for different node types
            if 'Trigger' in node_data['type']:
                color = "#2196f3"  # Blue for triggers
                shape = "diamond"
            elif 'whatsApp' in node_data['type'] or 'telegram' in node_data['type']:
                color = "#25D366"  # WhatsApp green
                shape = "box"
            elif 'email' in node_data['type']:
                color = "#EA4335"  # Gmail red
                shape = "box"
            elif 'slack' in node_data['type']:
                color = "#4A154B"  # Slack purple
                shape = "box"
            elif 'googleSheets' in node_data['type']:
                color = "#0F9D58"  # Google green
                shape = "box"
            else:
                color = "#757575"  # Default gray
                shape = "box"

            nodes.append(Node(
                id=node_data["name"],
                label=node_data["name"],
                shape=shape,
                color=color,
                size=25
            ))

    if "connections" in workflow_json:
        for conn_data in workflow_json["connections"]:
            edges.append(Edge(
                source=conn_data["source"],
                target=conn_data["target"],
                type="CURVE_SMOOTH"
            ))

    config = Config(
        width=800,
        height=400,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False
    )

    return agraph(nodes=nodes, edges=edges, config=config)

def simulate_workflow_execution(workflow_json):
    """
    Simulate workflow execution for testing
    """
    execution_log = []

    # Find trigger nodes
    trigger_nodes = [n for n in workflow_json.get('nodes', [])
                     if 'Trigger' in n.get('type', '')]

    for trigger in trigger_nodes:
        execution_log.append(f"🟢 **TRIGGER**: {trigger['name']} activated")

        if trigger['type'] == 'n8n-nodes-base.scheduleTrigger':
            cron = trigger['parameters'].get('cronExpression', 'Not set')
            execution_log.append(f"   ⏰ Schedule: {cron}")
        elif trigger['type'] == 'n8n-nodes-base.jotformTrigger':
            execution_log.append(f"   📝 Form submission received")

        # Find connected nodes
        connections = [c for c in workflow_json.get('connections', [])
                       if c['source'] == trigger['name']]

        for conn in connections:
            target_node = next((n for n in workflow_json['nodes']
                                if n['name'] == conn['target']), None)
            if target_node:
                if target_node['type'] == 'n8n-nodes-base.whatsApp':
                    phone = target_node['parameters'].get('phoneNumber', '[NO PHONE]')
                    msg = target_node['parameters'].get('message', '[NO MESSAGE]')
                    execution_log.append(f"📱 **WhatsApp** → {phone}")
                    execution_log.append(f"   Message: \"{msg[:50]}...\"" if len(msg) > 50 else f"   Message: \"{msg}\"")

                elif target_node['type'] == 'n8n-nodes-base.sendEmail':
                    recipient = target_node['parameters'].get('recipient', '[NO RECIPIENT]')
                    subject = target_node['parameters'].get('subject', '[NO SUBJECT]')
                    execution_log.append(f"📧 **Email** → {recipient}")
                    execution_log.append(f"   Subject: \"{subject}\"")

                elif target_node['type'] == 'n8n-nodes-base.slack':
                    channel = target_node['parameters'].get('channel', '[NO CHANNEL]')
                    msg = target_node['parameters'].get('message', '[NO MESSAGE]')
                    execution_log.append(f"💬 **Slack** → {channel}")
                    execution_log.append(f"   Message: \"{msg[:50]}...\"" if len(msg) > 50 else f"   Message: \"{msg}\"")

                elif target_node['type'] == 'n8n-nodes-base.googleSheets':
                    operation = target_node['parameters'].get('operation', 'append')
                    execution_log.append(f"📊 **Google Sheets** → {operation} data")

                elif target_node['type'] == 'n8n-nodes-base.telegram':
                    chat_id = target_node['parameters'].get('chatId', '[NO CHAT ID]')
                    msg = target_node['parameters'].get('message', '[NO MESSAGE]')
                    execution_log.append(f"✈️ **Telegram** → {chat_id}")
                    execution_log.append(f"   Message: \"{msg[:50]}...\"" if len(msg) > 50 else f"   Message: \"{msg}\"")

    return execution_log

# Main app
st.title("🤖 Agentic AI Flow Builder")
st.write("Describe the automation you want to build in plain English, and I'll create a workflow for you!")

# Initialize Session State
if "summary" not in st.session_state:
    st.session_state.summary = None
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "errors" not in st.session_state:
    st.session_state.errors = []
if "warnings" not in st.session_state:
    st.session_state.warnings = []

# Main input area
col1, col2 = st.columns([4, 1])

with col1:
    default_text = st.session_state.get('example_text', '')
    if default_text and 'user_query' not in st.session_state:
        st.session_state.user_query = default_text

    user_query = st.text_area(
        "Your Automation Request:",
        height=100,
        placeholder="e.g., When a Jotform is submitted, send a WhatsApp to +123 and an email to my admin.",
        value=st.session_state.get('user_query', default_text)
    )

    st.session_state.user_query = user_query

    if 'example_text' in st.session_state:
        del st.session_state.example_text

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacer
    generate_button = st.button("🚀 Generate Workflow", type="primary", use_container_width=True)

# Generate workflow
if generate_button:
    if user_query:
        with st.spinner("🤖 The meta-agent is analyzing your request and building the workflow..."):
            summary, workflow, errors, warnings = generate_workflow(user_query)
            st.session_state.summary = summary
            st.session_state.workflow = workflow
            st.session_state.errors = errors
            st.session_state.warnings = warnings
            st.success("✅ Workflow generated successfully!")
    else:
        st.warning("⚠️ Please enter a description of the workflow you want to build.")

# Display validation results
if st.session_state.errors:
    st.error("❌ **Workflow Errors:**")
    for error in st.session_state.errors:
        st.error(f"• {error}")

if st.session_state.warnings:
    st.warning("⚠️ **Workflow Warnings:**")
    for warning in st.session_state.warnings:
        st.warning(f"• {warning}")

# Display the outputs in tabs
if st.session_state.summary and st.session_state.workflow:
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🎨 Visual Workflow", "🧪 Test Run", "💾 Export"])

    with tab1:
        st.subheader("✅ Workflow Summary")
        for i, step in enumerate(st.session_state.summary, 1):
            st.write(f"{i}. {step}")

    with tab2:
        st.subheader("✨ Visual Workflow")
        create_visual_graph(st.session_state.workflow)

        # Node details
        with st.expander("📊 Node Details"):
            for node in st.session_state.workflow.get('nodes', []):
                node_type = "Trigger" if "Trigger" in node['type'] else "Action"
                st.markdown(f"**{node['name']}** ({node_type})")
                st.json(node['parameters'])

    with tab3:
        st.subheader("🧪 Workflow Test Simulation")
        st.info("This is a simulation of how your workflow would execute:")

        if st.button("▶️ Run Simulation"):
            execution_log = simulate_workflow_execution(st.session_state.workflow)
            for log in execution_log:
                if log.startswith("🟢"):
                    st.success(log)
                elif any(emoji in log for emoji in ["📱", "📧", "💬", "📊", "✈️"]):
                    st.info(log)
                else:
                    st.write(log)

    with tab4:
        st.subheader("💾 Export Options")

        col1, col2 = st.columns(2)

        with col1:
            # n8n JSON export
            st.download_button(
                label="⬇️ Download n8n Workflow",
                data=json.dumps(st.session_state.workflow, indent=2),
                file_name="workflow.n8n.json",
                mime="application/json",
                help="Import this file directly into n8n"
            )

        with col2:
            # Human-readable export
            readable_export = {
                "summary": st.session_state.summary,
                "workflow": st.session_state.workflow,
                "metadata": {
                    "created_with": "Agentic AI Flow Builder",
                    "query": user_query
                }
            }
            st.download_button(
                label="📄 Download Full Report",
                data=json.dumps(readable_export, indent=2),
                file_name="workflow_report.json",
                mime="application/json",
                help="Complete workflow with summary and metadata"
            )

        # Show JSON preview
        with st.expander("👁️ Preview n8n JSON"):
            st.json(st.session_state.workflow)

# Footer
st.markdown("---")